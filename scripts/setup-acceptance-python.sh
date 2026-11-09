#!/usr/bin/env bash
set -euo pipefail
: "${RUNNER_TEMP:?A runner-owned temporary directory is required}"
: "${GITHUB_ENV:?GitHub Actions environment output is required}"
directory="$(mktemp -d "$RUNNER_TEMP/acceptance-python.XXXXXX")"
python3 -m pip install --disable-pip-version-check --no-deps --only-binary=:all: --require-hashes \
  --target "$directory" -r scripts/requirements.txt
printf 'PYTHONPATH=%s%s\n' "$directory" "${PYTHONPATH:+:$PYTHONPATH}" >> "$GITHUB_ENV"
