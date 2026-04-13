from vinv.gen.client import _client_config, build_messages


def test_build_messages_with_system():
    assert build_messages("hello", "system") == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "hello"},
    ]


def test_build_messages_without_system():
    assert build_messages("hello") == [{"role": "user", "content": "hello"}]


def test_client_config_routes_supported_models():
    assert _client_config("gpt-4o").supports_n is True
    assert _client_config("deepseek-chat").kind == "openai"
    assert _client_config("claude-3-5-sonnet-latest").kind == "anthropic"
