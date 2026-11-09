# Answer checker

Checks every problem's stored `aime_answer` against its original source, taking the rewrite into account.

**How it works.** For each problem, Claude gets the original problem, the original answer and solution stored in Supabase, the matching problem and official answer from the contest's own PDFs (when one is found), your rewritten problem, and the stored `aime_answer`. It works out the original answer (solving the problem itself when the evidence is thin or disagrees), converts it the way the rewrite asks (2√2 written as a√b, so a+b = 4), and gives a verdict: `correct`, `incorrect`, `rewrite_changes_problem`, `ambiguous_rewrite`, or `unverifiable`.

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
CSV="$HOME/Downloads/problems_rows 2.csv"     # or most_recent_data/problems_rows.csv

# A. download the official contest PDFs into answer_check/pdfs/ (resumable)
python answer_check/download_pdfs.py               # all six contests
python answer_check/download_pdfs.py bmt --list    # see what the BMT crawler finds first

# B. Claude reads each PDF once and writes down its problems + official answers
#    (HMMT/PUMaC/SMT are already in data/official_mathpix.csv, so start with the rest)
python answer_check/read_pdfs.py run --contests bmt,cmimc,purple
python answer_check/read_pdfs.py status
python answer_check/read_pdfs.py collect

# C. pilot: check 20 problems right away at normal price
python answer_check/check_answers.py run --csv "$CSV" --limit 20 --now
python answer_check/check_answers.py collect --csv "$CSV" --skip-fetch
#    -> open answer_check/review.csv

# D. everything, through the Batch API (half price, usually under an hour)
python answer_check/check_answers.py run --csv "$CSV"
python answer_check/check_answers.py status
python answer_check/check_answers.py collect --csv "$CSV"

# E. send findings to the admin reports page
python answer_check/check_answers.py push --dry-run    # preview
python answer_check/check_answers.py push              # incorrect / changed / ambiguous, medium+ confidence
```

**How official answers reach the checker.** `official.py` loads `data/official_mathpix.csv` (5,660 HMMT/PUMaC/SMT problems from your October Mathpix run) and `data/official_pdfs.jsonl` (written by `read_pdfs.py`), plus Purple Comet's answer tables. For each database problem it picks the closest official problems from the same contest and year by text similarity, and Claude confirms it's the same problem before trusting its answer. Before any new PDFs, about 2,270 of your problems already have an official answer this way.

`push` remembers what it already sent (`reported.json`), so rerunning it only sends new findings. `--min-confidence high` or `--verdicts incorrect` narrow it down.

`fetch_aops.py` (AoPS threads) is optional and currently blocked by AoPS's bot check; the checker works without it.

Useful flags for `run`: `--ids 9888-11914`, `--min-id`, `--max-id`, `--limit`, `--skip-bad`, `--only-finalized`, `--model claude-sonnet-5-5` (about half the cost), `--effort low|medium|high`, `--redo`, and `--dry-run` (prints the first prompt without calling the API).

Problems that already have a result are skipped, so rerunning only checks new or failed ones. `collect` prints the running cost.

## Outputs

- `review.csv`: one row per problem, worst first (incorrect, then changed rewrites, ambiguous, unverifiable, correct), with the stored and expected answers and a short note.
- `proposed_fixes.sql`: `UPDATE` statements only for `incorrect` + `high` confidence. Read it before running it in the Supabase SQL editor.
- `results.jsonl`, `batches.json`, `reported.json`, `aops_cache/`: working files.
