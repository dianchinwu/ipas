# Reader Canonical Order Repair Report

## 1. Root Cause

Reader v2.1 used the occurrence order of IDs in `03_learning_units/learning_schedule.yaml` as `data-order`. That file defines date-to-LU scheduling, not stable Learning Unit identity order. Consequently the LU scheduled on 2026-09-29 was incorrectly displayed as Order 1.

## 2. Correct Authority

Canonical Order is the unmodified array order of `learning_units` in `03_learning_units/learning_unit_map.yaml`. Production Order and Learning Schedule remain independent and were not modified.

## 3. Before / After, Order 1–10

| Order | Before: schedule-derived LU | After: canonical-map LU |
|---:|---|---|
| 1 | `LU-SCOPE-Z02-03-L232-03-04` | `LU-SCOPE-Z02-01-L211-01-01` |
| 2 | `LU-SCOPE-Z02-03-L231-01-02` | `LU-SCOPE-Z02-01-L211-01-02` |
| 3 | `LU-SCOPE-Z02-03-L231-03-02` | `LU-SCOPE-Z02-01-L211-01-03` |
| 4 | `LU-SCOPE-Z02-01-L211-01-05` | `LU-SCOPE-Z02-01-L211-01-04` |
| 5 | `LU-SCOPE-Z02-01-L211-01-03` | `LU-SCOPE-Z02-01-L211-01-05` |
| 6 | `LU-SCOPE-Z02-03-L231-01-01` | `LU-SCOPE-Z02-01-L211-02-01` |
| 7 | `LU-SCOPE-Z02-03-L231-01-03` | `LU-SCOPE-Z02-01-L211-02-02` |
| 8 | `LU-SCOPE-Z02-03-04-04` | `LU-SCOPE-Z02-01-L211-02-03` |
| 9 | `LU-SCOPE-Z02-01-L211-03-01` | `LU-SCOPE-Z02-01-L211-02-04` |
| 10 | `LU-SCOPE-Z02-01-L211-03-03` | `LU-SCOPE-Z02-01-L211-03-01` |

## 4. Sequence Separation

- Canonical Order: stable Reader Order from `learning_unit_map.yaml`.
- Production Order: content-production workflow from `content_production_plan.yaml`.
- Learning Schedule: dated study assignments from `learning_schedule.yaml`.
- Canonical and Schedule have 0 matching positions out of 64. Difference is expected and is not normalized.

## 5. Implementation

- Generator parses the canonical map and enumerates its array directly.
- TOC, articles, current Order, Continue Learning, and progress display use generated canonical `data-order` values.
- LocalStorage records remain keyed by unchanged LU IDs, so prior completion records stay attached to the correct units.
- `CANONICAL_LU_ORDER.md` is generated documentation only; it does not replace the map as authority.

## 6. Validation

- 64 / 64 unique canonical IDs: PASS
- 64 / 64 Reader articles, anchors, and TOC links: PASS
- 167 tables and 64 source hashes: PASS
- ORDER-01 through ORDER-15: PASS
- PROGRESS-01 through PROGRESS-14: PASS
- Browser interaction: NOT AVAILABLE

## 7. Files Changed

- `index.html`
- `tools/generate_reader.py`
- `tools/validate_reader.py`
- `tools/test_order_contract.py`
- `README.md`
- `HTML_READER_QA.md`
- `LEARNING_READER_CHANGELOG.md`
- `CANONICAL_LU_ORDER.md`
- `ORDER_REPAIR_REPORT.md`

No LU content, Blueprint, Scope, Errata, Learning Schedule, Production Order, or Phase 1–4 artifact was modified.

## Final Gate

`ORDER_REPAIR_GATE = PASS`
