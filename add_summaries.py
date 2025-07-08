import json
import time
from openai import OpenAI

# === CONFIGURATION ===
JSON_PATH = "all_problems_cleaned_with_source.json"
SAVE_INTERVAL = 10
OPENAI_API_KEY = "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"  # Replace with your actual key

# === INITIALIZE CLIENT ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === LOAD DATA ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)

# === GPT SUMMARIZATION FUNCTION ===
def gpt_summarize(problem: str, solution: str) -> str:
    prompt = f"Summarize the mathematical ideas and techniques used in solving this problem:\n\nProblem: {problem}\n\nSolution: {solution}\n\nSummary:"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()

# === MAIN LOOP ===
num_updated = 0
for i, prob in enumerate(problems):
    # Only process problems that do NOT already have a valid summary
    summary = ''
    if "summary" in prob:
        summary = prob["summary"]
        continue
    else:
        problem_text = prob.get("cleaned_problem", "").strip()
        solution_text = prob.get("cleaned_solution", "").strip()

        if not problem_text or not solution_text:
            print(f"[{i}] ❌ Skipping problem {i} — missing 'problem' or 'cleaned_solution'.")
            continue  # skip if either field is empty or missing

        try:
            summary = gpt_summarize(problem_text, solution_text)
            problems[i]["solution_summary"] = summary
            print(f"[{i}] ✅ Summary added.")
            num_updated += 1

            if num_updated % SAVE_INTERVAL == 0:
                with open(JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(problems, f, indent=2)
                print(f"💾 Auto-saved after {num_updated} updates.")

            time.sleep(1)

        except Exception as e:
            print(f"[{i}] ❌ Error: {e}")
            continue

# === FINAL SAVE ===
if num_updated > 0:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2)
    print(f"\n💾 Final save complete. {num_updated} summaries added.")
else:
    print("✅ No new summaries added — all problems already summarized or missing data.")
