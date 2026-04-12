import os
import time
import traceback
from typing import Any, Dict, List, Optional

import openai
from anthropic import Anthropic
from anthropic import APIError as AnthropicAPIError
from anthropic import RateLimitError as AnthropicRateLimitError
from vinv.gen.cost_report import record_llm_call


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
    error_type: Optional[str] = None,
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
        # Never fail the main flow due to logging issues
        pass


def request_conversation_one(
    msg_list: List[Dict],
    model="gpt-4o",
    max_retry=5,
    temperature=1.0,
    max_tokens=4096,
    task_id: str = "default_task",
    prompt_type_id: str = "default_prompt",
) -> str:
    if model.startswith("gpt") or model.startswith("o4-mini"):
        client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )
    elif model.startswith("deepseek"):  # DeepSeek-V3-0324
        # client = openai.OpenAI(
        #     api_key=os.getenv("DEEPSEEK_API_KEY"),
        #     base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
        # )
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv(
                "OPENROUTER_QWEN_API_BASE", "https://openrouter.ai/api/v1"
            ),
        )
    elif model.startswith("qwen/qwen3-coder"):
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv(
                "OPENROUTER_QWEN_API_BASE", "https://openrouter.ai/api/v1"
            ),
        )
    elif model.startswith("anthropic/claude-"):
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
        )
    elif model.startswith("claude"):
        client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    else:
        raise NotImplementedError(
            f"Model {model} is not supported. Please use a valid model name."
        )

    # Exponential backoff for rate limits
    backoff_seconds = 1.0
    max_backoff_seconds = 60.0

    while True:
        try:
            start_ts = time.time()

            if model.startswith("claude"):
                # Anthropic API - extract system message if present
                system_message = None
                anthropic_messages = []
                for msg in msg_list:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        anthropic_messages.append(msg)

                # Create API call parameters
                api_params = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": anthropic_messages,
                    "temperature": temperature,
                }
                if system_message:
                    api_params["system"] = system_message

                response = client.messages.create(**api_params)

                # Create a usage object compatible with our tracking
                class AnthropicUsage:
                    def __init__(self, input_tokens, output_tokens):
                        self.prompt_tokens = input_tokens
                        self.completion_tokens = output_tokens
                        self.total_tokens = input_tokens + output_tokens

                usage = AnthropicUsage(
                    response.usage.input_tokens, response.usage.output_tokens
                )
                content = response.content[0].text
            else:
                # OpenAI-compatible API (includes anthropic/claude- via OpenRouter)
                params = {
                    "model": model,
                    "messages": msg_list,
                    "temperature": temperature,
                }
                if model.startswith("o4-mini"):
                    params["max_completion_tokens"] = max_tokens * 10
                else:
                    params["max_tokens"] = max_tokens
                response = client.chat.completions.create(**params)
                usage = getattr(response, "usage", None)
                content = response.choices[0].message.content

            # Record token usage for this call
            tid = task_id
            ptid = prompt_type_id
            _record_task_call_usage(
                task_id=tid,
                prompt_type_id=ptid,
                model=model,
                num_choices=1,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=usage,
                success=True,
            )
            return content
        except (openai.RateLimitError, AnthropicRateLimitError):
            traceback.print_exc()
            print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
            # Record failed attempt
            tid = task_id
            ptid = prompt_type_id
            _record_task_call_usage(
                task_id=tid,
                prompt_type_id=ptid,
                model=model,
                num_choices=1,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=None,
                success=False,
                error_type="RateLimitError",
            )
            time.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
            continue
        except (openai.InternalServerError, openai.APIError, AnthropicAPIError):
            max_retry -= 1
            if max_retry < 0:
                traceback.print_exc()
                print("Max retries exceeded, exiting...")
                break
            # Record failed attempt
            tid = task_id
            ptid = prompt_type_id
            _record_task_call_usage(
                task_id=tid,
                prompt_type_id=ptid,
                model=model,
                num_choices=1,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=None,
                success=False,
                error_type="ServerOrAPIError",
            )
            time.sleep(5)
            continue
        except Exception:
            traceback.print_exc()
            # Record failed attempt
            tid = task_id
            ptid = prompt_type_id
            _record_task_call_usage(
                task_id=tid,
                prompt_type_id=ptid,
                model=model,
                num_choices=1,
                start_ts=start_ts,
                end_ts=time.time(),
                usage_obj=None,
                success=False,
                error_type="Exception",
            )
            break

    raise RuntimeError("Failed to get response from API after all retries")


