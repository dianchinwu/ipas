from __future__ import annotations

import argparse
import hashlib
import html
import re
from pathlib import Path


INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline(value: str) -> str:
    escaped = html.escape(value, quote=False)
    escaped = INLINE_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    escaped = LINK.sub(lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', escaped)
    return escaped


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_markdown(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code_lines: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"<p>{inline(' '.join(part.strip() for part in paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not stripped:
            flush_paragraph()
            close_list()
            i += 1
            continue
        if i + 1 < len(lines) and stripped.startswith("|") and is_table_separator(lines[i + 1]):
            flush_paragraph()
            close_list()
            headers = [inline(cell.strip()) for cell in stripped.strip("|").split("|")]
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([inline(cell.strip()) for cell in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append('<div class="table-scroll"><table><thead><tr>')
            out.extend(f"<th>{cell}</th>" for cell in headers)
            out.append("</tr></thead><tbody>")
            for row in rows:
                out.append("<tr>")
                out.extend(f"<td>{cell}</td>" for cell in row)
                out.append("</tr>")
            out.append("</tbody></table></div>")
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            heading_text = heading.group(2)
            section_classes = {
                "Common Misconceptions": "section-misconceptions",
                "Active Recall": "section-recall",
                "Worked Example": "section-example",
                "Worked Examples": "section-example",
            }
            class_name = section_classes.get(heading_text)
            class_attr = f' class="{class_name}"' if class_name else ""
            out.append(f"<h{level}{class_attr}>{inline(heading_text)}</h{level}>")
            i += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            close_list()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip("> "))
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote_lines))}</blockquote>")
            continue
        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            kind = "ul" if unordered else "ol"
            if list_type != kind:
                close_list()
                out.append(f"<{kind}>")
                list_type = kind
            item = (unordered or ordered).group(1)
            out.append(f"<li>{inline(item)}</li>")
            i += 1
            continue
        if re.fullmatch(r"-{3,}", stripped):
            flush_paragraph()
            close_list()
            out.append("<hr>")
            i += 1
            continue
        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    close_list()
    if in_code:
        out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(out)


def plan_rows(plan_text: str) -> list[dict[str, str]]:
    blocks = re.split(r"(?m)(?=^- learning_unit_id:)", plan_text)
    rows = []
    for block in blocks:
        id_match = re.search(r'^- learning_unit_id: "([^"]+)"', block, re.M)
        if not id_match:
            continue
        def field(name: str) -> str:
            match = re.search(rf"^\s*{name}:\s*(.+?)\s*$", block, re.M)
            return match.group(1).strip('"') if match else ""
        rows.append({
            "id": id_match.group(1),
            "subject": field("subject"),
            "order": field("production_order"),
            "review": field("review_status"),
            "resolution": field("code_resolution"),
            "status": field("content_status"),
        })
    return sorted(rows, key=lambda row: int(row["order"]))


def schedule_ids(schedule_text: str) -> list[str]:
    ids = re.findall(r'^\s+- id: "([^"]+)"', schedule_text, re.M)
    if len(ids) != 64 or len(set(ids)) != 64:
        raise SystemExit(f"Expected 64 unique schedule IDs, found {len(ids)}")
    return ids


