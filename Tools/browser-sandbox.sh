#!/usr/bin/env bash
set -euo pipefail
# No fallback to an unsandboxed browser. The parent communicates only through
# Playwright's inherited pipes; all HTTP traffic is fulfilled by the app's broker.
if [[ "$(id -u)" == 0 || ! -x /usr/bin/bwrap ]]; then
    echo 'Browser resolution requires a non-root account and bubblewrap.' >&2
    exit 1
fi
browser="$(readlink -f "${CHAPTARR_BROWSER_EXECUTABLE:?}")"
config="$(readlink -f "${CHAPTARR_CONFIG_ROOT:?}")"
case "$config" in /usr|/usr/*|/lib|/lib/*|/lib64|/lib64/*) echo 'Config directory overlaps browser system mounts.' >&2; exit 1;; esac
browser_dir="$(dirname "$browser")"
case "$config/" in "$browser_dir/"*) echo 'Browser directory contains app configuration.' >&2; exit 1;; esac
case "$browser_dir/" in "$config/"*) echo 'Browser executable must not reside in app configuration.' >&2; exit 1;; esac
exec /usr/bin/bwrap --unshare-all --die-with-parent --new-session --cap-drop ALL \
    --uid 65534 --gid 65534 --clearenv \
    --ro-bind /usr /usr --ro-bind-try /lib /lib --ro-bind-try /lib64 /lib64 \
    --symlink usr/bin /bin --symlink usr/sbin /sbin \
    --ro-bind "$browser_dir" /browser --proc /proc --dev /dev --tmpfs /tmp \
    --dir /home --dir /etc --setenv HOME /tmp --setenv PATH /usr/bin:/bin \
    --chdir /tmp "/browser/$(basename "$browser")" "$@"
