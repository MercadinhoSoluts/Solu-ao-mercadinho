## Purpose

Defines the existing product registration and lookup behavior against a normalized, persistent Supabase product catalog.

## ADDED Requirements

### Requirement: Authorized users can register products with unique barcodes
The system SHALL allow authenticated operators, managers, and owners to register products using the existing fields: type, brand, weight in grams, and barcode. Product fields SHALL be validated, and a barcode SHALL identify at most one active product.

#### Scenario: User registers a valid product
- **WHEN** an authenticated user with a permitted role submits valid type, brand, weight, and barcode
- **THEN** the product is persisted once and the application displays a success result

#### Scenario: Invalid product fields are submitted
- **WHEN** product type, brand, weight, or barcode fails validation
- **THEN** no product is created and the user receives a safe field validation message

#### Scenario: Barcode belongs to another product
- **WHEN** a user submits a barcode already assigned to another product
- **THEN** the database rejects the product and the interface reports the duplicate without changing either product

### Requirement: Product queries return database records and support barcode relationships
The system SHALL retrieve products from Supabase for stock views and barcode-based workflows. Lookup by barcode SHALL return the existing product identity and its type, brand, and weight; lookup SHALL NOT create a product.

#### Scenario: Existing barcode is looked up
- **WHEN** an authenticated workflow searches a registered barcode
- **THEN** it returns the matching product's type, brand, weight, and stable identifier

#### Scenario: Unknown barcode is looked up
- **WHEN** a barcode query completes without a matching product
- **THEN** the application shows a not-found result and makes no database changes

#### Scenario: Product list is empty
- **WHEN** the catalog query succeeds with no matching products
- **THEN** the application displays an empty state without reporting an API failure
