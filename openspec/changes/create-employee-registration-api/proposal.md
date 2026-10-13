## Why

The Cadastro area is part of the initial dashboard, but the project has no
published API for provisioning employees. A controlled Xano endpoint is needed
so the Reflex interface can create accounts without handling user records or
password security itself.

## What Changes

- Add a real Reflex login flow backed by `POST /auth/login` and
  `GET /auth/me`.
- Define secure session lifecycle, logout, page-refresh behavior, and
  unauthorized-session handling before exposing administrative operations.
- Add a protected employee-registration capability using the existing native
  Xano `user` authentication table; do not introduce a custom password store.
- Disable the existing public `POST /auth/signup` after one-time creation of
  the initial owner account, so new accounts can only be provisioned through
  authorized employee registration.
- Define the registration contract for name, email, password, and operational
  role, with server-side validation, normalized unique email, and safe errors.
- Restrict provisioning to authenticated, authorized users. The published
  authorization matrix for `owner`, `manager`, and `operator` must be confirmed
  before implementation; the client must never grant authority based on a
  browser-supplied role.
- Specify how the Reflex backend consumes the Xano endpoint without exposing
  service credentials to the browser.

## Capabilities

### New Capabilities

- `employee-registration`: Securely provision employee accounts through a
  role-protected Xano API for consumption by the Reflex application.

### Modified Capabilities

None.

## Impact

- Xano: authenticated employee-provisioning endpoint, native `user` table,
  email uniqueness, role authorization, and password policy.
- Reflex: future integration from the Cadastro interface through the
  application backend; this proposal does not implement the UI or integration.
- Documentation: add the API behavior and validation contract to the OpenSpec
  capability specification.
- Session/authentication: add a server-side token/session strategy compatible
  with Reflex `0.8.28.post1`, without exposing credentials to browser code.

## Pending contract confirmation

The supplied API URL, login path, `/auth/me` path, and role identifiers are
inputs to this proposal. Before implementation, confirm against the currently
published Xano API:

- Exact `POST /users` input names and required fields.
- Success response shape and HTTP status.
- Validation, duplicate-email, authentication, and authorization status codes.
- Permission matrix for each role.
- Published password policy, including the special-character requirement.

No implementation task may call `POST /users` until these items are recorded
as confirmed.
