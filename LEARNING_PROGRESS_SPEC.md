# Learning Progress Data Specification

## State Model

Each canonical Learning Unit has one state: `NOT_STARTED`, `IN_PROGRESS`, or `COMPLETED`. The default is `NOT_STARTED`; `COMPLETED` means first-round learning is complete, not mastery. Current reading position is separate UI state.

## Storage

- LocalStorage key: `ipas-learning-progress-v1`
- Version: `1`
- Storage contains learning state only; LU content is never stored.
- No backend or cross-device synchronization is used.

## JSON Shape

```json
{"version":1,"updated_at":"2026-10-04T12:00:00.000Z","units":{"LU-SCOPE-Z02-03-L232-03-04":{"status":"COMPLETED","completed_at":{"date":"2026-10-04","timestamp":"2026-10-04T12:00:00.000Z"}}}}
```

Exports include all 64 states. Import also accepts the v1 shorthand where `completed_at` is a `YYYY-MM-DD` string.

## Rules

- Date is the user's device-local calendar date; display is `YYYY/MM/DD`.
- Import is atomic: version, IDs, statuses, and dates are validated before assignment.
- Unknown IDs or malformed records reject the entire import.
- A completed record is not replaced by an incomplete record.
- For two completed records, later date wins; on the same date, later timestamp wins.
- Between incomplete records, `IN_PROGRESS` takes precedence.
- Reset removes the key after two confirmations.

## Versioning

Schema-breaking changes require a new version and storage key.
