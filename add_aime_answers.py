import json
import re

def extract_and_sum_integers(s):
    """
    Extract all integers from a string, sum them, and return sum % 1000.
    """
    if not isinstance(s, str):
        return None
    nums = re.findall(r'-?\d+', s)
    total = sum(abs(int(n)) for n in nums)
    return total % 1000

def main():
    input_file = "bro_please_please.json"
    output_file = "with_aime_answers.json"

    with open(input_file, "r") as f:
        problems = json.load(f)

    count_success = 0
    for problem in problems:
        answer = problem.get("answer")
        aime = None

        if isinstance(answer, int):
            aime = answer % 1000
        elif isinstance(answer, str):
            aime = extract_and_sum_integers(answer)

        if aime is not None:
            problem["aime_answer"] = aime
            count_success += 1

    with open(output_file, "w") as f:
        json.dump(problems, f, indent=2)

    print(f"Added 'aime_answer' to {count_success} problems.")

if __name__ == "__main__":
    main()
