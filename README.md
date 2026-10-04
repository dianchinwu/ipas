# IPAS HTML Learning Reader

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
