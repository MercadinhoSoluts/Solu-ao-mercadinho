## Why

The Cadastro area is part of the initial dashboard, but the project has no
published API for provisioning employees. A controlled Xano endpoint is needed
so the Reflex interface can create accounts without handling user records or
password security itself.

## What Changes

- Add a protected employee-registration capability using the existing native
  Xano `user` authentication table; do not introduce a custom password store.
- Define the registration contract for name, email, password, and operational
  role, with server-side validation, normalized unique email, and safe errors.
- Restrict provisioning to authenticated, authorized users. As a policy
  assumption, an authorized manager may create operators only; the owner may
  assign any supported role (`operator`, `manager`, or `owner`).
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
