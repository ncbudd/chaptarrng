#!/usr/bin/env bash
set -euo pipefail

: "${CHAPTARRNG_POSTGRES_TEST_CONNECTION:?A disposable PostgreSQL test connection is required}"
port="${Chaptarr__Server__Port:-8789}"
export Chaptarr__Server__Port="$port"
export Chaptarr__Server__BindAddress=127.0.0.1
configuration="${CHAPTARRNG_TEST_CONFIGURATION:-Release}"

if [[ -n "${CHAPTARRNG_POSTGRES_SMOKE_DIR:-}" ]]; then
  data_dir="$CHAPTARRNG_POSTGRES_SMOKE_DIR"
  mkdir -m 700 -- "$data_dir"
else
  data_dir="$(mktemp -d "${TMPDIR:-/tmp}/chaptarr-migrations.XXXXXX")"
fi

app_log="$data_dir/app.log"
test_results_directory="$data_dir/nunit-results"
app_pid=""
readiness_timeout_seconds=300

cleanup() {
  local status=$?
  if [[ -n "$app_pid" ]]; then
    kill "$app_pid" >/dev/null 2>&1 || true
    wait "$app_pid" >/dev/null 2>&1 || true
  fi
  if (( status == 0 )) && [[ "${CHAPTARRNG_KEEP_POSTGRES_EVIDENCE:-false}" != true ]]; then
    rm -rf -- "$data_dir"
  else
    printf 'PostgreSQL smoke evidence kept in %s\n' "$data_dir" >&2
  fi
}
trap cleanup EXIT

if curl -fsS --max-time 2 "http://127.0.0.1:$port/ping" >/dev/null 2>&1; then
  echo 'The PostgreSQL smoke port is already serving another application.' >&2
  exit 1
fi

dotnet run --project src/NzbDrone.Console/Chaptarr.Console.csproj \
  -c "$configuration" --no-build --no-restore --framework net10.0 -- \
  /nobrowser "/data=$data_dir" >"$app_log" 2>&1 &
app_pid=$!

ready=""
for _ in $(seq 1 "$readiness_timeout_seconds"); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$port/ping" >/dev/null 2>&1; then
    ready="yes"
    break
  fi
  if ! kill -0 "$app_pid" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ "$ready" != "yes" ]]; then
  echo "Chaptarr failed to start or /ping did not become ready." >&2
  tail -n 400 "$app_log" >&2 || true
  exit 1
fi

# The PostgreSQL fixtures create and restore disposable schemas in the configured
# database and verify that their source database is idle before taking a dump.
# Stop the startup-smoke process before those checks so its connection pool does
# not look like an external client holding the source database open.
kill "$app_pid" >/dev/null 2>&1 || true
wait "$app_pid" >/dev/null 2>&1 || true
app_pid=""

mkdir -p "$test_results_directory"
dotnet test src/Chaptarr.Core.Test/Chaptarr.Core.Test.csproj \
  --configuration "$configuration" --no-restore --no-build --verbosity normal \
  --filter 'FullyQualifiedName~Postgres' \
  --results-directory "$test_results_directory" --logger 'trx;LogFileName=postgres.trx' \
  -- \
  "NUnit.WorkDirectory=$data_dir" \
  "NUnit.TestOutputXml=nunit-results"

python3 scripts/verify-postgres-test-results.py "$test_results_directory/postgres.trx"
echo "PostgreSQL migrations and BookshelfNG conversion smoke tests passed."
