## Why

The Reflex application still authenticates and persists employees, products, and stock through Xano, while the Prices screen uses only in-memory mock data. The project documentation now names Supabase as the target architecture, but there are no Supabase migrations, RLS policies, client configuration, or application queries; a versioned migration plan is needed before changing runtime behavior.

## What Changes

- Make Supabase Auth and PostgreSQL the authoritative persistence layer for the current application workflows, with reproducible SQL migrations and RLS enabled on every application table.
- Define and implement a server-side Supabase integration compatible with the Python Reflex application, using public project configuration and the authenticated user's JWT; keep service-role credentials out of the browser and repository.
- Move employee authentication and administration, product catalog/barcode lookup, stock lots/receiving, and Prices from Xano or local mocks to Supabase without redesigning existing screens.
- Preserve price changes as immutable history while the current Prices screen displays the latest price for each product.
- Adopt the Supabase guide's role matrix for product and stock operations: operators may register products and stock entries/adjustments; managers and owners may correct stock and cancel sales. Preserve the existing employee-management restriction that managers may manage operators only, while owners may assign any supported role.
- Start the Supabase application with an empty dataset; do not import Xano users, products, stock, or prices. Keep Xano and its records intact for historical lookup, but do not imply that writes to Supabase are synchronized back to Xano.
- Retain the Xano artifacts and existing Xano OpenSpec change as historical context rather than deleting them.
- Treat Reports and Cashier/PDV as existing visual placeholders only. Do not introduce sales, sale-item, cash-session, alert, or financial-report persistence until those workflows are specified and implemented.
- Define loading, empty, success, and error behavior so initial page loads do not show action feedback.

## Capabilities

### New Capabilities

- `supabase-foundation`: PostgreSQL schema, migrations, RLS, environment configuration, and the server-side Reflex integration contract.
- `authentication-session`: Supabase Auth login, session restoration/lifecycle, and role-based server-side authorization.
- `employee-management`: Profile provisioning and employee search, edit, and deletion under the agreed role rules.
- `product-catalog`: Product creation, listing, and unique barcode lookup.
- `inventory-management`: Product-associated stock lots, receiving, quantity updates, expiry, and inventory queries.
- `product-pricing`: Product barcode lookup, price creation/update with immutable history, and current-price search by barcode, product name, or brand.

### Modified Capabilities

None. The repository has no published main specs under `openspec/specs/`; the existing Xano registration/authentication documents belong to an active historical change and will remain intact.

## Impact

- Application: `bipsystem/bipsystem.py`, `bipsystem/auth_client.py`, and related tests currently call Xano for login, profiles, products, and stock; Prices currently uses local mock state.
- Infrastructure: add Supabase CLI configuration and versioned migrations for the entities justified by current screens; add RLS policies and database tests.
- Configuration/dependencies: add documented Supabase environment variable names in `.env.example` and a Python Supabase client compatible with Reflex. No real credentials are included.
- Data operations: document the empty-dataset cutover, first-owner bootstrap, and rollback limitation; do not remove Xano artifacts or data.
- Scope boundary: Reports and Cashier routes remain visually and behaviorally unchanged because their current contents do not implement persistent report or checkout workflows.
