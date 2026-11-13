#!/usr/bin/env python3
import hashlib, json, re, subprocess, sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w600-619-prep-20261103/repo")
CAND = Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w1187-m4b-candidate-free-20261103")
BLIND = Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w1187-m4b-blind-20261103")
OLD = REPO / "docs/pr-evidence/pr190-localization-2026-11-02/window-1150-1199"
RES = REPO / "docs/pr-evidence/pr190-localization-2026-11-03/w1187-dynamic-target-quality"
HEAD = "00d37b25ce5534135c2dacaf6a84d9d15fe0bb0b"
TREE = "13e57e7826db4db86556f244fb066e4915022511"
BRANCH = "codex/chaptarrng-localization-complete-20261031"
SOURCE_ID = "server.message.md764ed5e74b4"
SOURCE = "{value0} conversion was cancelled."
ORDINAL = 1187
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
REGISTRY_REL = Path("docs/localization/server-message-sources.json")
CALLER_REL = Path("src/NzbDrone.Core/MediaFiles/ConversionJobService.cs")

def sha(data):
    if isinstance(data, str): data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def j(path):
    return json.loads(path.read_text(encoding="utf-8"))

def jl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()

def check_sumlist(folder, name, allowed_missing=()):
    count = 0
    missing = []
    for line in (folder / name).read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, rel = line.split(None, 1)
        rel = rel.strip().lstrip("*")
        target = Path(rel) if Path(rel).is_absolute() else folder / rel
        if not target.is_file() and Path(rel).is_absolute() and "w1187-dynamic-target-quality/" in rel:
            target = folder / rel.split("w1187-dynamic-target-quality/", 1)[1]
        if not target.is_file():
            assert rel in allowed_missing, f"missing checksum input: {target}"
            missing.append(rel)
            continue
        assert sha(target.read_bytes()) == digest, f"checksum mismatch: {target}"
        count += 1
    return {"verified": count, "missing": missing}

def placeholders(text): return re.findall(r"\{[^{}]+\}", text)
def numeric_tokens(text): return re.findall(r"\d+(?:[.,]\d+)*", re.sub(r"\{[^{}]+\}", "", text))
def markup_tokens(text): return re.findall(r"</?[A-Za-z][^>]*>", text)