def metadata(markdown: str, label: str) -> str:
    match = re.search(rf"\|\s*{re.escape(label)}\s*\|\s*(.*?)\s*\|", markdown)
    return re.sub(r"`", "", match.group(1)).strip() if match else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = plan_rows(args.plan.read_text(encoding="utf-8-sig"))
    if len(rows) != 64 or any(row["status"] != "VALIDATED" for row in rows):
        raise SystemExit("Expected 64 validated production rows")

    by_id = {row["id"]: row for row in rows}
    order = schedule_ids(args.schedule.read_text(encoding="utf-8-sig"))
    if set(order) != set(by_id):
        raise SystemExit("Learning schedule and production plan IDs do not match")
    units = []
    for learning_order, unit_id in enumerate(order, 1):
        row = {**by_id[unit_id], "order": str(learning_order)}
        path = args.source / f'{row["id"]}.md'
        if not path.exists():
            raise SystemExit(f"Missing source: {path}")
        source = path.read_text(encoding="utf-8-sig")
        source_id = metadata(source, "Learning Unit ID")
        if source_id != row["id"]:
            raise SystemExit(f"ID mismatch: {path.name}: {source_id}")
        units.append({
            **row,
            "title": source.splitlines()[0].lstrip("# ").strip(),
            "topic": metadata(source, "Official Topic"),
            "html": render_markdown(source),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        })

    counts = {subject: sum(unit["subject"] == subject for unit in units) for subject in ("Z02-01", "Z02-03")}
    subject_names = {"Z02-01": "人工智慧技術應用與規劃", "Z02-03": "機器學習技術與應用"}
    toc_groups = []
    content_groups = []
    for subject in ("Z02-01", "Z02-03"):
        subject_units = [unit for unit in units if unit["subject"] == subject]
        toc_items = "\n".join(
            f'<li><a href="#{unit["id"]}" data-target="{unit["id"]}"><span class="toc-label"><b class="toc-state">○</b><span>Order {int(unit["order"])}</span><small class="toc-date"></small></span><span>{html.escape(unit["title"])}</span></a></li>'
            for unit in subject_units
        )
        toc_groups.append(
            f'<section class="toc-group"><h2>{subject}</h2><p>{subject_names[subject]} · {len(subject_units)} LU</p><ol>{toc_items}</ol></section>'
        )
        articles = []
        for unit in subject_units:
            flags = []
            if unit["review"] == "REVIEW_REQUIRED":
                flags.append('<span class="status status-review">REVIEW_REQUIRED</span>')
            if unit["resolution"] == "UNCERTAIN":
                flags.append('<span class="status status-uncertain">UNCERTAIN</span>')
            articles.append(
                f'<article class="learning-unit" id="{unit["id"]}" data-subject="{subject}" data-order="{unit["order"]}" data-title="{html.escape(unit["title"], quote=True)}" data-topic="{html.escape(unit["topic"], quote=True)}">'
                f'<div class="unit-kicker"><span>LU {int(unit["order"]):02d}</span><span>{subject}</span><span>{html.escape(unit["topic"])}</span>{"".join(flags)}</div>'
                f'<div class="unit-progress"><div><strong class="unit-progress-state">○ 尚未完成</strong><time class="unit-progress-date"></time></div><button class="complete-button" data-id="{unit["id"]}" type="button">✓ 完成今日學習</button><button class="cancel-button secondary-button" data-id="{unit["id"]}" type="button" hidden>取消完成</button></div>'
                f'<div class="unit-source" data-source-sha256="{unit["sha256"]}">{unit["html"]}</div>'
                '</article>'
            )
        content_groups.append(
            f'<section class="subject-section" aria-labelledby="heading-{subject}"><header class="subject-header"><p>{subject}</p><h2 id="heading-{subject}">{subject_names[subject]}</h2><span>{len(subject_units)} Learning Units</span></header>{"".join(articles)}</section>'
        )

    template = f'''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>IPAS AI 應用規劃師－中級｜Learning Reader</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <a class="skip-link" href="#reader-content">跳至教材內容</a>
  <header class="app-header" id="page-top">
    <button class="menu-button" id="menu-button" type="button" aria-controls="toc-panel" aria-expanded="false"><span aria-hidden="true">☰</span><span>LU 目錄</span></button>
    <div class="brand"><strong>IPAS AI 應用規劃師－中級</strong><span>Learning Reader</span></div>
    <div class="mobile-status"><span>進度 <b id="mobile-progress">0 / 64</b></span><span>目前 <b id="mobile-current">LU 01</b></span></div>
    <div class="coverage" aria-label="教材涵蓋範圍"><span>64 LU</span><span>Z02-01 · {counts['Z02-01']}</span><span>Z02-03 · {counts['Z02-03']}</span></div>
  </header>
  <div class="reader-shell">
    <div class="toc-backdrop" id="toc-backdrop" hidden></div>
    <aside class="toc-panel" id="toc-panel" aria-label="Learning Unit 目錄">
      <div class="toc-heading"><div><strong>學習控制</strong><span id="reading-position">閱讀位置：Order 1</span></div><button class="toc-close" id="toc-close" type="button" aria-label="關閉目錄">×</button></div>
      <a class="guide-link" href="#learning-guide" data-guide-link><span aria-hidden="true">📖</span><span><strong>學習說明</strong><small>閱讀方式、Order 與完成規則</small></span></a>
      <section class="side-progress" aria-label="側欄學習進度"><div><span>學習進度</span><b id="side-progress-count">0 / 64</b></div><div class="progress-track"><span id="side-progress-bar"></span></div><div><span>目前學習</span><b id="side-current-order">Order 1</b></div></section>
      <section class="side-tools" aria-label="搜尋與進度工具">
        <label for="lu-search">搜尋 Learning Unit</label><input id="lu-search" type="search" placeholder="搜尋 LU、主題、關鍵字..." autocomplete="off">
        <div class="filter-control" aria-label="進度篩選"><button class="is-selected" data-filter="all" type="button">全部</button><button data-filter="incomplete" type="button">未完成</button><button data-filter="completed" type="button">已完成</button></div>
        <div id="search-results" class="search-results" hidden></div>
        <button class="continue-button" data-continue type="button">繼續學習</button>
        <div class="data-actions"><button id="export-progress" type="button">匯出</button><button id="import-progress" type="button">匯入</button><button id="reset-progress" type="button">重設</button></div>
        <input id="import-file" type="file" accept="application/json,.json" hidden><p id="progress-live" class="progress-live" role="status" aria-live="polite"></p>
      </section>
      <nav>{''.join(toc_groups)}</nav>
    </aside>
    <main id="reader-content"><section class="learning-guide" id="learning-guide" aria-labelledby="guide-heading"><header><p>Learning Reader 使用指南</p><h1 id="guide-heading">如何使用 Learning Reader</h1><p>這是 iPAS AI 應用規劃師（中級）第一輪學習使用的 Reader，涵蓋 Z02-01、Z02-03，共 64 個 Learning Units。</p></header><div class="guide-content"><section><h2>1. 第一輪在做什麼？</h2><p>第一輪的目標是建立完整知識地圖、理解每個 LU 的核心內容，並透過 Active Recall 初步確認自己是否真的理解；不是要求第一次閱讀就全部背熟。</p></section><section><h2>2. Order 1～64 是什麼？</h2><p><strong>Order 是第一輪學習的建議順序位置。</strong>建議依 Order 1 → Order 2 → … → Order 64 進行。它不是官方考試題號、重要程度、難度排名、Scope Code 或 Learning Unit ID。</p></section><section><h2>3. 每個 LU 怎麼讀？</h2><p>依序閱讀 Learning Objective、Why It Matters、Core Concepts、Key Terms、Must Know、Must Understand、Must Compare、Must Calculate、Common Misconceptions，最後進行 Active Recall。標示 N/A 或沒有內容的區塊不必特別停留。</p></section><section><h2>4. Active Recall 怎麼做？</h2><p>讀完主要內容後先不看原文，嘗試用自己的話說明概念、列出核心要素、區分易混淆概念；遇到公式則寫出公式並計算，遇到情境則判斷適用方法。重點是從記憶中取回核心知識，而非逐字背誦。</p></section><section><h2>5. 什麼時候可以按「完成」？</h2><p>完成代表已完成本次第一輪閱讀，並至少嘗試該 LU 的 Active Recall；不代表完全熟練、能答對所有題目或不需複習。後續仍會經過 Active Recall、題目練習、錯誤分析、Adaptive Review 與 Mock Exam。</p></section><section><h2>6. 什麼時候回到官方 PDF？</h2><p>概念不清、需要確認官方原文或正式定義、LU 標示 REVIEW_REQUIRED／UNCERTAIN、需要查 Source Traceability，或 Reader 與自己的理解衝突時，請回到官方 PDF 核對。</p></section><section><h2>7. 左側 Menu 怎麼使用？</h2><p><strong>○</strong> 是尚未完成，<strong>✓</strong> 是已完成，Order 是第一輪學習順序。點擊 LU 可直接跳轉；按下完成後狀態由 ○ 變為 ✓，並記錄完成日期。</p></section><section><h2>8. 學習進度怎麼看？</h2><p>整體進度只以「已完成 LU / 64」計算；Z02-01 為已完成 / 26，Z02-03 為已完成 / 38。閱讀時間、Active Recall 正確率與題目正確率不計入第一輪完成率。</p></section><section class="guide-goal"><h2>9. 第一輪學習的核心目標</h2><p>第一輪不是追求一次學會全部內容，而是先建立完整、可回想、可定位的知識地圖。</p><p>找目前 LU → 閱讀 → Active Recall → 完成 → 下一個 Order</p></section></div></section><section class="learning-overview" aria-labelledby="progress-heading"><header><p>第一輪學習</p><h1 id="progress-heading">學習進度</h1></header><div class="overview-grid"><section><div class="metric-line"><strong id="overall-count">0 / 64 LU</strong><span id="overall-percent">0%</span></div><div class="progress-track"><span id="overall-bar"></span></div><div class="subject-progress"><div><span>Z02-01</span><b id="count-Z02-01">0 / 26</b><div class="progress-track"><span id="bar-Z02-01"></span></div></div><div><span>Z02-03</span><b id="count-Z02-03">0 / 38</b><div class="progress-track"><span id="bar-Z02-03"></span></div></div></div></section><section class="current-block"><p>目前學習位置</p><b id="current-order">Order 1</b><strong id="current-id">{units[0]['id']}</strong><span id="current-title">{html.escape(units[0]['title'])}</span><button class="continue-button" data-continue type="button">開始學習</button></section><section class="today-block"><p>今日已完成 · <time id="today-date"></time></p><strong id="today-count">今日完成 0 個 LU</strong><ul id="today-list"></ul></section></div></section>{''.join(content_groups)}</main>
  </div>
  <footer><p>Canonical source: <code>04_content/</code> · 64 / 64 VALIDATED · Phase 4C PASS_WITH_REVIEW</p></footer>
  <button class="back-to-top" id="back-to-top" type="button" aria-label="回到頁面最上方" title="回到最上方">↑</button>
  <script src="js/progress_core.js"></script>
  <script src="js/learning_reader.js"></script>
</body>
</html>'''
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(template, encoding="utf-8", newline="\n")
    print(f"Generated {args.output} with {len(units)} LUs: {counts}")


if __name__ == "__main__":
    main()
