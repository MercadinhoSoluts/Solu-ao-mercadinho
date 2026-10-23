## 1. Supabase project and schema

- [x] 1.1 Initialize and link the Supabase CLI project; verify the authenticated project reference and inspect the linked public schema. Docker/WSL local isolation is unavailable and the user explicitly approved using the linked project without isolated local validation.
- [x] 1.2 Inspect the available Xano schemas and Supabase baseline; document that record exports are unavailable, data migration is pending, Xano remains unchanged, and the application does not fall back to Xano.
- [x] 1.3 Create versioned migrations for profiles, products, stock lots, inventory movements, and price history with UUID keys, foreign keys, constraints, timestamps, and indexes; verify migrations against the explicitly linked Supabase project after reviewing its existing schemas.
- [x] 1.4 Add profile synchronization, current-price query/view, and atomic stock receipt/correction functions; verify profile synchronization and stock movement atomicity with database tests.
- [x] 1.5 Enable RLS on every application table and implement policies for anonymous, operator, manager, and owner roles; verify both allowed and denied reads/writes through the approved linked-project role simulations and REST/RPC checks.

## 2. Supabase Auth and employee management

- [x] 2.1 Add `.env.example` with public project URL/key and server-only function configuration names; verify it contains no real credentials and no privileged key is included in the browser build.
- [x] 2.2 Add the server-side Python Supabase client and request-scoped authenticated identity handling; verify authenticated queries carry the user's JWT and configuration failures are explicit.
- [ ] 2.3 Implement the employee-management Edge Function with caller JWT validation, stored-profile role checks, and Auth Admin operations; align manager/owner permissions and run Edge Function tests before deploying the policy update (Deno unavailable in this environment).
- [x] 2.4 Replace login/session/logout calls with Supabase Auth and profile lookup while preserving route destinations; Python tests cover login, invalid/inactive profiles, refresh, expiry, and logout. Full Supabase end-to-end verification remains in 6.2.
- [x] 2.5 Connect employee list/search/create/edit/delete to Supabase while preserving confirmation UX and optional-password behavior; Python tests cover requests and safe feedback. Full Supabase end-to-end verification remains in 6.2.
- [x] 2.6 Document the trusted one-time first-owner bootstrap. The linked project already has an active owner; the documented bootstrap must not be run there.

## 3. Product catalog and inventory

- [x] 3.1 Connect product registration and product queries to Supabase, including barcode uniqueness and existing type/brand/weight fields; Python tests cover creation, duplicate rejection, lookup, and empty results. Full Supabase end-to-end verification remains in 6.2.
- [x] 3.2 Preserve the approved operator access to Products, Conference, and Stock while retaining manager/owner administrative access; verify server-side role checks in the application.
- [x] 3.3 Connect stock receiving and inventory queries to product/lot records and atomic database functions; Python tests cover barcode resolution, grouping, label retention, and quantity updates. Full Supabase end-to-end verification remains in 6.2.
- [ ] 3.4 Verify concurrent receipts, unauthorized stock corrections, and movement audit consistency; prove failed operations leave both stock balances and movement history unchanged.

## 4. Product pricing

- [x] 4.1 Replace Prices mocks with Supabase product barcode lookup and joined product details without adding product creation fields; Python tests cover known and unknown barcode behavior.
- [x] 4.2 Persist every price change as immutable history and query the latest price per product; Python tests cover cent conversion, formatting, filtering, and writes.
- [x] 4.3 Connect price search by barcode, product name, and brand under the manager/owner route permission; Python tests cover results and empty search behavior.

## 5. Data migration and application behavior

- [ ] 5.1 Obtain, reconcile, import, and validate the Xano records. The current linked-project row counts are only a read-only baseline; data migration and cutover remain pending.
- [x] 5.2 Add explicit loading, success, empty, and action-specific error handling to connected views; Python tests cover action feedback and empty results. Full UI end-to-end verification remains in 6.2.
- [x] 5.3 Remove Xano runtime calls from the connected flows; source search confirms there is no application runtime fallback to Xano or mock pricing data.
- [x] 5.4 Preserve all current visual layouts and navigation except the approved operator access; the production frontend export completed successfully without visual component changes.

## 6. Integration and cutover validation

- [ ] 6.1 Run the complete unit-test set, including Edge Function role tests; Python tests pass, but Deno is unavailable and Edge Function tests remain unrun.
- [ ] 6.2 Run a clean Supabase migration and complete end-to-end tests for login, navigation, employee CRUD, product registration/lookup, stock receiving/query, and price history/search. Reconcile/import Xano data before operational cutover.
- [ ] 6.3 Verify security boundaries by inspecting browser artifacts and logs for access tokens, passwords, service-role keys, and database secrets; verify direct RLS bypass attempts are denied.
- [x] 6.4 Document deployment configuration, first-owner bootstrap, Xano export/import procedure, cutover gates, and non-lossless rollback implications; production cutover remains blocked until data import and all required checks are approved.
