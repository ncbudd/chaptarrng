from __future__ import annotations

import collections
import hashlib
import json
import subprocess
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[5]
HEAD = "a9a74f6ba733e8c1f06a2d260bd802d4fde2da0e"
TREE = "d9d25f309f3a7256056b4ed8deb1dabee58b64fe"
LEDGER = EVIDENCE / "crossreview" / "crossreview-ledger.jsonl"
SOURCE_PATH = "src/NzbDrone.Core/Localization/Core/en.json"


def sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


assert git("rev-parse", "HEAD") == HEAD
assert git("rev-parse", "HEAD^{tree}") == TREE
status = git("status", "--short").splitlines()
assert all(line.startswith("?? docs/pr-evidence/pr190-localization-2026-11-02/window-0900-0949") for line in status), status

for filename in ("live-pr-heads-before.json", "live-pr-heads-after.json"):
    snapshot = json.loads((EVIDENCE / "crossreview" / filename).read_text(encoding="utf-8"))
    assert len(snapshot["pullRequests"]) == 7
    chaptarr = next(item for item in snapshot["pullRequests"] if item["pullRequest"] == 190)
    assert chaptarr["repository"].lower() == "snapetech-org/chaptarrng"
    assert chaptarr["state"] == "OPEN" and chaptarr["isDraft"] is True
    assert chaptarr["apiHead"] == HEAD and chaptarr["remoteBranchHead"] == HEAD and chaptarr["tree"] == TREE

rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(rows) == 600
assert len({(row["sourceOrdinal"], row["locale"]) for row in rows}) == 600
assert collections.Counter(row["crossReviewDisposition"] for row in rows) == {
    "accept-current": 478,
    "accept-proposal": 121,
    "revise-proposal": 1,
}

source_raw = subprocess.check_output(["git", "show", f"{HEAD}:{SOURCE_PATH}"], cwd=REPO)
source_catalog = json.loads(source_raw)
locale_catalogs: dict[str, dict] = {}
locale_paths: dict[str, str] = {}
preapply_pins = {}

for row in rows:
    locale = row["locale"]
    path = row["currentTargetCatalogAttestation"]["catalogPath"]
    locale_paths[locale] = path

