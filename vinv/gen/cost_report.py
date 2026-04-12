import json
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

PRICING_CATALOG_CHECKED_AT = "2026-03-25"

_ACTIVE_REPORTER = None
_REPORTER_LOCK = threading.Lock()

_SUMMARY_KEYS = (
    "task_wall_clock_seconds",
    "llm_wall_clock_seconds_total",
    "llm_calls_total",
    "llm_calls_success",
    "llm_calls_failed",
    "choices_requested_total",
    "prompt_tokens_total",
    "completion_tokens_total",
    "total_tokens_total",
    "prompt_cost_usd_total",
    "completion_cost_usd_total",
    "cost_usd_total",
    "costed_calls_total",
    "uncosted_calls_total",
)


def _utc_iso(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _empty_summary() -> Dict[str, Any]:
    return {
        "task_wall_clock_seconds": None,
        "llm_wall_clock_seconds_total": 0.0,
        "llm_calls_total": 0,
        "llm_calls_success": 0,
        "llm_calls_failed": 0,
        "choices_requested_total": 0,
        "prompt_tokens_total": 0,
        "completion_tokens_total": 0,
        "total_tokens_total": 0,
        "prompt_cost_usd_total": 0.0,
        "completion_cost_usd_total": 0.0,
        "cost_usd_total": 0.0,
        "costed_calls_total": 0,
        "uncosted_calls_total": 0,
    }


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        try:
            return _json_safe(value.model_dump())
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            return _json_safe(value.dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return {
                str(k): _json_safe(v)
                for k, v in vars(value).items()
                if not str(k).startswith("_")
            }
        except Exception:
            pass
    return str(value)


def _usage_value(usage_obj: Any, field_name: str) -> Any:
    if usage_obj is None:
        return None
    if isinstance(usage_obj, dict):
        return usage_obj.get(field_name)
    value = getattr(usage_obj, field_name, None)
    if value is not None:
        return value
    if hasattr(usage_obj, "model_dump"):
        try:
            return usage_obj.model_dump().get(field_name)
        except Exception:
            return None
    return None


def _int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _round_money(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 12)


def _extract_usage(usage_obj: Any) -> Dict[str, Any]:
    prompt_tokens = _int_or_none(_usage_value(usage_obj, "prompt_tokens"))
    completion_tokens = _int_or_none(_usage_value(usage_obj, "completion_tokens"))
    total_tokens = _int_or_none(_usage_value(usage_obj, "total_tokens"))
    if total_tokens is None and (
        prompt_tokens is not None or completion_tokens is not None
    ):
        total_tokens = int(prompt_tokens or 0) + int(completion_tokens or 0)

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "prompt_tokens_details": _json_safe(
            _usage_value(usage_obj, "prompt_tokens_details")
        ),
        "completion_tokens_details": _json_safe(
            _usage_value(usage_obj, "completion_tokens_details")
        ),
    }


def _pricing_entry(
    *,
    canonical_model: str,
    provider: str,
    input_per_million_usd: float,
    output_per_million_usd: float,
    source_url: str,
) -> Dict[str, Any]:
    return {
        "canonical_model": canonical_model,
        "provider": provider,
        "input_per_million_usd": input_per_million_usd,
        "output_per_million_usd": output_per_million_usd,
        "source_url": source_url,
        "checked_at": PRICING_CATALOG_CHECKED_AT,
    }


def _resolve_model_pricing(model: str) -> Optional[Dict[str, Any]]:
    normalized = model.strip().lower()

    if normalized.endswith(":free"):
        return _pricing_entry(
            canonical_model=model.strip(),
            provider="openrouter",
            input_per_million_usd=0.0,
            output_per_million_usd=0.0,
            source_url="https://openrouter.ai/models",
        )

    if normalized.startswith("gpt-4o"):
        return _pricing_entry(
            canonical_model="gpt-4o",
            provider="openai",
            input_per_million_usd=2.50,
            output_per_million_usd=10.00,
            source_url="https://platform.openai.com/pricing",
        )

    if normalized.startswith("o4-mini"):
        return _pricing_entry(
            canonical_model="o4-mini",
            provider="openai",
            input_per_million_usd=1.10,
            output_per_million_usd=4.40,
            source_url="https://platform.openai.com/pricing",
        )

    if (
        normalized == "deepseek-chat"
        or normalized == "deepseek-chat-v3.1"
        or normalized.startswith("deepseek/deepseek-chat-v3.1")
    ):
        return _pricing_entry(
            canonical_model="deepseek-chat-v3.1",
            provider="openrouter",
            input_per_million_usd=0.15,
            output_per_million_usd=0.75,
            source_url="https://openrouter.ai/deepseek/deepseek-chat-v3.1",
        )

    if normalized.startswith("deepseek-reasoner") or normalized.startswith(
        "deepseek/deepseek-reasoner"
    ):
        return _pricing_entry(
            canonical_model="deepseek-reasoner",
            provider="deepseek",
            input_per_million_usd=0.28,
            output_per_million_usd=0.42,
            source_url="https://api-docs.deepseek.com/quick_start/pricing-details-usd",
        )

    if normalized.startswith("qwen/qwen3-coder"):
        return _pricing_entry(
            canonical_model="qwen/qwen3-coder",
            provider="openrouter",
            input_per_million_usd=0.22,
            output_per_million_usd=1.00,
            source_url="https://openrouter.ai/qwen/qwen3-coder",
        )

    if "claude" in normalized and "sonnet" in normalized:
        provider = (
            "anthropic" if not normalized.startswith("anthropic/") else "openrouter"
        )
        source_url = (
            "https://docs.anthropic.com/en/docs/about-claude/pricing"
            if provider == "anthropic"
            else "https://openrouter.ai/anthropic/claude-sonnet-4.5"
        )
        return _pricing_entry(
            canonical_model="claude-sonnet",
            provider=provider,
            input_per_million_usd=3.00,
            output_per_million_usd=15.00,
            source_url=source_url,
        )

    return None


def resolve_model_pricing(model: str) -> Optional[Dict[str, Any]]:
    pricing = _resolve_model_pricing(model)
    if pricing is None:
        return None
    return deepcopy(pricing)


def estimate_cost_usd(
    *, model: str, prompt_tokens: int | None, completion_tokens: int | None
) -> Optional[float]:
    pricing = _resolve_model_pricing(model)
    if pricing is None or prompt_tokens is None or completion_tokens is None:
        return None
    total = (
        prompt_tokens * pricing["input_per_million_usd"]
        + completion_tokens * pricing["output_per_million_usd"]
    ) / 1_000_000
    return _round_money(total)


def _new_bucket(name: str, key: str) -> Dict[str, Any]:
    return {
        name: key,
        "summary": _empty_summary(),
    }


def _add_call_to_summary(summary: Dict[str, Any], call_record: Dict[str, Any]) -> None:
    summary["llm_calls_total"] += 1
    summary["llm_wall_clock_seconds_total"] += float(
        call_record.get("wall_clock_seconds") or 0.0
    )
    summary["choices_requested_total"] += int(call_record.get("num_choices") or 0)
    if call_record.get("success"):
        summary["llm_calls_success"] += 1
    else:
        summary["llm_calls_failed"] += 1

    tokens = call_record.get("tokens", {})
    summary["prompt_tokens_total"] += int(tokens.get("prompt_tokens") or 0)
    summary["completion_tokens_total"] += int(tokens.get("completion_tokens") or 0)
    summary["total_tokens_total"] += int(tokens.get("total_tokens") or 0)

    costs = call_record.get("costs", {})
    cost_total = costs.get("cost_usd")
    if cost_total is None:
        summary["uncosted_calls_total"] += 1
        return

    summary["costed_calls_total"] += 1
    summary["prompt_cost_usd_total"] += float(costs.get("prompt_cost_usd") or 0.0)
    summary["completion_cost_usd_total"] += float(
        costs.get("completion_cost_usd") or 0.0
    )
    summary["cost_usd_total"] += float(cost_total)


def _finalize_summary(summary: Dict[str, Any]) -> None:
    for key in (
        "task_wall_clock_seconds",
        "llm_wall_clock_seconds_total",
        "prompt_cost_usd_total",
        "completion_cost_usd_total",
        "cost_usd_total",
        "run_wall_clock_seconds",
    ):
        if key in summary and summary.get(key) is not None:
            summary[key] = _round_money(summary.get(key) or 0.0)


def _merge_summary_into(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    for key in _SUMMARY_KEYS:
        value = source.get(key)
        if value is None:
            continue
        if key == "task_wall_clock_seconds":
            current = target.get(key)
            target[key] = float(current or 0.0) + float(value)
            continue
        if key.endswith("_usd_total") or key.endswith("_seconds_total"):
            target[key] = float(target.get(key) or 0.0) + float(value)
        else:
            target[key] = int(target.get(key) or 0) + int(value)


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=False)
    tmp_path.replace(path)


class TaskCostReporter:
    def __init__(self, report_path: Path, task_metadata: Dict[str, Any]):
        self.report_path = report_path
        self.report = {
            "schema_version": 1,
            "report_kind": "vinv_task_llm_cost_report",
            "pricing_catalog_checked_at": PRICING_CATALOG_CHECKED_AT,
            "task": _json_safe(task_metadata),
            "started_at_epoch_s": time.time(),
            "started_at_utc": None,
            "finished_at_epoch_s": None,
            "finished_at_utc": None,
            "completed": False,
            "summary": _empty_summary(),
            "by_model": {},
            "by_prompt_type": {},
            "subtasks": {},
            "calls": [],
            "final_status": None,
            "error": None,
        }
        self.report["started_at_utc"] = _utc_iso(self.report["started_at_epoch_s"])
        self._write()

    def _write(self) -> None:
        payload = deepcopy(self.report)
        _finalize_summary(payload["summary"])
        for bucket_map_name in ("by_model", "by_prompt_type", "subtasks"):
            for bucket in payload[bucket_map_name].values():
                _finalize_summary(bucket["summary"])
                if bucket_map_name == "subtasks":
                    for nested in ("by_model", "by_prompt_type"):
                        for nested_bucket in bucket.get(nested, {}).values():
                            _finalize_summary(nested_bucket["summary"])
        _write_json_atomic(self.report_path, payload)

    def record_call(
        self,
        *,
        task_id: str,
        prompt_type_id: str,
        model: str,
        num_choices: int,
        start_ts: float,
        end_ts: float,
        usage_obj: Any,
        success: bool,
        error_type: Optional[str] = None,
    ) -> None:
        usage = _extract_usage(usage_obj)
        pricing = _resolve_model_pricing(model)
        prompt_cost = None
        completion_cost = None
        total_cost = None
        if (
            pricing is not None
            and usage["prompt_tokens"] is not None
            and usage["completion_tokens"] is not None
        ):
            prompt_cost = (
                usage["prompt_tokens"] * pricing["input_per_million_usd"] / 1_000_000
            )
            completion_cost = (
                usage["completion_tokens"] * pricing["output_per_million_usd"] / 1_000_000
            )
            total_cost = prompt_cost + completion_cost

        call_record = {
            "sequence_id": len(self.report["calls"]) + 1,
            "task_id": task_id,
            "prompt_type_id": prompt_type_id,
            "model": model,
            "pricing_model": pricing["canonical_model"] if pricing else None,
            "num_choices": int(num_choices),
            "started_at_epoch_s": start_ts,
            "started_at_utc": _utc_iso(start_ts),
            "ended_at_epoch_s": end_ts,
            "ended_at_utc": _utc_iso(end_ts),
            "wall_clock_seconds": max(0.0, float(end_ts - start_ts)),
            "success": bool(success),
            "error_type": error_type,
            "tokens": usage,
            "pricing": pricing,
            "costs": {
                "prompt_cost_usd": _round_money(prompt_cost),
                "completion_cost_usd": _round_money(completion_cost),
                "cost_usd": _round_money(total_cost),
            },
        }

        self.report["calls"].append(call_record)
        _add_call_to_summary(self.report["summary"], call_record)

        model_key = pricing["canonical_model"] if pricing else model
        model_bucket = self.report["by_model"].setdefault(
            model_key, _new_bucket("model", model_key)
        )
        _add_call_to_summary(model_bucket["summary"], call_record)

        prompt_bucket = self.report["by_prompt_type"].setdefault(
            prompt_type_id, _new_bucket("prompt_type_id", prompt_type_id)
        )
        _add_call_to_summary(prompt_bucket["summary"], call_record)

        subtask_bucket = self.report["subtasks"].setdefault(
            task_id,
            {
                **_new_bucket("task_id", task_id),
                "by_model": {},
                "by_prompt_type": {},
            },
        )
        _add_call_to_summary(subtask_bucket["summary"], call_record)

        subtask_model_bucket = subtask_bucket["by_model"].setdefault(
            model_key, _new_bucket("model", model_key)
        )
        _add_call_to_summary(subtask_model_bucket["summary"], call_record)

        subtask_prompt_bucket = subtask_bucket["by_prompt_type"].setdefault(
            prompt_type_id, _new_bucket("prompt_type_id", prompt_type_id)
        )
        _add_call_to_summary(subtask_prompt_bucket["summary"], call_record)

        self._write()

    def finalize(
        self,
        *,
        final_status: Optional[Dict[str, Any]],
        error: Optional[str],
        finished_at: Optional[float] = None,
    ) -> None:
        done_ts = finished_at or time.time()
        self.report["finished_at_epoch_s"] = done_ts
        self.report["finished_at_utc"] = _utc_iso(done_ts)
        self.report["completed"] = True
        self.report["summary"]["task_wall_clock_seconds"] = max(
            0.0, done_ts - float(self.report["started_at_epoch_s"])
        )
        self.report["final_status"] = _json_safe(final_status)
        self.report["error"] = error
        self._write()

    def snapshot(self) -> Dict[str, Any]:
        payload = deepcopy(self.report)
        _finalize_summary(payload["summary"])
        return payload


def initialize_task_cost_report(
    *, report_path: str | Path, task_metadata: Dict[str, Any]
) -> Path:
    global _ACTIVE_REPORTER
    report_path = Path(report_path)
    with _REPORTER_LOCK:
        try:
            reporter = TaskCostReporter(report_path, task_metadata)
        except Exception:
            _ACTIVE_REPORTER = None
            return report_path
        _ACTIVE_REPORTER = reporter
        return reporter.report_path


def record_llm_call(
    *,
    task_id: str,
    prompt_type_id: str,
    model: str,
    num_choices: int,
    start_ts: float,
    end_ts: float,
    usage_obj: Any,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    global _ACTIVE_REPORTER
    with _REPORTER_LOCK:
        if _ACTIVE_REPORTER is None:
            return
        _ACTIVE_REPORTER.record_call(
            task_id=task_id,
            prompt_type_id=prompt_type_id,
            model=model,
            num_choices=num_choices,
            start_ts=start_ts,
            end_ts=end_ts,
            usage_obj=usage_obj,
            success=success,
            error_type=error_type,
        )


def finalize_task_cost_report(
    *,
    final_status: Optional[Dict[str, Any]],
    error: Optional[str],
    finished_at: Optional[float] = None,
) -> Optional[Path]:
    global _ACTIVE_REPORTER
    with _REPORTER_LOCK:
        if _ACTIVE_REPORTER is None:
            return None
        reporter = _ACTIVE_REPORTER
        _ACTIVE_REPORTER = None
        try:
            reporter.finalize(
                final_status=final_status,
                error=error,
                finished_at=finished_at,
            )
        except Exception:
            pass
        return reporter.report_path


def get_active_task_cost_report_snapshot() -> Dict[str, Any]:
    with _REPORTER_LOCK:
        if _ACTIVE_REPORTER is None:
            return {}
        return _ACTIVE_REPORTER.snapshot()


def merge_task_cost_reports(
    *,
    report_paths: Iterable[str | Path],
    output_path: str | Path,
    run_metadata: Dict[str, Any],
    run_started_at: float,
    run_finished_at: Optional[float] = None,
) -> Path:
    finished_at = run_finished_at or time.time()
    merged_summary = _empty_summary()
    merged_summary["task_wall_clock_seconds"] = 0.0
    merged = {
        "schema_version": 1,
        "report_kind": "vinv_run_llm_cost_report",
        "pricing_catalog_checked_at": PRICING_CATALOG_CHECKED_AT,
        "run": _json_safe(run_metadata),
        "started_at_epoch_s": run_started_at,
        "started_at_utc": _utc_iso(run_started_at),
        "finished_at_epoch_s": finished_at,
        "finished_at_utc": _utc_iso(finished_at),
        "summary": merged_summary,
        "by_model": {},
        "by_prompt_type": {},
        "tasks": {},
        "missing_reports": [],
        "invalid_reports": [],
    }

    for raw_path in report_paths:
        path = Path(raw_path)
        if not path.is_file():
            merged["missing_reports"].append(str(path))
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception as exc:
            merged["invalid_reports"].append(
                {"path": str(path), "error": str(exc)}
            )
            continue

        task_id = (
            report.get("task", {}).get("task_full_id")
            or report.get("task", {}).get("full_id")
            or path.parent.name
        )
        merged["tasks"][task_id] = report

        _merge_summary_into(merged["summary"], report.get("summary", {}))

        for model_key, bucket in report.get("by_model", {}).items():
            merged_bucket = merged["by_model"].setdefault(
                model_key, _new_bucket("model", model_key)
            )
            _merge_summary_into(merged_bucket["summary"], bucket.get("summary", {}))

        for prompt_key, bucket in report.get("by_prompt_type", {}).items():
            merged_bucket = merged["by_prompt_type"].setdefault(
                prompt_key, _new_bucket("prompt_type_id", prompt_key)
            )
            _merge_summary_into(merged_bucket["summary"], bucket.get("summary", {}))

    merged["summary"]["run_wall_clock_seconds"] = _round_money(
        max(0.0, finished_at - run_started_at)
    )
    merged["summary"]["task_reports_total"] = len(merged["tasks"])
    merged["summary"]["missing_reports_total"] = len(merged["missing_reports"])
    merged["summary"]["invalid_reports_total"] = len(merged["invalid_reports"])
    _finalize_summary(merged["summary"])
    for bucket_map_name in ("by_model", "by_prompt_type"):
        for bucket in merged[bucket_map_name].values():
            _finalize_summary(bucket["summary"])

    output_path = Path(output_path)
    _write_json_atomic(output_path, merged)
    return output_path
