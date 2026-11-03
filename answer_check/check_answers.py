"""Step 2: have Claude check every stored AIME answer against the original source.

For each problem Claude sees the original problem, the original answer and solution
stored in the database, the AoPS thread saved by fetch_aops.py (if any), your
rewritten problem, and the stored aime_answer. It works out what the original
answer is, converts it the way your rewrite asks (e.g. 2+sqrt(3) -> "a+sqrt(b), find
a+b" -> 5), and says whether the stored aime_answer is right.

Needs ANTHROPIC_API_KEY in your environment (never paste it into a script).

    # quick pilot, answers come back in a minute or two (normal price)
    python answer_check/check_answers.py run --csv "~/Downloads/problems_rows 2.csv" --limit 20 --now

    # the full pass through the Batch API (half price, usually done within an hour)
    python answer_check/check_answers.py run --csv "~/Downloads/problems_rows 2.csv"
    python answer_check/check_answers.py status
    python answer_check/check_answers.py collect --csv "~/Downloads/problems_rows 2.csv"

`collect` writes answer_check/review.csv (problems needing a look first) and
answer_check/proposed_fixes.sql (high-confidence fixes only).

`push` sends the findings to the Supabase problem_reports table, where they show up
on admin_reports.html under "From answer checker". Accepting one there updates
aime_answer. Nothing else in these scripts writes to the database.

    python answer_check/check_answers.py push --dry-run     # see what would be sent
    python answer_check/check_answers.py push
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from common import (HERE, REPORTED_FILE, RESULTS_FILE, load_cache, load_problems, load_results,
                    load_state, parse_ids, save_state, select_rows)

DEFAULT_MODEL = "claude-opus-5-5"
# $ per million tokens (input, output); batch is half of this.
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0),
          "claude-haiku-5-5": (0.10, 0.50)}

VERDICTS = ["correct", "incorrect", "rewrite_changes_problem", "ambiguous_rewrite", "unverifiable"]

SYSTEM_PROMPT = """You audit answers for mockaime.com, a site that turns problems from contests like HMMT, PUMaC, SMT, BMT, CMIMC and Purple Comet into AIME-style problems.

Every problem was taken from a source contest and often rewritten so that its answer is an integer, AIME-style. Typical rewrites:
- "Compute sqrt(2)+sqrt(2)" becomes "The value can be written as a*sqrt(b), where b is squarefree. Find a+b." (2*sqrt(2) -> 4)
- "Find the probability..." becomes "...can be written as m/n for relatively prime positive integers m and n. Find m+n."
- "Find x mod 3" becomes "Compute the remainder when x is divided by 3."
- A non-integer answer like 9*pi becomes "The perimeter is k*pi. Find k."
A rewrite that keeps the same problem but asks for an integer encoding of the original answer is normal and is NOT an error.

Your job for one problem:
1. Establish the ORIGINAL problem's answer. Evidence, best first: the official answer or a solution in the AoPS thread that others agree with; the solution stored in the database; the answer stored in the database. Stored answers were extracted automatically and can be wrong, and AoPS posts can be wrong or disagree. When the evidence is missing, thin, or conflicting, solve the original problem yourself and say so.
2. Read the REWRITTEN problem exactly as written. Check it asks about the same mathematical object as the original (same numbers, same conditions). Then convert the original answer into the quantity the rewrite asks for, respecting its conventions (squarefree, relatively prime, simplest form, which variables are summed). Do this arithmetic carefully.
3. Compare that expected value with the stored aime_answer.

Verdicts:
- correct: the stored aime_answer is what the rewritten problem asks for.
- incorrect: the rewrite is fine but the stored aime_answer is wrong. Before choosing this, recheck both your original answer and your conversion; give the right value in expected_aime_answer.
- rewrite_changes_problem: the rewritten problem no longer matches the original (changed numbers or conditions, lost information, a different question), so the source answer does not apply to it.
- ambiguous_rewrite: the rewrite's requested form is underspecified so more than one integer could be "right" (e.g. missing "relatively prime" or "squarefree").
- unverifiable: you cannot determine the answer with reasonable confidence (e.g. it depends on a missing diagram).

Confidence is high only if the source evidence and your own check agree. AIME answers are integers from 0 to 999; if the correct answer falls outside that range, still judge correctness and mention it in notes.

