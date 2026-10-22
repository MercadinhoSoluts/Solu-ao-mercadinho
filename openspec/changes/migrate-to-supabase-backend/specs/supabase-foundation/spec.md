## Purpose

Defines Supabase as the secure, reproducible persistence foundation for the existing Reflex application and its authenticated database operations.

## ADDED Requirements

### Requirement: Application schema is reproducible from versioned migrations
The system SHALL create and evolve application tables, constraints, indexes, functions, triggers, and RLS policies through ordered Supabase SQL migrations that can be applied to a new development project. Every application table exposed through the Supabase API SHALL have RLS enabled.

#### Scenario: New development database is provisioned
- **WHEN** all repository migrations are applied to a clean Supabase development project
- **THEN** the required application schema, constraints, indexes, database functions, and RLS policies are created in dependency order

#### Scenario: Application table is added
- **WHEN** a migration creates a table exposed to application requests
- **THEN** the migration also enables RLS and defines explicit policies before the table is used

### Requirement: Reflex accesses Supabase without exposing privileged credentials
The application SHALL access Supabase through its server-side Reflex layer using environment-provided project configuration and the authenticated user's access token for user-scoped operations. The system SHALL NOT include a service-role key, database password, or other privileged secret in source control, browser code, rendered state, URLs, or logs.

#### Scenario: Authenticated query reaches Supabase
- **WHEN** an authenticated Reflex action queries or changes application data
- **THEN** the request reaches Supabase with the user's authenticated identity so database policies can evaluate that user

#### Scenario: Privileged secret is configured
- **WHEN** a privileged server-side operation requires a service credential
- **THEN** the credential is read only from a protected server or Edge Function environment and is never returned to the browser

#### Scenario: Required configuration is absent
- **WHEN** a required Supabase URL or public key is not configured
- **THEN** the application reports an explicit configuration failure and does not silently fall back to Xano or mock persistence

### Requirement: Application data is related without duplicating product identity
The system SHALL relate authenticated profiles to Supabase Auth users, stock lots and inventory movements to existing products, and price history to existing products by foreign keys. A price record SHALL NOT copy product name, type, brand, weight, or barcode as independently editable product data. Product barcodes SHALL be unique when present.

#### Scenario: Product is referenced by stock and prices
- **WHEN** an inventory lot or price history row is created
- **THEN** it references an existing product and cannot create a duplicate product identity

#### Scenario: Duplicate product barcode is submitted
- **WHEN** a product is created with a barcode already assigned to another product
- **THEN** the database rejects the duplicate and the application presents a safe validation message

### Requirement: Role authorization is enforced by the database and trusted operations
The system SHALL derive role decisions from the authenticated user's profile, never from a role supplied by the browser. RLS and any trusted Auth administration operation SHALL enforce the approved role matrix: operators may create products and receive stock; managers and owners may perform stock corrections; managers and owners have identical employee-management permissions and may assign any supported role. No role SHALL gain permissions solely because a control is hidden in the UI.

#### Scenario: Operator attempts a manager-only stock correction
- **WHEN** an authenticated operator attempts to perform a stock correction
- **THEN** Supabase rejects the operation and leaves stock unchanged

#### Scenario: Manager assigns an elevated role
- **WHEN** a manager creates or changes a profile to manager or owner
- **THEN** the trusted employee-management operation applies the requested role under the same rules used for an owner

#### Scenario: Browser supplies a forged role
- **WHEN** a request claims a role different from the authenticated user's stored profile
- **THEN** authorization uses the stored profile role and ignores the supplied role

### Requirement: Data access reports loading, empty, success, and error distinctly
The system SHALL distinguish query loading, a successful empty result, a successful non-empty result, and a query failure. A successful empty result SHALL NOT be treated as an error, and page initialization SHALL NOT display feedback for an action that the user did not perform.

#### Scenario: First list query returns no rows
- **WHEN** a page loads successfully and its query returns an empty list
- **THEN** the page displays its empty state without an error or stale action feedback

#### Scenario: First list query fails
- **WHEN** a page's initial data query fails
- **THEN** the application exposes a query-specific safe error state and does not present it as a failed create, update, or delete action
