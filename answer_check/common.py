"""Shared helpers for the answer checker."""
import csv
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE_DIR = HERE / "aops_cache"      # one JSON per problem id, written by fetch_aops.py
STATE_FILE = HERE / "batches.json"   # submitted batch ids, written by check_answers.py
RESULTS_FILE = HERE / "results.jsonl"  # one verdict per line, keyed by problem id
REPORTED_FILE = HERE / "reported.json"  # findings already sent to problem_reports

csv.field_size_limit(sys.maxsize)


def load_problems(csv_path):
    path = Path(os.path.expanduser(csv_path))
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["id"] = str(r["id"]).strip()
    return rows


def select_rows(rows, ids=None, min_id=None, max_id=None, skip_bad=False,
                only_finalized=False, limit=None):
    out = []
    want = {str(i) for i in ids} if ids else None
    for r in rows:
        pid = int(r["id"])
        if want is not None and r["id"] not in want:
            continue
        if min_id is not None and pid < min_id:
            continue
        if max_id is not None and pid > max_id:
            continue
        if skip_bad and r.get("bad_problem", "").strip().lower() == "true":
            continue
        if only_finalized and r.get("finalized", "").strip().lower() != "true":
            continue
        out.append(r)
    if limit:
        out = out[:limit]
    return out


def parse_ids(s):
    """'12,15,20-25' -> ['12','15','20',...,'25']"""
    if not s:
        return None
    ids = []
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            ids.extend(str(i) for i in range(int(a), int(b) + 1))
        elif part:
            ids.append(part)
    return ids


def load_cache(pid):
    p = CACHE_DIR / f"{pid}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def load_results():
    results = {}
    if RESULTS_FILE.exists():
        for line in RESULTS_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                results[str(rec["id"])] = rec  # later lines win
    return results


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"batches": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