Keep notes to at most three short sentences, enough for the site owner to act on: what the original answer is, how it converts, and what is wrong if anything."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "original_answer": {"type": "string",
                            "description": "Answer to the original source problem, in LaTeX if needed."},
        "original_answer_basis": {"type": "string",
                                  "enum": ["aops_thread", "db_solution", "db_answer", "own_solution", "none"]},
        "sources_agree": {"type": "boolean",
                          "description": "Whether the AoPS thread, the stored solution and stored answer agree."},
        "expected_aime_answer": {"type": "string",
                                 "description": "The integer the rewritten problem should have, or empty if unknown."},
        "verdict": {"type": "string", "enum": VERDICTS},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "notes": {"type": "string"},
    },
    "required": ["original_answer", "original_answer_basis", "sources_agree",
                 "expected_aime_answer", "verdict", "confidence", "notes"],
    "additionalProperties": False,
}


def block(tag, text):
    text = (text or "").strip()
    return f"<{tag}>\n{text if text else '(none)'}\n</{tag}>"


def build_prompt(r):
    thread = load_cache(r["id"])
    if thread and thread.get("posts"):
        posts = "\n\n".join(f"--- post {i} by {p.get('author') or '?'} ---\n{p['text']}"
                            for i, p in enumerate(thread["posts"], 1))
        thread_txt = f"Topic title: {thread.get('title','')}\n\n{posts}"
    else:
        thread_txt = "(not fetched; rely on the stored solution and your own work)"
    rewritten = r.get("rewritten_problem", "").strip()
    original = r.get("text", "").strip()
    if not rewritten or rewritten == original:
        rewritten_note = "(identical to the original problem)"
        rewritten = rewritten or original
    else:
        rewritten_note = ""
    return "\n\n".join([
        f"Problem id {r['id']}. Source: {r.get('source','')}. Link: {r.get('link','')}",
        block("original_problem", original),
        block("stored_original_answer", r.get("answer")),
        block("stored_solution", r.get("solution")),
        block("aops_thread", thread_txt),
        block("rewritten_problem", f"{rewritten_note}\n{rewritten}".strip()),
        block("stored_aime_answer", r.get("aime_answer")),
        "Check the stored aime_answer and reply in the required JSON format.",
    ])


def params_for(r, model, effort):
    return {
        "model": model,
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort,
                          "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": build_prompt(r)}],
    }