def request_conversation_multi_response(
    msg_list: List[Dict],
    model="gpt-4o",
    max_retry=5,
    temperature=1.0,
    max_tokens=4096,
    num_responses=5,
    task_id: str = "default_task",
    prompt_type_id: str = "default_prompt",
) -> List[str]:
    """
    Return multiple chat completions for the same prompt.

    - For OpenAI GPT models, use the 'n' parameter to fetch multiple choices in one call.
    - For DeepSeek models (which do not support 'n'), issue multiple single-choice calls and concatenate results.
    """
    responses: List[str] = []

    # Branch by model family
    if model.startswith("gpt") or model.startswith("o4-mini"):
        client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )
        # Exponential backoff for rate limits
        backoff_seconds = 1.0
        max_backoff_seconds = 60.0

        while len(responses) < num_responses:
            try:
                start_ts = time.time()
                remaining = num_responses - len(responses)
                params = {
                    "model": model,
                    "messages": msg_list,
                    "temperature": temperature,
                    "n": remaining,
                }
                if model.startswith("o4-mini"):
                    params["max_completion_tokens"] = max_tokens * 10
                else:
                    params["max_tokens"] = max_tokens
                response = client.chat.completions.create(**params)
                usage = getattr(response, "usage", None)
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=remaining,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=usage,
                    success=True,
                )
                responses.extend(
                    [choice.message.content for choice in response.choices]
                )
                # Reset backoff after success
                backoff_seconds = 1.0
            except openai.RateLimitError:
                traceback.print_exc()
                print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=remaining,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="RateLimitError",
                )
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            except (openai.InternalServerError, openai.APIError):
                max_retry -= 1
                if max_retry < 0:
                    traceback.print_exc()
                    print("Max retries exceeded, exiting...")
                    break
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=remaining,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="ServerOrAPIError",
                )
                time.sleep(5)
                continue
            except Exception:
                traceback.print_exc()
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=remaining,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="Exception",
                )
                break
        return responses[:num_responses]

    elif model.startswith("deepseek"):
        # DeepSeek does not support 'n'; make num_responses single calls
        # client = openai.OpenAI(
        #     api_key=os.getenv("DEEPSEEK_API_KEY"),
        #     base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
        # )
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv(
                "OPENROUTER_QWEN_API_BASE", "https://openrouter.ai/api/v1"
            ),
        )
        # Exponential backoff for rate limits
        backoff_seconds = 1.0
        max_backoff_seconds = 60.0

        for i in range(num_responses):
            try:
                start_ts = time.time()
                response = client.chat.completions.create(
                    model=model,
                    messages=msg_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                usage = getattr(response, "usage", None)
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=usage,
                    success=True,
                )
                responses.append(response.choices[0].message.content)
                # Reset backoff after success
                backoff_seconds = 1.0
            except openai.RateLimitError:
                traceback.print_exc()
                print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="RateLimitError",
                )
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            except (openai.InternalServerError, openai.APIError):
                max_retry -= 1
                if max_retry < 0:
                    traceback.print_exc()
                    print("Max retries exceeded, exiting...")
                    break
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="ServerOrAPIError",
                )
                time.sleep(5)
                continue
            except Exception:
                traceback.print_exc()
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="Exception",
                )
                break
        return responses[:num_responses]

    elif model.startswith("qwen/qwen3-coder"):
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv(
                "OPENROUTER_QWEN_API_BASE", "https://openrouter.ai/api/v1"
            ),
        )
        # Exponential backoff for rate limits
        backoff_seconds = 1.0
        max_backoff_seconds = 60.0

        for i in range(num_responses):
            try:
                start_ts = time.time()
                response = client.chat.completions.create(
                    model=model,
                    messages=msg_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                usage = getattr(response, "usage", None)
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=usage,
                    success=True,
                )
                responses.append(response.choices[0].message.content)
                # Reset backoff after success
                backoff_seconds = 1.0
            except openai.RateLimitError:
                traceback.print_exc()
                print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="RateLimitError",
                )
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            except (openai.InternalServerError, openai.APIError):
                max_retry -= 1
                if max_retry < 0:
                    traceback.print_exc()
                    print("Max retries exceeded, exiting...")
                    break
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="ServerOrAPIError",
                )
                time.sleep(5)
                continue
            except Exception:
                traceback.print_exc()
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="Exception",
                )
                break
        return responses[:num_responses]

    elif model.startswith("anthropic/claude-"):
        # OpenRouter Claude does not support 'n'; make num_responses single calls
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
        )
        # Exponential backoff for rate limits
        backoff_seconds = 1.0
        max_backoff_seconds = 60.0

        for i in range(num_responses):
            try:
                start_ts = time.time()
                response = client.chat.completions.create(
                    model=model,
                    messages=msg_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                usage = getattr(response, "usage", None)
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=usage,
                    success=True,
                )
                responses.append(response.choices[0].message.content)
                # Reset backoff after success
                backoff_seconds = 1.0
            except openai.RateLimitError:
                traceback.print_exc()
                print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="RateLimitError",
                )
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            except (openai.InternalServerError, openai.APIError):
                max_retry -= 1
                if max_retry < 0:
                    traceback.print_exc()
                    print("Max retries exceeded, exiting...")
                    break
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="ServerOrAPIError",
                )
                time.sleep(5)
                continue
            except Exception:
                traceback.print_exc()
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="Exception",
                )
                break
        return responses[:num_responses]

    elif model.startswith("claude"):
        # Claude does not support 'n'; make num_responses single calls
        client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        # Extract system message if present
        system_message = None
        anthropic_messages = []
        for msg in msg_list:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)

        # Exponential backoff for rate limits
        backoff_seconds = 1.0
        max_backoff_seconds = 60.0

        for i in range(num_responses):
            try:
                start_ts = time.time()

                # Create API call parameters
                api_params = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": anthropic_messages,
                    "temperature": temperature,
                }
                if system_message:
                    api_params["system"] = system_message

                response = client.messages.create(**api_params)

                # Create a usage object compatible with our tracking
                class AnthropicUsage:
                    def __init__(self, input_tokens, output_tokens):
                        self.prompt_tokens = input_tokens
                        self.completion_tokens = output_tokens
                        self.total_tokens = input_tokens + output_tokens

                usage = AnthropicUsage(
                    response.usage.input_tokens, response.usage.output_tokens
                )
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=usage,
                    success=True,
                )
                responses.append(response.content[0].text)
                # Reset backoff after success
                backoff_seconds = 1.0
            except AnthropicRateLimitError:
                traceback.print_exc()
                print(f"Rate limit exceeded, waiting {backoff_seconds:.1f} seconds...")
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="RateLimitError",
                )
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            except AnthropicAPIError:
                max_retry -= 1
                if max_retry < 0:
                    traceback.print_exc()
                    print("Max retries exceeded, exiting...")
                    break
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="ServerOrAPIError",
                )
                time.sleep(5)
                continue
            except Exception:
                traceback.print_exc()
                _record_task_call_usage(
                    task_id=task_id,
                    prompt_type_id=prompt_type_id,
                    model=model,
                    num_choices=1,
                    start_ts=start_ts,
                    end_ts=time.time(),
                    usage_obj=None,
                    success=False,
                    error_type="Exception",
                )
                break
        return responses[:num_responses]
    else:
        raise NotImplementedError(
            f"Model {model} is not supported. Please use a valid model name."
        )
