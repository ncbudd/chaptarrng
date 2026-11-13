#!/usr/bin/env python3
"""Apply the independently reviewed W550–599 catalog targets with exact-hash guards."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = Path(__file__).resolve().parents[0]
PACKET = EVIDENCE.parent / "crossreview" / "full-cell-final-dispositions.jsonl"
PINNED_HEAD = "015ff68d96340292b5e6a45d34496a5936ebf09c"
PINNED_TREE = "bbb59a14a50a4b63bc209663c1e4b873ead4fc10"
HELD_SOURCE_ORDINALS = {561}


def sha(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def tokens(value: str) -> Counter[str]:
    return Counter(re.findall(r"\{[^{}]+\}", value))


def main() -> None:
    head = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    if (head, tree) != (PINNED_HEAD, PINNED_TREE):
        raise SystemExit(f"pinned head mismatch: {head} {tree}")

    rows = read_jsonl(PACKET)
    if len(rows) != 600:
        raise SystemExit(f"expected 600 reviewed cells, found {len(rows)}")

    updates: dict[str, dict[str, str]] = defaultdict(dict)
    plan: list[dict] = []
    holds: list[dict] = []
    file_baselines: dict[str, tuple[str, str]] = {}
    for row in rows:
        if row["exactHead"] != PINNED_HEAD or row["exactTree"] != PINNED_TREE:
            raise SystemExit(f"row pin mismatch: {row['sourceOrdinal']} {row['locale']}")
        target_file = row["targetFile"]
        source_file = row["sourceFile"]
        for file_path, expected_blob, expected_sha in (
            (source_file, row["sourceFileBlob"], row["sourceFileSha256"]),
            (target_file, row["targetFileBlob"], row["targetFileSha256"]),
        ):
            current_blob = git("rev-parse", f"HEAD:{file_path}")
            current_bytes = (ROOT / file_path).read_bytes()
            if current_blob != expected_blob or sha(current_bytes) != expected_sha:
                raise SystemExit(f"file baseline mismatch: {file_path}")
            file_baselines[file_path] = (current_blob, expected_sha)

        source_catalog = json.loads((ROOT / source_file).read_text(encoding="utf-8"))
        target_catalog = json.loads((ROOT / target_file).read_text(encoding="utf-8"))
        key = row["sourceId"]
        if source_catalog.get(key) != row["source"]:
            raise SystemExit(f"source mismatch: {key}")
        current = target_catalog.get(key)
        if current != row["currentTarget"] or sha(current) != row["currentTargetSha256"]:
            raise SystemExit(f"target mismatch: {row['sourceOrdinal']} {row['locale']} {key}")
        if tokens(row["source"]) != tokens(row["finalTarget"] or current):
            raise SystemExit(f"placeholder mismatch: {row['sourceOrdinal']} {row['locale']}")

        disposition = row["finalDisposition"]
        if row["sourceOrdinal"] in HELD_SOURCE_ORDINALS:
            if disposition != "hold":
                raise SystemExit("W561 was not held in cross-review packet")
            holds.append({
                "sourceOrdinal": row["sourceOrdinal"],
                "sourceId": key,
                "locale": row["locale"],
                "currentTarget": current,
                "behaviorBasedOption": row.get("behaviorBasedOption"),
                "reason": row.get("independentRationale"),
            })
            continue
        if disposition in ("propose-correction", "propose-refinement"):
            final_target = row["finalTarget"]
            if not final_target or sha(final_target) != row["finalTargetSha256"]:
                raise SystemExit(f"final target hash mismatch: {row['sourceOrdinal']} {row['locale']}")
            if final_target == current:
                raise SystemExit(f"no-op candidate incorrectly classified as change: {key}")
            if key in updates[target_file]:
                raise SystemExit(f"duplicate update: {target_file} {key}")
            updates[target_file][key] = final_target
            plan.append({
                "sourceOrdinal": row["sourceOrdinal"],
                "sourceId": key,
                "locale": row["locale"],
                "targetFile": target_file,
                "expectedCurrent": current,
                "expectedCurrentSha256": row["currentTargetSha256"],
                "target": final_target,
                "targetSha256": row["finalTargetSha256"],
                "disposition": disposition,
                "crossReviewVerdict": row["crossReviewVerdict"],
                "callerContextSha256": row["callerContextSha256"],
            })
        elif disposition != "accept-current":
            raise SystemExit(f"unexpected final disposition: {disposition}")

    if len(plan) != 266 or len(holds) != 12:
        raise SystemExit(f"unexpected apply/hold counts: {len(plan)} / {len(holds)}")

    for target_file, changes in updates.items():
        path = ROOT / target_file
        raw = path.read_bytes()
        catalog = json.loads(raw)
        for key, target in changes.items():
            catalog[key] = target
        rendered = (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if json.loads(rendered) != catalog:
            raise SystemExit(f"serialization readback failed: {target_file}")
        path.write_bytes(rendered)

    for item in plan:
        actual = json.loads((ROOT / item["targetFile"]).read_text(encoding="utf-8"))[item["sourceId"]]
        if actual != item["target"] or sha(actual) != item["targetSha256"]:
            raise SystemExit(f"post-write readback mismatch: {item['targetFile']} {item['sourceId']}")

    catalog_paths = sorted(updates)
    catalog_key_counts = {
        path: len(json.loads((ROOT / path).read_text(encoding="utf-8")))
        for path in catalog_paths
    }
    readback = {
        "schemaVersion": 1,
        "repository": "snapetech-org/chaptarrng",
        "pullRequest": 190,
        "inputHead": PINNED_HEAD,
        "inputTree": PINNED_TREE,
        "appliedCells": len(plan),
        "appliedCorrections": sum(item["disposition"] == "propose-correction" for item in plan),
        "appliedRefinements": sum(item["disposition"] == "propose-refinement" for item in plan),
        "heldCells": len(holds),
        "heldSourceOrdinal": 561,
        "catalogsChanged": len(catalog_paths),
        "catalogKeyCounts": catalog_key_counts,
        "allTargetsReadBackExactly": True,
        "placeholdersRechecked": True,
        "sourceBoundary": "English wording and 12 targets for ordinal 561 remain held; caller rejects >25000 and accepts 25000.",
        "testsBuildsScansCIorBrowserRun": False,
        "workflowFilesTouched": False,
        "nativeSpeakerApproval": False,
    }
    (EVIDENCE / "apply-plan.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in plan),
        encoding="utf-8",
    )
    (EVIDENCE / "held-cells.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in holds),
        encoding="utf-8",
    )
    (EVIDENCE / "readback.json").write_text(
        json.dumps(readback, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(readback, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
