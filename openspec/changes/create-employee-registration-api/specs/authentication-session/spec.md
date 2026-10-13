## Purpose

Provide authenticated Reflex sessions for the BIPSYSTEM using the published
Xano authentication endpoints without exposing tokens or credentials to the
browser.

## ADDED Requirements

### Requirement: Users authenticate through the published Xano login

The system SHALL send login credentials to `POST /auth/login` from the
server-side application layer and SHALL use the returned `authToken` only for
authenticated server-side calls. The system SHALL call `GET /auth/me` with the
Bearer token to establish the authenticated user and published role.

#### Scenario: Valid login

- **WHEN** a user submits valid Xano credentials
- **THEN** the server stores the authenticated session securely, retrieves the
  current user, and grants only the pages allowed by that user's role

#### Scenario: Invalid login

- **WHEN** a user submits invalid credentials
- **THEN** the system keeps the session unauthenticated and shows a safe
  authentication error without exposing credentials or backend details

### Requirement: Session credentials are not exposed to the browser

The system SHALL NOT place the Xano token in URLs, browser local storage,
rendered component state, browser-delivered JavaScript, or user-visible
messages. Passwords and authorization headers SHALL NOT be logged.

#### Scenario: Browser inspects rendered application state

- **WHEN** a user inspects browser-delivered state or URLs
- **THEN** no Xano token, password, or service credential is present

### Requirement: Sessions have explicit lifecycle behavior

The system SHALL define behavior for page refresh, logout, token expiration,
and unauthorized responses. A `401` from Xano SHALL invalidate the session and
redirect to login. Logout SHALL invalidate the server-side session and remove
authenticated public state.

#### Scenario: Expired session

- **WHEN** an authenticated Xano request returns `401`
- **THEN** the system clears the session and redirects the user to login

#### Scenario: Logout

- **WHEN** an authenticated user logs out
- **THEN** the system invalidates the session and prevents access to protected
  pages

### Requirement: Administrative access is role protected

The system SHALL enforce authorization on server-side route and operation
handlers. `owner` and `manager` SHALL be eligible for administrative
capabilities subject to the published Xano policy. `operator` SHALL NOT access
administrative employee registration solely because a navigation item is
hidden.

#### Scenario: Operator requests an administrative operation

- **WHEN** an authenticated operator requests an administrative route or
  employee registration operation
- **THEN** the system denies access without relying only on sidebar visibility
