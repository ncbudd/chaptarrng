#!/usr/bin/env bash
# Run the same retained archive under its native kernel/architecture.
set -euo pipefail
: "${RUNNER_TEMP:?}"
: "${GITHUB_SHA:?}"
: "${RID:?}"
evidence="$RUNNER_TEMP/native-audit-handoff"
mkdir -p "$evidence/work"
case "$RID" in
  win-x64|win-x86)
    python integration/standalone-handoff/windows.py \
      "$RUNNER_TEMP/native-audit-predecessor/BookshelfNG-v0.4.21.76-${RID}.zip" \
      "$RUNNER_TEMP/native-audit-candidate/ChaptarrNG-0.0.0-${RID}.zip" \
      --output "$evidence/results" --runtime-id "$RID" --candidate-revision "$GITHUB_SHA" \
      2>&1 | tee "$evidence/acceptance.log"
    ;;
  linux-musl-x64|linux-musl-arm64)
    image="chaptarrng-audit-handoff:${GITHUB_RUN_ID:?}"
    mkdir -p "$evidence/library/Fixture Author/Ebooks" "$evidence/library/Fixture Author/Audiobooks"
    docker build -t "$image" -f integration/standalone-handoff/Dockerfile.musl integration/standalone-handoff
    docker run --rm --network none --user "$(id -u):$(id -g)" \
      --cap-drop ALL --security-opt no-new-privileges --pids-limit 512 --memory 6g --cpus 2 \
      -e TMPDIR=/work/work -v "$PWD:/repo:ro" \
      -v "$RUNNER_TEMP/native-audit-predecessor:/predecessor:ro" \
      -v "$RUNNER_TEMP/native-audit-candidate:/candidate:ro" \
      -v "$evidence/library:/library" -v "$evidence:/work" \
      "$image" "/predecessor/BookshelfNG-v0.4.21.76-${RID}.tar.gz" "/candidate/ChaptarrNG-0.0.0-${RID}.tar.gz" \
      --output /work/results --candidate-revision "$GITHUB_SHA" --runtime-id "$RID" \
      2>&1 | tee "$evidence/acceptance.log"
    ;;
  linux-x64|linux-arm64|osx-x64|osx-arm64)
    command=(python packaging/scripts/test-bookshelf-standalone-handoff.py \
      "$RUNNER_TEMP/native-audit-predecessor/BookshelfNG-v0.4.21.76-${RID}.tar.gz" \
      "$RUNNER_TEMP/native-audit-candidate/ChaptarrNG-0.0.0-${RID}.tar.gz" \
      --output "$evidence/results" --candidate-revision "$GITHUB_SHA")
    [[ "$RID" != linux-* ]] || command+=(--runtime-id "$RID")
    TMPDIR="$evidence/work" "${command[@]}" \
      2>&1 | tee "$evidence/acceptance.log"
    ;;
  *) echo "Unsupported native acceptance RID: $RID" >&2; exit 1 ;;
esac
