## Purpose

Defines secure employee profile provisioning and the existing employee list, search, edit, and deletion workflows under Supabase Auth.

## ADDED Requirements

### Requirement: Authorized users can list and search employee profiles
The system SHALL allow owners and managers to list active and inactive employee profiles, including name, email, role, and identifier, and search the existing list by name, email, or role. A successful empty list SHALL remain an empty state.

#### Scenario: Authorized user searches employee records
- **WHEN** an owner or manager enters a search term
- **THEN** the visible profile list is filtered by name, email, and role without changing the underlying records

#### Scenario: No employees exist
- **WHEN** an authorized employee query succeeds and returns no profiles
- **THEN** the page displays the empty list without an error message

#### Scenario: Operator requests the employee list
- **WHEN** an operator requests employee records directly
- **THEN** the request is denied and no profile list is disclosed

### Requirement: Employee accounts use Supabase Auth and constrained role assignment
The system SHALL create employee credentials through Supabase Auth and store non-secret profile attributes separately. Owners and managers SHALL have identical permissions and MAY assign `owner`, `manager`, or `operator`. The system SHALL enforce a unique normalized email and SHALL never store a plaintext password in an application table.

#### Scenario: Owner creates an employee
- **WHEN** an owner submits valid name, email, password, and supported role
- **THEN** the system creates an Auth account and associated profile with only public profile fields returned

#### Scenario: Manager creates an employee with any supported role
- **WHEN** a manager submits valid data for an employee with any supported role
- **THEN** the system creates the Auth account and profile with the requested role

#### Scenario: Duplicate normalized email is submitted
- **WHEN** an authorized user submits an email that is already registered, regardless of case or surrounding whitespace
- **THEN** the operation returns a safe duplicate-email error and creates no second account

#### Scenario: Password fails policy
- **WHEN** an authorized user submits a password shorter than 12 characters or missing uppercase, lowercase, numeric, or symbol characters
- **THEN** the system rejects the operation and does not create an account

### Requirement: Employee edits preserve optional password semantics
The system SHALL allow owners and managers to edit any employee. Name and email updates SHALL affect the profile and Auth identity consistently. An empty optional password field SHALL leave the existing password unchanged; a submitted password SHALL satisfy the account password policy.

#### Scenario: Authorized user edits profile without changing password
- **WHEN** an authorized user changes employee details and leaves the optional password blank
- **THEN** the profile and email are updated while the current password remains unchanged

### Requirement: Employee deletion follows the existing confirmation and ownership safeguards
The system SHALL preserve explicit user confirmation before deletion, prevent duplicate concurrent delete submissions, and remove a profile only after the Auth account deletion succeeds. Owners and managers MAY delete any other employee but SHALL NOT delete their own account through this screen.

#### Scenario: User cancels deletion
- **WHEN** the user dismisses the employee deletion confirmation
- **THEN** no Auth account or profile is deleted

#### Scenario: Authorized deletion succeeds
- **WHEN** an authorized user confirms deletion of an eligible employee
- **THEN** the account and related profile are deleted and the row is removed from the list only after success

#### Scenario: Deletion fails
- **WHEN** Supabase rejects an employee deletion
- **THEN** the application retains the employee row and displays a safe deletion error

#### Scenario: User attempts self-deletion
- **WHEN** an owner attempts to delete their own account through the employee list
- **THEN** the operation is rejected and the current account remains active
