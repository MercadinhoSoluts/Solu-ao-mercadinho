## Purpose

Defines a professional, responsive shared BIPSYSTEM Sidebar that improves visual hierarchy and usability while preserving the existing administrative navigation, authenticated-user data, permissions, and logout behavior.

## ADDED Requirements

### Requirement: Shared branded Sidebar structure
The seven administrative screens SHALL render one shared Sidebar with a continuous blue gradient visual treatment, full viewport-height desktop layout, a subtle boundary from the main content, and the white text `BIPSYSTEM` centered at the top. The wordmark SHALL use the existing handwritten brand typography from the application and SHALL NOT be replaced or accompanied by a cart, supermarket, cashier, image, or other decorative symbol.

#### Scenario: Administrative screen renders the branded Sidebar
- **WHEN** a user opens Início, Estoque, Conferência, Produto, Relatórios, Cadastro, or Preços
- **THEN** the shared Sidebar presents only the white BIPSYSTEM wordmark at the top with the same branding and proportions on every screen

### Requirement: Dynamic authenticated-user profile
The Sidebar SHALL display the authenticated user's real name and role in a compact horizontal profile area with a circular initials avatar to the left, a prominent white name, and a secondary role label beneath it. The profile SHALL not hard-code a person name or invent profile actions that are not already supported.

#### Scenario: Authenticated user profile is shown
- **WHEN** an authenticated user views an administrative screen
- **THEN** the Sidebar derives the avatar initials, displayed name, and role from the existing authenticated-user state

### Requirement: Route-preserving navigation
The Sidebar SHALL preserve exactly the seven existing navigation destinations: Início, Estoque, Conferência, Produto, Relatórios, Cadastro, and Preços. Each item SHALL have a consistent existing-library icon, a full-width click target, visible text, subtle hover transition, visible keyboard focus, and an active style determined by the actual active destination.

#### Scenario: Active navigation follows the current destination
- **WHEN** a user opens or navigates to one of the seven administrative routes
- **THEN** only the corresponding Sidebar item receives the active highlight and its existing destination remains unchanged

#### Scenario: Navigation item is usable by pointer and keyboard
- **WHEN** a user hovers, focuses, or activates a Sidebar item
- **THEN** the item provides the specified visual feedback, remains accessible, and navigates using the existing route without changing authentication or permissions

### Requirement: Preserved logout behavior
The Sidebar SHALL keep the existing Sair control at the bottom of the flexible Sidebar layout, separated from navigation by a subtle divider, and SHALL invoke the existing logout handler without changing session or redirect behavior.

#### Scenario: User logs out
- **WHEN** an authenticated user activates Sair
- **THEN** the existing logout flow runs exactly as before, including its session termination and redirect behavior

### Requirement: Responsive Sidebar and content layout
The Sidebar SHALL remain usable across desktop, tablet, and mobile viewports. Desktop SHALL provide a fixed left Sidebar of approximately 250 pixels with content offset accordingly; tablet SHALL retain readable navigation without obscuring content; mobile SHALL use a closed-by-default drawer with a menu trigger, backdrop, close controls, Escape support, and automatic close after navigation. Short viewports SHALL allow Sidebar scrolling while keeping Sair reachable.

#### Scenario: Desktop layout remains visible during page scrolling
- **WHEN** the viewport is wider than 1024 pixels and the main content scrolls
- **THEN** the Sidebar remains fixed on the left, its controls remain visible, and the main content is not hidden beneath it

#### Scenario: Mobile drawer opens and closes accessibly
- **WHEN** the viewport is below 768 pixels
- **THEN** the Sidebar starts closed, opens from the content menu trigger with a dimmed backdrop, and closes from the close control, backdrop, Escape key, or after selecting a route

#### Scenario: Sidebar handles short viewports
- **WHEN** the viewport height is too small to show all Sidebar content at once
- **THEN** the Sidebar content can scroll vertically and the Sair control remains reachable without horizontal overflow

### Requirement: Preserve out-of-scope application behavior
The redesign SHALL preserve all existing page content, forms, tables, cards, reports, routes, authentication and authorization checks, backend integrations, database behavior, and Cashier/Sales screens.

#### Scenario: Non-sidebar application behavior is unchanged
- **WHEN** a user uses the redesigned administrative Sidebar
- **THEN** dashboard content and out-of-scope screens retain their existing structure and behavior
