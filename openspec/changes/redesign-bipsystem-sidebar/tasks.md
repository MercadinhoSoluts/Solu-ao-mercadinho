## 1. Shared Sidebar structure and branding

- [x] 1.1 Refactor the shared `sidebar()` presentation into a full-height blue-gradient column with the white BIPSYSTEM wordmark, subtle boundary, and internal overflow; verify the branding and Sidebar dimensions render consistently on all seven administrative routes.
- [x] 1.2 Add the dynamic authenticated-user profile with initials avatar, real name, and role label using existing state values; verify no user identity is hard-coded and existing loading/authenticated states remain valid.

## 2. Navigation and logout

- [x] 2.1 Update shared navigation items to use consistent existing icon primitives, full-width targets, hover/focus/active styles, and the existing seven destinations; verify each route highlights only its active item and retains its current href.
- [x] 2.2 Place the existing Sair action in a separated bottom section with the existing `AuthState.logout` handler; verify session termination and redirect behavior are unchanged.

## 3. Responsive behavior

- [x] 3.1 Add desktop and tablet layout rules that preserve readable controls, fixed/offset content alignment, and no horizontal overflow; verify Início, Estoque, Conferência, Produto, Relatórios, Cadastro, and Preços at representative wide and medium viewports.
- [x] 3.2 Add the mobile drawer trigger, backdrop, close control, Escape handling, and close-after-navigation using minimal existing Reflex state; verify closed-by-default behavior, keyboard/pointer dismissal, and access to all navigation and logout controls.
- [x] 3.3 Handle short viewport heights with internal Sidebar scrolling while keeping Sair reachable; verify no controls are clipped or overlapped.

## 4. Regression verification

- [x] 4.1 Add or extend focused Sidebar coverage for logo/profile/navigation/active-state/logout rendering and preserved route values; verify the targeted Python test suite passes.
- [x] 4.2 Verify dashboard content, forms, tables, cards, reports, authentication guards, backend integrations, and Cashier/Sales screens remain unchanged; run the smallest applicable regression suite and inspect the final diff for Sidebar-only scope.

## 5. Visual fidelity refinement

- [x] 5.1 Add layered, pointer-free curved decorative bands across the shared Sidebar background without covering interactive content.
- [x] 5.2 Increase the desktop Sidebar width to approximately 300 pixels and update only the shared dashboard content offset, preserving the mobile drawer behavior.
- [x] 5.3 Extend focused rendering coverage and run the complete regression suite to verify navigation, logout, responsiveness, and out-of-scope screens remain unchanged.
