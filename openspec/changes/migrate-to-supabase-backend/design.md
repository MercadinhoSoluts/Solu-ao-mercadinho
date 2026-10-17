## Context

See `proposal.md` for motivation and scope. The application is a Python Reflex server with state and handlers in `bipsystem/bipsystem.py`; `bipsystem/auth_client.py` currently sends HTTP requests to Xano. The existing UI persists employees, products, and stock through those calls, while Preços is in-memory only. The Cashier view is a static table/total and Reports is a set of navigation cards, so neither has a checkout or reporting data flow to migrate.

The current Xano artifacts are not a consistent migration contract: runtime code submits `tipo`, `marca`, `peso`, and `codigo_de_barra` to `/produtos`, while the exported Xano definitions split `produtos` and `codigobarra` and expose different field names. Inventory currently groups incoming units by product and expiry, retaining the first batch label. These differences must be included in a pre-cutover reconciliation report; records that cannot be mapped unambiguously block cutover rather than being silently discarded.

## Goals / Non-Goals

**Goals:**
- Define a small normalized schema for identity, catalog, stock, movement audit, and price history based on active UI workflows.
- Keep role checks in RLS and trusted server operations, and make the application usable with Supabase Auth sessions after reload.
- Provide an ordered, testable Xano data migration and cutover path.

**Non-Goals:**
- Implement or model checkout, sales, cash sessions, alerts, or financial reports in this change; the current pages do not submit or query those records.
- Add product categories, multiple barcodes per product, or new UI fields that the current application does not use.
- Expose the Supabase service-role key to the Reflex process or browser.

## Decisions

### Use the Python Supabase client from the Reflex server

The UI and event handlers are Python Reflex, not a handwritten browser application. Use the supported Python Supabase client in server-side handlers rather than adding `@supabase/supabase-js` to generated frontend code. Initialize it from `SUPABASE_URL` and `SUPABASE_ANON_KEY`; attach the user's access token for RLS-scoped requests. The Auth service credential is confined to the employee-management Edge Function and its secret store. Alternatives considered: browser-side supabase-js would duplicate session handling and expose access tokens to client state; direct PostgreSQL access from Reflex would bypass the PostgREST/RLS boundary.

### Keep employee Auth administration in one trusted Edge Function

Supabase Auth users are the credential source of truth. Use an `auth.users` trigger to create and synchronize a `public.profiles` row. Use a narrowly scoped Edge Function for employee list/create/update/delete because Auth Admin operations require privileged credentials; it validates the caller's JWT, reads the caller's role from `profiles`, applies the owner/manager restrictions, then invokes Auth Admin. Never accept caller identity or role from a request body. Profile RLS remains enabled, and employee UI operations continue to display only safe account fields.

### Model only entities backed by current workflows

Use UUID primary keys and UTC timestamps. The initial application schema is:

| Table | Fields and relationships | Constraints and indexes | Access |
|---|---|---|---|
| `profiles` | `id uuid` PK/FK to `auth.users.id`; `email text` synchronized from Auth for employee search; `name text`; `role app_role`; `is_active boolean`; `created_at`, `updated_at timestamptz` | Required name/email/role; normalized unique email; role in `operator`, `manager`, `owner`; index role and normalized email | RLS enabled. User can read own profile; managers/owners can read employee directory. Profile writes go through the trusted employee function. |
| `products` | `id uuid`; `product_type text`; `brand text`; `weight_grams numeric`; `barcode text`; `is_active boolean`; `created_by uuid` FK to profiles; timestamps | Required type/brand/weight; positive weight; unique non-empty barcode; indexes on barcode and searchable normalized type/brand | RLS enabled. Authenticated users may read active products; operator/manager/owner may insert; no edit/delete policy until the UI supports those actions. |
| `stock_lots` | `id uuid`; `product_id uuid` FK to products; `batch_label text`; `units integer`; `expires_on date`; `created_by uuid` FK to profiles; timestamps | Positive units, required expiry and product; unique `(product_id, expires_on)` to preserve existing application grouping; indexes `(product_id, expires_on)` and expiry | RLS enabled. Authenticated users may read; receiving is performed atomically through a database function for all three roles; correction function is manager/owner only. |
| `inventory_movements` | `id uuid`; `stock_lot_id uuid` FK to stock_lots; `units_delta integer`; `movement_type` (`receipt`, `correction`); `reason text` for corrections; `created_by uuid` FK to profiles; `created_at timestamptz` | Non-zero delta; indexes on lot and creation time; append-only, with no client update/delete policy | RLS enabled. Read access follows inventory visibility; inserts are made only inside validated database functions. |
| `product_price_history` | `id uuid`; `product_id uuid` FK to products; `price_cents bigint`; `created_by uuid` FK to profiles; `created_at timestamptz` | Positive price; indexes on `(product_id, created_at desc, id desc)` and product; rows are append-only | RLS enabled. Read and insert follow the current Prices route's owner/manager restriction. |

