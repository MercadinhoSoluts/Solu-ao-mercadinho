## 1. Xano User Schema

- [ ] 1.1 Inspect the development workspace's native user table, auth-create operation, role fields, and active-account behavior; record the confirmed mapping before changing the schema.
- [ ] 1.2 Add only missing profile fields and enforce case-insensitive email uniqueness without modifying existing accounts; verify duplicate and case-variant inserts are rejected.

## 2. Employee Registration Endpoint

- [ ] 2.1 Implement authenticated `POST /users` using native Xano authentication and request fields `name`, `email`, `password`, and `role`; verify a successful request creates an account and returns HTTP 201 with only the specified public fields.
- [ ] 2.2 Validate required fields, email format/normalization, supported roles, and the 12-character mixed-class password policy; verify invalid cases return HTTP 400 with safe field errors and create no account.
- [ ] 2.3 Enforce owner/manager authorization from the current session, including the manager-only-operator restriction; verify unauthenticated and unauthorized attempts return HTTP 401/403 without creating accounts.
- [ ] 2.4 Shape safe error responses and prevent credential logging or disclosure; verify responses and Xano logs contain no plaintext password, hash, token, or internal stack details.
- [ ] 2.5 Verify duplicate-email behavior, including concurrent requests; assert at most one account is created and later/conflicting requests return HTTP 409.

## 3. Reflex Consumption Contract

- [ ] 3.1 Document the request/response contract and configure the Reflex server-side caller to forward the authenticated user session; verify the browser bundle contains no Xano service credential.
- [ ] 3.2 Exercise the Cadastro-to-Xano flow for success, validation failure, authentication failure, and permission denial; verify the UI presents the created employee or the corresponding safe error.
