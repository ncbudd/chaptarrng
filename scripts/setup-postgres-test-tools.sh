#!/usr/bin/env bash
# Use the service image for clients too: a newer pg_dump can emit SQL that an
# older server cannot restore. This script is for disposable Actions runners.
set -euo pipefail
: "${RUNNER_TEMP:?A runner-owned temporary directory is required}"
: "${GITHUB_PATH:?GitHub Actions PATH output is required}"
: "${CHAPTARRNG_POSTGRES_IMAGE:?A digest-pinned PostgreSQL image is required}"
[[ "$RUNNER_TEMP" == /* && -d "$RUNNER_TEMP" ]]
[[ "$CHAPTARRNG_POSTGRES_IMAGE" =~ ^postgres:[0-9]+-bookworm@sha256:[a-f0-9]{64}$ ]]
bash scripts/setup-acceptance-python.sh
client_dir="$RUNNER_TEMP/postgres-client-bin"
mkdir -p -- "$client_dir"
cat > "$client_dir/postgres-tool" <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
tool="${0##*/}"
case "$tool" in pg_dump|pg_restore|psql) ;; *) exit 1 ;; esac
docker_args=(run --rm --read-only --cap-drop ALL --security-opt no-new-privileges
  --network host --user "$(id -u):$(id -g)" --volume "${RUNNER_TEMP}:${RUNNER_TEMP}"
  --tmpfs /tmp:rw,noexec,nosuid,size=64m)
while IFS= read -r name; do
  if [[ "$name" == PG* ]]; then docker_args+=(--env "$name"); fi
done < <(compgen -e)
exec docker "${docker_args[@]}" "$CHAPTARRNG_POSTGRES_IMAGE" "$tool" "$@"
WRAPPER
chmod 0755 "$client_dir/postgres-tool"
for tool in pg_dump pg_restore psql; do
  ln -sf postgres-tool "$client_dir/$tool"
  "$client_dir/$tool" --version
done
printf '%s\n' "$client_dir" >> "$GITHUB_PATH"
