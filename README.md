# IPAS HTML Learning Reader

## Learning Reader v2

Reader v2 在原有 64-LU 離線閱讀器上加入第一輪學習進度：整體與分科進度、目前／下一個 LU、今日完成清單、正文完成按鈕、目錄狀態同步、全文快速搜尋，以及全部／未完成／已完成篩選。

學習紀錄目前儲存在瀏覽器 LocalStorage，不會自動跨裝置同步。LocalStorage key 為 `ipas-learning-progress-v1`；可用側欄的「匯出」備份 JSON、「匯入」驗證並合併備份，或經兩次確認後「重設」。完成日期依使用者裝置的 local date 記錄，顯示為 `YYYY/MM/DD`。

目前閱讀位置與完成狀態分離；捲動與導覽只會更新閱讀位置，不會自動完成 LU。完整資料規格見 `LEARNING_PROGRESS_SPEC.md`。重新產生與驗證時須分別提供 `--schedule ../03_learning_units/learning_schedule.yaml`。

### Learning Guide 與 Order

左側最上方的「學習說明」會跳到頁面內的使用指南，說明第一輪目標、LU 閱讀順序、Active Recall、完成規則、官方 PDF 核對時機與進度定義。

側欄每個 LU 的 `Order 1` 至 `Order 64` 是第一輪建議學習順序，不是考試題號、重要度、難度、Scope Code 或 LU ID。唯一 Source of Truth 是 `03_learning_units/learning_schedule.yaml`，generator 依其中 `learning_units[].id` 的出現順序產生 `data-order` 與目錄標籤，並與 64 個正式 LU 核對。`○` 表示尚未完成，`✓` 表示已完成；完成日期、搜尋、篩選與 Continue Learning 仍使用相同的 Order 與 LocalStorage 狀態。

## 用途

這是一個 Phase 4C 教材閱讀層，將 64 份正式 Learning Unit 完整呈現在單一 HTML 頁面。它不會修改或摘要來源內容，也不包含題庫、測驗、錯題紀錄、適性複習或其他 Phase 5 功能。

## Canonical Source

- 內容來源：`../04_content/LU-*.md`（不含 `pilot/`）
- 排序與狀態：`../04_content/content_production_plan.yaml`
- 產生日期：2026-10-04
- 正式 LU：64
- Z02-01：26
- Z02-03：38

`index.html` 中每個 LU 都保存來源 Markdown 的 SHA-256，並以 `data-source-sha256` 屬性記錄；驗證器會重新計算並比對。

## 如何開啟

直接開啟 `08_learning_reader/index.html`，不需要伺服器、npm、backend 或網路連線。

桌面版左側提供 sticky 完整目錄。手機或窄螢幕使用頁首的「LU 目錄」按鈕開啟抽屜；點選 LU 後會跳轉並關閉目錄。頁面向下捲動後，右下角會顯示回到最上方按鈕。

## Rendering

`tools/generate_reader.py` 使用 Python 標準函式庫：

1. 從 Production Plan 取得 64 個 VALIDATED LU 與順序。
2. 驗證來源檔存在，且 Markdown 內的 Learning Unit ID 一致。
3. 將 heading、paragraph、list、table、blockquote、code 與公式內容轉成語義化 HTML。
4. 嵌入來源 SHA-256，產生單一 `index.html`。

重新產生：

```powershell
python .\08_learning_reader\tools\generate_reader.py `
  --source .\04_content `
  --plan .\04_content\content_production_plan.yaml `
  --output .\08_learning_reader\index.html
```

重新驗證：

```powershell
python .\08_learning_reader\tools\validate_reader.py `
  --reader .\08_learning_reader\index.html `
  --source .\04_content `
  --plan .\04_content\content_production_plan.yaml
```

## QA 結果

- 64/64 正式 LU：PASS
- 64 個唯一 anchor：PASS
- 64 個 TOC 到正文 mapping：PASS
- Z02-01 26 / Z02-03 38：PASS
- 來源 SHA-256：PASS
- 必要內容區段：PASS
- 表格、清單、公式與 code rendering：PASS
- 390px、430px、768px、1366px、1440px、1920px responsive rules：PASS（靜態檢查）
- 實際瀏覽器 screenshot：未執行；目前環境沒有可用的 browser runtime

完整結果見 `HTML_READER_QA.md`。
