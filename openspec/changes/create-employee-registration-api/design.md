## Context

See `proposal.md` for motivation. The Xano setup guide identifies the native
`user` authentication table as the source of account credentials and describes
the roles `operator`, `manager`, and `owner`. The workspace's current API
endpoints are not yet published, so the design must be validated against the
actual Xano authentication schema before implementation.

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

## Decisions

- **Use an authenticated `POST /users` operation in the Xano users/auth API
  group.** The Xano setup guide already reserves auth endpoints for account
  identity and requires user/role checks in the backend. A public
  `/auth/register` flow would enable uncontrolled self-registration; a private
  provisioning endpoint matches the employee-management use case.
- **Create accounts through Xano's native user-authentication mechanism.**
  Confirm the actual native table and available auth functions first, then
  store only the required profile fields (`name`, `role`, and `is_active`) on
  that account. This avoids a custom password field or parallel identity store.
- **Authorize by the current authenticated account and enforce role limits on
  the server.** Managers may create operators only; owners may assign any
  supported role. This makes the currently policy-dependent manager permission
  explicit and prevents callers from elevating themselves by supplying a role.
- **Normalize email before enforcing uniqueness.** Trim and lowercase input,
  and ensure a database-level uniqueness guarantee or equivalent atomic Xano
  operation exists. A pre-insert lookup alone is not sufficient for concurrent
  requests.
- **Enforce password policy before delegating credential storage to native
  Xano auth.** Require at least 12 characters with uppercase, lowercase,
  numeric, and symbol characters. Do not log request passwords; return only
  non-sensitive account fields.
- **Keep the Reflex integration server-side.** The browser submits form data
  through Reflex; the application backend calls Xano using the user's
  authenticated session. Any required service secret remains in the backend
  environment and is never sent to the client.

## Risks / Trade-offs

- [Native Xano auth schema or password functions differ from the assumed
  interface] → Inspect the authorized workspace and test the native create-auth
  flow in a non-production environment before implementation.
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

1. Inspect the native Xano user schema, authentication functions, existing
   roles, and active-account behavior in the development environment.
2. Add only missing profile fields and the required normalized-email uniqueness
   guarantee; preserve existing users and credentials.
3. Implement and test authorization, validation, duplicate handling, and
   response shaping in Xano before publishing the endpoint.
4. Configure Reflex backend-to-Xano access through environment-managed
   credentials/session forwarding, then integrate the Cadastro form.
5. If deployment must be rolled back, disable the new endpoint and remove its
   Reflex call path. Preserve accounts already created; do not delete users as
   an automatic rollback step.

## Open Questions

None. The current proposal records the role-provisioning policy assumption;
changing that policy requires an explicit requirements update.
