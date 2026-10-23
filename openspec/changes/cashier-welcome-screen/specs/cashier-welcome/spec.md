## ADDED Requirements

### Requirement: Authenticated operators receive a dedicated cashier welcome page
The system SHALL route authenticated users with the normalized `operator` role
to a protected cashier welcome page after login. The page SHALL show the
authenticated user's name, the “Operador de Caixa” label, the BIPSYSTEM
identity, “Bem-vindo!”, and the requested informational feature strip.

#### Scenario: Operator logs in
- **WHEN** an active operator successfully authenticates
- **THEN** the application routes the operator to `/caixa-inicio` with the
  existing session intact

#### Scenario: Unauthenticated user requests the welcome page
- **WHEN** a user without a valid session requests `/caixa-inicio`
- **THEN** the existing authentication guard redirects the user to `/login`

#### Scenario: Manager or owner requests the operator welcome page
- **WHEN** an authenticated manager or owner requests `/caixa-inicio`
- **THEN** the application redirects them to their existing landing page

### Requirement: Purchase action opens the existing cashier page
The welcome page SHALL provide one accessible purchase action. Activating it
with a pointer or keyboard Enter SHALL navigate to the existing `/caixa` route
without changing the session or creating a new authentication flow.

#### Scenario: Operator starts a purchase
- **WHEN** an operator activates the focused purchase button
- **THEN** the application navigates to `/caixa`

### Requirement: Welcome page displays local current date and time
The welcome page SHALL show the current local time in 24-hour `HH:MM` format
and the current date in Portuguese with the month spelled out. It SHALL update
at least once per minute without making authentication or Supabase requests.

#### Scenario: Page remains open across a minute boundary
- **WHEN** the local minute changes while the welcome page is open
- **THEN** the displayed time updates to the current local time
