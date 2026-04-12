# llm_as_judge.py
"""
Automatically reads files with the same name from analysis/data/unverified and 
analysis/data/verified, compares the diff, and calls the OpenAI LLM to classify the fix type.
Classification:
1. invariant non-inductive
2. invariant wrong fact
3. unsoundness
4. other
"""
import os
import difflib
import json
from openai import OpenAI # Modification 1: Import the OpenAI class

# Read the API KEY and create a client instance
# This is the recommended way for v1.x
# The client will automatically read the key from the 'OPENAI_API_KEY' environment variable
client = OpenAI() # Modification 2: Create an OpenAI client instance

UNVERIFIED_DIR = os.path.join(os.path.dirname(__file__), '../data/unverified')
VERIFIED_DIR = os.path.join(os.path.dirname(__file__), '../data/verified')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'judge_results.json')

CATEGORIES = [
    "invariant non-inductive",
    "invariant wrong fact",
    "unsoundness",
    "other"
]

PROMPT_TEMPLATE = '''You are an expert in program fix classification. Based on the diff below, please determine which category the fix belongs to:
1. invariant non-inductive: The fix is a pure strengthening of the invariant, such as only adding an invariant, or modifying an invariant to make it tighter.
2. invariant wrong fact: The fix involves deleting or modifying the invariant, but it is not a pure strengthening.
3. unsoundness: The fix is the addition of an assert, or the addition of a proof block that is necessary only due to Verus's incompleteness.
4. other: Does not belong to the above three categories. Corner cases also fall into this category.

Please output only the category name and nothing else.

Original program:
{unverified}

Fixed program:
{verified}

diff:
{diff}
'''

def get_file_pairs(unverified_dir, verified_dir):
    unverified_files = set(os.listdir(unverified_dir))
    verified_files = set(os.listdir(verified_dir))
    return list(unverified_files & verified_files)

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def get_diff(text1, text2):
    diff = difflib.unified_diff(
        text1.splitlines(), text2.splitlines(), lineterm=''
    )
    return '\n'.join(diff)

def classify_with_llm(unverified, verified, diff):
    prompt = PROMPT_TEMPLATE.format(unverified=unverified, verified=verified, diff=diff)
    
    # Modification 3: Use the client instance to call chat.completions.create
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    category = response.choices[0].message.content.strip().lower()
    # Only keep valid categories
    for c in CATEGORIES:
        if c in category:
            return c
    return "other"

def main():
    pairs = get_file_pairs(UNVERIFIED_DIR, VERIFIED_DIR)
    results = []
    for filename in pairs:
        unverified_path = os.path.join(UNVERIFIED_DIR, filename)
        verified_path = os.path.join(VERIFIED_DIR, filename)
        unverified = read_file(unverified_path)
        verified = read_file(verified_path)
        diff = get_diff(unverified, verified)
        category = classify_with_llm(unverified, verified, diff)
        results.append({
            "filename": filename,
            "category": category,
            "diff": diff
        })
        print(f"{filename}: {category}")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Classification results have been saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()