def run_packet(folder, script):
    p = subprocess.run([sys.executable, str(folder / script)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    return p.stdout.strip()

# Internal packet integrity.
output_sums = check_sumlist(OUT, "SHA256SUMS.txt")
assert output_sums["missing"] == []
assert output_sums["verified"] == len((OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines())
manifest = j(OUT / "manifest.json")
summary = j(OUT / "summary.json")
files = {x["path"]: x for x in manifest["files"]}
actual = {p.name for p in OUT.iterdir() if p.is_file()} - {"manifest.json", "SHA256SUMS.txt"}
assert set(files) == actual
for name, meta in files.items():
    data = (OUT / name).read_bytes()
    assert len(data) == meta["bytes"] and sha(data) == meta["sha256"], name
assert (manifest["head"], manifest["tree"], manifest["branch"]) == (HEAD, TREE, BRANCH)
assert manifest["repository"] == "snapetech-org/chaptarrng" and manifest["pullRequest"] == 190
assert (summary["head"], summary["tree"], summary["sourceId"], summary["sourceOrdinal"]) == (HEAD, TREE, SOURCE_ID, ORDINAL)

# Candidate-free input, blind packet, and prior primary/cross evidence checksums.
checksums = {
    "candidateFree": check_sumlist(CAND, "SHA256SUMS.txt"),
    "blind": check_sumlist(BLIND, "SHA256SUMS.txt"),
    "priorWindow": check_sumlist(OLD, "SHA256SUMS", {"independent-cross-review/__pycache__/compare-primary-after-independent.cpython-314.pyc"}),
    "priorPrimary": check_sumlist(OLD / "primary-review", "SHA256SUMS"),
    "priorCross": check_sumlist(OLD / "independent-cross-review", "SHA256SUMS", {"__pycache__/compare-primary-after-independent.cpython-314.pyc"}),
    "priorIndependentReview": check_sumlist(OLD / "independent-cross-review", "INDEPENDENT-REVIEW-SHA256SUMS"),
    "laterResolutionEvidence": check_sumlist(RES, "EVIDENCE-SHA256SUMS.txt"),
    "laterReview1": check_sumlist(RES / "independent-review-1", "SHA256SUMS"),
}
candidate_free_output = run_packet(CAND, "verify_packet.py")
blind_output = run_packet(BLIND, "verify_review.py")
verify_note = j(OUT / "input-verification.json")
assert verify_note["candidateFreeVerifier"]["exitCode"] == 0
assert verify_note["blindVerifier"]["exitCode"] == 0
assert verify_note["checksumFileCounts"] == checksums

inp = j(CAND / "input.json")
blind_manifest = j(BLIND / "manifest.json")
blind_summary = j(BLIND / "summary.json")
assert inp["sourceOrdinal"] == ORDINAL and inp["sourceId"] == SOURCE_ID and inp["source"]["source"] == SOURCE
assert inp["exactHead"] == HEAD and inp["exactTree"] == TREE
assert blind_manifest["head"] == HEAD and blind_manifest["tree"] == TREE
assert blind_manifest["sourceId"] == SOURCE_ID and blind_manifest["sourceOrdinal"] == ORDINAL
assert blind_summary["cellCount"] == 12 and blind_summary["dispositions"] == {"accept-current": 12, "correction": 0, "refinement": 0, "hold": 0}
assert inp["reviewConstraints"]["locales"] == LOCALES

# Exact local, GitHub PR, branch, and pull-ref attestation.
local = {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
         "branch": git("branch", "--show-current"), "status": git("status", "--porcelain=v1")}
assert local == {"head": HEAD, "tree": TREE, "branch": BRANCH, "status": ""}, local
pr = json.loads(subprocess.check_output(["gh", "api", "repos/snapetech-org/chaptarrng/pulls/190"], text=True))
assert pr["state"] == "open" and pr["draft"] is True
assert pr["head"]["sha"] == HEAD and pr["head"]["ref"] == BRANCH
assert pr["head"]["repo"]["full_name"].lower() == "snapetech-org/chaptarrng"
remote_rows = subprocess.check_output(["git", "-C", str(REPO), "ls-remote", "origin", f"refs/heads/{BRANCH}", "refs/pull/190/head"], text=True).splitlines()
remote = {line.split()[1]: line.split()[0] for line in remote_rows}
assert remote.get(f"refs/heads/{BRANCH}") == HEAD and remote.get("refs/pull/190/head") == HEAD

# Independently re-read the exact source registry and both caller lines.
registry_path = REPO / REGISTRY_REL
registry_raw = registry_path.read_bytes()
registry = json.loads(registry_raw)
record_index = next(i for i, row in enumerate(registry["records"]) if row.get("id") == SOURCE_ID)
record = registry["records"][record_index]
registry_sha = sha(registry_raw)
registry_blob = git("hash-object", str(registry_path))
assert registry_sha == inp["sourceRegistryPin"]["fileSha256"]
assert registry_blob == inp["sourceRegistryPin"]["gitBlob"] == git("rev-parse", f"{HEAD}:{REGISTRY_REL.as_posix()}")
assert record["source"] == SOURCE and record["sourceFingerprint"] == inp["source"]["sourceFingerprint"]
assert record["parameters"] == [{"name": "value0", "sourceToken": "{TargetQualityName}", "kind": "dynamic-data"}]
assert record["patterns"] == [SOURCE] and record["sourceTemplates"] == ["{TargetQualityName} conversion was cancelled."]
assert record["protectedLiterals"] == []
caller_path = REPO / CALLER_REL
caller_raw = caller_path.read_bytes()
caller_lines = caller_raw.decode("utf-8").splitlines()
caller_sha = sha(caller_raw)
caller_blob = git("hash-object", str(caller_path))
assert caller_blob == git("rev-parse", f"{HEAD}:{CALLER_REL.as_posix()}")
expected = [(195, "job.TargetQualityName", "8c6b4ea5b8dc186855cb06ec101976b7ee8c90364cce42f5d2b4f594034d6806"),
            (603, "request.TargetQualityName", "e60a2173817aeea3829f7590963e82994d2bc0e6ecce3ca48429c02a442bef37")]
for line_no, expression, expected_hash in expected:
    line = caller_lines[line_no - 1]
    trimmed = line.strip()
    assert expression + ' ?? "M4B"' in trimmed and trimmed.count("M4B") == 1
    assert sha(trimmed) == expected_hash
    row = next(x for x in record["callsites"] if x["file"] == CALLER_REL.as_posix() and x["line"] == line_no)
    assert row["sourceLine"] == trimmed and row["sourceLineSha256"] == expected_hash

source_audit = j(OUT / "source-caller-audit.json")
assert source_audit["registryFileSha256"] == registry_sha and source_audit["registryGitBlob"] == registry_blob
assert source_audit["callerFileSha256"] == caller_sha and len(source_audit["callers"]) == 2
assert source_audit["protectedLiterals"] == []
assert source_audit["m4bConclusion"] == "M4B is a caller-side null fallback value carried through dynamic placeholder {value0}; it is not protected source text."

# Reattest all prior W1150 primary/cross holds and reconcile current cells to blind and resolved exact hashes.
primary = [r for r in jl(OLD / "primary-review/holds.jsonl") if r.get("sourceId") == SOURCE_ID]
cross = [r for r in jl(OLD / "independent-cross-review/independent-holds.jsonl") if r.get("sourceId") == SOURCE_ID]
blind = jl(BLIND / "review-decisions.jsonl")
current_cells = {r["locale"]: r for r in inp["targetCells"]}
ledger = jl(OUT / "cross-audit-ledger.jsonl")
prior_rows = jl(OUT / "prior-hold-reattestation.jsonl")
plan = jl(OUT / "apply-plan.jsonl")
root_rows = {r["locale"]: r for r in jl(RES / "root-decisions.jsonl")}
apply_rows = {r["locale"]: r for r in jl(RES / "exact-hash-apply-plan.jsonl")}
assert len(primary) == len(cross) == len(blind) == len(ledger) == len(prior_rows) == len(plan) == 12
by_primary = {r["locale"]: r for r in primary}
by_cross = {r["locale"]: r for r in cross}
by_blind = {r["locale"]: r for r in blind}
by_ledger = {r["locale"]: r for r in ledger}
by_prior = {r["locale"]: r for r in prior_rows}
by_plan = {r["locale"]: r for r in plan}
assert all(set(x) == set(LOCALES) for x in (current_cells, by_primary, by_cross, by_blind, by_ledger, by_prior, by_plan, root_rows))
assert len(apply_rows) == 3 and set(apply_rows) == {"de", "fr", "vi"}
for locale in LOCALES:
    cell = current_cells[locale]
    target = cell["target"]
    target_hash = sha(target)
    assert target_hash == cell["targetSha256"]
    assert placeholders(SOURCE) == placeholders(target) == ["{value0}"]
    assert numeric_tokens(SOURCE) == numeric_tokens(target) == []
    assert markup_tokens(SOURCE) == markup_tokens(target) == []
    assert all(lit in target for lit in record["protectedLiterals"])
    assert not re.search(r"(?<![A-Za-z0-9])M4B(?![A-Za-z0-9])", target)
    catalog = REPO / cell["catalogPath"]
    pin = next(x for x in inp["catalogPins"] if x["path"] == cell["catalogPath"])
    current_catalog = json.loads(catalog.read_bytes())
    assert current_catalog[SOURCE_ID] == target
    assert sha(catalog.read_bytes()) == pin["fileSha256"]
    assert git("hash-object", str(catalog)) == pin["gitBlob"]
    assert git("rev-parse", f"{HEAD}:{cell['catalogPath']}") == pin["gitBlob"]
    b, p, x = by_blind[locale], by_primary[locale], by_cross[locale]
    assert b["disposition"] == "accept-current" and b["currentTargetSha256"] == b["selectedTargetSha256"] == target_hash
    assert p["primaryDisposition"] == x["independentDisposition"] == "hold"
    assert p["protectedLiterals"] == x["protectedLiterals"] == ["M4B"]
    assert p["currentTargetSha256"] == x["currentTargetSha256"]
    changed = p["currentTargetSha256"] != target_hash
    row, pr, ap = by_ledger[locale], by_prior[locale], by_plan[locale]
    assert row["crossAuditDisposition"] == "accept-current" and row["planAction"] == "no-op"
    assert row["currentTargetSha256"] == row["selectedTargetSha256"] == target_hash
    assert row["priorTargetSha256"] == pr["priorPrimaryTargetSha256"] == p["currentTargetSha256"]
    assert row["blindSelectedTargetSha256"] == b["selectedTargetSha256"]
    assert row["priorTargetHashMatchesCurrent"] is (not changed)
    assert pr["targetHashUnchanged"] is (not changed) and pr["currentTargetSha256"] == target_hash
    assert pr["priorHoldResolution"] == "cleared-at-current-head"
    assert ap["action"] == "no-op" and ap["apply"] is False and ap["currentTargetSha256"] == target_hash
    root = root_rows[locale]
    assert root["finalTarget"] == target and root["finalTargetSha256"] == target_hash
    if changed:
        a = apply_rows[locale]
        assert a["expectedCurrentTargetSha256"] == p["currentTargetSha256"]
        assert a["newTargetSha256"] == target_hash
    else:
        assert locale not in apply_rows

assert sum(x["priorTargetHashMatchesCurrent"] for x in ledger) == 9
assert {x["locale"] for x in ledger if not x["priorTargetHashMatchesCurrent"]} == {"de", "fr", "vi"}
assert summary["priorHoldsReattested"] == 12
assert summary["priorTargetHashesStillCurrent"] == 9
assert summary["priorTargetHashesSupersededByAppliedResolution"] == 3
assert summary["crossAuditDispositions"] == {"accept-current": 12}
assert (summary["updateCount"], summary["noOpCount"], summary["holdCount"]) == (0, 12, 0)
assert summary["currentTargetHashesMatchLaterRootSelection"] == 12
assert summary["repositoryFilesEdited"] is False and summary["pullRequestEdited"] is False
assert summary["testsBuildCIorBrowserRun"] is False
assert summary["nativeSpeakerApproval"] == "not obtained" and summary["browserReview"] == "not performed"

# Provenance pins must still match the exact bytes used for the audit.
pins = j(OUT / "evidence-pins.json")
for group in pins.values():
    for item in group:
        path = Path(item["path"])
        data = path.read_bytes()
        assert len(data) == item["bytes"] and sha(data) == item["sha256"], str(path)

print(json.dumps({
    "pass": True,
    "livePR": {"state": "OPEN", "draft": True, "branch": BRANCH, "head": HEAD, "tree": TREE},
    "cells": 12,
    "priorHoldsReattested": 12,
    "priorTargetHashesStillCurrent": 9,
    "priorTargetHashesSupersededByAppliedResolution": 3,
    "blindAcceptCurrent": 12,
    "crossAuditDispositions": {"accept-current": 12},
    "plan": {"updates": 0, "noOps": 12, "holds": 0},
    "m4bClassification": "dynamic placeholder fallback, not protected source text",
    "protectedLiteralMismatches": 0,
    "candidateFreeVerifier": "PASS",
    "blindVerifier": "PASS",
    "checksums": checksums,
    "outputChecksumList": output_sums,
    "priorEvidenceChecksumLimitations": summary["priorEvidenceChecksumLimitations"],
    "nativeSpeakerApproval": "not obtained",
    "browserReview": "not performed",
    "repositoryOrPRFilesEdited": False
}, ensure_ascii=False, indent=2))
