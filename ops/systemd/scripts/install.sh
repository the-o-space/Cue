#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)"
TEMPLATE_PATH="${SCRIPT_DIR}/../templates/service.service.template"
DEFAULT_ENV_FILE="${SCRIPT_DIR}/../.env.systemd"
ENV_FILE="${ENV_FILE:-${DEFAULT_ENV_FILE}}"
UNIT_NAME_OVERRIDE=""

usage() {
    echo "Usage: [ENV_FILE=path] $0 [-e path/to/.env.systemd] [-n unit_name.service]" >&2
}

while getopts ":e:n:h" opt; do
    case "$opt" in
        e) ENV_FILE="$OPTARG" ;;
        n) UNIT_NAME_OVERRIDE="$OPTARG" ;;
        h) usage; exit 0 ;;
        :) echo "Option -$OPTARG requires an argument" >&2; usage; exit 2 ;;
        \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 2 ;;
    esac
done

if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "Template not found: $TEMPLATE_PATH" >&2
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file not found: $ENV_FILE" >&2
    exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

UNIT_NAME="${UNIT_NAME_OVERRIDE:-${UNIT_NAME:-}}"
if [[ -z "${UNIT_NAME:-}" ]]; then
    echo "UNIT_NAME is required (e.g., cue-backend.service). Provide via env or -n." >&2
    exit 1
fi

TARGET_PATH="/etc/systemd/system/${UNIT_NAME}"

mapfile -t REQUIRED_VARS < <(grep -o '\${[A-Za-z_][A-Za-z0-9_]*}' "$TEMPLATE_PATH" | sed -E 's/\$\{|}//g' | sort -u)

MISSING=()
for var_name in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var_name:-}" ]]; then
        MISSING+=("$var_name")
    fi
done

if (( ${#MISSING[@]} > 0 )); then
    echo "Missing required variables: ${MISSING[*]}" >&2
    exit 1
fi

VAR_LIST=$(printf ' ${%s}' "${REQUIRED_VARS[@]}")
TMP_RENDER="$(mktemp)"
trap 'rm -f "$TMP_RENDER"' EXIT

envsubst "$VAR_LIST" < "$TEMPLATE_PATH" > "$TMP_RENDER"

if [[ "$EUID" -ne 0 ]]; then
    sudo cp "$TMP_RENDER" "$TARGET_PATH"
else
    cp "$TMP_RENDER" "$TARGET_PATH"
fi

echo "Installed: $TARGET_PATH"
echo "Reload systemd and enable if desired:"
echo "  systemctl daemon-reload"
echo "  systemctl enable --now ${UNIT_NAME}"

