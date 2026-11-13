#!/usr/bin/env python3
"""Build an independent, read-only cross-review packet for ChaptarrNG PR #190 W350-399."""
import collections, datetime, hashlib, json, re, subprocess, sys
from pathlib import Path

PRIMARY = Path("/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-primary-20261102")
REPO = Path("/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit")
OUT = Path("/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-crossreview-by-agent-20261102")
EXPECTED_HEAD = "e9de5ac22aba7780f4ff55b3fd903731fea89269"
EXPECTED_TREE = "1c8212fcc3623723b306865ac4d7f765ecf72a22"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]

# Independent semantic findings outside the primary candidate set.
EXTRA = {
    (377, "de"): {
        "disposition": "propose-correction",
        "target": "Sie müssen ein Gespräch mit dem Bot starten oder ihn zu Ihrer Gruppe hinzufügen, um Nachrichten zu erhalten.",
        "confidence": "high",
        "rationale": "The current German translation uses neuter 'es' for masculine 'der Bot'; the object pronoun must be 'ihn'. The corrected sentence retains both required setup actions.",
    },
    (394, "fr"): {
        "disposition": "propose-correction",
        "target": "Succès ! Vous avez correctement configuré vos paramètres de notification Apprise.",
        "confidence": "high",
        "rationale": "The current French translation omits the source's explicit success confirmation; restore it while retaining the configured-notification-settings meaning.",
    },
    (394, "pt-BR"): {
        "disposition": "propose-correction",
        "target": "Sucesso! Você configurou corretamente as opções de notificação do Apprise.",
        "confidence": "moderate",
        "rationale": "The current Portuguese repeats the configure/configurations root and omits 'Success!'; this wording restores the confirmation and avoids the redundancy.",
    },
}