for locale, path in sorted(locale_paths.items()):
    raw = (REPO / path).read_bytes()
    catalog = json.loads(raw)
    assert raw == (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    locale_catalogs[locale] = catalog
    preapply_pins[locale] = {
        "locale": locale,
        "path": path,
        "keyCount": len(catalog),
        "fileSha256": sha(raw),
        "gitBlobOid": git("rev-parse", f"{HEAD}:{path}"),
        "orderedKeysSha256": sha("\n".join(catalog)),
        "keySetSha256": sha("\n".join(sorted(catalog))),
    }

plan = []
for row in rows:
    locale = row["locale"]
    path = locale_paths[locale]
    source_id = row["sourceId"]
    source = row["source"]
    current = row["currentTarget"]
    disposition = row["crossReviewDisposition"]
    source_catalog_path = SOURCE_PATH
    catalog = locale_catalogs[locale]

    assert source_catalog.get(source_id) == source
    assert sha(source) == row["sourceSha256"]
    assert catalog.get(source_id) == current
    assert sha(current) == row["currentTargetSha256"]
    attestation = row["currentTargetCatalogAttestation"]
    assert attestation["catalogPath"] == path and attestation["exactValueMatchesCatalog"]
    assert attestation["targetHashMatches"]
    assert attestation["catalogBlob"] == preapply_pins[locale]["gitBlobOid"]
    assert attestation["catalogFileSha256"] == preapply_pins[locale]["fileSha256"]
    assert row["placeholderAttestation"]["status"] == "pass"
    assert row["markupAttestation"]["status"] == "pass"
    assert row["protectedLiteralAttestation"]["status"] == "pass"

    if disposition == "accept-current":
        final = current
    elif disposition == "accept-proposal":
        final = row["primaryFinalTarget"]
    else:
        assert disposition == "revise-proposal"
        final = row["recommendedTarget"]

    final_sha = sha(final)
    if disposition == "accept-proposal":
        assert final_sha == row["primaryFinalTargetSha256"]
    elif disposition == "revise-proposal":
        assert final_sha == row["recommendedTargetSha256"]
        assert row["sourceOrdinal"] == 947 and locale == "fr"
        assert final == "La demande de téléchargement échoue si MAM ne peut pas appliquer l’avantage Freeleech personnel requis."
    else:
        assert final_sha == row["currentTargetSha256"]

    plan.append({
        "exactHead": HEAD,
        "exactTree": TREE,
        "sourceOrdinal": row["sourceOrdinal"],
        "sourceId": source_id,
        "source": source,
        "sourceFile": source_catalog_path,
        "sourceSha256": row["sourceSha256"],
        "locale": locale,
        "catalogPath": path,
        "catalogBlobOid": attestation["catalogBlob"],
        "catalogFileSha256": attestation["catalogFileSha256"],
        "callerContextSha256": row["callerContextSha256"],
        "callerPinIds": row["callerPinIds"],
        "callerReferenceCount": row["callerReferenceCount"],
        "primaryDisposition": row["primaryDisposition"],
        "crossReviewDisposition": disposition,
        "currentTarget": current,
        "currentTargetSha256": row["currentTargetSha256"],
        "finalTarget": final,
        "finalTargetSha256": final_sha,
        "changed": final != current,
        "rationale": row["rationale"],
        "placeholderAttestation": row["placeholderAttestation"],
        "markupAttestation": row["markupAttestation"],
        "protectedLiteralAttestation": row["protectedLiteralAttestation"],
    })

assert len(plan) == 600 and sum(item["changed"] for item in plan) == 122
write_jsonl(EVIDENCE / "application" / "catalog-preapply-pins.jsonl", list(preapply_pins.values()))
write_jsonl(EVIDENCE / "application" / "apply-plan.jsonl", plan)

for row in plan:
    if row["changed"]:
        locale_catalogs[row["locale"]][row["sourceId"]] = row["finalTarget"]

for locale, path in sorted(locale_paths.items()):
    (REPO / path).write_text(json.dumps(locale_catalogs[locale], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

readback = []
for row in plan:
    actual = json.loads((REPO / row["catalogPath"]).read_text(encoding="utf-8"))[row["sourceId"]]
    assert actual == row["finalTarget"] and sha(actual) == row["finalTargetSha256"]
    readback.append({**row, "readbackTarget": actual, "readbackTargetSha256": sha(actual), "readbackMatches": True})
write_jsonl(EVIDENCE / "application" / "apply-readback.jsonl", readback)

postapply = []
for locale, path in sorted(locale_paths.items()):
    raw = (REPO / path).read_bytes()
    catalog = json.loads(raw)
    assert list(catalog) == list(locale_catalogs[locale])
    postapply.append({
        "locale": locale,
        "path": path,
        "keyCount": len(catalog),
        "fileSha256": sha(raw),
        "gitBlobOid": git("hash-object", path),
        "orderedKeysSha256": sha("\n".join(catalog)),
        "keySetSha256": sha("\n".join(sorted(catalog))),
    })

assert len({item["keySetSha256"] for item in postapply}) == 1
write_json(EVIDENCE / "application" / "post-apply-catalog-attestation.json", {
    "repository": "snapetech-org/ChaptarrNG",
    "pullRequest": 190,
    "sourceHead": HEAD,
    "sourceTree": TREE,
    "changedCells": 122,
    "readbackCells": len(readback),
    "allReadbacksMatch": True,
    "catalogKeySetParity": True,
    "catalogOrderPreservedPerLocale": True,
    "globalCatalogOrderParity": len({item["orderedKeysSha256"] for item in postapply}) == 1,
    "catalogs": postapply,
})

summary = {
    "repository": "snapetech-org/ChaptarrNG",
    "pullRequest": 190,
    "exactSourceHead": HEAD,
    "exactSourceTree": TREE,
    "window": "W900-W949",
    "sourceCount": 50,
    "localeCount": 12,
    "cells": len(plan),
    "changedCells": 122,
    "retainedCells": len(plan) - 122,
    "crossReviewDispositions": {"accept-current": 478, "accept-proposal": 121, "revise-proposal": 1},
    "frenchW947RootAdjudication": {
        "source": "Fail the grab if MAM cannot apply the required personal freeleech wedge",
        "acceptedTarget": "La demande de téléchargement échoue si MAM ne peut pas appliquer l’avantage Freeleech personnel requis.",
        "preservedLiterals": ["MAM", "Freeleech"],
    },
    "currentProtectedLiteralFailureCells": 7,
    "finalProtectedLiteralFailureCells": 0,
    "placeholderMismatches": 0,
    "markupMismatches": 0,
    "catalogKeyCountPerLocale": 4165,
    "allLocaleCatalogKeySetsIdentical": True,
    "perLocaleChangedCells": dict(sorted(collections.Counter(row["locale"] for row in plan if row["changed"]).items())),
    "callerReferences": 86,
    "providerOptionPipelineReferences": 20,
    "serverMessagePipelineReferences": 76,
    "priorDispositionRowsReattested": 10800,
    "w899BoundaryCellsReattested": 12,
    "w899BoundaryMatchesAllLocales": True,
    "nativeSpeakerApproval": False,
    "headedBrowserReview": False,
    "testsBuildScansCi": False,
    "workflowFilesTouched": False,
    "mergeReleaseOrTag": False,
}
write_json(EVIDENCE / "application" / "apply-summary.json", summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))
