## Context

`AuthState` owns the current authenticated user's public name and normalized
role, the login redirect, the existing logout operation, and protected-route
checks. The existing cashier page is `/caixa` and is protected by
`AuthState.require_auth`. The app uses Reflex 0.8.28.post1 and already includes
the white BIPSYSTEM logo asset.

## Decisions

- Add `/caixa-inicio` as a separate operator-only route. Its load handler first
  validates the current session with `require_auth`, then redirects non-operator
  roles to their normal landing page.
- Normalize roles using the existing `normalize_role` behavior; do not trust a
  browser-supplied role.
- Use `AuthState.user_name`, show the role as “Operador de Caixa”, and reuse
  `AuthState.logout`.
- Navigate to the existing `/caixa` route from the purchase card. Implement the
  whole card as one autofocus button so keyboard Enter invokes the same
  navigation through native button behavior. Do not install a global key
  listener.
- Use Reflex `Moment` with the browser's local timezone, Portuguese locale, and
  a one-minute interval for dynamic time and date without backend requests.
- Build the page from local Reflex components and page-specific styles; do not
  change shared layouts, shared assets, or the existing cashier page.

## Risks

- Browser timezone and locale support determine the local display. Pin the
  locale to Portuguese while allowing Moment to use the browser's local
  timezone.
- Auto-focus behavior can vary in browsers. Keep the card a semantic button
  with a visible focus treatment so it remains keyboard accessible.
