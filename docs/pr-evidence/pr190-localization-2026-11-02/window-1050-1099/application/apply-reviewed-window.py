#!/usr/bin/env python3
"""Apply independently confirmed ChaptarrNG W1050-W1099 translations."""

from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path


HEAD = "c0a098e4e2b23117860c6e6827c1e84485273a7a"
TREE = "669c5d82ab651dc38abb2db9d35fc2f893a19fef"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_]+)\}")
MARKUP = re.compile(r"<[^>]+>")

EVIDENCE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[5]
CATALOG_DIR = ROOT / "src/NzbDrone.Core/Localization/Core"


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_target(value: object) -> str:
    if isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha_bytes(data)


def leaves(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [leaf for child in value.values() for leaf in leaves(child)]
    if isinstance(value, list):
        return [leaf for child in value for leaf in leaves(child)]
    return []


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def verify_checksums(folder: Path) -> None:
    for line in (folder / "SHA256SUMS").read_text().splitlines():
        digest, relative = line.split("  ", 1)
        path = folder / relative.removeprefix("./")
        if sha_bytes(path.read_bytes()) != digest:
            raise SystemExit(f"packet checksum mismatch: {path}")


def verify_primary_manifest(primary: Path) -> int:
    manifest = json.loads((primary / "manifest.json").read_text())
    artifacts = manifest.get("artifacts", [])
    if len(artifacts) != 24:
        raise SystemExit(f"expected 24 primary manifest artifacts, got {len(artifacts)}")
    for item in artifacts:
        data = (primary / item["path"]).read_bytes()
        actual = {"bytes": len(data), "sha256": sha_bytes(data)}
        expected = {"bytes": item["bytes"], "sha256": item["sha256"]}
        if actual != expected:
            raise SystemExit(f"primary manifest mismatch: {item['path']}")
    return len(artifacts)


def main() -> None:
    if run("git", "rev-parse", "HEAD") != HEAD or run("git", "rev-parse", "HEAD^{tree}") != TREE:
        raise SystemExit("repository is not at the pinned pre-apply head/tree")

    primary = EVIDENCE / "primary"
    crossreview = EVIDENCE / "crossreview"
    application = EVIDENCE / "application"
    verify_checksums(primary)
    verify_checksums(crossreview)
    manifest_artifact_count = verify_primary_manifest(primary)

    cross_summary = json.loads((crossreview / "summary.json").read_text())
    if cross_summary.get("cellCount") != 600:
        raise SystemExit("cross-review summary does not attest 600 cells")
    rows = [json.loads(line) for line in (crossreview / "cross-review-cells.jsonl").read_text().splitlines()]
    if len(rows) != 600:
        raise SystemExit(f"expected 600 cross-review rows, got {len(rows)}")

    en_path = CATALOG_DIR / "en.json"
    english = json.loads(en_path.read_text())
    locale_index = json.loads((CATALOG_DIR / "ui-locales.json").read_text())
    locale_files = {entry["tag"]: entry["file"] for entry in locale_index["locales"]}
    locale_catalogs: dict[str, dict[str, object]] = {}
    locale_paths: dict[str, Path] = {}
    key_orders: dict[str, list[str]] = {}
    for locale in LOCALES:
        filename = locale_files[locale]
        path = CATALOG_DIR / f"{filename}.json"
        locale_paths[locale] = path
        locale_catalogs[locale] = json.loads(path.read_text())
        key_orders[locale] = list(locale_catalogs[locale])
    first_keys = set(key_orders[LOCALES[0]])
    if any(set(order) != first_keys for order in key_orders.values()):
        raise SystemExit("locale catalog key sets differ before apply")

    expected_pairs: set[tuple[str, str]] = set()
    changes: list[dict[str, object]] = []
    all_plan: list[dict[str, object]] = []
    for row in rows:
        if row.get("sourceOrdinal") not in range(1050, 1100):
            raise SystemExit(f"unexpected source ordinal: {row.get('sourceOrdinal')}")
        source_id = str(row["sourceId"])
        locale = str(row["locale"])
        pair = (source_id, locale)
        if pair in expected_pairs or locale not in locale_catalogs:
            raise SystemExit(f"duplicate/unknown review cell: {pair}")
        expected_pairs.add(pair)
        if row.get("callerPinsExact") is not True or row.get("nativeSpeakerApproval") is not False:
            raise SystemExit(f"unexpected review assurance flag: {pair}")
        if row.get("placeholderParity") is not True or row.get("icuParity") is not True or row.get("markupParity") is not True:
            raise SystemExit(f"structure parity flag is not clean: {pair}")
        source = english.get(source_id)
        if source is None or sha_bytes(str(source).encode("utf-8")) != row["sourceSha256"]:
            raise SystemExit(f"source catalog hash mismatch: {pair}")
        catalog = locale_catalogs[locale]
        if source_id not in catalog:
            raise SystemExit(f"missing localized key: {pair}")
        current = catalog[source_id]
        if current != row["currentTarget"] or sha_target(current) != row["currentTargetSha256"]:
            raise SystemExit(f"current target changed since cross-review: {pair}")
        final = row["crossReviewedTarget"]
        if sha_target(final) != row["crossReviewedTargetSha256"]:
            raise SystemExit(f"final target hash mismatch: {pair}")
        for leaf in leaves(final):
            if collections.Counter(PLACEHOLDER.findall(str(source))) != collections.Counter(PLACEHOLDER.findall(leaf)):
                raise SystemExit(f"placeholder mismatch: {pair}")
            if collections.Counter(MARKUP.findall(str(source))) != collections.Counter(MARKUP.findall(leaf)):
                raise SystemExit(f"markup mismatch: {pair}")
            for literal in row.get("protectedLiterals", []):
                if literal not in leaf:
                    raise SystemExit(f"protected literal {literal!r} missing: {pair}")

        change = current != final
        independent = str(row["independentDisposition"])
        if change and independent not in {"confirm-correction", "confirm-refinement"}:
            raise SystemExit(f"unapproved changed target: {pair} / {independent}")
        if not change and independent not in {"confirm-accept-current", "confirm-hold"}:
            raise SystemExit(f"no-op has unexpected disposition: {pair} / {independent}")
        if row["sourceOrdinal"] == 1054:
            if "Dodge" not in str(final) or change:
                raise SystemExit(f"protected Dodge-ing hold was altered: {pair}")

        final_row = dict(row)
        final_row["willChange"] = change
        all_plan.append(final_row)
        if change:
            changes.append({
                "sourceOrdinal": row["sourceOrdinal"],
                "sourceId": source_id,
                "locale": locale,
                "catalogPath": str(locale_paths[locale].relative_to(ROOT)),
                "independentDisposition": independent,
                "currentTarget": current,
                "currentTargetSha256": sha_target(current),
                "finalTarget": final,
                "finalTargetSha256": sha_target(final),
                "independentAssessment": row["independentAssessment"],
            })
    if len(expected_pairs) != 600 or len(changes) != 42:
        raise SystemExit(f"unexpected coverage/change count: {len(expected_pairs)} / {len(changes)}")

    write_jsonl(application / "exact-hash-apply-plan.jsonl", changes)
    write_jsonl(application / "full-window-apply-plan.jsonl", all_plan)
    preapply = [{
        "sourceOrdinal": row["sourceOrdinal"],
        "sourceId": row["sourceId"],
        "locale": row["locale"],
        "catalogPath": row["catalogPath"],
        "beforeTarget": row["currentTarget"],
        "beforeTargetSha256": row["currentTargetSha256"],
        "afterTarget": row["finalTarget"],
        "afterTargetSha256": row["finalTargetSha256"],
    } for row in changes]
    write_jsonl(application / "catalog-preapply-pins.jsonl", preapply)

    before = {}
    for locale in LOCALES:
        path = locale_paths[locale]
        before[locale] = {
            "path": str(path.relative_to(ROOT)),
            "keyCount": len(key_orders[locale]),
            "orderedKeySha256": sha_bytes("\n".join(key_orders[locale]).encode("utf-8")),
            "fileSha256": sha_bytes(path.read_bytes()),
        }
    for row in changes:
        locale_catalogs[str(row["locale"])][str(row["sourceId"])] = row["finalTarget"]
    for locale in LOCALES:
        locale_paths[locale].write_text(json.dumps(locale_catalogs[locale], ensure_ascii=False, indent=2) + "\n")

    readback: list[dict[str, object]] = []
    after = {}
    for locale in LOCALES:
        reread = json.loads(locale_paths[locale].read_text())
        if list(reread) != key_orders[locale]:
            raise SystemExit(f"catalog keys/order changed: {locale}")
        after[locale] = {
            "path": str(locale_paths[locale].relative_to(ROOT)),
            "keyCount": len(reread),
            "orderedKeySha256": sha_bytes("\n".join(reread).encode("utf-8")),
            "fileSha256": sha_bytes(locale_paths[locale].read_bytes()),
        }
    for row in all_plan:
        locale = str(row["locale"])
        source_id = str(row["sourceId"])
        actual = json.loads(locale_paths[locale].read_text())[source_id]
        expected = row["crossReviewedTarget"]
        if actual != expected or sha_target(actual) != row["crossReviewedTargetSha256"]:
            raise SystemExit(f"post-apply readback mismatch: {source_id} / {locale}")
        readback.append({
            "sourceOrdinal": row["sourceOrdinal"],
            "sourceId": source_id,
            "locale": locale,
            "independentDisposition": row["independentDisposition"],
            "willChange": row["willChange"],
            "actualTarget": actual,
            "actualTargetSha256": sha_target(actual),
            "matchesExpected": True,
        })
    write_jsonl(application / "full-window-readback.jsonl", readback)

    changed_paths = sorted(p for p in run("git", "diff", "--name-only", HEAD).splitlines() if p)
    expected_paths = sorted({str(row["catalogPath"]) for row in changes})
    if changed_paths != expected_paths:
        raise SystemExit(f"unexpected changed paths: {changed_paths!r} != {expected_paths!r}")
    write_json(application / "catalog-postapply-attestation.json", {
        "inputHead": HEAD,
        "inputTree": TREE,
        "localeCount": len(LOCALES),
        "before": before,
        "after": after,
        "changedPaths": changed_paths,
        "changedCellCount": len(changes),
        "reviewCellsReadBack": len(readback),
        "allReadbacksMatch": True,
        "keySetsPreserved": True,
        "eachLocaleKeyOrderPreserved": True,
        "primaryManifestArtifactsVerified": manifest_artifact_count,
    })
    write_json(application / "apply-summary.json", {
        "repository": "snapetech-org/chaptarrng",
        "pullRequest": 190,
        "window": "W1050-W1099",
        "inputHead": HEAD,
        "inputTree": TREE,
        "reviewedCells": len(rows),
        "changedCells": len(changes),
        "changedLocaleCatalogs": len(expected_paths),
        "acceptCurrent": 546,
        "confirmedCorrections": 24,
        "confirmedRefinements": 18,
        "protectedDodgeHolds": 12,
        "fullWindowReadbacks": len(readback),
        "nativeSpeakerApproval": False,
        "testsBuildScansCIOrBrowserRun": False,
    })
    print(json.dumps({"changedCells": len(changes), "changedPaths": changed_paths, "readbackCells": len(readback)}, indent=2))


if __name__ == "__main__":
    main()
