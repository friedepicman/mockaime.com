import openai
import json
import time

# 🚨 Keep your API key private in real use
client = openai.OpenAI(api_key="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")

def clean_with_gpt(text):
    prompt = (
        "Here is a math competition problem. The LaTeX is correct, but the punctuation "
        "(commas, periods, etc.) is missing. Fix the punctuation only and only return the updated problem statement.\n\n"
        f"Text: {text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


# 🧠 Load the problems
with open("CMIMC_answers.json", "r", encoding="utf-8") as f:
    problems = json.load(f)

# 🛠 Clean each problem text
updated = []
for i, prob in enumerate(problems):
    original = prob.get("text", "")
    try:
        cleaned_text = clean_with_gpt(original)
        prob["text"] = cleaned_text
        updated.append(prob)
        print(f"✅ Processed {i+1}/{len(problems)}")
        time.sleep(1.5)  # ⏱ Avoid rate limits (adjust if needed)
    except Exception as e:
        print(f"❌ Error at index {i}: {e}")
        updated.append(prob)  # Keep original in case of error

# 💾 Save to new file
with open("CMIMC_punctuated.json", "w", encoding="utf-8") as f:
    json.dump(updated, f, indent=2, ensure_ascii=False)

print("🎉 Done! Saved to CMIMC_punctuated.json")
