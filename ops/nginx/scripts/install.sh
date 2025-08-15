#!/usr/bin/env bash
set -euo pipefail

# Render Nginx site config from template with envsubst and install into /etc/nginx/sites-available
# - Loads variables from ops/nginx/.env.nginx if present (or a file provided via -e)
# - Validates required variables by scanning the template
# - Writes to /etc/nginx/sites-available/$SITE_CONF_NAME
# - Does NOT create symlink in sites-enabled (left to operator)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TEMPLATE_PATH="${SCRIPT_DIR}/../site.conf.template"
DEFAULT_ENV_FILE="${SCRIPT_DIR}/../.env.nginx"
ENV_FILE="${ENV_FILE:-${DEFAULT_ENV_FILE}}"
SITE_CONF_NAME_OVERRIDE=""

usage() {
    echo "Usage: [ENV_FILE=path] $0 [-e path/to/.env.nginx] [-n site_conf_name]" >&2
    echo "  -e  Path to env file (sets ENV_FILE; defaults to ${DEFAULT_ENV_FILE})" >&2
    echo "  -n  Output filename in /etc/nginx/sites-available (overrides SITE_CONF_NAME)" >&2
}

while getopts ":e:n:h" opt; do
    case "$opt" in
        e) ENV_FILE="$OPTARG" ;;
        n) SITE_CONF_NAME_OVERRIDE="$OPTARG" ;;
        h) usage; exit 0 ;;
        :) echo "Option -$OPTARG requires an argument" >&2; usage; exit 2 ;;
        \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 2 ;;
    esac
done

if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "Template not found: $TEMPLATE_PATH" >&2
    exit 1
fi

# Load env file (ENV_FILE may be overridden by -e; defaults to ${DEFAULT_ENV_FILE})
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file not found: $ENV_FILE" >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

# Determine output file name
SITE_CONF_NAME="${SITE_CONF_NAME_OVERRIDE:-${SITE_CONF_NAME:-}}"
if [[ -z "${SITE_CONF_NAME:-}" ]]; then
    # Derive from ALT_HOST or CANONICAL_HOST if available
    if [[ -n "${ALT_HOST:-}" ]]; then
        SITE_CONF_NAME="$ALT_HOST"
    elif [[ -n "${CANONICAL_HOST:-}" ]]; then
        SITE_CONF_NAME="$CANONICAL_HOST"
    else
        echo "SITE_CONF_NAME is not set and cannot be derived; provide via env or -n" >&2
        exit 1
    fi
fi

TARGET_PATH="/etc/nginx/sites-available/${SITE_CONF_NAME}"

# Collect required variables from template: ${VARNAME}
mapfile -t REQUIRED_VARS < <(grep -o '\${[A-Za-z_][A-Za-z0-9_]*}' "$TEMPLATE_PATH" | sed -E 's/\$\{|}//g' | sort -u)

MISSING=()
for var_name in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var_name:-}" ]]; then
        MISSING+=("$var_name")
    fi
done

if (( ${#MISSING[@]} > 0 )); then
    echo "Missing required variables for template: ${MISSING[*]}" >&2
    echo "Provide them via environment or an env file (-e)." >&2
    exit 1
fi

# Prepare variable list for envsubst to avoid substituting unrelated variables
VAR_LIST=$(printf ' ${%s}' "${REQUIRED_VARS[@]}")

echo "Rendering template to $TARGET_PATH"
TMP_RENDER="$(mktemp)"
trap 'rm -f "$TMP_RENDER"' EXIT

envsubst "$VAR_LIST" < "$TEMPLATE_PATH" > "$TMP_RENDER"

# Write with sudo if needed
if [[ "$EUID" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
        sudo mkdir -p /etc/nginx/sites-available
        sudo cp "$TMP_RENDER" "$TARGET_PATH"
    else
        echo "Root privileges required to write $TARGET_PATH and create directory. Install sudo or run as root." >&2
        exit 1
    fi
else
    mkdir -p /etc/nginx/sites-available
    cp "$TMP_RENDER" "$TARGET_PATH"
fi

echo "Wrote: $TARGET_PATH"
echo "Next steps:"
echo "  - Enable with: ln -sfn $TARGET_PATH /etc/nginx/sites-enabled/${SITE_CONF_NAME}"
echo "  - Test: nginx -t"
echo "  - Reload: systemctl reload nginx"

