from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--generator", required=True, type=Path)
    parser.add_argument("--app", required=True, type=Path)
    args = parser.parse_args()

    mapped = json.loads(args.map.read_text(encoding="utf-8-sig"))["learning_units"]
    canonical = [unit["id"] for unit in mapped]
    schedule = re.findall(r'^\s+- id: "([^"]+)"', args.schedule.read_text(encoding="utf-8-sig"), re.M)
    plan = args.plan.read_text(encoding="utf-8-sig")
    production = [item for _, item in sorted(
        (int(order), item) for item, order in re.findall(
            r'^- learning_unit_id: "([^"]+)"[\s\S]*?^\s*production_order: (\d+)', plan, re.M
        )
    )]
    page = args.reader.read_text(encoding="utf-8")
    generator = args.generator.read_text(encoding="utf-8")
    app = args.app.read_text(encoding="utf-8")
    articles = [(item, int(order), subject) for item, subject, order in re.findall(
        r'<article class="learning-unit" id="([^"]+)" data-subject="([^"]+)" data-order="(\d+)"', page
    )]
    by_order = [item for item, _, _ in sorted(articles, key=lambda row: row[1])]
    toc = [(item, int(order)) for item, order in re.findall(
        r'<a href="#([^"]+)" data-target="[^"]+"><span class="toc-label"><b[^>]*>.*?</b><span>Order (\d+)</span>', page
    )]
    tests = {
        "ORDER-01": len(canonical) == len(set(canonical)) == 64,
        "ORDER-02": canonical[0] == "LU-SCOPE-Z02-01-L211-01-01",
        "ORDER-03": canonical[1] == "LU-SCOPE-Z02-01-L211-01-02",
        "ORDER-04": canonical[2] == "LU-SCOPE-Z02-01-L211-01-03",
        "ORDER-05": {order for _, order, _ in articles} == set(range(1, 65)),
        "ORDER-06": len({order for _, order, _ in articles}) == 64,
        "ORDER-07": 'parser.add_argument("--map"' in generator and "schedule_ids" not in generator,
        "ORDER-08": 'order = [unit["id"] for unit in mapped_units]' in generator and canonical != production,
        "ORDER-09": set(by_order) == set(canonical),
        "ORDER-10": len(toc) == 64 and all(canonical[order - 1] == item for item, order in toc),
        "ORDER-11": len(by_order) == len(set(by_order)) == 64,
        "ORDER-12": by_order == canonical and len({order for _, order, _ in articles}) == 64,
        "ORDER-13": "sort((a, b) => Number(a.dataset.order) - Number(b.dataset.order))" in app and "core.nextId(state, ids)" in app,
        "ORDER-14": "const ids = units.map((unit) => unit.id)" in app and "state[unit.id]" in app,
        "ORDER-15": canonical != schedule and canonical != production,
    }
    print(json.dumps(tests, ensure_ascii=False, indent=2))
    if not all(tests.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
