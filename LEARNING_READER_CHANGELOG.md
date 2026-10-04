# Learning Reader Changelog

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