def parse_message(msg):
    if msg.stop_reason == "refusal":
        return {"error": "refusal"}
    if msg.stop_reason == "max_tokens":
        return {"error": "max_tokens"}
    text = next((b.text for b in msg.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "bad_json", "raw": text[:500]}


def append_result(pid, data, msg, model, batch):
    rec = {"id": pid, "model": model, "batch": batch, **data}
    if msg is not None:
        u = msg.usage
        rec["usage"] = {"input": u.input_tokens + (u.cache_read_input_tokens or 0)
                        + (u.cache_creation_input_tokens or 0),
                        "output": u.output_tokens}
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def cmd_run(args):
    rows = select_rows(load_problems(args.csv), ids=parse_ids(args.ids), min_id=args.min_id,
                       max_id=args.max_id, skip_bad=args.skip_bad,
                       only_finalized=args.only_finalized)
    done = load_results()
    if not args.redo:
        rows = [r for r in rows if r["id"] not in done or "error" in done[r["id"]]]
    rows = [r for r in rows if r.get("aime_answer", "").strip()]
    if args.limit:
        rows = rows[:args.limit]
    cached = sum(1 for r in rows if load_cache(r["id"]))
    print(f"{len(rows)} problems to check ({cached} with a saved AoPS thread), model {args.model}, effort {args.effort}")
    if not rows:
        return
    if args.dry_run:
        print("\n" + "=" * 70 + "\n" + build_prompt(rows[0]))
        return
    client = anthropic.Anthropic()

    if args.now:
        def one(r):
            msg = client.messages.create(**params_for(r, args.model, args.effort))
            return r, msg
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(one, r) for r in rows]
            for i, fut in enumerate(as_completed(futs), 1):
                try:
                    r, msg = fut.result()
                except anthropic.APIError as e:
                    print(f"[{i}/{len(rows)}] API error: {e}")
                    continue
                data = parse_message(msg)
                append_result(r["id"], data, msg, args.model, None)
                print(f"[{i}/{len(rows)}] {r['id']}: {data.get('verdict', data.get('error'))}")
        print("Now run: collect")
        return

    requests = [Request(custom_id=f"p{r['id']}",
                        params=MessageCreateParamsNonStreaming(**params_for(r, args.model, args.effort)))
                for r in rows]
    state = load_state()
    for start in range(0, len(requests), 5000):
        chunk = requests[start:start + 5000]
        batch = client.messages.batches.create(requests=chunk)
        state["batches"].append({"id": batch.id, "model": args.model, "count": len(chunk),
                                 "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "collected": False})
        save_state(state)
        print(f"submitted batch {batch.id} with {len(chunk)} problems")
    print("Check progress with: status   (then: collect)")


def cmd_status(args):
    client = anthropic.Anthropic()
    for b in load_state()["batches"]:
        info = client.messages.batches.retrieve(b["id"])
        c = info.request_counts
        print(f"{b['id']}  {info.processing_status:11}  ok {c.succeeded}  err {c.errored}  "
              f"processing {c.processing}  expired {c.expired}  collected={b['collected']}")


def fetch_batch_results(client):
    state = load_state()
    for b in state["batches"]:
        if b["collected"]:
            continue
        info = client.messages.batches.retrieve(b["id"])
        if info.processing_status != "ended":
            print(f"{b['id']} still {info.processing_status}; collecting the others")
            continue
        n = 0
        for res in client.messages.batches.results(b["id"]):
            pid = res.custom_id[1:]
            if res.result.type == "succeeded":
                msg = res.result.message
                append_result(pid, parse_message(msg), msg, b["model"], b["id"])
            else:
                append_result(pid, {"error": res.result.type}, None, b["model"], b["id"])
            n += 1
        b["collected"] = True
        save_state(state)
        print(f"collected {n} results from {b['id']}")


ORDER = {"incorrect": 0, "rewrite_changes_problem": 1, "ambiguous_rewrite": 2,
         "unverifiable": 3, "error": 4, "correct": 5}


def cmd_collect(args):
    if not args.skip_fetch:
        fetch_batch_results(anthropic.Anthropic())
    results = load_results()
    rows = {r["id"]: r for r in load_problems(args.csv)} if args.csv else {}

    # cost
    tin = tout = 0.0
    for rec in results.values():
        u, (pi, po) = rec.get("usage"), PRICES.get(rec.get("model"), (0, 0))
        if u:
            half = 0.5 if rec.get("batch") else 1.0
            tin += u["input"] * pi / 1e6 * half
            tout += u["output"] * po / 1e6 * half
    counts = {}
    for rec in results.values():
        v = rec.get("verdict", "error")
        counts[v] = counts.get(v, 0) + 1
    print(f"{len(results)} problems checked: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"approx. spend so far: ${tin + tout:.2f} (input ${tin:.2f}, output ${tout:.2f})")

    out = HERE / "review.csv"
    fields = ["id", "verdict", "confidence", "stored_aime_answer", "expected_aime_answer",
              "original_answer", "stored_original_answer", "original_answer_basis",
              "sources_agree", "notes", "source", "link", "rewritten_problem"]
    recs = sorted(results.values(), key=lambda x: (ORDER.get(x.get("verdict", "error"), 9),
                                                   {"high": 0, "medium": 1, "low": 2}.get(x.get("confidence"), 3),
                                                   int(x["id"])))
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rec in recs:
            r = rows.get(str(rec["id"]), {})
            w.writerow({
                "id": rec["id"], "verdict": rec.get("verdict", "error:" + rec.get("error", "?")),
                "confidence": rec.get("confidence", ""),
                "stored_aime_answer": r.get("aime_answer", ""),
                "expected_aime_answer": rec.get("expected_aime_answer", ""),
                "original_answer": rec.get("original_answer", ""),
                "stored_original_answer": r.get("answer", ""),
                "original_answer_basis": rec.get("original_answer_basis", ""),
                "sources_agree": rec.get("sources_agree", ""),
                "notes": rec.get("notes", ""), "source": r.get("source", ""),
                "link": r.get("link", ""), "rewritten_problem": r.get("rewritten_problem", ""),
            })
    print(f"wrote {out}")

    sql = HERE / "proposed_fixes.sql"
    lines = ["-- High-confidence answer fixes proposed by check_answers.py.",
             "-- Review each one before running it in the Supabase SQL editor.", "BEGIN;"]
    for rec in recs:
        exp = str(rec.get("expected_aime_answer", "")).strip()
        if rec.get("verdict") == "incorrect" and rec.get("confidence") == "high" and exp.lstrip("-").isdigit():
            stored = rows.get(str(rec["id"]), {}).get("aime_answer", "?")
            note = rec.get("notes", "").replace("\n", " ")
            lines.append(f"-- {rec['id']}: {stored} -> {exp}. {note}")
            lines.append(f"UPDATE problems SET aime_answer = '{exp}' WHERE id = {int(rec['id'])};")
    lines.append("COMMIT;")
    sql.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {sql}")


# The site's public anon key (already in every docs/*.html page). Inserting into
# problem_reports is allowed for anonymous users, which is how the site's own
# report button works. Override with SUPABASE_URL / SUPABASE_ANON_KEY if needed.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ftdbplxkyaocyrjpmjyb.supabase.co")
SUPABASE_ANON_KEY = os.environ.get(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0ZGJwbHhreWFvY3lyanBtanliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIxMDgxMDUsImV4cCI6MjA2NzY4NDEwNX0.hE0V09JxdLYNbZqPVH3HZxNpLPP2rXIaBsNGUHO3upc",
)
CONF_RANK = {"low": 0, "medium": 1, "high": 2}


def report_row(rec):
    exp = str(rec.get("expected_aime_answer", "")).strip()
    is_int = exp.lstrip("-").isdigit()
    rtype = "wrong_answer" if rec["verdict"] == "incorrect" and is_int else "answer_check"
    agent = {k: rec.get(k) for k in ("verdict", "confidence", "original_answer", "original_answer_basis",
                                     "sources_agree", "expected_aime_answer", "notes", "model")}
    agent["checked_at"] = time.strftime("%Y-%m-%d")
    details = {"source": "answer_checker", "report_types": [rtype], "agent": agent,
               "answer_details": rec.get("notes", "")}
    if rtype == "wrong_answer":
        details["proposed_answer"] = exp
    return {"problem_id": int(rec["id"]), "report_type": rtype,
            "details": json.dumps(details, ensure_ascii=False), "user_id": None}


def cmd_push(args):
    results = load_results()
    verdicts = set(args.verdicts.split(","))
    reported = json.loads(REPORTED_FILE.read_text()) if REPORTED_FILE.exists() else {}
    todo = []
    for rec in sorted(results.values(), key=lambda r: int(r["id"])):
        if rec.get("verdict") not in verdicts:
            continue
        if CONF_RANK.get(rec.get("confidence"), 0) < CONF_RANK[args.min_confidence]:
            continue
        key = f"{rec['id']}:{rec.get('verdict')}:{rec.get('expected_aime_answer')}"
        if reported.get(str(rec["id"])) == key and not args.again:
            continue
        todo.append((rec, key))
    print(f"{len(todo)} findings to send (verdicts {sorted(verdicts)}, confidence >= {args.min_confidence})")
    if not todo:
        return
    if args.dry_run:
        for rec, _ in todo[:30]:
            print(f"  {rec['id']}: {rec['verdict']} ({rec['confidence']}) expected {rec.get('expected_aime_answer')}: {rec.get('notes','')[:90]}")
        return
    sent = 0
    for start in range(0, len(todo), 200):
        chunk = todo[start:start + 200]
        body = json.dumps([report_row(rec) for rec, _ in chunk]).encode()
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/problem_reports", data=body, method="POST",
            headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"})
        try:
            urllib.request.urlopen(req, timeout=60).read()
        except urllib.error.HTTPError as e:
            print(f"Supabase refused the insert ({e.code}): {e.read().decode()[:300]}")
            break
        for rec, key in chunk:
            reported[str(rec["id"])] = key
        REPORTED_FILE.write_text(json.dumps(reported, indent=1))
        sent += len(chunk)
        print(f"sent {sent}/{len(todo)}")
    print("Open admin_reports.html and pick 'From answer checker'.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="check problems (Batch API by default)")
    run.add_argument("--csv", required=True)
    run.add_argument("--ids", help="e.g. 6087,9888-9999")
    run.add_argument("--min-id", type=int)
    run.add_argument("--max-id", type=int)
    run.add_argument("--limit", type=int)
    run.add_argument("--skip-bad", action="store_true", help="skip rows marked bad_problem")
    run.add_argument("--only-finalized", action="store_true")
    run.add_argument("--redo", action="store_true", help="recheck problems that already have a result")
    run.add_argument("--model", default=DEFAULT_MODEL)
    run.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    run.add_argument("--now", action="store_true", help="call the API directly instead of batching")
    run.add_argument("--workers", type=int, default=4, help="parallel requests with --now")
    run.add_argument("--dry-run", action="store_true", help="print the first prompt and stop")
    run.set_defaults(func=cmd_run)

    st = sub.add_parser("status", help="show batch progress")
    st.set_defaults(func=cmd_status)

    co = sub.add_parser("collect", help="download finished batches and write review.csv")
    co.add_argument("--csv", help="the same export, to show stored answers in review.csv")
    co.add_argument("--skip-fetch", action="store_true", help="only rebuild review.csv")
    co.set_defaults(func=cmd_collect)

    pu = sub.add_parser("push", help="send findings to the Supabase problem_reports table")
    pu.add_argument("--verdicts", default="incorrect,rewrite_changes_problem,ambiguous_rewrite",
                    help="comma list; add unverifiable to include those too")
    pu.add_argument("--min-confidence", default="medium", choices=["low", "medium", "high"])
    pu.add_argument("--again", action="store_true", help="resend findings already sent")
    pu.add_argument("--dry-run", action="store_true")
    pu.set_defaults(func=cmd_push)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
