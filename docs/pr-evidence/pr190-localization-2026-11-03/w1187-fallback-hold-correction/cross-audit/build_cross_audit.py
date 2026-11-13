#!/usr/bin/env python3
import hashlib, json, re, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
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
ORDINAL = 1187
SOURCE = "{value0} conversion was cancelled."
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

def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()

def verify_sumlist(folder, name, allowed_missing=()):
    count = 0
    missing = []
    path = folder / name
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, rel = line.split(None, 1)
        rel = rel.strip().lstrip("*")
        target = Path(rel) if Path(rel).is_absolute() else folder / rel
        if not target.is_file() and Path(rel).is_absolute() and "w1187-dynamic-target-quality/" in rel:
            target = folder / rel.split("w1187-dynamic-target-quality/", 1)[1]
        if not target.is_file():
            if rel in allowed_missing:
                missing.append(rel)
                continue
            raise ValueError(f"missing checksum input: {target}")
        if sha(target.read_bytes()) != digest:
            raise ValueError(f"checksum mismatch: {target}")
        count += 1
    return {"verified": count, "missing": missing}

def placeholders(text):
    return re.findall(r"\{[^{}]+\}", text)

def numeric_tokens(text):
    bare = re.sub(r"\{[^{}]+\}", "", text)
    return re.findall(r"\d+(?:[.,]\d+)*", bare)

def markup_tokens(text):
    return re.findall(r"</?[A-Za-z][^>]*>", text)

