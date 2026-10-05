# Learning Reader Changelog

## Version 2.2 — 2026-10-05

### Changes

- Repaired the incorrect use of Learning Schedule sequence as Reader Order.
- Changed Canonical Order authority to `03_learning_units/learning_unit_map.yaml` and its original `learning_units` array order.
- Preserved schedule and production order as independent concepts.
- Updated Continue Learning, current position, TOC labels, article metadata, and progress display through regenerated canonical `data-order` values.
- Kept LocalStorage progress identity keyed by unchanged LU IDs; no progress migration is required.
- Added `CANONICAL_LU_ORDER.md`, `ORDER_REPAIR_REPORT.md`, and ORDER-01 through ORDER-15 validation.

### QA Result

- Canonical Order 1–64: PASS
- Existing Reader and progress regression: PASS
- Browser interaction: NOT AVAILABLE

## Version 2.1 — 2026-10-04

### Changes

- Added an in-page Learning Guide with first-round learning, Active Recall, completion, progress, and official PDF guidance.
- Added a sidebar Learning Guide entry.
- Changed all 64 sidebar labels from ambiguous `LU nn` text to explicit `Order n` learning-sequence labels.
- Added compact sidebar progress and current Order indicators.
- Unified home, mobile, current-reading, and Continue Learning displays with canonical Order metadata.
- Extended validation to verify each Order-to-LU mapping against `learning_schedule.yaml`.

### Files Changed

- `index.html`
- `css/style.css`
- `js/learning_reader.js`
- `tools/generate_reader.py`
- `tools/validate_reader.py`
- `README.md`
- `HTML_READER_QA.md`
- `LEARNING_READER_CHANGELOG.md`

### QA Result

- Static / DOM validation: PASS
- 64-LU content and source hashes: PASS
- Progress contract PROGRESS-01 through PROGRESS-14: PASS
- Order 1 through 64 and schedule mapping: PASS

### Known Limitations

- Browser interaction and screenshot QA were not available in the execution environment. Responsive behavior is statically covered by the existing desktop, tablet, 430px, and narrower CSS rules and remains pending visual browser review.
