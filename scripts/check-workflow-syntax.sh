#!/usr/bin/env bash
# Validate expressions and job contexts in addition to YAML syntax.
set -euo pipefail
work="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/chaptarr-actionlint.XXXXXX")"
trap 'rm -rf -- "$work"' EXIT
archive=actionlint_1.7.12_linux_amd64.tar.gz
curl --fail --silent --show-error --location --retry 3 --max-time 120 \
  "https://github.com/rhysd/actionlint/releases/download/v1.7.12/$archive" --output "$work/$archive"
printf '%s  %s\n' 8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8 "$work/$archive" | sha256sum --check --status
tar --extract --gzip --file "$work/$archive" --directory "$work" --no-same-owner actionlint
"$work/actionlint" -shellcheck='' -pyflakes=''