def verify_packet(folder, script):
    proc = subprocess.run([sys.executable, str(folder / script)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout + proc.stderr)
    return {"exitCode": proc.returncode, "output": proc.stdout.strip()}

if any(p.name not in {"build_cross_audit.py", "verify_cross_audit.py"} for p in OUT.iterdir()):
    raise SystemExit("cross-audit output directory already contains generated artifacts")

# Verify upstream packets and every retained prior evidence bundle used here.
checksums = {
    "candidateFree": verify_sumlist(CAND, "SHA256SUMS.txt"),
    "blind": verify_sumlist(BLIND, "SHA256SUMS.txt"),
    "priorWindow": verify_sumlist(OLD, "SHA256SUMS", {"independent-cross-review/__pycache__/compare-primary-after-independent.cpython-314.pyc"}),
    "priorPrimary": verify_sumlist(OLD / "primary-review", "SHA256SUMS"),
    "priorCross": verify_sumlist(OLD / "independent-cross-review", "SHA256SUMS", {"__pycache__/compare-primary-after-independent.cpython-314.pyc"}),
    "priorIndependentReview": verify_sumlist(OLD / "independent-cross-review", "INDEPENDENT-REVIEW-SHA256SUMS"),
    "laterResolutionEvidence": verify_sumlist(RES, "EVIDENCE-SHA256SUMS.txt"),
    "laterReview1": verify_sumlist(RES / "independent-review-1", "SHA256SUMS"),
}
candidate_free_run = verify_packet(CAND, "verify_packet.py")
blind_run = verify_packet(BLIND, "verify_review.py")

# Exact-head local checkout, PR metadata, and both published refs.
local = {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
         "branch": git("branch", "--show-current"), "status": git("status", "--porcelain=v1")}
if local != {"head": HEAD, "tree": TREE, "branch": BRANCH, "status": ""}:
    raise ValueError(f"local exact-head checkout mismatch: {local}")
pr = json.loads(subprocess.check_output(["gh", "api", "repos/snapetech-org/chaptarrng/pulls/190"], text=True))
if pr["state"] != "open" or pr["draft"] is not True or pr["head"]["sha"] != HEAD or pr["head"]["ref"] != BRANCH or pr["head"]["repo"]["full_name"].lower() != "snapetech-org/chaptarrng":
    raise ValueError("live PR metadata mismatch")
remote_rows = subprocess.check_output(["git", "-C", str(REPO), "ls-remote", "origin", f"refs/heads/{BRANCH}", "refs/pull/190/head"], text=True).splitlines()
remote = {line.split()[1]: line.split()[0] for line in remote_rows}
if remote.get(f"refs/heads/{BRANCH}") != HEAD or remote.get("refs/pull/190/head") != HEAD:
    raise ValueError(f"published refs differ from exact head: {remote}")

inp = j(CAND / "input.json")
cm = j(CAND / "manifest.json")
bm = j(BLIND / "manifest.json")
bsummary = j(BLIND / "summary.json")
assert cm["exactHead"] == bm["head"] == inp["exactHead"] == HEAD
assert cm["exactTree"] == bm["tree"] == inp["exactTree"] == TREE
assert inp["sourceOrdinal"] == ORDINAL and inp["sourceId"] == SOURCE_ID and inp["source"]["source"] == SOURCE
assert inp["reviewConstraints"]["locales"] == LOCALES
assert cm["cellCount"] == 12 and bm["cellCount"] == 12

# Re-read source registry and both exact production callers from this tree.
registry_path = REPO / REGISTRY_REL
registry_raw = registry_path.read_bytes()
registry = json.loads(registry_raw)
record_index = next(i for i, row in enumerate(registry["records"]) if row.get("id") == SOURCE_ID)
record = registry["records"][record_index]
registry_sha = sha(registry_raw)
registry_blob = git("hash-object", str(registry_path))
registry_tree_blob = git("rev-parse", f"{HEAD}:{REGISTRY_REL.as_posix()}")
assert registry_sha == inp["sourceRegistryPin"]["fileSha256"]
assert registry_blob == inp["sourceRegistryPin"]["gitBlob"] == registry_tree_blob
assert record["source"] == SOURCE and record["sourceFingerprint"] == inp["source"]["sourceFingerprint"]
assert record["parameters"] == [{"name": "value0", "sourceToken": "{TargetQualityName}", "kind": "dynamic-data"}]
assert record["patterns"] == [SOURCE] and record["sourceTemplates"] == ["{TargetQualityName} conversion was cancelled."]
assert record["protectedLiterals"] == []
assert "M4B" not in record["source"] and "M4B" not in record["sourceTemplates"][0]

caller_path = REPO / CALLER_REL
caller_raw = caller_path.read_bytes()
caller_lines = caller_raw.decode("utf-8").splitlines()
caller_sha = sha(caller_raw)
caller_blob = git("hash-object", str(caller_path))
caller_tree_blob = git("rev-parse", f"{HEAD}:{CALLER_REL.as_posix()}")
assert caller_blob == caller_tree_blob
expected_callers = [(195, "job.TargetQualityName", "8c6b4ea5b8dc186855cb06ec101976b7ee8c90364cce42f5d2b4f594034d6806"),
                    (603, "request.TargetQualityName", "e60a2173817aeea3829f7590963e82994d2bc0e6ecce3ca48429c02a442bef37")]
caller_audit = []
for line_no, expression, expected_trimmed_hash in expected_callers:
    raw_line = caller_lines[line_no - 1]
    trimmed = raw_line.strip()
    assert expression + ' ?? "M4B"' in trimmed
    assert trimmed.count("M4B") == 1
    assert sha(trimmed) == expected_trimmed_hash
    registry_site = next(x for x in record["callsites"] if x["file"] == CALLER_REL.as_posix() and x["line"] == line_no)
    assert registry_site["sourceLine"] == trimmed and registry_site["sourceLineSha256"] == expected_trimmed_hash
    caller_audit.append({"path": CALLER_REL.as_posix(), "line": line_no, "lineText": raw_line,
                         "rawLineSha256": sha(raw_line), "trimmedLineSha256": sha(trimmed),
                         "dynamicExpression": expression, "nullFallbackLiteral": "M4B",
                         "registryLineHashMatches": True})
assert len(caller_audit) == 2

# Prior W1150–W1199 holds, blind decisions, and current cells.
primary_holds = [x for x in jl(OLD / "primary-review/holds.jsonl") if x.get("sourceId") == SOURCE_ID]
cross_holds = [x for x in jl(OLD / "independent-cross-review/independent-holds.jsonl") if x.get("sourceId") == SOURCE_ID]
blind_rows = jl(BLIND / "review-decisions.jsonl")
assert len(primary_holds) == len(cross_holds) == len(blind_rows) == len(inp["targetCells"]) == 12
assert all(x.get("exactHead") == "6e7a5341b7ccac31d950c73db68277f9a1f18f8e" and x.get("exactTree") == "d073e1373021bf715db37461a12654f7e993cdbf" for x in primary_holds + cross_holds)
assert all(x.get("primaryDisposition") == "hold" and x.get("protectedLiterals") == ["M4B"] for x in primary_holds)
assert all(x.get("independentDisposition") == "hold" and x.get("protectedLiterals") == ["M4B"] for x in cross_holds)

# Cross-check the later exact-hash corrections already present in the current catalog.
root_rows = jl(RES / "root-decisions.jsonl")
apply_rows = jl(RES / "exact-hash-apply-plan.jsonl")
resolution_summary = j(RES / "summary.json")
readback = j(RES / "apply-readback.json")
source_caller_evidence = j(RES / "source-caller-evidence.json")
assert len(root_rows) == 12 and len(apply_rows) == 3
assert resolution_summary["rootDispositions"] == {"accept-current": 9, "correction": 1, "refinement": 2, "hold": 0}
assert source_caller_evidence["sourceRegistryProtectedLiteralsBefore"] == ["M4B"]
assert source_caller_evidence["sourceRegistryProtectedLiteralsAfter"] == []
assert source_caller_evidence["sourceRegistryAfterSha256"] == registry_sha
assert source_caller_evidence["callerEvidence"]["fileSha256"] == caller_sha
assert readback["plannedTargetsReadBack"] is True and readback["noUnplannedCatalogValueChanges"] is True

input_cells = {x["locale"]: x for x in inp["targetCells"]}
blind_by_locale = {x["locale"]: x for x in blind_rows}
primary_by_locale = {x["locale"]: x for x in primary_holds}
cross_by_locale = {x["locale"]: x for x in cross_holds}
root_by_locale = {x["locale"]: x for x in root_rows}
plan_by_locale = {x["locale"]: x for x in apply_rows}
assert set(input_cells) == set(blind_by_locale) == set(primary_by_locale) == set(cross_by_locale) == set(root_by_locale) == set(LOCALES)

current_records = []
prior_reattest = []
apply_plan = []
ledger = []

locale_reason = {
 "ar": "Arabic states that the conversion of {value0} was cancelled; the named quality remains a single dynamic placeholder.",
 "de": "German states that conversion to {value0} was cancelled; the current wording has no fixed M4B prefix.",
 "es": "Spanish states that the {value0} conversion was cancelled and preserves the dynamic name.",
 "fr": "French explicitly states that conversion toward {value0} was cancelled.",
 "hi": "Hindi states that the {value0} conversion was cancelled.",
 "id": "Indonesian states that conversion of {value0} was cancelled.",
 "ja": "Japanese states that conversion of {value0} was cancelled.",
 "ko": "Korean states that conversion of {value0} was cancelled.",
 "pt-BR": "Brazilian Portuguese states that conversion of {value0} was cancelled.",
 "vi": "Vietnamese states that conversion to {value0} was cancelled.",
 "zh-Hans": "Simplified Chinese states that the {value0} conversion was cancelled.",
 "zh-Hant": "Traditional Chinese states that the {value0} conversion was cancelled."
}

for locale in LOCALES:
    cell = input_cells[locale]
    target = cell["target"]
    target_hash = sha(target)
    assert target_hash == cell["targetSha256"]
    source = inp["source"]["source"]
    assert placeholders(source) == ["{value0}"] and placeholders(target) == ["{value0}"]
    assert numeric_tokens(source) == numeric_tokens(target) == []
    assert markup_tokens(source) == markup_tokens(target) == []
    assert all(literal in target for literal in record["protectedLiterals"])
    assert not re.search(r"(?<![A-Za-z0-9])M4B(?![A-Za-z0-9])", target)
    pin = next(x for x in inp["catalogPins"] if x["path"] == cell["catalogPath"])
    cat_path = REPO / cell["catalogPath"]
    cat_raw = cat_path.read_bytes()
    catalog = json.loads(cat_raw)
    assert catalog.get(SOURCE_ID) == target
    assert sha(cat_raw) == pin["fileSha256"]
    assert git("hash-object", str(cat_path)) == pin["gitBlob"]
    assert git("rev-parse", f"{HEAD}:{cell['catalogPath']}") == pin["gitBlob"]
    blind_row = blind_by_locale[locale]
    assert blind_row["sourceId"] == SOURCE_ID and blind_row["sourceOrdinal"] == ORDINAL
    assert blind_row["disposition"] == "accept-current"
    assert blind_row["currentTargetSha256"] == blind_row["selectedTargetSha256"] == target_hash
    assert blind_row.get("proposedTarget") in (None, target)
    prior_p, prior_x = primary_by_locale[locale], cross_by_locale[locale]
    assert prior_p["currentTargetSha256"] == prior_x["currentTargetSha256"]
    assert prior_p["currentTarget"] == prior_x.get("currentTarget")
    assert prior_p["currentTargetSha256"] == sha(prior_p["currentTarget"])
    old_hash = prior_p["currentTargetSha256"]
    changed = old_hash != target_hash
    root = root_by_locale[locale]
    assert root["finalTarget"] == target and root["finalTargetSha256"] == target_hash
    assert root["sourceId"] == SOURCE_ID and root["sourceSha256"] == sha(source)
    assert root["currentTargetSha256"] == old_hash
    if changed:
        assert locale in plan_by_locale
        plan_row = plan_by_locale[locale]
        assert plan_row["expectedCurrentTargetSha256"] == old_hash and plan_row["newTargetSha256"] == target_hash
    else:
        assert locale not in plan_by_locale
    rationale = ("The exact current registry marks value0 as dynamic-data from TargetQualityName and has no protected literals. "
                 "Both exact caller expressions choose TargetQualityName or M4B as the placeholder value, so M4B is a possible "
                 "runtime fallback, not fixed source text. The current translation preserves {value0} once and does not hardcode M4B. "
                 + locale_reason[locale])
    row = {
        "schema": "chaptarrng-cross-audit-cell/v1", "application": "snapetech-org/chaptarrng", "pullRequest": 190,
        "window": "W1187", "head": HEAD, "tree": TREE, "sourceOrdinal": ORDINAL, "sourceId": SOURCE_ID,
        "source": source, "sourceSha256": sha(source), "sourceFingerprint": record["sourceFingerprint"],
        "locale": locale, "catalogPath": cell["catalogPath"], "catalogFileSha256": pin["fileSha256"],
        "catalogGitBlob": pin["gitBlob"], "currentTarget": target, "currentTargetSha256": target_hash,
        "priorPrimaryDisposition": "hold", "priorCrossDisposition": "hold", "priorProtectedLiteralClaim": ["M4B"],
        "blindDisposition": blind_row["disposition"], "blindSelectedTargetSha256": blind_row["selectedTargetSha256"],
        "crossAuditDisposition": "accept-current", "selectedTarget": target, "selectedTargetSha256": target_hash,
        "planAction": "no-op", "priorHoldStatus": "cleared-at-current-head",
        "priorTargetSha256": old_hash, "priorTargetHashMatchesCurrent": not changed,
        "matchesLaterRootFinalTarget": True, "laterRootDisposition": root["finalDisposition"],
        "tokenAudit": {"sourcePlaceholders": placeholders(source), "targetPlaceholders": placeholders(target),
                       "placeholderParity": True, "sourceNumericTokens": numeric_tokens(source),
                       "targetNumericTokens": numeric_tokens(target), "numericParity": True,
                       "sourceMarkupTokens": markup_tokens(source), "targetMarkupTokens": markup_tokens(target),
                       "markupParity": True, "sourceProtectedLiterals": record["protectedLiterals"],
                       "protectedLiteralsPreserved": True, "staticM4BInTarget": False},
        "rationale": rationale, "confidence": "moderate", "nativeSpeakerApproval": "not obtained"
    }
    ledger.append(row)
    prior_reattest.append({
        "sourceOrdinal": ORDINAL, "sourceId": SOURCE_ID, "locale": locale,
        "priorHead": prior_p["exactHead"], "priorTree": prior_p["exactTree"],
        "primaryDisposition": prior_p["primaryDisposition"], "crossDisposition": prior_x["independentDisposition"],
        "priorPrimaryTarget": prior_p["currentTarget"], "priorPrimaryTargetSha256": old_hash,
        "priorCrossTargetSha256": prior_x["currentTargetSha256"],
        "priorPrimaryProtectedLiterals": prior_p["protectedLiterals"], "priorCrossProtectedLiterals": prior_x["protectedLiterals"],
        "priorPrimaryRationale": prior_p["decisionRationale"], "priorCrossRationale": prior_x["rationale"],
        "currentHead": HEAD, "currentTree": TREE, "currentTarget": target, "currentTargetSha256": target_hash,
        "targetHashUnchanged": not changed, "priorHoldResolution": "cleared-at-current-head",
        "resolutionBasis": "The current exact source registry has protectedLiterals=[]; both exact callsites pass TargetQualityName ?? M4B as the dynamic {value0} value. The current target retains the placeholder and does not force M4B."
    })
    apply_plan.append({
        "sourceOrdinal": ORDINAL, "sourceId": SOURCE_ID, "locale": locale,
        "catalogPath": cell["catalogPath"], "currentTargetSha256": target_hash,
        "selectedDisposition": "accept-current", "action": "no-op", "apply": False,
        "reason": "The current exact-head catalog target matches the cross-audit selection; the prior hold is cleared by the corrected source classification."
    })
    current_records.append({"locale": locale, "catalogPath": cell["catalogPath"], "catalogFileSha256": pin["fileSha256"],
                            "catalogGitBlob": pin["gitBlob"], "targetSha256": target_hash})

counts = Counter(x["crossAuditDisposition"] for x in ledger)
assert len(ledger) == 12 and counts == Counter({"accept-current": 12})
changed_rows = [x for x in prior_reattest if not x["targetHashUnchanged"]]
assert {x["locale"] for x in changed_rows} == {"de", "fr", "vi"}
assert len(changed_rows) == 3
assert len([x for x in prior_reattest if x["targetHashUnchanged"]]) == 9
assert len(apply_plan) == 12 and all(x["action"] == "no-op" and x["apply"] is False for x in apply_plan)
assert all(x["priorHoldResolution"] == "cleared-at-current-head" for x in prior_reattest)
assert bsummary["dispositions"] == {"accept-current": 12, "correction": 0, "refinement": 0, "hold": 0}

source_audit = {
    "application": "snapetech-org/chaptarrng", "pullRequest": 190, "head": HEAD, "tree": TREE,
    "sourceOrdinal": ORDINAL, "sourceId": SOURCE_ID, "source": SOURCE, "sourceSha256": sha(SOURCE),
    "sourceFingerprint": record["sourceFingerprint"], "registryPath": REGISTRY_REL.as_posix(),
    "registryFileSha256": registry_sha, "registryGitBlob": registry_blob, "registryTreeBlob": registry_tree_blob,
    "registryRecordIndex": record_index, "parameter": record["parameters"][0], "sourceTemplates": record["sourceTemplates"],
    "protectedLiterals": record["protectedLiterals"], "callerPath": CALLER_REL.as_posix(),
    "callerFileSha256": caller_sha, "callerGitBlob": caller_blob, "callers": caller_audit,
    "m4bConclusion": "M4B is a caller-side null fallback value carried through dynamic placeholder {value0}; it is not protected source text.",
    "priorMetadataCorrectionEvidence": {
        "sourceRegistryBeforeSha256": source_caller_evidence["sourceRegistryBaseSha256"],
        "sourceRegistryBeforeProtectedLiterals": source_caller_evidence["sourceRegistryProtectedLiteralsBefore"],
        "sourceRegistryAfterProtectedLiterals": source_caller_evidence["sourceRegistryProtectedLiteralsAfter"],
        "sourceCallerEvidencePath": "docs/pr-evidence/pr190-localization-2026-11-03/w1187-dynamic-target-quality/source-caller-evidence.json"
    },
    "catalogCells": current_records,
    "localCheckout": local,
    "livePR": {"state": "OPEN", "draft": True, "branch": BRANCH, "head": HEAD, "tree": TREE,
                "headRef": remote.get(f"refs/heads/{BRANCH}"), "pullRef": remote.get("refs/pull/190/head")}
}


def pin_file(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha(data)}

evidence_pins = {
    "candidateFree": [pin_file(CAND / x) for x in ("input.json", "manifest.json", "SHA256SUMS.txt")],
    "blind": [pin_file(BLIND / x) for x in ("manifest.json", "SHA256SUMS.txt", "review-decisions.jsonl", "summary.json")],
    "priorWindow": [pin_file(OLD / x) for x in ("manifest.json", "SHA256SUMS")],
    "priorPrimary": [pin_file(OLD / x) for x in ("primary-review/manifest.json", "primary-review/SHA256SUMS", "primary-review/holds.jsonl")],
    "priorCross": [pin_file(OLD / x) for x in ("independent-cross-review/manifest.json", "independent-cross-review/SHA256SUMS", "independent-cross-review/INDEPENDENT-REVIEW-SHA256SUMS", "independent-cross-review/independent-holds.jsonl")],
    "laterResolution": [pin_file(RES / x) for x in ("EVIDENCE-SHA256SUMS.txt", "source-caller-evidence.json", "exact-hash-apply-plan.jsonl", "root-decisions.jsonl", "apply-readback.json", "summary.json")],
    "currentSource": [pin_file(registry_path), pin_file(caller_path)]
}

summary = {
    "schemaVersion": 1, "application": "ChaptarrNG", "repository": "snapetech-org/chaptarrng", "pullRequest": 190,
    "window": "W1187", "sourceOrdinal": ORDINAL, "sourceId": SOURCE_ID, "head": HEAD, "tree": TREE,
    "sourceRegistryProtectedLiterals": [], "m4bClassification": "dynamic placeholder fallback, not protected source text",
    "cellCount": 12, "blindAcceptCurrent": 12, "priorPrimaryAndCrossHolds": 12,
    "priorHoldConflictsAdjudicated": 12, "priorTargetHashesStillCurrent": 9, "priorTargetHashesSupersededByAppliedResolution": 3,
    "crossAuditDispositions": dict(counts), "updateCount": 0, "noOpCount": 12, "holdCount": 0,
    "placeholderMismatchCount": 0, "numericMismatchCount": 0, "markupMismatchCount": 0,
    "protectedLiteralMismatchCount": 0, "staticM4BInSelectedTargets": 0,
    "priorHoldsReattested": 12, "currentTargetHashesMatchLaterRootSelection": 12,
    "candidateFreeVerifier": candidate_free_run, "blindVerifier": blind_run, "checksumCounts": checksums,
    "priorEvidenceChecksumLimitations": ["The prior top-level and independent-cross SHA256SUMS list reference one missing generated __pycache__/compare-primary-after-independent.cpython-314.pyc file; all other listed entries verified, and the primary and independent-review subpacket checksum lists passed."],
    "repositoryFilesEdited": False, "pullRequestEdited": False, "testsBuildCIorBrowserRun": False,
    "browserReview": "not performed", "nativeSpeakerApproval": "not obtained",
    "createdAtUtc": datetime.now(timezone.utc).isoformat()
}

# Persist evidence outputs.
def dump_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def dump_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")

dump_jsonl(OUT / "cross-audit-ledger.jsonl", ledger)
dump_jsonl(OUT / "prior-hold-reattestation.jsonl", prior_reattest)
dump_jsonl(OUT / "apply-plan.jsonl", apply_plan)
dump_json(OUT / "source-caller-audit.json", source_audit)
dump_json(OUT / "evidence-pins.json", evidence_pins)
dump_json(OUT / "input-verification.json", {"candidateFreeVerifier": candidate_free_run, "blindVerifier": blind_run,
    "checksumFileCounts": checksums, "livePR": summary["head"], "tree": summary["tree"]})
dump_json(OUT / "summary.json", summary)
(OUT / "README.md").write_text(
    "# ChaptarrNG PR #190 W1187 cross-audit\n\n"
    f"This packet cross-audits source ordinal {ORDINAL} (`{SOURCE_ID}`) at exact live PR head `{HEAD}` / tree `{TREE}`. "
    "The source registry and both exact `ConversionJobService.cs` callers were re-read and hash-checked. They establish that `M4B` is the null fallback passed as dynamic `{value0}`, not protected source text; the current registry has an empty protected-literal list.\n\n"
    "The earlier W1150–W1199 primary and independent cross packets held all 12 cells with `M4B` recorded as protected. The current blind packet accepts all 12. At the requested head, 9 current hashes are unchanged from those old held cells; German, French, and Vietnamese now match the later exact-hash correction/refinement plan already read back into the catalogs. All 12 current targets retain `{value0}` once and do not hardcode `M4B`. The cross-audit clears all 12 prior holds and selects 12 no-op actions: 0 updates, 12 no-ops, 0 holds.\n\n"
    "The verifier rechecks the candidate-free and blind packets, prior W1150–W1199 evidence checksums, current source registry/callers/catalogs, source and target hashes, prior-hold lineage, later exact-hash readback, local/remote refs, and live PR metadata. One generated `__pycache__/compare-primary-after-independent.cpython-314.pyc` entry is absent from the old top-level and cross-review checksum lists; all other listed entries passed, including the primary and independent-review subpacket lists. No repository/PR files were edited; no tests, builds, CI, or browser review were run. Native-speaker approval was not obtained.\n\n"
    "Run `python3 verify_cross_audit.py` and `sha256sum -c SHA256SUMS.txt` in this directory.\n", encoding="utf-8")

manifest = {
    "schemaVersion": 1, "artifact": "ChaptarrNG PR #190 W1187 independent cross-audit",
    "application": "ChaptarrNG", "repository": "snapetech-org/chaptarrng", "pullRequest": 190,
    "branch": BRANCH, "head": HEAD, "tree": TREE, "sourceOrdinal": ORDINAL, "sourceId": SOURCE_ID,
    "candidateFreePacket": str(CAND), "candidateFreeInputSha256": sha((CAND / "input.json").read_bytes()),
    "candidateFreeManifestSha256": sha((CAND / "manifest.json").read_bytes()),
    "candidateFreeChecksumListSha256": sha((CAND / "SHA256SUMS.txt").read_bytes()),
    "blindPacket": str(BLIND), "blindManifestSha256": sha((BLIND / "manifest.json").read_bytes()),
    "blindChecksumListSha256": sha((BLIND / "SHA256SUMS.txt").read_bytes()),
    "priorWindow": "W1150-W1199", "priorHead": "6e7a5341b7ccac31d950c73db68277f9a1f18f8e",
    "priorTree": "d073e1373021bf715db37461a12654f7e993cdbf", "priorPrimaryHoldCount": 12,
    "priorCrossHoldCount": 12, "priorHoldsReattested": 12, "dispositionCounts": dict(counts),
    "updateCount": 0, "noOpCount": 12, "holdCount": 0,
    "m4bClassification": "dynamic placeholder fallback, not protected source text",
    "nativeSpeakerApproval": "not obtained", "browserReview": "not performed",
    "repositoryOrPRFilesEdited": False, "createdAtUtc": datetime.now(timezone.utc).isoformat(), "evidencePins": evidence_pins
}
files = []
for path in sorted(OUT.iterdir(), key=lambda p: p.name):
    if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS.txt"}:
        data = path.read_bytes()
        files.append({"path": path.name, "bytes": len(data), "sha256": sha(data)})
manifest["files"] = files
dump_json(OUT / "manifest.json", manifest)
paths = sorted((p for p in OUT.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt"), key=lambda p: p.name)
(OUT / "SHA256SUMS.txt").write_text("".join(f"{sha(p.read_bytes())}  {p.name}\n" for p in paths), encoding="utf-8")
print(json.dumps({"built": True, "head": HEAD, "tree": TREE, "cells": len(ledger), "dispositions": dict(counts),
                  "updateCount": 0, "noOpCount": 12, "holdCount": 0, "priorHoldsReattested": 12,
                  "unchangedOldTargetHashes": 9, "changedByLaterAppliedPlan": 3,
                  "m4bClassification": summary["m4bClassification"], "checksums": checksums}, ensure_ascii=False, indent=2))
