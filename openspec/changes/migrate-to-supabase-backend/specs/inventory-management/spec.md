## Purpose

Defines persistent stock-lot receiving and queries using existing product records, preserving the current barcode, batch, units, and expiry workflow.

## ADDED Requirements

### Requirement: Stock receiving references an existing product and records a lot
The system SHALL allow authenticated users with an operator, manager, or owner role to receive stock only for an existing product found by barcode. A receipt SHALL record product, batch label, positive integer units, expiry date, receipt timestamp, and responsible profile.

#### Scenario: Valid stock is received for a product
- **WHEN** a permitted user submits a known barcode, batch, positive unit count, and valid expiry date
- **THEN** the stock is recorded against the existing product and the operation is reflected in the inventory query

#### Scenario: Unknown barcode is submitted
- **WHEN** a permitted user attempts to receive stock for an unregistered barcode
- **THEN** no lot or product is created and the interface reports that the product was not found

#### Scenario: Invalid quantity or expiry is submitted
- **WHEN** a user submits a non-positive or non-integer unit count or invalid expiry date
- **THEN** the database state remains unchanged and the interface reports a safe validation message

### Requirement: Repeated receipts preserve existing stock grouping behavior
The system SHALL maintain the current application behavior of adding received units to the existing record for the same product and expiry date. A subsequent receipt for that same product and expiry SHALL NOT silently replace the original stored batch label.

#### Scenario: Receipt matches an existing product and expiry
- **WHEN** stock is received for a product and expiry date already present in inventory
- **THEN** the existing quantity is incremented atomically and its stored batch label is retained

#### Scenario: Concurrent receipts target the same product and expiry
- **WHEN** two permitted receipts concurrently target the same product and expiry
- **THEN** both quantities are applied exactly once without lost updates or a duplicate stock group

### Requirement: Inventory quantities are changed through authorized atomic operations
The system SHALL prevent direct client updates that bypass its stock operation rules. Operators MAY receive stock; only managers and owners MAY perform stock corrections. An inventory movement SHALL be recorded for every committed receipt or correction, and a failed operation SHALL leave both stock and movement history unchanged.

#### Scenario: Operator attempts a stock correction
- **WHEN** an operator attempts to reduce or correct an existing stock balance outside the receipt workflow
- **THEN** the operation is denied and no movement is recorded

#### Scenario: Manager corrects stock
- **WHEN** a manager or owner submits a valid correction
- **THEN** the balance and corresponding movement are committed atomically

### Requirement: Inventory queries join lot data to the product catalog
The system SHALL query stock from persisted lots and display the product name derived from the existing product fields, batch, units, barcode, and expiry. Inventory search SHALL filter the displayed product and lot information.

#### Scenario: Inventory is loaded
- **WHEN** an authorized user opens the inventory page
- **THEN** the displayed rows are derived from persisted lots joined to their existing products

#### Scenario: Inventory query returns no rows
- **WHEN** the inventory query succeeds and returns no lots
- **THEN** the interface displays an empty inventory state without an error message
