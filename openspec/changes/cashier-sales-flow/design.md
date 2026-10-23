# Design: cashier sales flow

## Existing structures inspected

- `products` uses UUID identifiers, text barcodes, and active flags.
- `product_price_history` stores immutable integer-cent prices.
- `current_product_prices` exposes the latest price, but its underlying
  history is administrator-only under RLS.
- No purchase/sale tables or cashier RPCs exist in the checked-in migrations.
- Existing Supabase operations use the authenticated user's access token and
  database RPCs with `SECURITY DEFINER`; no service-role key is needed.

## Data model

- `purchases`: responsible profile, `open`/`completed`/`cancelled` status,
  opening/closing timestamps, and current exact-cent total. A partial unique
  index allows one open purchase per operator so reload recovery is
  deterministic.
- `purchase_open_requests`: maps each idempotency UUID to its created or
  recovered purchase, including when concurrent starts encounter an already
  open purchase.
- `purchase_items`: purchase/product references plus immutable barcode,
  description, applied unit price in cents, quantity, and line total in cents.
  A unique key on purchase, product, and applied unit price consolidates
  repeated additions at the same price while preserving separate rows if the
  product's price changes during an open purchase.
- `purchase_item_requests`: unique request UUID and payload, used to make a
  repeated network submission idempotent without losing the original applied
  price.

Items are never recalculated from `current_product_prices` after insertion.
An add-item RPC reads the latest valid price and snapshots it in the same
transaction that updates the line and purchase total. All monetary arithmetic
uses `bigint` cents.

## Backend operations

Authenticated, `SECURITY DEFINER` RPCs create or recover an idempotent purchase,
fetch a purchase and its snapshot items, add an item atomically, finalize an
open non-empty purchase, and cancel an open purchase. Each operation validates
the actor and purchase ownership. Direct client writes are not granted.
Cancellation and finalization retain items; neither changes inventory nor
performs payment processing.

## UI state

Reflex state holds the active purchase identifier, item snapshots, total,
entry-card visibility, loading flags, input values, feedback, and confirmation
state. Opening a purchase persists it before routing. Reloading `/caixa`
recovers that purchase from state and Supabase. The existing table columns
remain; only their rows and total become data-backed.

## Remote status

Local migrations are evidence of the checked-in schema only. The Supabase CLI
is not installed, so this change does not claim to inspect or modify the
remote database. No remote migration or function is applied by implementation.
