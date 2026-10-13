## Context

See `proposal.md` for motivation. The Xano workspace was inspected on branch
`v1` with the `live` data source selected. The native `user` table has a unique
index on its normalized email. With the user's approval, the role enum was
migrated to `operator`, `manager`, and `owner`, `is_active` was added, the
legacy signup was changed to create only `operator` accounts and require user
authentication, and authenticated `POST /users` was implemented and
published. Account ID 2 is the bootstrapped `owner`. Xano Run verified owner and manager provisioning behavior, password boundaries,
email normalization, duplicate rejection, and special-character names;
temporary test users were removed. An external anonymous request to the legacy
signup returned HTTP 401. CORS preflight succeeded but reflected an unrelated
origin and allowed credentials, so the origin policy needs tightening before
production. Concurrent duplicate requests, external duplicate/validation status
mapping, and execution-log redaction remain unverified. The Reflex app still
lacks an authenticated Xano session.

## Goals / Non-Goals

**Goals:**
- Define one stable registration contract that can be called by the Cadastro
  interface through the Reflex backend.
- Keep account creation, password handling, role authorization, and duplicate
  protection in Xano.

**Non-Goals:**
- Implement login/session issuance, password reset, employee editing/deletion,
  or the Cadastro user interface.
- Add a second user table or put database/service credentials in Reflex or the
  browser.

## Authentication and session design

- Add a real login flow using `POST /auth/login` with `email` and `password`.
- After login, call `GET /auth/me` with `Authorization: Bearer <authToken>` to
  obtain the authenticated user and published role.
- Keep the token in a server-side session mechanism compatible with the
  installed Reflex version. Do not put it in query parameters, browser
  `localStorage`, rendered component state, or client-side JavaScript.
- Define page-refresh restoration, logout, token expiration, and unauthorized
  response handling before exposing administrative operations.
- On `401`, clear the session and redirect to login. On `403`, show a safe
  access-denied state without exposing backend details.
- Select and validate the concrete Reflex session primitive in a spike before
  implementation; the repository currently has no session layer.

## Role-based access

The UI may hide navigation items for usability, but authorization must be
enforced by server-side route and operation handlers and by Xano:

- `owner`: administrative access and employee registration.
- `manager`: administrative access and employee registration, subject to the
  published Xano matrix.
- `operator`: only the published operational/cashier area.

The exact operation matrix remains pending confirmation from the published
Xano endpoint and must not be inferred from the client.

## Decisions

- **Use an authenticated `POST /users` operation in the Xano users/auth API
  group.** The Xano setup guide already reserves auth endpoints for account
  identity and requires user/role checks in the backend. A public
  `/auth/register` flow would enable uncontrolled self-registration; a private
  provisioning endpoint matches the employee-management use case.
- **Bootstrap without exposing owner assignment publicly.** The legacy signup
  creates only an `operator`; account ID 2 was promoted to `owner` in Xano.
  `POST /auth/signup` now requires native user authentication and was published
  together with `POST /users`. An external anonymous HTTP request with valid
  JSON returned `401 Unauthorized`. Its preflight currently reflects an
  unrelated origin with credentials enabled; restrict allowed origins to the
  deployed Reflex origin before production.
- **Create accounts through Xano's native user-authentication mechanism.**
  Confirm the actual native table and available auth functions first, then
  store only the required profile fields (`name`, `role`, and `is_active`) on
  that account. This avoids a custom password field or parallel identity store.
- **Authorize by the current authenticated account and enforce role limits on
  the server.** Managers may create operators only; owners may assign any
  supported role. This makes the currently policy-dependent manager permission
  explicit and prevents callers from elevating themselves by supplying a role.
- **Normalize email before enforcing uniqueness.** Trim and lowercase input.
  The existing unique email index is retained; a pre-insert lookup provides a
  friendly duplicate response, while the database index remains the final
  concurrent-write guard. A whitespace-padded email was stored in normalized
  form, and an uppercase variant was rejected as a duplicate. Concurrent
  requests and external duplicate/validation status mapping remain unverified.
- **Enforce password policy before delegating credential storage to native
  Xano auth.** Require at least 12 characters with uppercase, lowercase,
  numeric, and symbol characters. Do not log request passwords; return only
  non-sensitive account fields.
- **Keep the Reflex integration server-side.** The browser submits form data
  through Reflex; the application backend calls Xano using the user's
  authenticated session. Any required service secret remains in the backend
  environment and is never sent to the client.

## Risks / Trade-offs

- [Native Xano password hashing or response-code behavior differs from the
  assumed interface] → Verify the native `db.add` auth behavior and exact
  success/conflict HTTP status mapping before publishing.
- [Concurrent requests can bypass an application-level duplicate lookup] →
  Require a case-insensitive unique constraint or an atomic database-side
  creation operation and verify it with concurrent tests.
- [Password rules may conflict with Xano's native policy] → Configure the
  native policy to meet or exceed the specified minimum and test the same
  password cases at both validation layers.
- [Managers may need broader provisioning rights] → Begin with the restricted
  policy specified in the proposal; change it only through an explicit
  permission-policy update, not a client-side option.

## Migration Plan

1. [x] Bootstrap the initial account and promote account ID 2 to `owner`.
2. [x] Set `user authentication` on legacy `POST /auth/signup`.
   After publication, an external anonymous HTTP request returned `401`.
3. [x] Verify in Xano Run the owner and manager role paths, manager role limit,
   weak-password rejection, normalized duplicate behavior, special-character
   name, exact 12-character password acceptance, and non-credential success
   response. [ ] Still verify malformed email, all password-class boundaries,
   concurrent duplicates, external duplicate/validation status codes, and
   request-history redaction.
4. [x] Review and publish the two Xano API drafts (`auth/signup` and `users`);
   Xano reported zero remaining drafts. Temporary test accounts were removed.
5. Implement Reflex server-side Xano calls after the app has a real
   authenticated session flow and environment-managed API URL. Keep tokens and
   caller identity out of browser-controlled inputs.
6. If deployment must be rolled back, disable the new endpoint and remove its
   Reflex call path. Preserve accounts already created; do not delete users as
   an automatic rollback step.

## Open Questions

- What are the exact published input names and required fields for `POST /users`?
- What are the exact success and error response shapes/statuses?
- Which employee roles may `owner` and `manager` create?
- Does the published password policy require all four stated character classes?
- Which server-side session mechanism is supported by Reflex `0.8.28.post1` in
  this deployment?
- Which authorized development credentials/environment can validate the flow
  without putting secrets in the repository or browser?
