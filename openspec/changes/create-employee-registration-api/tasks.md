## 1. Published contract and authorization

- [ ] 1.1 Confirm `POST /users` input names, required fields, method, and path
      against the currently published Xano API.
- [ ] 1.2 Confirm success response fields and status code.
- [ ] 1.3 Confirm validation, duplicate-email, `401`, and `403` response
      formats/statuses.
- [ ] 1.4 Confirm the permission matrix for `owner`, `manager`, and
      `operator`.
- [ ] 1.5 Confirm the published password policy, including all character-class
      requirements.
- [ ] 1.6 Record the contract in the capability specification before coding.

## 2. Xano User Schema

- [x] 2.1 Inspect the Xano workspace's native user table, auth-create operation, role fields, and active-account behavior; record the confirmed mapping before changing the schema. Verified the `user` table and signup stack on branch `v1` with the `live` data source; the existing email index is unique.
- [ ] 2.2 Reconcile versioned Xano artifacts with the published configuration without changing the published API as part of this change.

## 3. Authentication and session

- [ ] 3.1 Implement `POST /auth/login` consumption server-side.
- [ ] 3.2 Implement authenticated `GET /auth/me` consumption server-side.
- [ ] 3.3 Select and validate a server-side session mechanism for Reflex
      `0.8.28.post1`.
- [ ] 3.4 Define refresh, logout, expiration, `401`, and `403` behavior.
- [ ] 3.5 Add centralized route and operation authorization.
- [ ] 3.6 Verify no token, password, or privileged credential reaches browser
      code, URLs, rendered state, or logs.

## 4. Employee Registration Endpoint

- [ ] 4.1 Implement authenticated `POST /users` only after the published
      contract is confirmed.
- [ ] 4.2 Validate required fields, email format/normalization, supported
      roles, and the published password policy.
- [ ] 4.3 Enforce authorization from the authenticated session, never from
      browser-supplied authority.
- [ ] 4.4 Shape safe error responses and prevent credential logging or
      disclosure.
- [ ] 4.5 Verify duplicate-email behavior, including concurrent requests.

## 5. Reflex consumption contract

- [ ] 5.1 Preserve the existing Cadastro layout and replace only the
      function field with a controlled selector.
- [ ] 5.2 Add loading, duplicate-submit prevention, safe feedback, and
      success-only form reset.
- [ ] 5.3 Exercise the Cadastro-to-Xano flow for success, validation failure,
      authentication failure, and permission denial.
- [ ] 5.4 Verify the browser bundle contains no Xano service credential.

## 6. Validation

- [ ] 6.1 Test valid and invalid login.
- [ ] 6.2 Test session restoration, expiration, logout, `401`, and `403`.
- [ ] 6.3 Test access behavior for `owner`, `manager`, and `operator`.
- [ ] 6.4 Test valid employee registration and safe handling of API errors.
- [ ] 6.5 Test duplicate email, invalid email, missing fields, and password
      policy failures.
- [ ] 6.6 Test repeated clicks and unexpected responses.
- [ ] 6.7 Verify passwords and tokens never appear in logs or UI.
