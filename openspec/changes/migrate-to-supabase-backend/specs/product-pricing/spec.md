## Purpose

Defines persistent product pricing linked to existing catalog records, including historical price changes and current-price search.

## ADDED Requirements

### Requirement: Price entry looks up an existing product and never creates one
The system SHALL resolve a product by its existing barcode before accepting a price. The price form SHALL not create or edit product type, brand, weight, name, or barcode.

#### Scenario: Registered product barcode is found
- **WHEN** an authenticated user searches a registered barcode
- **THEN** the interface displays the existing product's name, type, brand, and weight

#### Scenario: Product barcode is not found
- **WHEN** an authenticated user searches an unknown barcode
- **THEN** the interface displays a not-found result and does not create a product or price

### Requirement: Price changes are stored as immutable history
The system SHALL store each accepted price as a new history record referencing an existing product and the responsible profile, with an exact monetary value and creation timestamp. Previous price records SHALL NOT be overwritten or deleted as a side effect of recording a new price. The current-price query SHALL select the latest valid record per product.

#### Scenario: First price is recorded
- **WHEN** an authorized user submits a valid positive price for a product with no prior price
- **THEN** a history record is created and becomes that product's current price

#### Scenario: Existing product price is changed
- **WHEN** an authorized user submits a different valid price for a product with a prior price
- **THEN** a new history record is created, the prior record remains available, and the new record becomes current

#### Scenario: Invalid price is submitted
- **WHEN** a user submits a blank, non-numeric, non-finite, or non-positive price
- **THEN** no history record is created and the user receives a safe validation message

### Requirement: Current prices can be searched by barcode, product name, or brand
The system SHALL query the current price for each product and support search by the existing barcode, product name, or brand. Results SHALL derive product details through the product relationship rather than duplicated editable values in price records.

#### Scenario: Search matches barcode, name, or brand
- **WHEN** an authenticated user searches for a barcode, product name, or brand
- **THEN** the results include matching products with current price and the current price's registration date

#### Scenario: Search has no matches
- **WHEN** the query succeeds but no current price matches
- **THEN** the interface displays an empty result state without an error message

#### Scenario: Product has no recorded price
- **WHEN** a product exists but has no price history
- **THEN** the product is not presented as having a current price
