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
            f'<li><a href="#{unit["id"]}" data-target="{unit["id"]}"><span class="toc-label"><b class="toc-state">○</b> LU {int(unit["order"]):02d}<small class="toc-date"></small></span><span>{html.escape(unit["title"])}</span></a></li>'
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
      <div class="toc-heading"><div><strong>學習控制</strong><span id="reading-position">閱讀位置：LU 01</span></div><button class="toc-close" id="toc-close" type="button" aria-label="關閉目錄">×</button></div>
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
    <main id="reader-content"><section class="learning-overview" aria-labelledby="progress-heading"><header><p>第一輪學習</p><h1 id="progress-heading">學習進度</h1></header><div class="overview-grid"><section><div class="metric-line"><strong id="overall-count">0 / 64 LU</strong><span id="overall-percent">0%</span></div><div class="progress-track"><span id="overall-bar"></span></div><div class="subject-progress"><div><span>Z02-01</span><b id="count-Z02-01">0 / 26</b><div class="progress-track"><span id="bar-Z02-01"></span></div></div><div><span>Z02-03</span><b id="count-Z02-03">0 / 38</b><div class="progress-track"><span id="bar-Z02-03"></span></div></div></div></section><section class="current-block"><p>目前學習位置</p><strong id="current-id">{units[0]['id']}</strong><span id="current-title">{html.escape(units[0]['title'])}</span><button class="continue-button" data-continue type="button">開始學習</button></section><section class="today-block"><p>今日已完成 · <time id="today-date"></time></p><strong id="today-count">今日完成 0 個 LU</strong><ul id="today-list"></ul></section></div></section>{''.join(content_groups)}</main>
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
