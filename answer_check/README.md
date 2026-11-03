# Answer checker

Checks every problem's stored `aime_answer` against its original source, taking the rewrite into account.

**How it works.** For each problem, Claude gets the original problem, the original answer and solution stored in Supabase, the AoPS thread for the problem's link (if you fetched it), your rewritten problem, and the stored `aime_answer`. It works out the original answer (solving the problem itself when the evidence is thin or disagrees), converts it the way the rewrite asks (2√2 written as a√b, so a+b = 4), and gives a verdict: `correct`, `incorrect`, `rewrite_changes_problem`, `ambiguous_rewrite`, or `unverifiable`.

You get a CSV to review, and `push` sends the findings to the `problem_reports` table so they show up on the admin reports page under "From answer checker". Accepting one there sets `aime_answer` (the original `answer` is never touched).

## Setup (once)

```bash
cd ~/Documents/git/math
python3 -m venv .venv && source .venv/bin/activate
pip install -r answer_check/requirements.txt
export ANTHROPIC_API_KEY=...      # put this in ~/.zshrc, never in a script
```

Export the `problems` table from Supabase as CSV (Table editor > Export > CSV).

## Run

```bash
CSV="$HOME/Downloads/problems_rows 2.csv"

# 1. (optional but recommended) save each problem's AoPS thread; resumable, ~3s per problem
python answer_check/fetch_aops.py --csv "$CSV" --limit 20

# 2. pilot: 20 problems, answers in a couple of minutes at normal price
python answer_check/check_answers.py run --csv "$CSV" --limit 20 --now
python answer_check/check_answers.py collect --csv "$CSV" --skip-fetch
#    -> open answer_check/review.csv

# 3. everything, through the Batch API (half price, usually under an hour)
python answer_check/check_answers.py run --csv "$CSV"
python answer_check/check_answers.py status
python answer_check/check_answers.py collect --csv "$CSV"

# 4. send findings to the admin reports page
python answer_check/check_answers.py push --dry-run    # preview
python answer_check/check_answers.py push              # incorrect / changed / ambiguous, medium+ confidence
```

`push` remembers what it already sent (`reported.json`), so rerunning it only sends new findings. `--min-confidence high` or `--verdicts incorrect` narrow it down.

Useful flags for `run` (and `fetch_aops.py`): `--ids 9888-11914`, `--min-id`, `--max-id`, `--limit`. `run` also has `--skip-bad`, `--only-finalized`, `--model claude-sonnet-5-5` (about half the cost), `--effort low|medium|high`, `--redo`, and `--dry-run` (prints the first prompt without calling the API).

Problems that already have a result are skipped, so rerunning only checks new or failed ones. `collect` prints the running cost.

## Outputs

- `review.csv`: one row per problem, worst first (incorrect, then changed rewrites, ambiguous, unverifiable, correct), with the stored and expected answers and a short note.
- `proposed_fixes.sql`: `UPDATE` statements only for `incorrect` + `high` confidence. Read it before running it in the Supabase SQL editor.
- `results.jsonl`, `batches.json`, `reported.json`, `aops_cache/`: working files.