def now(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def sha(b): return hashlib.sha256(b).hexdigest()
def enc(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
def read_json(path): return json.loads(path.read_text(encoding="utf-8"))
def rows(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
def git(*args): return subprocess.check_output(["git", "-C", str(REPO), *args])
def show(head, path): return subprocess.check_output(["git", "-C", str(REPO), "show", f"{head}:{path}"])
def live_pr():
    raw = subprocess.check_output(["gh", "pr", "view", "190", "--repo", "snapetech-org/ChaptarrNG", "--json", "state,isDraft,headRefOid,baseRefOid,url"])
    return json.loads(raw)
def tree_state():
    return {"head": git("rev-parse", "HEAD").decode().strip(), "tree": git("rev-parse", "HEAD^{tree}").decode().strip(), "status": git("status", "--porcelain").decode().strip()}
def require_pin(pr, state):
    assert pr["state"] == "OPEN" and pr["isDraft"] is True, pr
    assert pr["headRefOid"] == EXPECTED_HEAD, pr
    assert state["head"] == EXPECTED_HEAD and state["tree"] == EXPECTED_TREE and state["status"] == "", state

assert all(f.name in {"build_cross_review.py", "README.md", "SHA256SUMS", "cross-review-cells.jsonl", "proposal-review.jsonl", "w349-context-reattestation.jsonl", "live-input-reattestation.json", "summary.json"} for f in OUT.iterdir()) if OUT.exists() else True
manifest = read_json(PRIMARY / "manifest.json")
assert manifest["head"] == EXPECTED_HEAD and manifest["tree"] == EXPECTED_TREE
assert manifest["scope"]["positions"] == [350, 399] and manifest["scope"]["cells"] == 600
# Verify both packet manifests before reading their review data.
for manifest_name in ("INPUT-SHA256SUMS", "SHA256SUMS"):
    check = subprocess.run(["sha256sum", "-c", manifest_name], cwd=PRIMARY, text=True, capture_output=True)
    assert check.returncode == 0, check.stdout + check.stderr
pre_pr, pre_git = live_pr(), tree_state()
pre_checked_at = now()
require_pin(pre_pr, pre_git)

source_slices = rows(PRIMARY / "source-slice.jsonl")
inputs = rows(PRIMARY / "input-cells.jsonl")
callers = rows(PRIMARY / "caller-context.jsonl")
primary_reviews = rows(PRIMARY / "review-cells.jsonl")
protected_rows = rows(PRIMARY / "protected-literal-integrity.jsonl")
prior = rows(PRIMARY / "prior-context-dispositions.jsonl")
manifest_input = read_json(PRIMARY / "manifest.json")
assert len(source_slices) == 50 and len(inputs) == 600 and len(callers) == 50 and len(primary_reviews) == 600
assert len(prior) == 12 and {r["sourceId"] for r in prior} == {"provider.field.f46124e023603"}
assert [r["sourceOrdinal"] for r in source_slices] == list(range(350, 400))
source_by_ord = {r["sourceOrdinal"]: r for r in source_slices}
caller_by_ord = {r["sourceOrdinal"]: r for r in callers}
input_by_key = {(r["sourceOrdinal"], r["locale"]): r for r in inputs}
review_by_key = {(r["sourceOrdinal"], r["locale"]): r for r in primary_reviews}
protected_by_key = {(r["sourceOrdinal"], r["locale"]): r for r in protected_rows}
assert len(protected_rows) == 600
assert set(input_by_key) == {(n, l) for n in range(350, 400) for l in LOCALES}

# Re-attest exact Git objects, file bytes, inventory order, every target, and every caller line.
def check_file(obj):
    data = show(EXPECTED_HEAD, obj["path"])
    blob = git("rev-parse", f"{EXPECTED_HEAD}:{obj['path']}").decode().strip()
    assert blob == obj["blob"] and sha(data) == obj["sha256"]
    if "bytes" in obj: assert len(data) == obj["bytes"]
    return data
source_followup_data = check_file(manifest["sourceFollowup"])
source_data = check_file(manifest["sourceFile"])
registry_data = check_file(manifest["registry"])
catalog_data = {loc: check_file(obj) for loc, obj in manifest["catalogs"].items()}
source_followup = json.loads(source_followup_data)
source_ids = source_followup["currentMissingIds"]
assert sha(enc(source_ids)) == manifest["sourceFollowup"]["currentMissingIdsSha256"]
assert [s["sourceId"] for s in source_slices] == source_ids[350:400]
source_catalog = json.loads(source_data)
locale_catalogs = {loc: json.loads(data) for loc, data in catalog_data.items()}
for s in source_slices:
    assert source_catalog[s["sourceId"]] == s["source"]
    assert sha(s["source"].encode()) == s["sourceTextSha256"]
for row in inputs:
    assert locale_catalogs[row["locale"]][row["sourceId"]] == row["target"]
    assert sha(row["target"].encode()) == row["targetSha256"]
caller_refs = []
for context in callers:
    assert context["attestedHead"] == EXPECTED_HEAD and context["attestedTree"] == EXPECTED_TREE and not context["callerMismatches"]
    for ref in context["callerRefs"]:
        line = show(EXPECTED_HEAD, ref["file"]).decode("utf-8").splitlines()[ref["currentLine"] - 1]
        assert line == ref["currentLineText"] and sha(line.encode()) == ref["currentLineSha256"]
        caller_refs.append(ref)
assert len(caller_refs) == 64 and len({r["file"] for r in caller_refs}) == 28

# Re-attest the adjacent W349 disposition and every live locale target.
source_id_349 = prior[0]["sourceId"]
assert source_catalog[source_id_349] == "Sound"
prior_rechecks = []
for row in prior:
    live_target = locale_catalogs[row["locale"]][source_id_349]
    assert live_target == row["currentLiveTarget"] == row["priorCrossReviewCurrentTarget"]
    assert sha(live_target.encode()) == row["currentLiveTargetSha256"]
    assert row["primaryDisposition"] == "accept-current" and row["crossReviewDisposition"] == "accept-current"
    prior_rechecks.append({"sourceOrdinal":349,"sourceId":source_id_349,"locale":row["locale"],"currentTarget":live_target,"currentTargetSha256":sha(live_target.encode()),"primaryDisposition":row["primaryDisposition"],"crossReviewDisposition":row["crossReviewDisposition"],"callerContextSha256":row["callerContextSha256"],"callerRefs":row["currentCallerRefs"]})
assert len(prior_rechecks) == 12

# Independently set the final target for every cell. All 72 primary proposals are accepted after review;
# the three additional findings below cover omitted/redundant/grammatically incorrect content.
ledger = []
proposal_rows = []
by_locale = {l: collections.Counter() for l in LOCALES}
primary_candidate_accepts = 0
for ordinal in range(350, 400):
    source = source_by_ord[ordinal]
    context = caller_by_ord[ordinal]
    for locale in LOCALES:
        key = (ordinal, locale)
        inp, primary = input_by_key[key], review_by_key[key]
        assert inp["sourceId"] == primary["sourceId"] == source["sourceId"]
        extra = EXTRA.get(key)
        if extra:
            final_disposition, final_target, verdict = extra["disposition"], extra["target"], "additional-proposal"
            independent_rationale, confidence = extra["rationale"], extra["confidence"]
        elif primary["recommendedTarget"] is not None:
            final_disposition, final_target, verdict = primary["disposition"], primary["recommendedTarget"], "accept-primary-candidate"
            independent_rationale = "Candidate was independently reviewed against the English source and caller context; its meaning and grammatical change are sound, and its exact tokens are preserved."
            confidence = "moderate"
            primary_candidate_accepts += 1
        else:
            final_disposition, final_target, verdict = "accept-current", inp["target"], "accept-current"
            independent_rationale = "Current target preserves the source meaning in its pinned caller context; no material semantic, grammatical, or token issue was found."
            confidence = "moderate"
        placeholders = re.findall(r"\{[^{}]+\}", final_target)
        markup = re.findall(r"</?[A-Za-z][^>]*>", final_target)
        protected = inp["protectedLiterals"]
        integrity = protected_by_key[key]
        protected_checks = []
        for item in integrity["checks"]:
            preferred = item["recommendedMatchedForm"] if final_target == primary["recommendedTarget"] and item["recommendedMatchedForm"] else item["currentMatchedForm"]
            allowed = [x for x in (item["literal"], preferred, item["currentMatchedForm"], item["recommendedMatchedForm"]) if x]
            matched = next((x for x in dict.fromkeys(allowed) if x in final_target), None)
            protected_checks.append({"literal":item["literal"],"matchMode":item["matchMode"],"finalMatchedForm":matched,"preserved":matched is not None})
        structural = {
            "sourcePlaceholders": inp["sourcePlaceholders"], "finalPlaceholders": placeholders,
            "placeholderParity": collections.Counter(placeholders) == collections.Counter(inp["sourcePlaceholders"]),
            "sourceMarkup": inp["sourceMarkup"], "finalMarkup": markup,
            "markupParity": collections.Counter(markup) == collections.Counter(inp["sourceMarkup"]),
            "protectedLiterals": protected,
            "protectedLiteralsPreserved": all(x["preserved"] for x in protected_checks),
            "protectedLiteralChecks": protected_checks,
        }
        assert structural["placeholderParity"] and structural["markupParity"] and structural["protectedLiteralsPreserved"], (key, structural, final_target)
        caller_refs_compact = [{
            "kind": r["kind"], "file": r["file"], "line": r["currentLine"],
            "lineSha256": r["currentLineSha256"], "lineText": r["currentLineText"],
            "contextBefore": r["contextBefore"], "contextAfter": r["contextAfter"],
            "registryLine": r.get("registryLine"), "registrySourceLineSha256": r.get("registrySourceLineSha256"),
        } for r in context["callerRefs"]]
        row = {
            "repository":"snapetech-org/chaptarrng", "pullRequest":190,
            "exactHead":EXPECTED_HEAD, "exactTree":EXPECTED_TREE,
            "sourceOrdinal":ordinal,"sourceId":source["sourceId"],"locale":locale,
            "source":source["source"],"sourceTextSha256":source["sourceTextSha256"],
            "currentTarget":inp["target"],"currentTargetSha256":sha(inp["target"].encode()),
            "targetFile":inp["targetFile"],"targetFileBlob":inp["targetFileBlob"],"targetFileSha256":inp["targetFileSha256"],
            "callerContextSha256":context["callerContextSha256"],"callerRefs":caller_refs_compact,
            "priorDisposition":"no exact prior source-ID disposition among positions 0-349; W349 is separately pinned as adjacent context",
            "primaryDisposition":primary["disposition"],"primaryRecommendedTarget":primary["recommendedTarget"],
            "primaryRecommendedTargetSha256":primary["recommendedTargetSha256"],
            "independentVerdict":verdict,"finalDisposition":final_disposition,
            "finalTarget":final_target,"finalTargetSha256":sha(final_target.encode()),
            "independentRationale":independent_rationale,"confidence":confidence,
            "structuralChecks":structural,"nativeSpeakerApproval":False,
        }
        ledger.append(row); by_locale[locale][final_disposition] += 1
        if primary["recommendedTarget"] is not None:
            proposal_rows.append({
                "sourceOrdinal":ordinal,"sourceId":source["sourceId"],"locale":locale,
                "currentTarget":inp["target"],"currentTargetSha256":sha(inp["target"].encode()),
                "primaryCandidate":primary["recommendedTarget"],"primaryCandidateSha256":sha(primary["recommendedTarget"].encode()),
                "primaryDisposition":primary["disposition"],"primaryRationale":primary["rationale"],
                "independentVerdict":"accept-primary-candidate","finalTarget":primary["recommendedTarget"],"finalTargetSha256":sha(primary["recommendedTarget"].encode()),
                "callerContextSha256":context["callerContextSha256"],"source":source["source"],
                "placeholderParity":structural["placeholderParity"],"markupParity":structural["markupParity"],
                "protectedLiteralsPreserved":structural["protectedLiteralsPreserved"],
            })
        elif extra:
            proposal_rows.append({
                "sourceOrdinal":ordinal,"sourceId":source["sourceId"],"locale":locale,
                "currentTarget":inp["target"],"currentTargetSha256":sha(inp["target"].encode()),
                "primaryCandidate":None,"primaryCandidateSha256":None,"primaryDisposition":"accept-current",
                "independentVerdict":"additional-proposal","finalDisposition":final_disposition,
                "finalTarget":final_target,"finalTargetSha256":sha(final_target.encode()),
                "independentRationale":independent_rationale,"callerContextSha256":context["callerContextSha256"],
                "source":source["source"],"placeholderParity":structural["placeholderParity"],"markupParity":structural["markupParity"],
                "protectedLiteralsPreserved":structural["protectedLiteralsPreserved"],
            })
assert primary_candidate_accepts == 72
assert len(ledger) == 600 and len(proposal_rows) == 75
for row in primary_reviews:
    if row["recommendedTarget"] is not None:
        assert row["recommendedTargetSha256"] == sha(row["recommendedTarget"].encode())

# Lock the live PR/tree again before writing artifacts.
pre_write_pr, pre_write_git = live_pr(), tree_state()
pre_write_checked_at = now()
require_pin(pre_write_pr, pre_write_git)
OUT.mkdir(parents=True, exist_ok=True)
def write_json(path, obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def write_jsonl(path, records): path.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for x in records),encoding="utf-8")
write_jsonl(OUT/"cross-review-cells.jsonl", ledger)
write_jsonl(OUT/"proposal-review.jsonl", proposal_rows)
write_jsonl(OUT/"w349-context-reattestation.jsonl", prior_rechecks)

# Final live state attestation after all review inputs have been verified.
post_pr, post_git = live_pr(), tree_state()
post_checked_at = now()
require_pin(post_pr, post_git)
reattest = {
    "repository":"snapetech-org/chaptarrng","pullRequest":190,
    "beforeReview":{"checkedAtUtc":pre_checked_at,"livePullRequest":pre_pr,"worktree":pre_git},
    "beforeWrite":{"checkedAtUtc":pre_write_checked_at,"livePullRequest":pre_write_pr,"worktree":pre_write_git},
    "afterReview":{"checkedAtUtc":post_checked_at,"livePullRequest":post_pr,"worktree":post_git},
    "exactHead":EXPECTED_HEAD,"exactTree":EXPECTED_TREE,
    "sourceFollowup":{"path":manifest["sourceFollowup"]["path"],"blob":manifest["sourceFollowup"]["blob"],"sha256":manifest["sourceFollowup"]["sha256"],"sourceIds":len(source_ids),"sourceIdListSha256":manifest["sourceFollowup"]["currentMissingIdsSha256"],"positionsReattested":50},
    "sourceFile":{"path":manifest["sourceFile"]["path"],"blob":manifest["sourceFile"]["blob"],"sha256":manifest["sourceFile"]["sha256"]},
    "registry":{"path":manifest["registry"]["path"],"blob":manifest["registry"]["blob"],"sha256":manifest["registry"]["sha256"]},
    "catalogs":{loc:{"path":obj["path"],"blob":obj["blob"],"sha256":obj["sha256"]} for loc,obj in manifest["catalogs"].items()},
    "sourceIdsReattested":50,"cellsReattested":600,"callerRefsReattested":64,"callerFilesReattested":28,
    "callerMismatches":0,"cellMismatches":0,"sourceMismatches":0,"priorW349CellsReattested":12,
    "inputPacket":{"path":str(PRIMARY),"inputSha256ManifestSha256":sha((PRIMARY/"INPUT-SHA256SUMS").read_bytes()),"packetSha256ManifestSha256":sha((PRIMARY/"SHA256SUMS").read_bytes())},
    "worktreeUnmodified":True,"repositoryModified":False,
}
write_json(OUT/"live-input-reattestation.json", reattest)
counts = collections.Counter(r["finalDisposition"] for r in ledger)
per_locale = {loc:dict(sorted(by_locale[loc].items())) for loc in LOCALES}
summary = {
    "schemaVersion":1,"repository":"snapetech-org/chaptarrng","pullRequest":190,
    "exactHead":EXPECTED_HEAD,"exactTree":EXPECTED_TREE,
    "scope":{"positions":[350,399],"sourceIds":50,"locales":LOCALES,"cells":600},
    "independentVerdictCounts":dict(sorted(collections.Counter(r["independentVerdict"] for r in ledger).items())),
    "finalDispositionCounts":dict(sorted(counts.items())),"holdCount":counts.get("hold",0),"holds":[],"perLocale":per_locale,
    "primaryCandidateCount":72,"primaryCandidatesAccepted":72,"additionalFindings":3,"totalProposals":75,
    "additionalFindingCells":[{"sourceOrdinal":a,"locale":b,"disposition":x["disposition"],"finalTarget":x["target"],"finalTargetSha256":sha(x["target"].encode()),"confidence":x["confidence"]} for (a,b),x in EXTRA.items()],
    "priorW349":{"cellsReattested":12,"primaryAcceptCurrent":12,"crossReviewAcceptCurrent":12,"currentTargetsMatchLive":12,"callerRefsReattested":1},
    "placeholders":{"cellsChecked":600,"mismatches":0},"markup":{"cellsChecked":600,"mismatches":0},
    "protectedLiterals":{"cellsChecked":600,"mismatches":0},
    "callerContext":{"sourceIds":50,"callerRefs":64,"uniqueFiles":28,"mismatches":0},
    "confidence":"moderate","confidenceReason":"Source/catalog/caller pins and structural checks are high-confidence exact-hash checks; semantic judgments are model-based and need native-speaker review.",
    "nativeSpeakerApproval":False,"browserReview":False,"repositoryModified":False,"testsBuildsScansCiRun":False,"workflowFilesTouched":False,
    "limitations":["No native-speaker approval is claimed.","No browser review or test/build/scan/CI workflow was run."],
}
write_json(OUT/"summary.json", summary)
readme = f"""# ChaptarrNG PR #190 W350–399 independent cross-review

Read-only semantic cross-review of the primary packet at `{PRIMARY}`. The live PR remained OPEN/DRAFT at `{EXPECTED_HEAD}` with tree `{EXPECTED_TREE}`. Source, all 12 locale catalogs, registry, 50 source IDs, 600 current cells, 64 caller references across 28 files, and the 12 W349 adjacent context cells were re-attested from that exact Git tree.

## Results

- Reviewed all 600 current cells and all 72 primary candidate targets against English source and pinned caller context.
- Accepted all 72 primary candidates after independent review.
- Added 3 proposals: German W377 pronoun correction; French W394 restoration of the omitted success confirmation; Brazilian Portuguese W394 wording correction that restores the confirmation and removes the configure/configurations repetition.
- Final dispositions: `{dict(sorted(counts.items()))}`. Candidate and additional proposal strings and exact hashes are in `proposal-review.jsonl`; all 600 final strings and exact hashes are in `cross-review-cells.jsonl`.
- Placeholder, markup, and protected-literal checks pass for all 600 final targets. W349's 12 accepted targets are re-attested in `w349-context-reattestation.jsonl`.

## Limits

Semantic confidence is moderate. No native-speaker approval is claimed. This packet is a read-only review artifact; it includes no repository/PR edits, tests, builds, scans, CI, browser work, workflow work, releases, tags, or merges. Every packet file is covered by `SHA256SUMS`.
"""
(OUT/"README.md").write_text(readme,encoding="utf-8")
# Generate checksum manifest last, excluding the manifest itself.
files=sorted(f for f in OUT.iterdir() if f.is_file() and f.name!="SHA256SUMS")
(OUT/"SHA256SUMS").write_text("".join(f"{sha(f.read_bytes())}  {f.name}\n" for f in files),encoding="utf-8")
print(json.dumps({"output":str(OUT),"cells":len(ledger),"primaryCandidatesAccepted":primary_candidate_accepts,"additionalFindings":len(EXTRA),"finalDispositions":dict(sorted(counts.items())),"files":[f.name for f in sorted(OUT.iterdir())]},indent=2))
