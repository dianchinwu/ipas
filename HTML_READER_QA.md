# HTML Reader QA

## Reader v2 Update — 2026-10-04

- Existing reader regression: PASS (64 LU, 64 anchors, 64 TOC mappings, 167 tables, 64 source hashes).
- Canonical learning order: PASS against `03_learning_units/learning_schedule.yaml`.
- Progress contract: PROGRESS-01 through PROGRESS-14 PASS; see `PROGRESS_QA.md`.
- JavaScript browser execution and responsive screenshots: REVIEW_REQUIRED because no browser runtime was available in the execution environment.
- v2 gate: PASS_WITH_REVIEW.

## Source

- Canonical source: `04_content/`
- Production Plan: `04_content/content_production_plan.yaml`
- Phase 4C state: 64 VALIDATED / 0 PLANNED
- Reader generation: Python standard-library Markdown renderer
- Source integrity: every rendered LU includes and passes its Markdown SHA-256 comparison

## LU Coverage

- Z02-01: 26 / 26
- Z02-03: 38 / 38
- Total: 64 / 64
- Duplicate Learning Unit IDs: 0
- Missing Learning Units: None
- Unexpected Learning Units: None

## Navigation QA

PASS（static DOM）。目錄包含 64 個 LU links，與 64 個正文 sections 一一對應；所有 `href` 均找到實際 anchor。桌面 sticky 目錄與手機抽屜控制已實作。

## Anchor QA

PASS。64 個 canonical `learning_unit_id` 均各自成為唯一 article anchor；anchor CSS 具 header offset。

## Content Integrity QA

PASS。64 個來源 hash 全數一致，沒有重新摘要或改寫來源。所有 LU 均保留 Learning Objective、Must sections、Worked Example(s)、Scenario、Active Recall、Exam-Oriented Check、Source Traceability、Errata 與 Review Status。共轉換 167 個 Markdown tables。

## Mobile QA

PASS_WITH_REVIEW。390px 與 430px 規則採單欄正文、抽屜目錄、44px 以上控制、局部表格捲動與 48px 回頂端按鈕。靜態 CSS/DOM 檢查通過；目前環境沒有可用的 browser runtime，因此未取得實際手機 viewport screenshot。

## Desktop QA

PASS_WITH_REVIEW。768px 以下切換手機布局；1366px、1440px 與 1920px 使用 320px sticky 目錄和受限正文寬度。靜態 CSS/DOM 檢查通過；目前環境沒有可用的 browser runtime，因此未取得實際桌面 screenshot。

## Formula / Table QA

PASS。inline code 與 fenced code 使用可換行或局部捲動樣式；表格由 `.table-scroll` 單獨水平捲動，不要求整頁水平捲動。Calculation Contract headings 與內容均保留。

## Active Recall QA

PASS。64 個 LU 都保留 `Active Recall` 區段；沒有轉為題庫或新增答案內容。

## HTML-01 to HTML-10

| Check | Result | Evidence |
|---|---|---|
| HTML-01 | PASS | 64 / 64 formal LU articles |
| HTML-02 | PASS | 64 canonical IDs all present |
| HTML-03 | PASS | 0 duplicate Learning Unit IDs |
| HTML-04 | PASS | 64 unique anchors |
| HTML-05 | PASS | 64 TOC entries map 1:1 to content |
| HTML-06 | PASS | Every TOC href resolves to an anchor |
| HTML-07 | PASS | Z02-01 = 26; Z02-03 = 38 |
| HTML-08 | PASS | No TODO, TBD, PLACEHOLDER or Lorem ipsum |
| HTML-09 | PASS | Required sections, 167 tables, formulas, lists and source hashes verified |
| HTML-10 | PASS_WITH_REVIEW | Responsive rules pass static QA; live screenshots unavailable |

## Missing Content

None.

## Known Issues

1. Ten source `REVIEW_REQUIRED` and eight `UNCERTAIN` states remain visible by design; the Reader does not resolve them.
2. The current execution environment exposed no connected browser. Runtime screenshots and physical click tests could not be performed; DOM mapping and responsive implementation were validated statically instead.

## Final Gate

`PASS_WITH_REVIEW`

Content coverage and integrity are complete. Review status reflects preserved Phase 4C source flags and the unavailable live-browser visual pass, not missing Reader content.
