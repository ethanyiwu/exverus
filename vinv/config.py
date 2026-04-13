import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
ORI_BENCHMARK_ROOT_DIR = ROOT_DIR / "verus-proof-synthesis" / "benchmarks"
AUTOVERUS_TOOL_DIR = ROOT_DIR / "verus-proof-synthesis"
CLEANED_BENCHMARK_ROOT_DIR = ROOT_DIR / "cleaned-verusbench"
ADDITIONAL_BENCHMARK_ROOT_DIR = ROOT_DIR / "Benchmarks"
PROMPT_ROOT_DIR = ROOT_DIR / "vinv" / "prompt"
RESULTS_ROOT_DIR = ROOT_DIR / "results"
PERTURB_RESULTS_DIR = RESULTS_ROOT_DIR / "perturb"
OBFUSC_RESULTS_DIR = PERTURB_RESULTS_DIR / "obfuscate"
OBFUSC_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ORI_RESULTS_DIR = RESULTS_ROOT_DIR / "ori"
CF_BENCHMARK_ROOT_DIR = ROOT_DIR / "codeforces_problems"
AUTOVERUS_RESULTS_DIR = RESULTS_ROOT_DIR / "autoverus_cleaned_vb"
INV_INJECT_RESULTS_DIR = RESULTS_ROOT_DIR / "inv_inject"
INV_INJECT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# for trajectory result parsing
AUTOVERUS_TRAJECTORY_RESULTS_DIR = Path(
    "/zp_vegeta/scratch_sb/verus_inv_shared_results/results_autoverus_gpt4o_verus_250712"
)
AUTOVERUS_TRAJECOTRY_ENTRY_POINTS = {
    "cloverbench": AUTOVERUS_TRAJECTORY_RESULTS_DIR / "20250830-gpt4o-clover-1.0",
    "diffy": AUTOVERUS_TRAJECTORY_RESULTS_DIR / "20250830-gpt4o-diffy-1.0",
    "mbpp": AUTOVERUS_TRAJECTORY_RESULTS_DIR / "20250831-gpt4o-mbpp-1.0",
    "misc": AUTOVERUS_TRAJECTORY_RESULTS_DIR / "20250831-gpt4o-misc-1.0",
}

_TRAJ_ENTRY_POINTS_MAPPING = {
    "20250830-gpt4o-clover-1.0": "cloverbench",
    "20250830-gpt4o-diffy-1.0": "diffy",
    "20250831-gpt4o-mbpp-1.0": "mbpp",
    "20250831-gpt4o-misc-1.0": "misc",
}

AUTOVERUS_CLEANED_VB_RESULT_JSON_FILE = (
    RESULTS_ROOT_DIR
    / "autoverus_result_json"
    / "output_autoverus_gpt4o_verusbench_filtered.json"
)

AUTOVERUS_ADDITONAL_RESULT_JSON_FILE = (
    RESULTS_ROOT_DIR
    / "autoverus_result_json"
    / "output_autoverus_gpt4o_additional.json"
)

PIPELINE_RESULTS_DIR = RESULTS_ROOT_DIR / "pipeline"
PIPELINE_DEBUG_RESULTS_DIR = RESULTS_ROOT_DIR / "pipeline_debug"
PIPELINE_CLEANED_VB_RESULT_JSON_FILE = (
    PIPELINE_RESULTS_DIR
    / "gpt-4o"
    / "CLEANED_VB"
    / "global_repair_status_z3_mut_val.json"
)
PIPELINE_ADDITONAL_RESULT_JSON_FILE = (
    PIPELINE_RESULTS_DIR
    / "gpt-4o"
    / "ADDITIONAL"
    / "global_repair_status_z3_mut_val.json"
)
TRAJECTORY_RESULT_FILE = (
    RESULTS_ROOT_DIR
    / "autoverus_trajectories_json"
    / "autoverus_gpt4o_verusbench_pass1_trajectories.json"
)