The active product display name is derived from type, brand, and grams. `profiles.email` is a synchronized directory projection of `auth.users.email`, not an authentication credential. A database trigger updates the projection when Auth email changes. `product_price_history` is the sole source of pricing records; a latest-price view/query selects one record per product by timestamp and stable ID. Monetary values are stored as integer cents to avoid floating-point rounding.

The current stock grouping merges entries for the same product and expiry, even if a later batch label differs. Keep that observable behavior in the initial migration and retain the original label; report this limitation for explicit future product/lot workflow decisions rather than changing it during backend migration.

### Use database functions for stock balance mutations

Receiving and manager/owner corrections update `stock_lots.units` and append `inventory_movements` in one transaction. Functions validate `auth.uid()` and the role from `profiles`; clients cannot update lot balances or insert movement rows directly. A per-lot row lock/atomic upsert prevents concurrent receipts from losing units. Alternatives considered: direct table updates are simpler but permit untracked balance changes and race conditions.

### Apply the guide's operation matrix without inventing missing screens

All authenticated roles can read active products and stock needed for existing workflows. Operators may create products and receive stock, and can use the product, conference, and stock routes needed for those tasks. Only managers and owners may correct stock. Employee directory/provisioning follows the explicit rule confirmed for this change: managers may manage operator accounts only; owners may assign any supported role. Prices remains restricted to owner/manager as it is today. Sales cancellation stays deferred with the rest of checkout because no sales UI or current sales API client exists.

### Start Supabase empty and retain Xano as an unsynchronized archive

Do not import or dual-write Xano users, products, stock, or prices. Provision the initial Supabase owner through a documented, one-time trusted bootstrap procedure, then require that owner to create active accounts through the employee workflow. Products and stock begin empty and must be re-entered by authorized users; prices are added only after their products exist. Keep Xano and its data unchanged for historical lookup, but do not describe it as a complete rollback target after new Supabase writes begin: reversing application configuration would omit those new writes. Do not present Xano records as if they were in Supabase or silently fall back to Xano. The user-selected empty-dataset decision removes the need for a historical export/import, while the existing schema mismatches remain documented for any future migration.

### Use the explicitly linked project for migration verification

Docker Desktop was installed, but WSL is absent and its installation requires administrator privileges. The user explicitly chose to apply migrations to the linked Supabase project without isolated local validation. Treat that linked project as the approved validation/deployment target, inspect its existing schemas before any DDL, and do not claim local migration verification. The dashboard's `public` schema visualizer currently reports no tables. Continue to keep every migration in version control and apply it through a tracked migration workflow; do not create tables manually in the dashboard.

## Risks / Trade-offs

- [Existing employees, products, and stock are not available in the new application after cutover] → Confirm the owner accepts an empty Supabase start; preserve Xano read-only and require authorized re-entry of the required catalog and stock before operations resume.
- [Xano schemas differ from runtime contracts] → Keep this mismatch documented; do not import or infer mappings under the selected fresh-start decision.
- [Auth trigger and employee Edge Function drift from `profiles`] → Test create, email change, role change, deactivation, and deletion against Auth and Postgres together.
- [The selected role matrix intentionally broadens current operator access to product/stock routes] → Protect every route and operation with server checks and RLS; add role-matrix tests before enabling the routes.
- [Price history changes the persistence model from the current in-memory upsert] → The UI continues to show only the current price; verify the latest-record query and timestamp ordering in tests.
- [Supabase credentials are unavailable in this workspace] → Complete migrations and local/CI tests against Supabase CLI local services; live project configuration remains an explicit deployment prerequisite.

## Migration Plan

1. Add local Supabase CLI configuration and ordered migrations for `profiles`, `products`, `stock_lots`, `inventory_movements`, and `product_price_history`, including constraints, indexes, helper functions, triggers, and explicit RLS policies.
2. Validate the schema and role policies in a clean local Supabase project, including direct REST/RPC attempts by anonymous, operator, manager, and owner identities.
3. Add `.env.example` with variable names only; install/configure the Python client and the employee-management Edge Function without adding live credentials to Git.
4. Bootstrap the first owner in the empty Supabase project through a one-time trusted operation, then connect authentication and employee operations, product registration/lookup, stock receiving/query, and Prices, keeping each workflow independently testable.
5. Verify that the application starts with empty employee, product, stock, and price datasets; verify no page reads from Xano or local mocks after its Supabase workflow is enabled.
6. Cut over to Supabase only after acceptance tests pass. Keep Xano and its existing data unchanged for historical lookup. Document that returning application writes to Xano after Supabase writes begin is not a lossless rollback.

Rollback before cutover is to leave the current Xano runtime untouched. After cutover, do not claim rollback to Xano preserves new data; first export/reconcile Supabase writes or keep the application in maintenance mode until a recovery plan is approved.

## Open Questions

- Which authorized Supabase project and non-production credentials will be available for migration dry-runs and deployment? No credentials are required to complete this change's source artifacts.
