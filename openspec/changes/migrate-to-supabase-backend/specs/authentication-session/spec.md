## Purpose

Defines account authentication and session behavior using Supabase Auth while preserving the application's existing login and role-based navigation behavior.

## ADDED Requirements

### Requirement: Users authenticate with Supabase Auth
The system SHALL authenticate users with Supabase Auth using their email and password and SHALL load their active profile and role before granting protected access. It SHALL preserve the existing post-login destinations: operators go to `/caixa`, and managers and owners go to `/`.

#### Scenario: Active user logs in
- **WHEN** a user submits valid credentials and has an active profile with a supported role
- **THEN** the application establishes an authenticated session and routes the user according to that role

#### Scenario: Invalid credentials are submitted
- **WHEN** a user submits invalid credentials
- **THEN** the application keeps the session unauthenticated and displays a safe login error without disclosing whether the email exists

#### Scenario: User profile is inactive or invalid
- **WHEN** authentication succeeds but the profile is inactive or has an unsupported role
- **THEN** the application denies protected access and does not establish an authorized application session

### Requirement: Session secrets remain server-side and have explicit lifecycle behavior
The system SHALL keep access and refresh credentials out of browser-rendered state, URLs, local storage, and logs. It SHALL restore valid sessions after page reload, validate the current authenticated identity before protected operations, and clear application session state on logout or invalid/expired authentication.

#### Scenario: Page reload restores a valid session
- **WHEN** an authenticated user reloads a protected route while the session remains valid
- **THEN** the application restores the identity and profile role without requiring a new login

#### Scenario: Session expires or is revoked
- **WHEN** Supabase reports an expired or invalid session during a protected operation
- **THEN** the application clears the session and redirects to `/login`

#### Scenario: User logs out
- **WHEN** an authenticated user selects logout
- **THEN** the application invalidates the Supabase session, clears public authenticated state, and redirects to `/login`

### Requirement: Protected routes enforce role access on the server
The system SHALL enforce access in server-side route and event handlers in addition to RLS. Operators SHALL be confined to operational routes supported by the application; administrative routes SHALL be restricted according to the approved role matrix.

#### Scenario: Operator requests an administrative route directly
- **WHEN** an operator opens an administrative URL without using the sidebar
- **THEN** the server denies access and does not return protected data

#### Scenario: Authenticated user opens a permitted route
- **WHEN** an authenticated user opens a route permitted by their stored role
- **THEN** the application allows access after validating the current profile