AUTOVERUS_ALMOST_CORRECT_RESULTS_DIR = ROOT_DIR / "Benchmarks" / "one-step-dataset"
VERUS_PATH = shutil.which("verus")
OLD_VERUS_PATH = os.environ.get("OLD_VERUS_PATH")


def resolve_verus_path(use_old_verus: bool = False) -> str:
    if use_old_verus:
        verus_path = os.environ.get("OLD_VERUS_PATH")
        if not verus_path:
            raise EnvironmentError(
                "OLD_VERUS_PATH environment variable is not set. Please set it to the path of the old Verus executable."
            )
        return verus_path

    verus_path = shutil.which("verus")
    if verus_path is None:
        raise EnvironmentError(
            "Verus executable not found in PATH. Please ensure Verus is installed and available."
        )
    return verus_path

# Mutant ranking mode configuration
# - "cex_block": filter out non-compilable candidates, rank by blocked CEXs (default)
# - "veval_score": rank directly by VEval score (see verus-proof-synthesis/code/veval.py)
ALLOWED_MUT_RANKING_MODES = ("cex_block", "veval_score")
mut_ranking_mode = os.environ.get("MUT_RANKING_MODE", "cex_block")
if mut_ranking_mode not in ALLOWED_MUT_RANKING_MODES:
    raise ValueError(
        f"Invalid MUT_RANKING_MODE '{mut_ranking_mode}'. Allowed: {ALLOWED_MUT_RANKING_MODES}"
    )
# Uppercase alias for consistency with other constants
MUT_RANKING_MODE = mut_ranking_mode

NAIVE_REPAIR_PROMPT_FILE = PROMPT_ROOT_DIR / "iterative" / "naive_repair.txt"

COMPILATION_REPAIR_PROMPT_FILE = (
    PROMPT_ROOT_DIR / "iterative" / "compilation_repair.txt"
)

VB_BENCHMARK_VERIFIED_ENTRY_POINTS = {
    # "humaneval": BENCHMARK_ROOT_DIR / "human-eval-verus" / "tasks",
    # "interprocedural": BENCHMARK_ROOT_DIR / "interprocedural" / "AlgorithmRust",
    "cloverbench": ORI_BENCHMARK_ROOT_DIR / "CloverBench" / "verified",
    "diffy": ORI_BENCHMARK_ROOT_DIR / "Diffy" / "verified",
    "mbpp": ORI_BENCHMARK_ROOT_DIR / "MBPP" / "verified",
    "misc": ORI_BENCHMARK_ROOT_DIR / "Misc" / "verified",
    # "svcompnonl": BENCHMARK_ROOT_DIR / "SVComp-Array-fpi-nonl" / "verified"
}

VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS = {
    # "humaneval": BENCHMARK_ROOT_DIR / "human-eval-verus" / "tasks",
    # "interprocedural": BENCHMARK_ROOT_DIR / "interprocedural" / "AlgorithmRust",
    "cloverbench": ORI_BENCHMARK_ROOT_DIR / "CloverBench" / "unverified",
    "diffy": ORI_BENCHMARK_ROOT_DIR / "Diffy" / "unverified",
    "mbpp": ORI_BENCHMARK_ROOT_DIR / "MBPP" / "unverified",
    "misc": ORI_BENCHMARK_ROOT_DIR / "Misc" / "unverified",
    # "svcompnonl": BENCHMARK_ROOT_DIR / "SVComp-Array-fpi-nonl" / "verified"
}

CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS = {
    # "humaneval": BENCHMARK_ROOT_DIR / "human-eval-verus" / "tasks",
    # "interprocedural": BENCHMARK_ROOT_DIR / "interprocedural" / "AlgorithmRust",
    "cloverbench": CLEANED_BENCHMARK_ROOT_DIR / "CloverBench" / "verified",
    "diffy": CLEANED_BENCHMARK_ROOT_DIR / "Diffy" / "verified",
    "mbpp": CLEANED_BENCHMARK_ROOT_DIR / "MBPP" / "verified",
    "misc": CLEANED_BENCHMARK_ROOT_DIR / "Misc" / "verified",
    # "svcompnonl": BENCHMARK_ROOT_DIR / "SVComp-Array-fpi-nonl" / "verified"
}

CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS = {
    # "humaneval": BENCHMARK_ROOT_DIR / "human-eval-verus" / "tasks",
    # "interprocedural": BENCHMARK_ROOT_DIR / "interprocedural" / "AlgorithmRust",
    "cloverbench": CLEANED_BENCHMARK_ROOT_DIR / "CloverBench" / "unverified",
    "diffy": CLEANED_BENCHMARK_ROOT_DIR / "Diffy" / "unverified",
    "mbpp": CLEANED_BENCHMARK_ROOT_DIR / "MBPP" / "unverified",
    "misc": CLEANED_BENCHMARK_ROOT_DIR / "Misc" / "unverified",
    # "svcompnonl": BENCHMARK_ROOT_DIR / "SVComp-Array-fpi-nonl" / "verified"
}

ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS = {
    "humaneval_alphaverus": ADDITIONAL_BENCHMARK_ROOT_DIR
    / "HumanEval_Alphaverus"
    / "verified",
    "leetcode": ADDITIONAL_BENCHMARK_ROOT_DIR / "Leetcode" / "verified",
    "obfuscated_verusbench": ADDITIONAL_BENCHMARK_ROOT_DIR
    / "Obfuscated_Verusbench"
    / "verified",
    "dafnybench": ADDITIONAL_BENCHMARK_ROOT_DIR / "Dafnybench" / "verified",
}

ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS = {
    "humaneval_alphaverus": ADDITIONAL_BENCHMARK_ROOT_DIR
    / "HumanEval_Alphaverus"
    / "unverified",
    "leetcode": ADDITIONAL_BENCHMARK_ROOT_DIR / "Leetcode" / "unverified",
    "obfuscated_verusbench": ADDITIONAL_BENCHMARK_ROOT_DIR
    / "Obfuscated_Verusbench"
    / "unverified",
    "dafnybench": ADDITIONAL_BENCHMARK_ROOT_DIR / "Dafnybench" / "unverified",
}

THREEBENCH_BENCHMARK_VERIFIED_ENTRY_POINTS = {
    benchmark: ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS[benchmark]
    for benchmark in ("humaneval_alphaverus", "leetcode", "dafnybench")
}

THREEBENCH_BENCHMARK_UNVERIFIED_ENTRY_POINTS = {
    benchmark: ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS[benchmark]
    for benchmark in ("humaneval_alphaverus", "leetcode", "dafnybench")
}

VSBHERB_BENCHMARK_VERIFIED_ENTRY_POINTS = {
    "verusage-bench": ADDITIONAL_BENCHMARK_ROOT_DIR / "VeruSAGE-Bench" / "verified",
    "humaneval-rustbench": ADDITIONAL_BENCHMARK_ROOT_DIR
    / "HumanEval-RustBench"
    / "verified",
}

VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS = {
    "verusage-bench": ADDITIONAL_BENCHMARK_ROOT_DIR / "VeruSAGE-Bench" / "unverified",
    "humaneval-rustbench": ADDITIONAL_BENCHMARK_ROOT_DIR
    / "HumanEval-RustBench"
    / "unverified",
}


# proofs that cannot be verified by original verus
VB_VERIFY_FAILED_BLACKLIST = [
    "diffy_res2",
    "misc_deduplicate",
    "misc_reverse",
    "misc_bubble",  # verusbench missing verified
]

