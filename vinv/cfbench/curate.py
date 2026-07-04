import os
import pickle
from typing import Dict

from datasets import load_dataset
from fire import Fire
from loguru import logger

from vinv.config import CF_SPECIFIED_PROBLEMS

multi_answer_list = [
    "print any of them",
    "If there are multiple solutions, you may output any.",
    "If there are several such trees, output any.",
    "If there are multiple possible solutions",
    "If there are several solutions",
    "The answer will be considered correct,",
    "an interactive problem",
    "its absolute or relative error does not exceed",
    "print in any order",
    "with an accuracy of",
    "in arbitrary order.",
    "If there is more than one solution, find any of them.",
    "If there are multiple answers, print any.",
    "Your answer will be considered correct if its relative or absolute error",
]


def get_cf_problems(use_specified_problem: bool = False):
    """Get Codeforces datasets.

    Load the datasets from dataset.pkl (if existed) or code_contests
    and filter codeforces problems.

    Returns:
    - A list of all codeforces problems
    """
    # Load the dataset
    if not use_specified_problem:
        if os.path.exists("dataset.pkl"):
            with open("dataset.pkl", "rb") as file:
                cf_problems = pickle.load(file)
        else:
            dataset = load_dataset("deepmind/code_contests")
            all_problems = dataset["train"]

            # Filter codeforces data
            cf_problems = all_problems.filter(lambda example: example["source"] == 2)
            with open(r"dataset.pkl", "wb") as file:
                pickle.dump(cf_problems, file)
    else:
        assert len(CF_SPECIFIED_PROBLEMS) > 0, "No specified problem is provided."
        if os.path.exists("specified_problem_dataset.pkl"):
            with open(r"specified_problem_dataset.pkl", "rb") as file:
                cf_problems = pickle.load(file)
                cf_problems = cf_problems.filter(
                    lambda example: example["name"].split(".")[0]
                    in CF_SPECIFIED_PROBLEMS
                )
        else:
            dataset = load_dataset("deepmind/code_contests")
            all_problems = dataset["train"]

            # Filter codeforces data
            cf_problems = all_problems.filter(lambda example: example["source"] == 2)
            cf_problems = cf_problems.filter(
                lambda example: example["name"].split(".")[0] in CF_SPECIFIED_PROBLEMS
            )
            with open(r"specified_problem_dataset.pkl", "wb") as file:
                pickle.dump(cf_problems, file)

    return cf_problems


def idx_to_lang(idx: int) -> str:
    """
    PYTHON = 1
    CPP = 2
    PYTHON3 = 3
    JAVA = 4
    """
    if idx == 1 or idx == 3:
        return "python"
    elif idx == 2:
        return "cpp"
    elif idx == 4:
        return "java"
    else:
        raise ValueError(f"Unknown language index: {idx}")


def have_multiple_cpp_correct_solutions(problem: Dict, solution_num: int = 10) -> bool:
    solution_cnt = len(problem["solutions"]["solution"])
    py_cnt, cpp_cnt, java_cnt = 0, 0, 0
    for solution_idx in range(solution_cnt):
        language_idx = problem["solutions"]["language"][solution_idx]
        if idx_to_lang(language_idx) in ["python", "python3"]:
            py_cnt += 1
        elif idx_to_lang(language_idx) == "cpp":
            cpp_cnt += 1
        elif idx_to_lang(language_idx) == "java":
            java_cnt += 1

    return cpp_cnt >= solution_num


def have_good_solution_length(
    problem: Dict, min_lines: int = 50, max_lines: int = 100
) -> bool:
    """
    Check if the average length of cpp solutions is within a good range.
    A good length is defined as:
    - At least `min_lines` lines of code
    - At most `max_lines` lines of code
    """
    solution_cnt = len(problem["solutions"]["solution"])
    line_count_list = []
    for solution_idx in range(solution_cnt):
        language_idx = problem["solutions"]["language"][solution_idx]
        if idx_to_lang(language_idx) == "cpp":
            code = problem["solutions"]["solution"][solution_idx]
            line_count = len(code.splitlines())
            line_count_list.append(line_count)

    if not line_count_list:
        raise ValueError("No cpp solutions found for the problem.")

    avg_line_count = sum(line_count_list) / len(line_count_list)

    return min_lines <= avg_line_count <= max_lines


def problem_to_id(problem: Dict) -> str:
    return problem["name"].split(".")[0]


def main():
    """
    criteria for filtering:
    1. Skip if the problem accepts multiple answers or the problem is not on the list.
    2. Skip if the problem is not deterministic.
    3. Skip if the problem is too complex, e.g., needs more than 100 lines of cpp code to solve.
    4. Skip if the problem is too simple, e.g., less than 50 lines of cpp code to solve.
    5. At least one loop is required in the solution.
    6. You can write a pure spec function that defines the correct answer declaratively (mathematically).
    """
    problems = get_cf_problems(use_specified_problem=False)
    logger.info(f"Total number of problems: {len(problems)}")
    filtered_problems = [
        problem
        for problem in problems
        if not any(
            multi_answer in problem["description"] for multi_answer in multi_answer_list
        )
    ]
    logger.info(
        f"Number of problems after filtering multi-answer: {len(filtered_problems)}"
    )
    filtered_problems = [
        problem
        for problem in filtered_problems
        if have_multiple_cpp_correct_solutions(problem, solution_num=10)
    ]
    logger.info(
        f"Number of problems after filtering multiple cpp solutions: {len(filtered_problems)}"
    )
    filtered_problems = [
        problem
        for problem in filtered_problems
        if have_good_solution_length(problem, min_lines=50, max_lines=100)
    ]
    logger.info(
        f"Number of problems after filtering good solution length: {len(filtered_problems)}"
    )

    filtered_problem_ids = [problem_to_id(problem) for problem in filtered_problems]
    print(filtered_problem_ids[:50])


if __name__ == "__main__":
    Fire(main)
