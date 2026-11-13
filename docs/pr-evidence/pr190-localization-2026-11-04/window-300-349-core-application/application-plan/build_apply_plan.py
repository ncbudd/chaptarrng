#!/usr/bin/env python3
"""Build a source-pinned, exact-hash catalog apply plan for W300-W349."""
import argparse
import collections
import hashlib
import json
import subprocess
from pathlib import Path

HEAD = "f0082d1b655c05b8d4019ede523dd695cd6d745a"
TREE = "4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def stsha(value):
    return sha(value.encode("utf-8"))

def fail(message):
    raise SystemExit("FAIL: " + message)

def need(value, message):
    if not value:
        fail(message)

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_jsonl(path):
    raw = path.read_bytes()
    lines = raw.splitlines()
    return raw, [json.loads(line) for line in lines if line.strip()]

def verify_checksums(directory, sums_name):
    directory = Path(directory)
    sums_path = directory / sums_name
    checks = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.strip()
        need(Path(name).name == name, f"non-local checksum path in {sums_name}: {name}")
        checks[name] = digest
    actual = {p.name for p in directory.iterdir() if p.is_file() and p.name != sums_name}
    extra = actual - set(checks)
    need(extra <= {"SEALED_PACKET_SHA256.txt"}, f"unindexed packet files in {directory}: {sorted(extra)}")
    for name, digest in checks.items():
        need((directory / name).is_file() and sha((directory / name).read_bytes()) == digest,
             f"checksum mismatch in {directory}/{name}")
    if "SEALED_PACKET_SHA256.txt" in extra:
        seal = (directory / "SEALED_PACKET_SHA256.txt").read_text(encoding="utf-8").split()
        need(len(seal) == 2 and seal[1] == sums_name and seal[0] == sha(sums_path.read_bytes()),
             f"sealed packet checksum index mismatch in {directory}")
    return {
        "checksumListSha256": sha(sums_path.read_bytes()),
        "checksumListBytes": sums_path.stat().st_size,
        "checksummedFiles": {name: {"sha256": digest, "bytes": (directory / name).stat().st_size} for name, digest in sorted(checks.items())},
        "additionalFiles": {name: {"sha256": sha((directory / name).read_bytes()), "bytes": (directory / name).stat().st_size} for name in sorted(extra)},
    }

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def canonical_key_order_sha(keys):
    return sha(json.dumps(keys, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--candidate-input", type=Path, required=True)
    parser.add_argument("--primary-dir", type=Path, required=True)
    parser.add_argument("--cross-dir", type=Path, required=True)
    parser.add_argument("--blind-dir", type=Path, required=True)
    parser.add_argument("--root-suggestions-dir", type=Path, required=True)
    parser.add_argument("--root-cross-dir", type=Path, required=True)
    parser.add_argument("--root-manual-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    ci = args.candidate_input.resolve()
    primary = args.primary_dir.resolve()
    cross = args.cross_dir.resolve()
    blind = args.blind_dir.resolve()
    roots = args.root_suggestions_dir.resolve()
    rootcross = args.root_cross_dir.resolve()
    rootmanual = args.root_manual_dir.resolve()
    need(git(repo, "rev-parse", "HEAD") == HEAD, "apply worktree is not at pinned head")
    need(git(repo, "rev-parse", "HEAD^{tree}") == TREE, "apply worktree tree differs from pin")
    need(not git(repo, "status", "--porcelain=v1"), "apply worktree is not clean")

    candidate_files = verify_checksums(ci, "SHA256SUMS.txt")
    primary_files = verify_checksums(primary, "primary-review-SHA256SUMS.txt")
    cross_files = verify_checksums(cross, "SHA256SUMS.txt")
    blind_files = verify_checksums(blind, "SHA256SUMS.txt")
    root_files = verify_checksums(roots, "SHA256SUMS.txt")
    rootcross_files = verify_checksums(rootcross, "SHA256SUMS.txt")
    rootmanual_files = verify_checksums(rootmanual, "SHA256SUMS.txt")
    rootmanual_review = read_json(rootmanual / "review.json")
    need((rootmanual_review.get("head"), rootmanual_review.get("tree")) == (HEAD, TREE), "root manual review pin mismatch")
    need(rootmanual_review["coverage"]["expectedSelectedChangeCount"] == 106
         and rootmanual_review["coverage"]["callerlessHoldCellsApplied"] == 0, "root manual review scope mismatch")
    need(rootmanual_review["nativeSpeakerApproval"] is False and rootmanual_review["testsBuildsScansCiRun"] is False,
         "root manual review claim mismatch")
    manual_inputs = rootmanual_review["inputFiles"]
    for label, raw in {
        "candidateFreeManifest": (ci / "candidate-free-manifest.json").read_bytes(),
        "primaryProposals": (primary / "primary-review-proposals.jsonl").read_bytes(),
        "blindDecisions": (blind / "decisions.jsonl").read_bytes(),
        "primaryCrossDecisions": (cross / "cross-review-decisions.jsonl").read_bytes(),
        "rootSuggestions": (roots / "root-hold-proposals.jsonl").read_bytes(),
        "rootSuggestionCross": (rootcross / "review-results.jsonl").read_bytes(),
    }.items():
        need(manual_inputs[label]["sha256"] == sha(raw), "root manual review input hash mismatch: " + label)

    manifest = read_json(ci / "candidate-free-manifest.json")
    need((manifest.get("head"), manifest.get("tree")) == (HEAD, TREE), "candidate-free pin mismatch")
    cand_raw, candidates = read_jsonl(ci / "candidate-free-cells.jsonl")
    need(len(candidates) == 600, "candidate-free scope is not 600 cells")
    cand_lines = cand_raw.splitlines()
    candidate_by_id = {}
    candidate_line_sha = {}
    for raw_line, row in zip(cand_lines, candidates):
        cid = row["sourceKey"] + "::" + row["locale"]
        need(cid not in candidate_by_id, "duplicate candidate-free cell " + cid)
        candidate_by_id[cid] = row
        candidate_line_sha[cid] = sha(raw_line)
        need(stsha(row["sourceText"]) == row["sourceTextSha256"], "source hash mismatch " + cid)
        need(stsha(row["currentTarget"]) == row["currentTargetSha256"], "current target hash mismatch " + cid)
        need(row["sourceOrdinal"] >= 300 and row["sourceOrdinal"] <= 349, "cell outside W300-W349: " + cid)
        need(row["callerReferenceCount"] >= 0, "invalid caller count " + cid)

    proposal_raw, proposals = read_jsonl(primary / "primary-review-proposals.jsonl")
    cross_raw, cross_rows = read_jsonl(cross / "cross-review-decisions.jsonl")
    blind_raw, blind_rows = read_jsonl(blind / "decisions.jsonl")
    root_prop_raw, root_proposals = read_jsonl(roots / "root-hold-proposals.jsonl")
    root_cross_raw, root_cross_rows = read_jsonl(rootcross / "review-results.jsonl")
    proposal_row_hashes = {r["cellId"]: sha(line) for line, r in zip(proposal_raw.splitlines(), proposals)}
    cross_row_hashes = {r["cellId"]: sha(line) for line, r in zip(cross_raw.splitlines(), cross_rows)}
    root_proposal_row_hashes = {r["cellId"]: sha(line) for line, r in zip(root_prop_raw.splitlines(), root_proposals)}
    root_cross_row_hashes = {r["cellId"]: sha(line) for line, r in zip(root_cross_raw.splitlines(), root_cross_rows)}
    proposal_map = {r["cellId"]: r for r in proposals}
    cross_map = {r["cellId"]: r for r in cross_rows}
    blind_map = {r["sourceKey"] + "::" + r["locale"]: r for r in blind_rows}
    root_prop_map = {r["cellId"]: r for r in root_proposals}
    root_cross_map = {r["cellId"]: r for r in root_cross_rows}
    need(len(proposals) == 87 and len(proposal_map) == 87, "primary proposal count or uniqueness mismatch")
    need(len(cross_rows) == 87 and len(cross_map) == 87 and set(cross_map) == set(proposal_map),
         "cross review rows do not exactly cover primary proposals")
    need(len(blind_rows) == 600 and len(blind_map) == 600, "blind review does not cover 600 unique cells")
    need(len(root_proposals) == 19 and len(root_prop_map) == 19, "root suggestion count or uniqueness mismatch")
    need(len(root_cross_rows) == 19 and len(root_cross_map) == 19 and set(root_cross_map) == set(root_prop_map),
         "root cross review does not exactly cover root suggestions")

    primary_counts = collections.Counter(r["decision"] for r in cross_rows)
    root_counts = collections.Counter(r["decision"] for r in root_cross_rows)
    need(dict(primary_counts) == {"accept": 86, "revise": 1}, "primary cross decision counts differ")
    need(dict(root_counts) == {"accept": 19}, "root-suggestion cross decisions differ")

    changed_by_id = {}
    for cid, proposal in proposal_map.items():
        review = cross_map[cid]
        need(cid in candidate_by_id, "primary proposal missing candidate cell " + cid)
        candidate = candidate_by_id[cid]
        need((proposal["sourceKey"], proposal["locale"]) == (candidate["sourceKey"], candidate["locale"]),
             "primary proposal identity mismatch " + cid)
        need(proposal["currentTargetSha256"] == candidate["currentTargetSha256"], "primary current hash mismatch " + cid)
        need(proposal["sourceTextSha256"] == candidate["sourceTextSha256"], "primary source hash mismatch " + cid)
        need(proposal["recommendedTargetSha256"] == stsha(proposal["recommendedTarget"]), "primary target hash mismatch " + cid)
        need(proposal["candidateFreeRowSha256"] == sha(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
             "primary candidate row hash mismatch " + cid)
        need(review["currentTargetSha256"] == candidate["currentTargetSha256"] and review["sourceTextSha256"] == candidate["sourceTextSha256"],
             "primary cross source/current hash mismatch " + cid)
        need(review["callerContextSha256"] == candidate["callerContextSha256"], "primary cross caller pin mismatch " + cid)
        final = review["reviewerTarget"]
        need(review["reviewerTargetSha256"] == stsha(final), "primary cross final hash mismatch " + cid)
        need(all(review["structuralChecks"].values()), "primary cross structural check failed " + cid)
        if review["decision"] == "accept":
            need(final == proposal["recommendedTarget"], "accepted cross target differs from proposal " + cid)
        elif review["decision"] == "revise":
            need(final != proposal["recommendedTarget"], "revised cross target equals primary proposal " + cid)
        else:
            fail("unsupported primary cross decision " + cid)
        add_change(changed_by_id, cid, candidate, final, "primary-cross-review",
                   review["decision"], candidate_line_sha[cid], proposal_row_hashes[cid], cross_row_hashes[cid],
                   proposal["recommendedTargetSha256"], review["reviewerTargetSha256"])

    root_suggestion_blind_ids = set()
    for cid, prop in root_prop_map.items():
        need(cid not in proposal_map, "root suggestion overlaps primary proposal " + cid)
        need(cid in candidate_by_id and cid in blind_map, "root suggestion lacks candidate/blind row " + cid)
        candidate = candidate_by_id[cid]
        blind_row = blind_map[cid]
        need(blind_row["decision"] == "hold" and blind_row["findingType"] == "semantic-review",
             "root suggestion is not a direct-caller semantic blind hold " + cid)
        need(blind_row["directCallerBacked"] is True and blind_row["callerReferenceCount"] > 0,
             "root suggestion lacks direct caller context " + cid)
        need(prop["currentTargetSha256"] == candidate["currentTargetSha256"] and prop["sourceTextSha256"] == candidate["sourceTextSha256"],
             "root suggestion source/current hash mismatch " + cid)
        need(prop["candidateFreeRowSha256"] == candidate_line_sha[cid], "root suggestion raw candidate row hash mismatch " + cid)
        result = root_cross_map[cid]
        need(result["decision"] == "accept" and result["finalTarget"] == prop["proposedTarget"],
             "root cross acceptance/target mismatch " + cid)
        need(result["finalTargetSha256"] == stsha(result["finalTarget"]), "root cross final hash mismatch " + cid)
        need(result["currentTargetSha256"] == candidate["currentTargetSha256"] and result["sourceTextSha256"] == candidate["sourceTextSha256"],
             "root cross source/current hash mismatch " + cid)
        need(result["integrity"]["callerContextSha256"] == candidate["callerContextSha256"], "root cross caller pin mismatch " + cid)
        need(all(result["integrity"].values()), "root cross integrity check failed " + cid)
        need(result["integrity"]["candidateFreeRowSha256"] == candidate_line_sha[cid], "root cross raw candidate row hash mismatch " + cid)
        root_suggestion_blind_ids.add(cid)
        add_change(changed_by_id, cid, candidate, result["finalTarget"], "root-suggestion-cross-review",
                   result["decision"], candidate_line_sha[cid], root_proposal_row_hashes[cid], root_cross_row_hashes[cid],
                   prop["proposedTargetSha256"], result["finalTargetSha256"])

    need(len(changed_by_id) == 106, "expected exactly 106 selected unique cells")
    need(not any(change["finalTarget"] == candidate_by_id[cid]["currentTarget"] for cid, change in changed_by_id.items()),
         "a selected target is already current; expected 106 actual catalog value changes")

    callerless_ids = {
        r["sourceKey"] + "::" + r["locale"] for r in blind_rows
        if r["decision"] == "hold" and r["findingType"] == "callerless-hold"
        and r["directCallerBacked"] is False and r["callerReferenceCount"] == 0
    }
    need(len(callerless_ids) == 48, "expected 48 blind callerless hash-only holds")
    need(not (callerless_ids & set(changed_by_id)), "callerless hold selected for application")
    callerless_hold_rows = read_jsonl(primary / "primary-review-holds.jsonl")[1]
    need(len(callerless_hold_rows) == 48, "primary callerless hold count mismatch")
    for row in callerless_hold_rows:
        cid = next((k for k, c in candidate_by_id.items()
                    if c["locale"] == row["locale"] and c["sourceOrdinal"] == row["sourceOrdinal"]), None)
        need(cid is not None and cid not in changed_by_id, "primary callerless hold selected or missing")
        need(row["targetTextIncluded"] is False and row["sourceTextIncluded"] is False, "primary hold contains text")
    semantic_hold_ids = {
        r["sourceKey"] + "::" + r["locale"] for r in blind_rows
        if r["decision"] == "hold" and r["findingType"] == "semantic-review"
    }
    need(len(semantic_hold_ids) == 55 and root_suggestion_blind_ids <= semantic_hold_ids,
         "blind semantic hold scope mismatch")
    need(len(semantic_hold_ids & set(proposal_map)) == 36, "expected 36 blind semantic holds in the primary proposal set")
    need(semantic_hold_ids <= set(changed_by_id), "a blind semantic hold lacks a cross-reviewed selected target")
    need(set(changed_by_id) == set(proposal_map) | set(root_prop_map), "application includes an unreviewed cell")

    catalogs = []
    target_meta = manifest["targetCatalogs"]
    need(set(target_meta) == set(LOCALES), "target catalog locale set mismatch")
    locale_for_path = {}
    for locale in LOCALES:
        meta = target_meta[locale]
        path = repo / meta["path"]
        raw = path.read_bytes()
        need(sha(raw) == meta["sha256"], "target catalog preimage hash mismatch " + locale)
        data = json.loads(raw)
        need(len(data) == meta["keyCount"] == 4165, "target key count mismatch " + locale)
        need(raw == (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
             "catalog serialization differs from canonical preimage " + locale)
        catalog_rows = [r for r in candidates if r["locale"] == locale]
        need(len(catalog_rows) == 50, "candidate row count by locale mismatch " + locale)
        need(all(data[r["sourceKey"]] == r["currentTarget"] for r in catalog_rows),
             "candidate current values do not match catalog " + locale)
        need(all(r["targetFile"] == meta["path"] and r["targetFileSha256"] == meta["sha256"]
                 and r["targetFileGitBlob"] == meta["gitBlob"] for r in catalog_rows),
             "candidate target file pin mismatch " + locale)
        path_text = meta["path"]
        locale_for_path[path_text] = locale
        catalogs.append({
            "locale": locale,
            "path": path_text,
            "preimageSha256": meta["sha256"],
            "preimageGitBlob": meta["gitBlob"],
            "preimageBytes": len(raw),
            "keyCount": len(data),
            "keyOrderSha256": canonical_key_order_sha(list(data)),
        })

    changes = sorted(changed_by_id.values(), key=lambda r: (r["sourceOrdinal"], LOCALES.index(r["locale"])))
    plan = {
        "schemaVersion": 1,
        "artifact": "ChaptarrNG PR #190 Core W300-W349 exact-hash catalog apply plan",
        "repository": "snapetech-org/chaptarrng",
        "pullRequest": 190,
        "batch": "W300-349-Core",
        "sourcePin": {"head": HEAD, "tree": TREE},
        "scope": {"sourceKeys": 50, "locales": 12, "candidateCells": 600},
        "inputPacketChecksums": {
            "candidateFree": candidate_files,
            "primaryReview": primary_files,
            "primaryCrossReview": cross_files,
            "independentBlindReview": blind_files,
            "rootSuggestions": root_files,
            "rootSuggestionCrossReview": rootcross_files,
            "rootManualReview": rootmanual_files,
        },
        "selection": {
            "primaryCrossRows": 87,
            "primaryCrossDecisions": dict(sorted(primary_counts.items())),
            "rootSuggestionRows": 19,
            "rootSuggestionCrossDecisions": dict(sorted(root_counts.items())),
            "selectedUniqueCells": 106,
            "callerlessHashOnlyHolds": 48,
            "blindSemanticHoldsSelected": 55,
            "blindAcceptedCurrentCellsSelected": 51,
            "unselectedBlindSemanticHolds": 0,
            "selectedCellIds": [r["cellId"] for r in changes],
        },
        "catalogs": catalogs,
        "changes": changes,
        "applyGuard": "Each catalog must match the exact pinned preimage SHA-256 and blob before any write; every cell must match its exact current target SHA-256 before update.",
        "nativeSpeakerApproval": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": "PASS",
        "plan": str(args.output.resolve()),
        "candidateCells": 600,
        "primaryAccept": primary_counts["accept"],
        "primaryRevise": primary_counts["revise"],
        "rootAccept": root_counts["accept"],
        "selectedCells": len(changes),
        "changedLocales": sorted({r["locale"] for r in changes}),
        "callerlessHoldsSelected": len(callerless_ids & set(changed_by_id)),
    }, ensure_ascii=False, sort_keys=True))

def add_change(target, cid, candidate, final, selection, decision, candidate_raw_line_sha, source_review_row_sha, decision_row_sha, proposal_sha, final_sha):
    need(cid not in target, "duplicate selected cell " + cid)
    need(candidate["callerReferenceCount"] > 0, "selected cell lacks verified caller " + cid)
    need(candidate["currentTargetSha256"] == stsha(candidate["currentTarget"]), "current target hash mismatch " + cid)
    need(stsha(final) == final_sha, "final target hash mismatch " + cid)
    target[cid] = {
        "cellId": cid,
        "sourceOrdinal": candidate["sourceOrdinal"],
        "sourceKey": candidate["sourceKey"],
        "locale": candidate["locale"],
        "targetFile": candidate["targetFile"],
        "currentTargetSha256": candidate["currentTargetSha256"],
        "sourceTextSha256": candidate["sourceTextSha256"],
        "callerContextSha256": candidate["callerContextSha256"],
        "candidateFreeRowSha256": sha(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
        "candidateFreeRawLineSha256": candidate_raw_line_sha,
        "selection": selection,
        "reviewDecision": decision,
        "sourceReviewRowSha256": source_review_row_sha,
        "reviewDecisionRowSha256": decision_row_sha,
        "proposalTargetSha256": proposal_sha,
        "finalTarget": final,
        "finalTargetSha256": final_sha,
    }

if __name__ == "__main__":
    main()

