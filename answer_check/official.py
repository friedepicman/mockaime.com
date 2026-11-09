"""Official answer keys: load them and find the entry that matches a database problem."""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF_DIR = HERE / "pdfs"
MATHPIX_CSV = HERE / "data" / "official_mathpix.csv"   # from the October Mathpix + Claude run
OFFICIAL_JSONL = HERE / "data" / "official_pdfs.jsonl"  # written by read_pdfs.py

csv.field_size_limit(sys.maxsize)

CONTESTS = {"hmmt": "hmmt", "pumac": "pumac", "smt": "smt", "bmt": "bmt", "cmimc": "cmimc",
            "purple": "purple", "purplecomet": "purple"}


def contest_of(text):
    """'PurpleComet_2024_HS_Problems' / 'Purple Comet 2014 ...' / 'HMMT February ...' -> short key."""
    first = re.split(r"[\s_/]+", (text or "").strip())[0].lower()
    return CONTESTS.get(first, first)


def year_of(text):
    m = re.search(r"(?<!\d)((?:19|20)\d\d)(?!\d)", text or "")
    return m.group(1) if m else None


def tokens(text):
    t = re.sub(r"\\[a-zA-Z]+", " ", (text or "").lower())
    return set(re.findall(r"[a-z]{3,}|\d+", t))


def load_pdf_results():
    out = {}
    if OFFICIAL_JSONL.exists():
        for line in OFFICIAL_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                out[rec["file"]] = rec
    return out


def _purple_answers():
    """Answer tables saved by purple_comet_scraper.py: answers/PurpleComet_<year>_<div>_Answers.csv"""
    out = {}
    for p in PDF_DIR.rglob("PurpleComet_*_Answers.csv"):
        m = re.match(r"PurpleComet_(\d{4})_([A-Za-z]+)_Answers", p.stem)
        if not m:
            continue
        with p.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                out[(m.group(1), m.group(2).upper(), str(row.get("problem", "")).strip())] = row.get("answer", "")
    return out


def load_official():
    entries = []
    if MATHPIX_CSV.exists():
        with MATHPIX_CSV.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                entries.append({"label": r["source"], "origin": "official PDF (Mathpix)",
                                "problem": r.get("problem", ""), "answer": r.get("answer", ""),
                                "solution": (r.get("solution") or "")[:1500]})
    purple = _purple_answers()
    for rec in load_pdf_results().values():
        if "error" in rec:
            continue
        stem = Path(rec["file"]).stem
        m = re.match(r"PurpleComet_(\d{4})_([A-Za-z]+)_", stem)
        for it in rec.get("items", []):
            ans = it.get("answer", "")
            if not ans.strip() and m:
                ans = purple.get((m.group(1), m.group(2).upper(), it["number"].strip().lstrip("#")), "")
            entries.append({"label": f"{stem.replace('_', ' ')} #{it['number']}",
                            "origin": f"official PDF ({rec['file']})",
                            "problem": it.get("problem", ""), "answer": ans,
                            "solution": it.get("solution_excerpt", "")})
    for e in entries:
        e["contest"], e["year"], e["tokens"] = contest_of(e["label"]), year_of(e["label"]), tokens(e["problem"])
    return entries


PURPLE_SRC = re.compile(r"Purple Comet\s+((?:19|20)\d\d)\s+(High|Middle) School\s+#(\d+)", re.I)


class Matcher:
    def __init__(self, entries=None):
        self.purple = _purple_answers()
        self.by_key = defaultdict(list)
        self.by_contest = defaultdict(list)
        for e in (entries if entries is not None else load_official()):
            self.by_key[(e["contest"], e["year"])].append(e)
            self.by_contest[e["contest"]].append(e)

    def candidates(self, row, k=3, min_score=0.25):
        """Best official entries for a database row, merging duplicates that share an answer."""
        c, y = contest_of(row.get("source")), year_of(row.get("source"))
        direct = []
        m = PURPLE_SRC.search(row.get("source") or "")
        if m:
            div = "HS" if m.group(2).lower() == "high" else "MS"
            ans = self.purple.get((m.group(1), div, m.group(3)), "")
            if ans.strip():
                direct = [(1.0, {"label": f"Purple Comet {m.group(1)} {div} answer key #{m.group(3)}",
                                 "origin": "official answer table on purplecomet.org (matched by year, division and number, not by text)",
                                 "problem": "(not transcribed)", "answer": ans, "solution": ""})]
        pool = self.by_key.get((c, y)) or self.by_contest.get(c, [])
        t = tokens(row.get("text"))
        if not t or not pool:
            return direct
        scored = sorted(((len(t & e["tokens"]) / len(t | e["tokens"]), e) for e in pool if e["tokens"]),
                        key=lambda x: -x[0])
        out = []
        for s, e in scored:
            if s < min_score or len(out) >= k:
                break
            # prefer an entry that has an answer if the same problem appears twice
            if any(o["problem"][:80] == e["problem"][:80] for _, o in out):
                continue
            out.append((round(s, 2), e))
        out.sort(key=lambda x: (-x[0], not x[1]["answer"].strip()))
        return (direct + out)[:k]
