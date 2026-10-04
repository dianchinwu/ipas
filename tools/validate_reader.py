from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class ReaderParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.articles: list[dict[str, object]] = []
        self.toc_links: list[str] = []
        self.ids: list[str] = []
        self.current: dict[str, object] | None = None
        self.heading_text: list[str] = []
        self.capture_heading = False
        self.tables = 0
        self.progress_controls = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"] or "")
        classes = set((data.get("class") or "").split())
        if tag == "article" and "learning-unit" in classes:
            self.current = {
                "id": data.get("id"),
                "subject": data.get("data-subject"),
                "order": data.get("data-order"),
                "headings": [],
                "sha256": None,
            }
            self.articles.append(self.current)
        if self.current and "unit-source" in classes:
            self.current["sha256"] = data.get("data-source-sha256")
        if self.current and tag == "button" and "complete-button" in classes:
            self.progress_controls += 1
        if tag == "a" and data.get("data-target"):
            self.toc_links.append(data.get("href") or "")
        if self.current and tag in {"h1", "h2", "h3"}:
            self.capture_heading = True
            self.heading_text = []
        if self.current and tag == "table":
            self.tables += 1

    def handle_data(self, data: str) -> None:
        if self.capture_heading:
            self.heading_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current and tag in {"h1", "h2", "h3"} and self.capture_heading:
            self.current["headings"].append("".join(self.heading_text).strip())
            self.capture_heading = False
            self.heading_text = []
        if tag == "article":
            self.current = None


def plan_ids(plan: str) -> list[str]:
    return re.findall(r'^- learning_unit_id: "([^"]+)"', plan, re.M)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--schedule", required=True, type=Path)
    args = parser.parse_args()

    html_text = args.reader.read_text(encoding="utf-8")
    dom = ReaderParser()
    dom.feed(html_text)
    expected = plan_ids(args.plan.read_text(encoding="utf-8-sig"))
    schedule = re.findall(r'^\s+- id: "([^"]+)"', args.schedule.read_text(encoding="utf-8-sig"), re.M)
    article_ids = [str(article["id"]) for article in dom.articles]
    anchors = set(dom.ids)
    required_headings = {
        "Learning Objective", "Why It Matters", "Core Concepts", "Key Terms",
        "Must Know", "Must Understand", "Must Compare", "Must Calculate",
        "Must Apply", "Must Memorize", "Common Misconceptions", "Worked Example",
        "Worked Examples", "Scenario / Application", "Active Recall",
        "Exam-Oriented Check", "Source Traceability", "Errata References", "Review Status",
    }
    heading_failures = []
    hash_failures = []
    for article in dom.articles:
        headings = set(article["headings"])
        required = required_headings - ({"Worked Example"} if "Worked Examples" in headings else {"Worked Examples"})
        missing = sorted(required - headings)
        if missing:
            heading_failures.append({"id": article["id"], "missing": missing})
        source = args.source / f'{article["id"]}.md'
        digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
        if digest != article["sha256"]:
            hash_failures.append(str(article["id"]))

    forbidden = [token for token in ("TODO", "TBD", "Lorem ipsum") if token.lower() in html_text.lower()]
    toc_targets = [href.removeprefix("#") for href in dom.toc_links]
    toc_orders = [(item, int(order)) for item, order in re.findall(r'<a href="#([^"]+)" data-target="[^"]+"><span class="toc-label"><b[^>]*>.*?</b><span>Order (\d+)</span>', html_text)]
    result = {
        "html_01_lu_count": len(dom.articles) == 64,
        "html_02_all_ids_present": set(article_ids) == set(expected),
        "html_03_unique_ids": len(article_ids) == len(set(article_ids)) == 64,
        "html_04_unique_anchors": all(article_ids.count(item) == 1 and item in anchors for item in article_ids),
        "html_05_toc_content_mapping": len(toc_targets) == 64 and set(toc_targets) == set(article_ids),
        "html_06_href_targets": all(target in anchors for target in toc_targets),
        "html_07_subjects": {
            "Z02-01": sum(article["subject"] == "Z02-01" for article in dom.articles),
            "Z02-03": sum(article["subject"] == "Z02-03" for article in dom.articles),
        },
        "html_08_forbidden_tokens": forbidden,
        "html_09_content_integrity": not heading_failures and not hash_failures and dom.tables > 0,
        "html_10_schedule_order": [str(item["id"]) for item in sorted(dom.articles, key=lambda item: int(str(item["order"])))] == schedule,
        "html_11_progress_controls": dom.progress_controls == 64,
        "html_12_progress_shell": all(token in html_text for token in ('id="overall-count"', 'id="lu-search"', 'id="export-progress"', 'id="import-progress"', 'id="reset-progress"', 'js/progress_core.js')),
        "html_13_learning_guide": all(token in html_text for token in ('id="learning-guide"', 'data-guide-link', '如何使用 Learning Reader', 'Order 是第一輪學習的建議順序位置')),
        "html_14_toc_orders": len(toc_orders) == 64 and {order for _, order in toc_orders} == set(range(1, 65)) and all(schedule[order - 1] == item for item, order in toc_orders),
        "source_hash_failures": hash_failures,
        "heading_failures": heading_failures,
        "table_count": dom.tables,
        "toc_count": len(toc_targets),
        "article_count": len(dom.articles),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not all([
        result["html_01_lu_count"], result["html_02_all_ids_present"],
        result["html_03_unique_ids"], result["html_04_unique_anchors"],
        result["html_05_toc_content_mapping"], result["html_06_href_targets"],
        result["html_07_subjects"] == {"Z02-01": 26, "Z02-03": 38},
        not result["html_08_forbidden_tokens"], result["html_09_content_integrity"],
        result["html_10_schedule_order"], result["html_11_progress_controls"], result["html_12_progress_shell"],
        result["html_13_learning_guide"], result["html_14_toc_orders"],
    ]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
