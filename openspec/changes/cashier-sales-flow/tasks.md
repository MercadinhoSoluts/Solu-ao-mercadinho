## Schema and specification

- [x] 1.1 Inspect checked-in Supabase migrations, product/price schemas, RLS,
      current cashier UI, and Supabase client conventions.
- [x] 1.2 Record the immutable applied-price requirement and the limitation
      that remote schema status is unavailable in this environment.
- [ ] 1.3 Review and apply the incremental migration in the authorized Supabase
      project after verifying its remote migration history.

## Database operations

- [x] 2.1 Add purchase, item snapshot, and item-request idempotency schema only
      because no corresponding entities exist in checked-in migrations.
- [x] 2.2 Add ownership-scoped, authenticated RPCs for open, read, add,
      finalize, and cancel.
- [ ] 2.3 Test migration and RPC transaction behavior against a local Supabase
      database.

## Reflex integration

- [x] 3.1 Persist a purchase before routing from the welcome screen.
- [x] 3.2 Recover active purchase and snapshot items after page reload.
- [x] 3.3 Add quantity/barcode entry with server-side validation and
      duplicate-request prevention.
- [x] 3.4 Bind the existing table and total to persisted item snapshots.
- [x] 3.5 Support closing/reopening entry and confirmed purchase cancellation.
- [x] 3.6 Support non-empty purchase finalization without payment or stock
      side-effects.

## Validation

- [x] 4.1 Add unit tests for input validation, exact-cent formatting, errors,
      idempotency, and purchase state transitions.
- [x] 4.2 Run all existing tests and production frontend export.
- [ ] 4.3 Perform authenticated integration tests against an authorized
      Supabase environment and report remote deployment status separately.
