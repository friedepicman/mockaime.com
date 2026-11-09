"""Step B: have Claude read each official PDF and write down its problems and answers.

Every PDF under answer_check/pdfs/ is sent to Claude once (Batch API, half price).
The result is answer_check/data/official_pdfs.jsonl: one line per PDF with the
problems it contains and, for solution/answer PDFs, the official answers.
check_answers.py then uses these (plus data/official_mathpix.csv from your earlier
Mathpix run) as evidence.

    python answer_check/read_pdfs.py run --contests bmt,cmimc,purple   # skip ones Mathpix already covers
    python answer_check/read_pdfs.py run --limit 3 --now                # quick test
    python answer_check/read_pdfs.py status
    python answer_check/read_pdfs.py collect
"""
import argparse
import base64
import json
import sys
import time

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from official import OFFICIAL_JSONL, PDF_DIR, contest_of, load_pdf_results

STATE = PDF_DIR.parent / "data" / "pdf_batches.json"
MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_BATCH_BYTES = 180 * 1024 * 1024

SCHEMA = {
    "type": "object",
    "properties": {
        "contest": {"type": "string"},
        "year": {"type": "integer"},
        "round": {"type": "string"},
        "kind": {"type": "string", "enum": ["problems", "solutions", "answers", "other"]},
        "items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "number": {"type": "string", "description": "problem number as printed, e.g. 7 or A3"},
                "problem": {"type": "string", "description": "full problem statement in LaTeX"},
                "answer": {"type": "string", "description": "official final answer in LaTeX, or empty if this PDF has none"},
                "solution_excerpt": {"type": "string", "description": "at most 2 sentences of the official solution, or empty"},
            },
            "required": ["number", "problem", "answer", "solution_excerpt"],
            "additionalProperties": False}},
    },
    "required": ["contest", "year", "round", "kind", "items"],
    "additionalProperties": False,
}

PROMPT = """This PDF is from a math competition ({hint}). Transcribe every problem in it.

For each problem give its number as printed, the full statement in LaTeX (keep all numbers and conditions exactly), and the official final answer if this PDF states one (solutions and answer-key PDFs do; a problems-only PDF does not, so leave answer empty). Do not solve anything yourself. Add at most two sentences of the official solution when there is one. For a diagram, describe what it shows in one sentence inside the statement.

Also give the contest name, year, round (e.g. Algebra, Geometry, Team, Guts, Individual, Power) and what kind of PDF this is."""


def all_pdfs():
    return sorted(p for p in PDF_DIR.rglob("*.pdf") if p.stat().st_size > 0)


def params(path, model):
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return {
        "model": model,
        "max_tokens": 32000,
        "output_config": {"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        "messages": [{"role": "user", "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}},
            {"type": "text", "text": PROMPT.format(hint=path.stem.replace("_", " "))},
        ]}],
    }


def rel(path):
    return str(path.relative_to(PDF_DIR))


def save(path_rel, msg, model):
    rec = {"file": path_rel, "model": model}
    if msg is None:
        rec["error"] = "failed"
    elif msg.stop_reason in ("refusal", "max_tokens"):
        rec["error"] = msg.stop_reason
    else:
        text = next((b.text for b in msg.content if b.type == "text"), "")
        try:
            rec.update(json.loads(text))
        except json.JSONDecodeError:
            rec["error"] = "bad_json"
    OFFICIAL_JSONL.parent.mkdir(exist_ok=True)
    with OFFICIAL_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"batches": []}


def cmd_run(args):
    done = load_pdf_results()
    pdfs = [p for p in all_pdfs() if args.redo or rel(p) not in done or "error" in done[rel(p)]]
    if args.contests:
        want = {c.strip().lower() for c in args.contests.split(",")}
        pdfs = [p for p in pdfs if contest_of(p.stem) in want]
    big = [p for p in pdfs if p.stat().st_size > MAX_PDF_BYTES]
    pdfs = [p for p in pdfs if p.stat().st_size <= MAX_PDF_BYTES]
    if args.limit:
        pdfs = pdfs[:args.limit]
    print(f"{len(pdfs)} PDFs to read" + (f" ({len(big)} skipped as over 30MB)" if big else ""))
    if not pdfs:
        return
    client = anthropic.Anthropic()
    if args.now:
        for i, p in enumerate(pdfs, 1):
            try:
                with client.messages.stream(**params(p, args.model)) as s:
                    msg = s.get_final_message()
            except anthropic.APIError as e:
                print(f"[{i}/{len(pdfs)}] {rel(p)}: API error {e}")
                continue
            rec = save(rel(p), msg, args.model)
            print(f"[{i}/{len(pdfs)}] {rel(p)}: {rec.get('error') or str(len(rec['items'])) + ' problems, kind ' + rec['kind']}")
        return
    state = load_state()
    batch, size = [], 0

    def flush():
        nonlocal batch, size
        if not batch:
            return
        b = client.messages.batches.create(requests=[r for r, _ in batch])
        state["batches"].append({"id": b.id, "model": args.model, "files": {r["custom_id"]: f for r, f in batch},
                                 "collected": False})
        STATE.parent.mkdir(exist_ok=True)
        STATE.write_text(json.dumps(state, indent=1))
        print(f"submitted batch {b.id} with {len(batch)} PDFs")
        batch, size = [], 0

    for i, p in enumerate(pdfs):
        if size + p.stat().st_size * 1.4 > MAX_BATCH_BYTES:
            flush()
        cid = f"pdf{i}_{int(time.time())}"
        batch.append((Request(custom_id=cid, params=MessageCreateParamsNonStreaming(**params(p, args.model))), rel(p)))
        size += p.stat().st_size * 1.4
    flush()
    print("Check with: status   (then: collect)")


def cmd_status(args):
    client = anthropic.Anthropic()
    for b in load_state()["batches"]:
        info = client.messages.batches.retrieve(b["id"])
        c = info.request_counts
        print(f"{b['id']}  {info.processing_status:11}  ok {c.succeeded}  err {c.errored}  processing {c.processing}  collected={b['collected']}")


def cmd_collect(args):
    client = anthropic.Anthropic()
    state = load_state()
    for b in state["batches"]:
        if b["collected"]:
            continue
        if client.messages.batches.retrieve(b["id"]).processing_status != "ended":
            print(f"{b['id']} still running")
            continue
        n = 0
        for res in client.messages.batches.results(b["id"]):
            f = b["files"][res.custom_id]
            save(f, res.result.message if res.result.type == "succeeded" else None, b["model"])
            n += 1
        b["collected"] = True
        STATE.write_text(json.dumps(state, indent=1))
        print(f"collected {n} PDFs from {b['id']}")
    done = load_pdf_results()
    ok = [r for r in done.values() if "error" not in r]
    print(f"{len(ok)} PDFs read, {sum(len(r['items']) for r in ok)} problems, "
          f"{sum(1 for r in ok for it in r['items'] if it['answer'].strip())} with an official answer; "
          f"{len(done) - len(ok)} failed (rerun `run` to retry)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--contests", help="comma list: hmmt,pumac,smt,bmt,cmimc,purple")
    r.add_argument("--limit", type=int)
    r.add_argument("--now", action="store_true", help="read right away instead of batching")
    r.add_argument("--redo", action="store_true")
    r.add_argument("--model", default="claude-opus-5-5")
    r.set_defaults(func=cmd_run)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("collect").set_defaults(func=cmd_collect)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
