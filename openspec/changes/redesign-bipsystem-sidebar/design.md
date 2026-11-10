## Context

The seven administrative pages call the shared `sidebar()` through `dashboard_layout()` in `bipsystem/bipsystem.py`. The current component already owns route destinations, active-destination selection, the dynamic authenticated user name, and `AuthState.logout`; the redesign must retain those contracts. Existing public assets include `logo_bipsystem_branca.png` and `logo_bipsystem.png`. The project uses Reflex components and Lucide-style `rx.icon` names rather than a separate frontend component framework.

## Goals / Non-Goals

**Goals:**
- Rework the shared Sidebar into a consistent professional blue-gradient layout with a text-only brand wordmark, horizontal profile, navigation, logout, and responsive drawer presentation.
- Keep all existing route values, page guards, authenticated state, and logout handler intact.
- Make the seven callers receive the same responsive behavior without duplicated Sidebar implementations.

**Non-Goals:**
- Change page content, data fetching, route paths, page guards, authentication, permissions, Supabase integrations, database behavior, or Cashier/Sales screens.
- Add a new icon package, backend endpoint, or hard-coded user data.
- Redesign unrelated content illustrations or dashboard components.

## Decisions

- **Keep `sidebar()` as the single source of truth.** Modify the shared component and the existing `dashboard_layout()` integration instead of creating per-page menus. This preserves identical navigation across all seven pages.
- **Reuse existing brand typography and icon primitives.** Render the text-only `BIPSYSTEM` wordmark with the handwritten font family already used by the application, and retain the existing `rx.icon` library. The former Sidebar image is a cashier illustration, so it is intentionally not used in the Sidebar.
- **Match existing blue identity.** Use the same blue gradient tones already present on the Cashier, Sales, and Login surfaces while keeping the gradient continuous across the entire Sidebar.
- **Build the reference curves with local CSS.** Layer large absolute rounded bands inside the Sidebar with pointer events disabled and a lower stacking level than the content. This keeps the decoration responsive without adding assets or dependencies.
- **Use a wider shared desktop rail.** Set the Sidebar and dashboard offset to 19rem (approximately 304px), while retaining the existing mobile drawer breakpoint and zero mobile content offset.
- **Preserve routing and authentication boundaries.** Keep `ROUTE_BY_DESTINATION`, `SIDEBAR_ITEMS`, `active_destination`, page decorators, and `AuthState.logout` unchanged. The redesign changes presentation and responsive interaction only.
- **Use the existing Reflex state model for the drawer.** Add only the minimal UI state and event handlers required to open, close, Escape-close, and close-after-navigation on mobile. Desktop and tablet presentation should not require alternate route or permission logic.
- **Use a flexible column layout.** Keep brand/profile/navigation in the main flow, place logout in a bottom section with `margin-top`/flex growth, and apply an internal vertical overflow strategy for short viewports. The main content receives only the necessary responsive offset or full-width mobile treatment.
- **Use component-local style dictionaries/classes for interaction states.** Preserve visible focus, hover transitions, active-route contrast, and pointer behavior without introducing global styling that can affect dashboard content.

## Risks / Trade-offs

- [Responsive drawer state could interfere with existing page rendering] → Keep state scoped to the shared layout, use explicit close handlers, and verify all seven routes plus desktop/tablet/mobile breakpoints.
- [Changing the sidebar width or content offset could obscure existing pages] → Centralize the width token, preserve `box-sizing`, test horizontal overflow, and compare the existing fixed registration/prices layouts.
- [Role data may have multiple existing representations] → Read the existing authenticated-user role values and normalize only at presentation time; never modify stored roles or authorization checks.
- [A visual redesign could accidentally alter out-of-scope screens] → Limit edits to Sidebar/layout styling and targeted responsive triggers; run the existing focused tests and inspect Cashier/Sales snapshots or component output.
