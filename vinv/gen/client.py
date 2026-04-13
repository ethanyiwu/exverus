from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass
from typing import Any

import openai
from anthropic import Anthropic
from anthropic import APIError as AnthropicAPIError
from anthropic import RateLimitError as AnthropicRateLimitError

from vinv.gen.cost_report import record_llm_call

Message = dict[str, str]


@dataclass(frozen=True)
class ClientConfig:
    kind: str
    api_key_env: str
    base_url_env: str | None = None
    default_base_url: str | None = None
    supports_n: bool = False
    use_max_completion_tokens: bool = False


def build_messages(prompt: str, system: str | None = None) -> list[Message]:
    messages: list[Message] = []
    if system is not None:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _record_task_call_usage(
    *,
    task_id: str,
    prompt_type_id: str,
    model: str,
    num_choices: int,
    start_ts: float,
    end_ts: float,
    usage_obj: Any,
    success: bool,
    error_type: str | None = None,
) -> None:
    try:
        record_llm_call(
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
    except Exception:
        pass


def _client_config(model: str) -> ClientConfig:
    if model.startswith(("gpt", "o4-mini")):
        return ClientConfig(
            kind="openai",
            api_key_env="OPENAI_API_KEY",
            base_url_env="OPENAI_API_BASE",
            default_base_url="https://api.openai.com/v1",
            supports_n=True,
            use_max_completion_tokens=model.startswith("o4-mini"),
        )
    if model.startswith(("deepseek", "qwen/qwen3-coder")):
        return ClientConfig(
            kind="openai",
            api_key_env="OPENROUTER_API_KEY",
            base_url_env="OPENROUTER_QWEN_API_BASE",
            default_base_url="https://openrouter.ai/api/v1",
        )
    if model.startswith("anthropic/claude-"):
        return ClientConfig(
            kind="openai",
            api_key_env="OPENROUTER_API_KEY",
            base_url_env="OPENROUTER_API_BASE",
            default_base_url="https://openrouter.ai/api/v1",
        )
    if model.startswith("claude"):
        return ClientConfig(kind="anthropic", api_key_env="ANTHROPIC_API_KEY")
    raise NotImplementedError(f"Unsupported model: {model}")


def _make_client(config: ClientConfig) -> Any:
    if config.kind == "anthropic":
        return Anthropic(api_key=os.getenv(config.api_key_env))
    return openai.OpenAI(
        api_key=os.getenv(config.api_key_env),
        base_url=os.getenv(config.base_url_env, config.default_base_url),
    )


def _split_system_message(messages: list[Message]) -> tuple[str | None, list[Message]]:
    system = None
    non_system = []
    for message in messages:
        if message["role"] == "system":
            system = message["content"]
            continue
        non_system.append(message)
    return system, non_system


def _anthropic_usage(response: Any) -> dict[str, int]:
    return {
        "prompt_tokens": response.usage.input_tokens,
        "completion_tokens": response.usage.output_tokens,
        "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
    }


def _openai_params(
    *,
    model: str,
    messages: list[Message],
    temperature: float,
    max_tokens: int,
    num_choices: int,
    config: ClientConfig,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if num_choices > 1:
        params["n"] = num_choices
    if config.use_max_completion_tokens:
        params["max_completion_tokens"] = max_tokens * 10
    else:
        params["max_tokens"] = max_tokens
    return params


def _request_batch(
    *,
    client: Any,
    config: ClientConfig,
    messages: list[Message],
    model: str,
    temperature: float,
    max_tokens: int,
    num_choices: int,
) -> tuple[list[str], Any]:
    if config.kind == "anthropic":
        system, anthropic_messages = _split_system_message(messages)
        params: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system is not None:
            params["system"] = system
        response = client.messages.create(**params)
        contents = [block.text for block in response.content if hasattr(block, "text")]
        return ["".join(contents)], _anthropic_usage(response)

    response = client.chat.completions.create(
        **_openai_params(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            num_choices=num_choices,
            config=config,
        )
    )
    return [choice.message.content or "" for choice in response.choices], getattr(
        response, "usage", None
    )


def _request_messages(
    messages: list[Message],
    *,
    model: str,
    max_retry: int,
    temperature: float,
    max_tokens: int,
    num_responses: int,
    task_id: str,
    prompt_type_id: str,
) -> list[str]:
    config = _client_config(model)
    client = _make_client(config)
    responses: list[str] = []
    backoff_seconds = 1.0
    retries_left = max_retry

    while len(responses) < num_responses:
        num_choices = num_responses - len(responses) if config.supports_n else 1
        start_ts = time.time()
        try:
            batch, usage = _request_batch(
                client=client,
                config=config,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                num_choices=num_choices,
            )
            _record_task_call_usage(
                task_id=task_id,
                prompt_type_id=prompt_type_id,
                model=model,
                num_choices=num_choices,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=usage,
                success=True,
            )
            responses.extend(batch)
            backoff_seconds = 1.0
            continue
        except (openai.RateLimitError, AnthropicRateLimitError):
            traceback.print_exc()
            print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
            _record_task_call_usage(
                task_id=task_id,
                prompt_type_id=prompt_type_id,
                model=model,
                num_choices=num_choices,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=None,
                success=False,
                error_type="RateLimitError",
            )
            time.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2.0, 60.0)
            continue
        except (openai.InternalServerError, openai.APIError, AnthropicAPIError):
            retries_left -= 1
            _record_task_call_usage(
                task_id=task_id,
                prompt_type_id=prompt_type_id,
                model=model,
                num_choices=num_choices,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=None,
                success=False,
                error_type="ServerOrAPIError",
            )
            if retries_left < 0:
                traceback.print_exc()
                break
            time.sleep(5)
            continue
        except Exception:
            traceback.print_exc()
            _record_task_call_usage(
                task_id=task_id,
                prompt_type_id=prompt_type_id,
                model=model,
                num_choices=num_choices,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=None,
                success=False,
                error_type="Exception",
            )
            break

    if responses:
        return responses[:num_responses]
    raise RuntimeError("Failed to get response from API after all retries")


def request_prompt_one(
    prompt: str,
    *,
    system: str | None = None,
    model: str = "gpt-4o",
    max_retry: int = 5,
    temperature: float = 1.0,
    max_tokens: int = 4096,
    task_id: str = "default_task",
    prompt_type_id: str = "default_prompt",
) -> str:
    return _request_messages(
        build_messages(prompt, system),
        model=model,
        max_retry=max_retry,
        temperature=temperature,
        max_tokens=max_tokens,
        num_responses=1,
        task_id=task_id,
        prompt_type_id=prompt_type_id,
    )[0]


def request_prompt_multi_response(
    prompt: str,
    *,
    system: str | None = None,
    model: str = "gpt-4o",
    max_retry: int = 5,
    temperature: float = 1.0,
    max_tokens: int = 4096,
    num_responses: int = 5,
    task_id: str = "default_task",
    prompt_type_id: str = "default_prompt",
) -> list[str]:
    return _request_messages(
        build_messages(prompt, system),
        model=model,
        max_retry=max_retry,
        temperature=temperature,
        max_tokens=max_tokens,
        num_responses=num_responses,
        task_id=task_id,
        prompt_type_id=prompt_type_id,
    )


def request_conversation_one(
    msg_list: list[Message],
    model: str = "gpt-4o",
    max_retry: int = 5,
    temperature: float = 1.0,
    max_tokens: int = 4096,
    task_id: str = "default_task",
    prompt_type_id: str = "default_prompt",
) -> str:
    return _request_messages(
        msg_list,
        model=model,
        max_retry=max_retry,
        temperature=temperature,
        max_tokens=max_tokens,
        num_responses=1,
        task_id=task_id,
        prompt_type_id=prompt_type_id,
    )[0]


def request_conversation_multi_response(
    msg_list: list[Message],
    model: str = "gpt-4o",
    max_retry: int = 5,
    temperature: float = 1.0,
    max_tokens: int = 4096,
    num_responses: int = 5,
    task_id: str = "default_task",
    prompt_type_id: str = "default_prompt",
) -> list[str]:
    return _request_messages(
        msg_list,
        model=model,
        max_retry=max_retry,
        temperature=temperature,
        max_tokens=max_tokens,
        num_responses=num_responses,
        task_id=task_id,
        prompt_type_id=prompt_type_id,
    )
