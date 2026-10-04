from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader", required=True, type=Path)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--app", required=True, type=Path)
    args = parser.parse_args()
    page = args.reader.read_text(encoding="utf-8")
    core = args.core.read_text(encoding="utf-8")
    app = args.app.read_text(encoding="utf-8")
    ids = re.findall(r'<article class="learning-unit" id="([^"]+)"', page)
    subjects = re.findall(r'<article class="learning-unit"[^>]+data-subject="([^"]+)"', page)
    tests = {
        "PROGRESS-01": len(ids) == len(set(ids)) == 64 and 'status: "NOT_STARTED"' in core,
        "PROGRESS-02": 'status: "COMPLETED"' in core and "timestamp: v.toISOString()" in core,
        "PROGRESS-03": "localStorage.getItem(core.KEY)" in app and "localStorage.setItem(core.KEY" in app,
        "PROGRESS-04": page.count('class="toc-state"') == 64 and page.count('class="toc-date"') == 64,
        "PROGRESS-05": all(token in page for token in ('id="overall-count"', 'id="overall-percent"', 'id="overall-bar"')),
        "PROGRESS-06": subjects.count("Z02-01") == 26 and subjects.count("Z02-03") == 38,
        "PROGRESS-07": "completed_at.date === today" in core,
        "PROGRESS-08": 'status === "IN_PROGRESS"' in core and 'status === "NOT_STARTED"' in core,
        "PROGRESS-09": "u.search.includes(query)" in app and 'id="lu-search"' in page,
        "PROGRESS-10": "filter === \"completed\"" in app and "runSearch();" in app,
        "PROGRESS-11": "exportPayload" in core and "ipas-learning-progress-${core.localDate()}.json" in app,
        "PROGRESS-12": "core.merge(state, payload, ids)" in app and "value.completed_at.date > old.completed_at.date" in core,
        "PROGRESS-13": app.count("confirm(") >= 3 and "removeItem(core.KEY)" in app,
        "PROGRESS-14": "const merged = core.merge" in app and app.index("const merged = core.merge") < app.index("state = merged"),
    }
    print(json.dumps(tests, ensure_ascii=False, indent=2))
    if not all(tests.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
