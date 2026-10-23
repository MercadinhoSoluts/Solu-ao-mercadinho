## ADDED Requirements

### Requirement: A cashier purchase is persisted before navigation
The system SHALL create an authenticated, user-owned open purchase before
navigating from the welcome page to the existing cashier page. A repeated
opening request SHALL return the same purchase. An operator SHALL have at
most one open purchase at a time so the cashier page can recover it after a
reload; a new request after the previous purchase is closed SHALL receive a
new purchase identifier.

#### Scenario: Operator starts a purchase
- **WHEN** an authenticated operator activates the purchase action
- **THEN** the database confirms an open purchase before the app navigates to
  `/caixa`

#### Scenario: Opening request is retried
- **WHEN** the same opening request is submitted more than once
- **THEN** only one purchase is created for that request

### Requirement: Purchase items preserve their applied price
The system SHALL persist a snapshot of product description, barcode, quantity,
unit price in integer cents, and line total when adding an item. Later product
price changes SHALL NOT alter existing purchase item snapshots or totals.

#### Scenario: Product price changes after inclusion
- **WHEN** the current catalog price changes after an item was added
- **THEN** the item's applied unit price and line total remain unchanged

#### Scenario: Same product is added again at the same price
- **WHEN** another quantity of the same product is added at the same applied
  unit price
- **THEN** the existing line quantity and total increase atomically

#### Scenario: Same product is added at a different price
- **WHEN** another quantity is added after the product's current price changes
- **THEN** the different applied price is kept in a separate line

### Requirement: Cashier page recovers persisted purchase state
The system SHALL display only items belonging to the active purchase and
recover their snapshots and exact-cent total when the cashier page is loaded
again.

### Requirement: Product entry is validated and idempotent
The system SHALL accept text barcodes without stripping leading zeroes and
positive integer quantities. It SHALL reject missing products and products
without a current positive price. Repeated submission of one request SHALL NOT
add the item more than once.

### Requirement: Closing item entry does not close the purchase
The operator SHALL be able to close or reopen the product-entry card without
finalizing or cancelling the purchase or removing persisted items.

### Requirement: Purchase completion and cancellation preserve history
The system SHALL allow an owned open purchase with at least one item to be
finalized. It SHALL allow an owned open purchase to be cancelled only after
confirmation. Both operations SHALL preserve purchase and item history and
prevent further additions. Neither operation SHALL initiate payment or modify
inventory.
