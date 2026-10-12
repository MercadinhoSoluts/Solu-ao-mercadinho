## 1. Xano User Schema

- [x] 1.1 Inspect the Xano workspace's native user table, auth-create operation, role fields, and active-account behavior; record the confirmed mapping before changing the schema. Verified the `user` table and signup stack on branch `v1` with the `live` data source; the existing email index is unique.
- [ ] 1.2 Migrate the `role` enum to `operator`, `manager`, and `owner`, add `is_active`, and verify normalized-email uniqueness without modifying existing accounts. The schema is published and the owner account (ID 2) remains. Whitespace was trimmed and email lowercased; the uppercase variant was rejected as a duplicate. Concurrent requests remain untested.

## 2. Employee Registration Endpoint

- [x] 2.1 Implement authenticated `POST /users` using native Xano authentication and request fields `name`, `email`, `password`, and `role`; owner and manager provisioning paths succeeded in Xano Run. The endpoint was published with a response limited to non-credential fields.
- [ ] 2.2 Validate required fields, email format/normalization, supported roles, and the 12-character mixed-class password policy; a password shorter than 12 characters was rejected. A 12-character password passed, and email whitespace/case normalization plus an accented/punctuated name were accepted. Required-field, malformed-email, supported-role input, and each password character-class edge case still need explicit tests.
- [x] 2.3 Enforce owner/manager authorization from the current session, including the manager-only-operator restriction; owner creation succeeded, manager creation of an operator succeeded, manager creation of a manager was denied, and a no-token `POST /users` Run was denied.
- [ ] 2.4 Shape safe error responses and prevent credential logging or disclosure; the success response excluded password/token fields, the input is marked sensitive, and tested validation errors did not include credentials. Request-history/log redaction still needs verification.
- [ ] 2.5 Verify duplicate-email behavior, including concurrent requests; an exact duplicate and an uppercase variant of the normalized email were rejected. HTTP status mapping for duplicate/validation failures and concurrent creation remain untested.
- [x] 2.6 Bootstrap the first account as `operator`, promote that specific account to `owner`, then require authentication on legacy public `POST /auth/signup`; do not publish before verifying public signup is blocked. Account ID 2 is owner; the published signup route was subsequently verified from an external anonymous HTTP request to return `401 Unauthorized`. CORS currently reflects an unrelated origin while allowing credentials and should be restricted before production.

## 3. Reflex Consumption Contract

- [ ] 3.1 Document the request/response contract and configure the Reflex server-side caller to forward the authenticated user session; verify the browser bundle contains no Xano service credential.
- [ ] 3.2 Exercise the Cadastro-to-Xano flow for success, validation failure, authentication failure, and permission denial; verify the UI presents the created employee or the corresponding safe error.
