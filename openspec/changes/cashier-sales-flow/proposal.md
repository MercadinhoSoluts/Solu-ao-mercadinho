# Cashier sales flow

## Why

The existing cashier page is a visual shell. Operators need to create a
persisted purchase, add real products by barcode, and retain the exact price
applied at inclusion so later catalog price changes cannot rewrite sales
history.

## What changes

- Create purchases and purchase items through authenticated, atomic Supabase
  RPCs, after checking existing migrations for reusable schema.
- Snapshot product identity, quantity, applied unit price in cents, and line
  total when an item is included.
- Recover an open purchase and its persisted items on cashier page load.
- Add, close, and reopen the product-entry card; finalize or cancel a purchase
  without deleting its history or changing inventory.
- Preserve the existing cashier page and its table/total presentation.

## Non-goals

- Payment processing, fiscal documents, refunds, or inventory movements.
- Replacing Supabase authentication or exposing service-role credentials.
- Applying migrations or deploying database functions to the remote project as
  part of local implementation.

## Schema inspection

The checked-in migrations define profiles, products, stock, inventory
movements, and product price history, but no purchase, sale, order, or line
item entities. Product prices are stored as integer cents in
`product_price_history`; `current_product_prices` selects the current value.
The Supabase CLI is unavailable in the implementation environment, so remote
schema and migration status could not be inspected. The incremental migration
must be reviewed and applied by the project operator after verifying the
linked project state.
