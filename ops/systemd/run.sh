#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)"
ENV_SERVICE_FILE="${ENV_SERVICE_FILE:-${SCRIPT_DIR}/.env.systemd}"

if [[ -f "$ENV_SERVICE_FILE" ]]; then
	# shellcheck disable=SC1090
	source "$ENV_SERVICE_FILE"
fi

: "${SERVICE_CMD:?SERVICE_CMD is required (e.g., 'uv run uvicorn server:app --host 0.0.0.0 --port 8001') }"
exec bash -lc "$SERVICE_CMD"


