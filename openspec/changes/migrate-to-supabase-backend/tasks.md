## 1. Supabase project and schema

- [x] 1.1 Initialize and link the Supabase CLI project; verify the authenticated project reference and inspect the linked public schema. Docker/WSL local isolation is unavailable and the user explicitly approved using the linked project without isolated local validation.
- [x] 1.2 Document and verify the approved empty-dataset start: no Xano users/products/stock/prices are imported, Xano remains unchanged for historical lookup, and the application does not silently fall back to Xano.
- [x] 1.3 Create versioned migrations for profiles, products, stock lots, inventory movements, and price history with UUID keys, foreign keys, constraints, timestamps, and indexes; verify migrations against the explicitly linked Supabase project after reviewing its existing schemas.
- [x] 1.4 Add profile synchronization, current-price query/view, and atomic stock receipt/correction functions; verify profile synchronization and stock movement atomicity with database tests.
- [x] 1.5 Enable RLS on every application table and implement policies for anonymous, operator, manager, and owner roles; verify both allowed and denied reads/writes through the approved linked-project role simulations and REST/RPC checks.

## 2. Supabase Auth and employee management

- [x] 2.1 Add `.env.example` with public project URL/key and server-only function configuration names; verify it contains no real credentials and no privileged key is included in the browser build.
- [x] 2.2 Add the server-side Python Supabase client and request-scoped authenticated identity handling; verify authenticated queries carry the user's JWT and configuration failures are explicit.
- [x] 2.3 Implement the employee-management Edge Function with caller JWT validation, stored-profile role checks, and Auth Admin operations; verify owner, manager, operator, duplicate-email, inactive-profile, and self-delete cases.
- [ ] 2.4 Replace login/session/logout calls with Supabase Auth and profile lookup while preserving route destinations; verify valid/invalid login, reload restoration, expiry, logout, and route authorization for all roles.
- [ ] 2.5 Connect employee list/search/create/edit/delete to Supabase while preserving confirmation UX and optional-password behavior; verify successful and failed actions, case-insensitive email uniqueness, safe feedback, and manager/owner permissions.
- [ ] 2.6 Implement and document a one-time trusted first-owner bootstrap for the empty Supabase project; verify only the configured bootstrap procedure can grant the initial owner role.

## 3. Product catalog and inventory

- [ ] 3.1 Connect product registration and product queries to Supabase, including barcode uniqueness and existing type/brand/weight fields; verify valid creation, duplicate rejection, search/lookup, and empty results.
- [ ] 3.2 Update server route and navigation authorization only as needed for operators to register products and stock, while retaining manager/owner administrative access; verify direct URL and sidebar behavior by role.
- [ ] 3.3 Connect stock receiving and inventory queries to product/lot records and atomic database functions; verify barcode resolution, product/expiry grouping, batch-label retention, quantity updates, and empty inventory behavior.
- [ ] 3.4 Verify concurrent receipts, unauthorized stock corrections, and movement audit consistency; prove failed operations leave both stock balances and movement history unchanged.

## 4. Product pricing

- [ ] 4.1 Replace Prices mocks with Supabase product barcode lookup and joined product details without adding product creation fields; verify known and unknown barcode behavior.
- [ ] 4.2 Persist every price change as immutable history and query the latest price per product; verify precise cent conversion, timestamp ordering, and preservation of previous prices.
- [ ] 4.3 Connect price search by barcode, product name, and brand under the existing owner/manager route permission; verify current results and successful empty search behavior.

## 5. Data migration and application behavior

- [ ] 5.1 Verify and document the empty initial datasets for profiles, products, stock, and prices, the manual re-entry prerequisite, and the limitation that new Supabase writes are not present in the preserved Xano archive.
- [ ] 5.2 Add explicit loading, success, empty, and action-specific error handling to connected views; verify initial loads and reloads never display stale action feedback and empty query results are not errors.
- [ ] 5.3 Remove Xano runtime calls only after the corresponding Supabase flow and migration checks pass; verify no runtime path silently falls back to Xano or mock data.
- [ ] 5.4 Preserve all current visual layouts and navigation except operator access required by the approved matrix; verify route/build output and focused UI regression checks.

## 6. Integration and cutover validation

- [ ] 6.1 Run unit tests for Auth, employee management, product catalog, inventory, and pricing; verify role-specific allow/deny cases and safe failures.
- [ ] 6.2 Run a clean Supabase migration and complete end-to-end tests for login, navigation, employee CRUD, product registration/lookup, stock receiving/query, and price history/search.
- [ ] 6.3 Verify security boundaries by inspecting browser artifacts and logs for access tokens, passwords, service-role keys, and database secrets; verify direct RLS bypass attempts are denied.
- [ ] 6.4 Document deployment configuration, first-owner bootstrap, empty-dataset operational prerequisites, cutover gates, and non-lossless rollback implications; verify production cutover is blocked until all required checks are approved.
