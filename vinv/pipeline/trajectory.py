from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class IterationRecord:
    attempt: int
    target_error: Optional[str] = None
    all_errors: List[str] = field(default_factory=list)
    mutator: Optional[str] = None
    cex_generated: Optional[int] = None
    cex_validated_true: Optional[int] = None
    mutants_generated: Optional[int] = None
    mutants_compilable: Optional[int] = None
    selected_mutant_id: Optional[str] = None
    selected_mutant_path: Optional[str] = None
    blocked_cex: Optional[int] = None
    verification_passed: Optional[bool] = None
    compilation_error: Optional[bool] = None


class TrajectoryRecorder:
    def __init__(self) -> None:
        self._base_dir: Optional[Path] = None
        self._out_file: Optional[Path] = None
        self._strategy: Dict[str, Any] = {}
        self._iterations: Dict[int, IterationRecord] = {}
        self._enabled: bool = False

    def enable(self, enabled: bool) -> None:
        self._enabled = enabled

    def init_run(
        self, run_dir: Path, gen_strategy: str, genz_strategy: str, num_cex: int
    ) -> None:
        if not self._enabled:
            return
        self._base_dir = Path(run_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._out_file = self._base_dir / "trajectory.json"
        self._strategy = {
            "generation_strategy": gen_strategy,
            "generalization_strategy": genz_strategy,
            "num_cex": int(num_cex),
        }
        # Load existing trajectory if present (support resume)
        if self._out_file.exists():
            try:
                data = json.loads(self._out_file.read_text())
                self._strategy = data.get("strategy", self._strategy)
                for it in data.get("iterations", []):
                    att = int(it.get("attempt"))
                    self._iterations[att] = IterationRecord(
                        attempt=att,
                        target_error=it.get("target_error"),
                        all_errors=list(it.get("all_errors", []) or []),
                        mutator=it.get("mutator"),
                        cex_generated=it.get("cex", {}).get("generated")
                        if isinstance(it.get("cex"), dict)
                        else it.get("cex_generated"),
                        cex_validated_true=it.get("cex", {}).get("validated_true")
                        if isinstance(it.get("cex"), dict)
                        else it.get("cex_validated_true"),
                        mutants_generated=it.get("mutants", {}).get("generated")
                        if isinstance(it.get("mutants"), dict)
                        else it.get("mutants_generated"),
                        mutants_compilable=it.get("mutants", {}).get("compilable")
                        if isinstance(it.get("mutants"), dict)
                        else it.get("mutants_compilable"),
                        selected_mutant_id=(
                            it.get("mutants", {}).get("selected", {}) or {}
                        ).get("id")
                        if isinstance(it.get("mutants"), dict)
                        else it.get("selected_mutant_id"),
                        selected_mutant_path=(
                            it.get("mutants", {}).get("selected", {}) or {}
                        ).get("path")
                        if isinstance(it.get("mutants"), dict)
                        else it.get("selected_mutant_path"),
                        blocked_cex=(
                            it.get("mutants", {}).get("selected", {}) or {}
                        ).get("blocked_cex")
                        if isinstance(it.get("mutants"), dict)
                        else it.get("blocked_cex"),
                        verification_passed=(it.get("status", {}) or {}).get(
                            "verification_passed"
                        )
                        if isinstance(it.get("status"), dict)
                        else it.get("verification_passed"),
                        compilation_error=(it.get("status", {}) or {}).get(
                            "compilation_error"
                        )
                        if isinstance(it.get("status"), dict)
                        else it.get("compilation_error"),
                    )
            except Exception:
                # Ignore malformed previous file; start fresh
                pass
        self._flush()

    def begin_iteration(
        self, attempt: int, target_error: Optional[str], all_errors: List[str]
    ) -> None:
        if not self._enabled:
            return
        rec = self._iterations.get(attempt) or IterationRecord(attempt=attempt)
        rec.target_error = target_error
        rec.all_errors = list(all_errors)
        self._iterations[attempt] = rec
        self._flush()

    def record_mutator(self, attempt: int, mutator_name: str) -> None:
        if not self._enabled:
            return
        rec = self._iterations.get(attempt) or IterationRecord(attempt=attempt)
        rec.mutator = str(mutator_name)
        self._iterations[attempt] = rec
        self._flush()

    def record_cex(self, attempt: int, generated: int, validated_true: int) -> None:
        if not self._enabled:
            return
        rec = self._iterations.get(attempt) or IterationRecord(attempt=attempt)
        rec.cex_generated = int(generated)
        rec.cex_validated_true = int(validated_true)
        self._iterations[attempt] = rec
        self._flush()

    def record_mutants(self, attempt: int, generated: int, compilable: int) -> None:
        if not self._enabled:
            return
        rec = self._iterations.get(attempt) or IterationRecord(attempt=attempt)
        rec.mutants_generated = int(generated)
        rec.mutants_compilable = int(compilable)
        self._iterations[attempt] = rec
        self._flush()

    def record_selection(
        self,
        attempt: int,
        candidate_id: Optional[str],
        candidate_path: Optional[str],
        blocked_cex: Optional[int],
    ) -> None:
        if not self._enabled:
            return
        rec = self._iterations.get(attempt) or IterationRecord(attempt=attempt)
        rec.selected_mutant_id = candidate_id
        rec.selected_mutant_path = candidate_path
        rec.blocked_cex = int(blocked_cex) if isinstance(blocked_cex, int) else None
        self._iterations[attempt] = rec
        self._flush()

    def record_status(
        self, attempt: int, verification_passed: bool, compilation_error: bool
    ) -> None:
        if not self._enabled:
            return
        rec = self._iterations.get(attempt) or IterationRecord(attempt=attempt)
        rec.verification_passed = bool(verification_passed)
        rec.compilation_error = bool(compilation_error)
        self._iterations[attempt] = rec
        self._flush()

    def _serialize(self) -> Dict[str, Any]:
        iters: List[Dict[str, Any]] = []
        for attempt in sorted(self._iterations.keys()):
            r = self._iterations[attempt]
            iters.append(
                {
                    "attempt": r.attempt,
                    "target_error": r.target_error,
                    "all_errors": r.all_errors,
                    "mutator": r.mutator,
                    "cex": {
                        "generated": r.cex_generated,
                        "validated_true": r.cex_validated_true,
                    },
                    "mutants": {
                        "generated": r.mutants_generated,
                        "compilable": r.mutants_compilable,
                        "selected": {
                            "id": r.selected_mutant_id,
                            "path": r.selected_mutant_path,
                            "blocked_cex": r.blocked_cex,
                        },
                    },
                    "status": {
                        "verification_passed": r.verification_passed,
                        "compilation_error": r.compilation_error,
                    },
                }
            )
        return {"strategy": self._strategy, "iterations": iters}

    def _flush(self) -> None:
        if not self._enabled:
            return
        if not self._out_file:
            return
        try:
            self._out_file.write_text(json.dumps(self._serialize(), indent=2))
        except Exception:
            # Best-effort; do not raise
            pass


# Module-level singleton used by pipeline components
recorder = TrajectoryRecorder()
