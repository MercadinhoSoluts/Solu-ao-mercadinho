## Why

Operators currently go directly from login to the existing cashier placeholder.
A dedicated welcome screen provides the requested operator-facing entry point
without replacing or redesigning the cashier page.

## What Changes

- Route operators to a protected cashier welcome page after successful login.
- Show the authenticated operator identity, a browser-local Portuguese clock,
  the BIPSYSTEM brand, a welcome message, a single accessible purchase action,
  and an informational footer.
- Let the purchase action navigate to the existing `/caixa` route. Give it
  initial keyboard focus so Enter activates the same button without a
  page-global keyboard listener.
- Preserve existing manager/owner login destinations, authentication state,
  logout behavior, and cashier-page implementation.

## Capabilities

### New Capabilities

- `cashier-welcome`: Protected operator welcome page and navigation to the
  existing cashier route.

### Modified Capabilities

- `authentication-session`: Change only the operator's post-login destination;
  preserve other role destinations and session lifecycle.

## Non-Goals

- Implement checkout, sales persistence, or cashier functionality.
- Change Supabase schema, authentication policy, or role permissions.
- Redesign login, cashier, or any existing operational screen.

## Impact

- Reflex routes and state in `bipsystem/bipsystem.py`.
- Focused authentication/navigation tests.
- OpenSpec capability documentation.