# cherry-pick 10 proofs that were solved (invariant mask-filling) without obfuscation for testing
VB_SPECIFIED_TASKIDS = [
    "cloverbench_linear_search2",
    "cloverbench_is_prime",
    "cloverbench_binary_search",
    "mbpp_task_id_804",
    "mbpp_task_id_460",
    "mbpp_task_id_8",
    "misc_choose_odd",
    "misc_binary_search",
    "misc_fib",
    "misc_max_index",
]
# VB_SPECIFIED_TASKIDS = [
#     "cloverbench_all_digits_strong",
#     "diffy_condm",
#     "diffy_s3lif",
#     "mbpp_task_id_414",
#     "cloverbench_array_append_strong",
#     "diffy_condn",
#     "diffy_s42if",
#     "mbpp_task_id_460",
#     "cloverbench_array_concat_strong",
#     "diffy_ms1",
#     "diffy_s4if",
#     "mbpp_task_id_461",
#     "cloverbench_array_copy_strong",
#     "diffy_ms2",
#     "diffy_s4lif",
#     "mbpp_task_id_472",
#     "cloverbench_array_product_strong",
#     "diffy_ms3",
#     "diffy_s52if",
#     "mbpp_task_id_476",
#     "cloverbench_array_sum_strong",
#     "diffy_ms4",
#     "diffy_s5if",
#     "mbpp_task_id_477",
#     "cloverbench_binary_search",
#     "diffy_ms5",
#     "diffy_s5lif",
#     "mbpp_task_id_572",
#     "cloverbench_cal_div",
#     "diffy_res1",
#     "diffy_sina1",
#     "mbpp_task_id_576",
#     "cloverbench_is_prime",
#     "diffy_res1o",
#     "diffy_sina2",
#     "mbpp_task_id_624",
#     "cloverbench_linear_search2",
#     "diffy_res2o",
#     "diffy_sina3",
#     "mbpp_task_id_644",
#     "cloverbench_two_sum",
#     "diffy_s12if",
#     "diffy_sina4",
#     "mbpp_task_id_70",
#     "diffy_brs1",
#     "diffy_s1if",
#     "diffy_sina5",
#     "mbpp_task_id_741",
#     "diffy_brs2",
#     "diffy_s1lif",
#     "mbpp_task_id_105",
#     "mbpp_task_id_769",
#     "diffy_brs3",
#     "diffy_s22if",
#     "mbpp_task_id_113",
#     "mbpp_task_id_798",
#     "diffy_brs4",
#     "diffy_s2if",
#     "mbpp_task_id_161",
#     "mbpp_task_id_8",
#     "diffy_brs5",
#     "diffy_s2lif",
#     "mbpp_task_id_230",
#     "mbpp_task_id_804",
#     "diffy_conda",
#     "diffy_s32if",
#     "mbpp_task_id_240",
#     "mbpp_task_id_95",
#     "diffy_condg",
#     "diffy_s3if",
#     "mbpp_task_id_399",
# ]


def get_autoverus_config_file(model_id: str) -> Path:
    """
    Get the path to the Autoverus configuration file.
    Args:
        model_id (str): The model identifier to select the configuration file.
    Returns:
        config_file (Path): The path to the Autoverus configuration file.
    """
    config_dir = AUTOVERUS_TOOL_DIR / "code"
    config_file = config_dir / f"config_{_simplify_model_id(model_id)}.json"
    if not config_file.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    return config_file


def _simplify_model_id(model_id: str) -> str:
    if model_id == "deepseek/deepseek-chat-v3.1:free":
        return "deepseek-chat-free"
    elif model_id == "deepseek/deepseek-chat-v3.1":
        return "deepseek-chat"
    elif model_id == "qwen/qwen3-coder":
        return "qwen3-coder"
    elif model_id == "o4-mini":
        return "o4-mini"
    elif model_id.startswith("anthropic/claude-"):
        return model_id.replace("anthropic/claude-", "claude-")
    return model_id


def get_results_entry_file() -> Path:
    return ROOT_DIR / "vinv" / "analysis" / "entry.json"
