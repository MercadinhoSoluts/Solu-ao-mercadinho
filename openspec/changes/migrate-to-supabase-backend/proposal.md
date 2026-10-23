## Why

The Reflex application still authenticates and persists employees, products, and stock through Xano, while the Prices screen uses only in-memory mock data. The project documentation now names Supabase as the target architecture, but there are no Supabase migrations, RLS policies, client configuration, or application queries; a versioned migration plan is needed before changing runtime behavior.

## What Changes

- Make Supabase Auth and PostgreSQL the authoritative persistence layer for the current application workflows, with reproducible SQL migrations and RLS enabled on every application table.
- Define and implement a server-side Supabase integration compatible with the Python Reflex application, using public project configuration and the authenticated user's JWT; keep service-role credentials out of the browser and repository.
- Move employee authentication and administration, product catalog/barcode lookup, stock lots/receiving, and Prices from Xano or local mocks to Supabase without redesigning existing screens.
- Preserve price changes as immutable history while the current Prices screen displays the latest price for each product.
- Adopt the approved role matrix for current workflows: operators may access Products, Conference, and Stock to register products and receive stock; managers and owners may correct stock and manage employees with identical role-assignment permissions. Keep Prices restricted to managers and owners. Cashier/PDV and Reports remain visual placeholders.
- Migrate Xano users, products, barcodes, stock balances, and prices before declaring cutover. The available Xano artifacts contain schemas but not data exports, so data migration remains pending; document and validate the export/import procedure without inventing records or implying that Supabase writes synchronize back to Xano.
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
- Data operations: document the pending Xano export/import, first-owner bootstrap, and rollback limitation; do not remove or modify Xano artifacts or data.
- Scope boundary: Reports and Cashier routes remain visually and behaviorally unchanged because their current contents do not implement persistent report or checkout workflows.
