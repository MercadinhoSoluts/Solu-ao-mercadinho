## Why

The current shared Sidebar provides navigation and logout but lacks the structured visual hierarchy, brand treatment, profile context, responsive behavior, and interaction polish needed for a professional commercial application. A focused redesign can improve clarity and usability while preserving every existing route, permission check, authenticated-user value, navigation destination, and logout action.

## What Changes

- Redesign the shared Sidebar used by the seven administrative screens with a continuous blue-gradient visual system, layered curved decoration, subtle separation from the main content, and fixed desktop positioning.
- Present only the white `BIPSYSTEM` wordmark at the top using the application's existing handwritten typography; do not add a cart, cashier illustration, or other replacement symbol.
- Replace the current name-only identity area with a dynamic authenticated-user profile containing an initials avatar, user name, role label, and only an existing profile affordance if it already has behavior.
- Preserve the seven existing navigation destinations while adding consistent Lucide-style icons, full-width click targets, active-route highlighting, hover transitions, visible keyboard focus, and the existing route-driven active state.
- Keep the existing logout action and place it in a separated bottom area with the established `AuthState.logout` behavior.
- Structure the Sidebar as a full-height flexible column with accessible overflow handling for short viewports.
- Add responsive behavior for desktop, tablet, and mobile: preserve usable content sizing, provide a collapsible mobile drawer with backdrop/close interactions, close after navigation, and keep all routes and logout available.
- Preserve all dashboard content, forms, tables, cards, reports, authentication, authorization, backend integrations, and Cashier/Sales screens.

## Capabilities

### New Capabilities
- `dashboard-sidebar-redesign`: Defines the shared BIPSYSTEM Sidebar’s branding, profile presentation, navigation interactions, logout placement, and responsive drawer behavior.

### Modified Capabilities
- None.

## Impact

- Primarily affects `bipsystem/bipsystem.py`, including the shared `sidebar()`, `sidebar_item()`, dashboard layout integration, and any minimal responsive state/style additions required by the existing Reflex architecture.
- May add or extend focused Sidebar tests without changing backend or dependency manifests.
- No route, database, Supabase, authentication, permission, or logout API changes are intended.
