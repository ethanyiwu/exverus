from fire import Fire

from vinv.cfbench.curate import get_cf_problems, problem_to_id
from vinv.config import CF_BENCHMARK_ROOT_DIR, PROMPT_ROOT_DIR
from vinv.gen.client import request_conversation_one
from vinv.gen.prompt_utils import read_solution_gen_prompt


def compile_solution_gen_prompt(prompt_type: str, problem_statement: str) -> str:
    """
    Compile the solution generation prompt for Rust solutions.

    Args:
        prompt_type (str): The type of prompt to compile.
        problem_statement (str): The problem statement to include in the prompt.

    Returns:
        str: The compiled prompt.
    """
    solution_gen_prompt = read_solution_gen_prompt(prompt_type)

    return solution_gen_prompt.replace("<problem_statement>", problem_statement)


def main(
    model: str = "gpt-4o",
):
    """
    Generate Rust solutions for specified Codeforces problems.
    """
    # Get the specified problems
    cf_problems = get_cf_problems(use_specified_problem=True)

    prompt_file = PROMPT_ROOT_DIR / "cf_rust_solution_gen.txt"

    # Create a directory for the generated solutions
    solutions_dir = CF_BENCHMARK_ROOT_DIR / "gpt_solutions" / "rust"
    solutions_dir.mkdir(parents=True, exist_ok=True)

    for problem in cf_problems:
        problem_id = problem_to_id(problem)
        solution_dir = solutions_dir / problem_id
        solution_dir.mkdir(parents=True, exist_ok=True)
        solution_file = solution_dir / "solution.rs"
        problem_statement = problem["description"]
        prompt = compile_solution_gen_prompt("rust_solution_gen", problem_statement)
        print(f"Generating solution for problem {problem_id}...")
        response = request_conversation_one(
            [
                {
                    "role": "system",
                    "content": "You are an experienced Rust and formal language programmer. You are very familiar with Rust and Verus, which is a tool for verifying the correctness of code written in Rust.",
                },
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=1.0,
            task_id=problem_id,
            prompt_type_id="cf_solution_gen",
        )
        prompt_file = solution_dir / "prompt.txt"
        response_file = solution_dir / "response.txt"
        with open(prompt_file, "w") as f:
            f.write(prompt)
        with open(response_file, "w") as f:
            f.write(response)
        # parse the response to extract the Rust solution
        solution_code = response.split("```rust")[1].split("```")[0].strip()
        with open(solution_file, "w") as f:
            f.write(solution_code)


if __name__ == "__main__":
    Fire(main)
