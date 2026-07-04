#!/usr/bin/env bash

setup_script_path() {
    if [[ -n "${BASH_VERSION-}" ]]; then
        printf '%s\n' "${BASH_SOURCE[0]}"
    elif [[ -n "${ZSH_VERSION-}" ]]; then
        printf '%s\n' "${(%):-%N}"
    else
        printf '%s\n' "$0"
    fi
}

is_sourced() {
    if [[ -n "${BASH_VERSION-}" ]]; then
        [[ "${BASH_SOURCE[0]}" != "$0" ]]
    elif [[ -n "${ZSH_VERSION-}" ]]; then
        [[ "${ZSH_EVAL_CONTEXT-}" == *:file* ]]
    else
        return 1
    fi
}

fail_setup() {
    echo "$1" >&2
    if is_sourced; then
        return 1
    fi
    exit 1
}

ROOT_DIR="$(cd -- "$(dirname -- "$(setup_script_path)")" && pwd)"

prepend_pythonpath() {
    case ":${PYTHONPATH-}:" in
        *":$1:"*) ;;
        *) export PYTHONPATH="$1${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac
}

require_verus() {
    if [[ -n "${VERUS_PATH-}" ]]; then
        [[ -x "$VERUS_PATH" ]] && return 0
        fail_setup "VERUS_PATH is not executable: $VERUS_PATH"
        return 1
    fi

    if [[ -n "${VERUS_BIN-}" ]]; then
        [[ -x "$VERUS_BIN" ]] && export VERUS_PATH="$VERUS_BIN" && return 0
        fail_setup "VERUS_BIN is not executable: $VERUS_BIN"
        return 1
    fi

    VERUS_PATH="$(command -v verus 2>/dev/null || true)"
    [[ -n "$VERUS_PATH" ]] && export VERUS_PATH && return 0
    fail_setup $'Verus executable not found.\nSet VERUS_PATH=/path/to/verus, set VERUS_BIN=/path/to/verus, or add `verus` to PATH before sourcing ./setup.sh.'
    return 1
}

if ! is_sourced; then
    fail_setup $'Run this script with:\n  source ./setup.sh [--sync]'
fi

case "${1-}" in
    "")
        ;;
    --sync)
        uv sync
        ;;
    *)
        fail_setup "Usage: source ./setup.sh [--sync]"
        ;;
esac

prepend_pythonpath "$ROOT_DIR"
prepend_pythonpath "$ROOT_DIR/verus-proof-synthesis/code"

if [[ -f "$ROOT_DIR/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT_DIR/.venv/bin/activate"
fi

require_verus || return 1

export VINV_ROOT="$ROOT_DIR"

echo "Environment ready."
echo "ROOT_DIR=$ROOT_DIR"
echo "PYTHONPATH=$PYTHONPATH"
echo "VERUS_PATH=$VERUS_PATH"
