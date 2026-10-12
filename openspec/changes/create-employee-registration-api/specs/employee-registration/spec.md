## Purpose

Provide a secure, auditable way for authorized store users to provision employee
accounts for the mercadinho application through its Xano API.

## ADDED Requirements

### Requirement: Employee accounts are provisioned only by authorized users

The system SHALL expose `POST /users` as an authenticated employee-registration
operation. The JSON request SHALL contain `name`, `email`, `password`, and
`role`. Once the initial owner account has been bootstrapped, the existing
`POST /auth/signup` operation SHALL NOT permit unauthenticated account
creation.
Authorization SHALL be derived from the authenticated user's stored role, not
from a role or user identifier supplied as authority by the request. An
authorized manager SHALL be allowed to create only `operator` accounts. An
owner SHALL be allowed to create accounts with the supported roles `operator`,
`manager`, and `owner`. The operation SHALL create accounts in the existing
native Xano authentication user store and SHALL NOT permit public self-service
registration.

#### Scenario: Owner registers an employee
- **WHEN** an authenticated owner submits valid registration data with a supported role
- **THEN** the system creates the employee account and returns HTTP 201 with its public account details

#### Scenario: Manager registers an operator
- **WHEN** an authenticated manager submits valid registration data with role `operator`
- **THEN** the system creates the operator account

#### Scenario: Manager attempts to grant a privileged role
- **WHEN** an authenticated manager submits registration data with role `manager` or `owner`
- **THEN** the system rejects the request as forbidden and creates no account

#### Scenario: Unauthenticated caller attempts registration
- **WHEN** a caller without a valid authenticated session submits registration data
- **THEN** the system rejects the request as unauthenticated and creates no account

#### Scenario: Unauthenticated caller uses the legacy signup route after bootstrap
- **WHEN** a caller without a valid authenticated session submits a request to `POST /auth/signup` after the initial owner account is created
- **THEN** the system rejects the request as unauthenticated and creates no account

### Requirement: Registration input is validated by the backend

The system SHALL require a non-empty name, a valid email address, a password
with at least 12 characters including uppercase and lowercase letters, a
number, and a symbol, and a supported role. The system SHALL trim surrounding
whitespace from the name and email and normalize the email to lowercase before
uniqueness checks and storage. Validation SHALL occur in the backend before
account creation.

#### Scenario: Required field or format is invalid
- **WHEN** a caller submits a blank name, malformed email, unsupported role, or password that fails the password policy
- **THEN** the system returns a client validation error identifying the invalid fields and creates no account

#### Scenario: Valid email contains surrounding whitespace or uppercase letters
- **WHEN** an authorized caller submits an otherwise valid email with surrounding whitespace or uppercase letters
- **THEN** the system stores and uses the trimmed lowercase email value

### Requirement: Email addresses are unique

The system SHALL prevent more than one account from being registered with the
same email address, regardless of letter case. The uniqueness guarantee SHALL
remain valid for concurrent registration requests.

#### Scenario: Email already belongs to an account
- **WHEN** an authorized caller submits an email that is already registered, ignoring case
- **THEN** the system returns a conflict response and does not create another account

#### Scenario: Concurrent requests register the same email
- **WHEN** multiple authorized requests attempt to register the same normalized email concurrently
- **THEN** at most one request creates an account and the remaining requests receive a conflict response

### Requirement: Credentials and responses protect sensitive data

The system SHALL use the native Xano authentication mechanism to store and
verify passwords. It SHALL NOT store or log plaintext passwords, return
passwords or password hashes, or expose authentication/service credentials to
the browser. A successful response SHALL return only the new account's
identifier, name, normalized email, role, and active status.
Validation failures SHALL return HTTP 400, unauthenticated requests HTTP 401,
unauthorized roles HTTP 403, and duplicate email addresses HTTP 409. Error
responses SHALL provide a stable error code and safe message; validation
responses SHALL identify invalid fields without disclosing internal details.

#### Scenario: Account is created successfully
- **WHEN** valid registration data is accepted
- **THEN** the response contains the account identifier, name, normalized email, role, and active status without credential material

#### Scenario: Validation or authorization fails
- **WHEN** registration is rejected for invalid input or insufficient permission
- **THEN** the response contains a safe error and does not disclose passwords, hashes, tokens, or internal stack details

### Requirement: Reflex consumes the registration API through its backend

The Reflex application SHALL call the Xano registration endpoint from its
server-side application layer using the authenticated user's session. It SHALL
NOT embed Xano service credentials in browser-delivered code or permit the
browser to override the authenticated user's identity or authorization role.

#### Scenario: Cadastro interface submits employee data
- **WHEN** an authorized user submits the Cadastro form with employee details
- **THEN** the Reflex backend forwards the request to Xano and presents the resulting success or safe validation/authorization error

#### Scenario: Browser attempts to supply service credentials or caller role
- **WHEN** a browser request attempts to provide privileged service credentials or to choose the caller's authorization role
- **THEN** the system ignores or rejects that authority and makes the authorization decision from the authenticated session
