#!/usr/bin/env python3
"""Verify all W300-W349 source pins, selected decisions, 600 catalog readbacks, and commit scope."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

HEAD = "f0082d1b655c05b8d4019ede523dd695cd6d745a"
TREE = "4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
IDENTITY_HASH = lambda cell_id: hashlib.sha256(cell_id.encode("utf-8")).hexdigest()

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
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return raw, rows

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def verify_packet(directory, sums_name, expected):
    directory = Path(directory)
    sums_path = directory / sums_name
    need(sha(sums_path.read_bytes()) == expected["checksumListSha256"], "checksum-list hash mismatch in " + str(directory))
    checks = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.strip()
        need(Path(name).name == name, "non-local checksum path in " + str(directory))
        checks[name] = digest
    actual = {p.name for p in directory.iterdir() if p.is_file() and p.name != sums_name}
    extra = actual - set(checks)
    need(extra <= {"SEALED_PACKET_SHA256.txt"}, "unindexed packet files in " + str(directory) + ": " + repr(sorted(extra)))
    files = {name: {"sha256": digest, "bytes": (directory / name).stat().st_size} for name, digest in sorted(checks.items())}
    for name, record in files.items():
        need((directory / name).is_file() and sha((directory / name).read_bytes()) == record["sha256"],
             "packet file hash mismatch: " + str(directory / name))
    additional = {}
    if "SEALED_PACKET_SHA256.txt" in extra:
        seal = (directory / "SEALED_PACKET_SHA256.txt").read_text(encoding="utf-8").split()
        need(len(seal) == 2 and seal[1] == sums_name and seal[0] == sha(sums_path.read_bytes()),
             "sealed packet index mismatch: " + str(directory))
        additional["SEALED_PACKET_SHA256.txt"] = {
            "sha256": sha((directory / "SEALED_PACKET_SHA256.txt").read_bytes()),
            "bytes": (directory / "SEALED_PACKET_SHA256.txt").stat().st_size,
        }
    found = {
        "checksumListSha256": sha(sums_path.read_bytes()),
        "checksumListBytes": sums_path.stat().st_size,
        "checksummedFiles": files,
        "additionalFiles": additional,
    }
    need(found == expected, "packet hash manifest differs from apply plan: " + str(directory))
    return found

def verify_structural(candidate, target):
    source = candidate["sourceText"]
    placeholders = collections.Counter(re.findall(r"\{[^{}]+\}", source)) == collections.Counter(re.findall(r"\{[^{}]+\}", target))
    markup = collections.Counter(re.findall(r"</?[A-Za-z][^>]*>", source)) == collections.Counter(re.findall(r"</?[A-Za-z][^>]*>", target))
    inline = collections.Counter(re.findall(r"\x60[^\x60]*\x60", source)) == collections.Counter(re.findall(r"\x60[^\x60]*\x60", target))
    numeric = collections.Counter(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", source)) == collections.Counter(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", target))
    protected = all(token in target for token in candidate.get("protectedLiterals", []) if token)
    return {"placeholder": placeholders, "markup": markup, "inlineCode": inline, "numericToken": numeric, "protectedLiteral": protected}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--phase", choices=["precommit", "committed", "delivered"], default="precommit")
    parser.add_argument("--product-commit", default=None)
    parser.add_argument("--evidence-commit", default=None)
    args = parser.parse_args()
    repo = args.repo.resolve()
    root = args.evidence_root.resolve()
    plan_path = root / "apply-plan.json"
    plan = read_json(plan_path)
    need(plan["sourcePin"] == {"head": HEAD, "tree": TREE}, "plan source pin mismatch")
    need(len(plan["changes"]) == 106, "plan selected cell count mismatch")
    need(plan["selection"]["primaryCrossDecisions"] == {"accept": 86, "revise": 1}, "primary cross counts mismatch")
    need(plan["selection"]["rootSuggestionCrossDecisions"] == {"accept": 19}, "root suggestion cross counts mismatch")
    need(plan["selection"]["callerlessHashOnlyHolds"] == 48, "callerless hold count mismatch")
    need(plan["nativeSpeakerApproval"] is False, "plan claims native-speaker approval")

    packets = root / "source-packets"
    packet_dirs = {
        "candidateFree": packets / "candidate-free" / "input",
        "primaryReview": packets / "primary-review",
        "primaryCrossReview": packets / "primary-cross-review",
        "independentBlindReview": packets / "independent-blind-review",
        "rootSuggestions": packets / "root-suggestions",
        "rootSuggestionCrossReview": packets / "root-suggestion-cross-review",
    }
    sums_names = {
        "candidateFree": "SHA256SUMS.txt",
        "primaryReview": "primary-review-SHA256SUMS.txt",
        "primaryCrossReview": "SHA256SUMS.txt",
        "independentBlindReview": "SHA256SUMS.txt",
        "rootSuggestions": "SHA256SUMS.txt",
        "rootSuggestionCrossReview": "SHA256SUMS.txt",
    }
    for name, directory in packet_dirs.items():
        verify_packet(directory, sums_names[name], plan["inputPacketChecksums"][name])

    manual = packets / "root-manual-review"
    manual_sums = manual / "SHA256SUMS.txt"
    verify_packet(manual, "SHA256SUMS.txt", plan["inputPacketChecksums"]["rootManualReview"])
    manual_review = read_json(manual / "review.json")
    need((manual_review["head"], manual_review["tree"]) == (HEAD, TREE), "root manual review pin mismatch")
    need(manual_review["coverage"]["expectedSelectedChangeCount"] == 106 and manual_review["coverage"]["callerlessHoldCellsApplied"] == 0,
         "root manual review application scope mismatch")
    need(manual_review["nativeSpeakerApproval"] is False and manual_review["testsBuildsScansCiRun"] is False,
         "root manual review claim mismatch")

    candidate_dir = packet_dirs["candidateFree"]
    candidate_manifest = read_json(candidate_dir / "candidate-free-manifest.json")
    need((candidate_manifest["head"], candidate_manifest["tree"]) == (HEAD, TREE), "candidate-free manifest pin mismatch")
    candidate_raw, candidates = read_jsonl(candidate_dir / "candidate-free-cells.jsonl")
    need(sha(candidate_raw) == candidate_manifest["candidateFreeCells"]["sha256"], "candidate-free cells hash mismatch")
    need(len(candidates) == 600, "candidate-free cell count mismatch")
    candidate_by_id = {}
    candidate_raw_line_sha = {}
    for raw_line, candidate in zip(candidate_raw.splitlines(), candidates):
        cid = candidate["sourceKey"] + "::" + candidate["locale"]
        need(cid not in candidate_by_id, "duplicate candidate cell " + cid)
        candidate_by_id[cid] = candidate
        candidate_raw_line_sha[cid] = sha(raw_line)
        need(stsha(candidate["sourceText"]) == candidate["sourceTextSha256"], "source text hash mismatch " + cid)
        need(stsha(candidate["currentTarget"]) == candidate["currentTargetSha256"], "current target hash mismatch " + cid)

    primary_dir = packet_dirs["primaryReview"]
    cross_dir = packet_dirs["primaryCrossReview"]
    blind_dir = packet_dirs["independentBlindReview"]
    root_suggestions_dir = packet_dirs["rootSuggestions"]
    root_cross_dir = packet_dirs["rootSuggestionCrossReview"]
    primary_proposals_raw, primary_proposals = read_jsonl(primary_dir / "primary-review-proposals.jsonl")
    cross_raw, cross_rows = read_jsonl(cross_dir / "cross-review-decisions.jsonl")
    blind_raw, blind_rows = read_jsonl(blind_dir / "decisions.jsonl")
    root_prop_raw, root_proposals = read_jsonl(root_suggestions_dir / "root-hold-proposals.jsonl")
    root_cross_raw, root_cross_rows = read_jsonl(root_cross_dir / "review-results.jsonl")
    plan_changes = {r["cellId"]: r for r in plan["changes"]}
    primary_map = {r["cellId"]: r for r in primary_proposals}
    cross_map = {r["cellId"]: r for r in cross_rows}
    blind_map = {r["sourceKey"] + "::" + r["locale"]: r for r in blind_rows}
    root_prop_map = {r["cellId"]: r for r in root_proposals}
    root_cross_map = {r["cellId"]: r for r in root_cross_rows}
    need(len(primary_map) == 87 and len(cross_map) == 87 and set(primary_map) == set(cross_map), "primary cross scope mismatch")
    need(len(blind_map) == 600 and len(root_prop_map) == 19 and len(root_cross_map) == 19, "blind/root scope mismatch")
    need(len(plan_changes) == 106 and set(plan_changes) == set(primary_map) | set(root_prop_map), "plan selected set is not exact reviewed union")
    need(not (set(primary_map) & set(root_prop_map)), "primary and root suggestion sets overlap")

    primary_lines = {r["cellId"]: sha(line) for line, r in zip(primary_proposals_raw.splitlines(), primary_proposals)}
    cross_lines = {r["cellId"]: sha(line) for line, r in zip(cross_raw.splitlines(), cross_rows)}
    root_prop_lines = {r["cellId"]: sha(line) for line, r in zip(root_prop_raw.splitlines(), root_proposals)}
    root_cross_lines = {r["cellId"]: sha(line) for line, r in zip(root_cross_raw.splitlines(), root_cross_rows)}
    for cid, change in plan_changes.items():
        candidate = candidate_by_id[cid]
        need(change["sourceKey"] == candidate["sourceKey"] and change["locale"] == candidate["locale"], "plan cell identity mismatch " + cid)
        need(change["candidateFreeRawLineSha256"] == candidate_raw_line_sha[cid], "plan raw candidate line pin mismatch " + cid)
        need(change["currentTargetSha256"] == candidate["currentTargetSha256"], "plan current hash mismatch " + cid)
        need(change["sourceTextSha256"] == candidate["sourceTextSha256"] and change["callerContextSha256"] == candidate["callerContextSha256"],
             "plan source/caller pin mismatch " + cid)
        need(stsha(change["finalTarget"]) == change["finalTargetSha256"], "plan final target hash mismatch " + cid)
        need(candidate["targetFile"] == change["targetFile"], "plan target file mismatch " + cid)
        if change["selection"] == "primary-cross-review":
            proposal = primary_map[cid]
            review = cross_map[cid]
            need(change["sourceReviewRowSha256"] == primary_lines[cid] and change["reviewDecisionRowSha256"] == cross_lines[cid],
                 "primary proposal/cross row hashes mismatch " + cid)
            need(review["reviewerTarget"] == change["finalTarget"] and review["reviewerTargetSha256"] == change["finalTargetSha256"],
                 "plan final target differs from primary cross reviewer " + cid)
            need(review["decision"] == change["reviewDecision"], "primary decision mismatch " + cid)
            need(proposal["recommendedTargetSha256"] == change["proposalTargetSha256"], "proposal hash mismatch " + cid)
            need(all(review["structuralChecks"].values()), "primary cross structural check failed " + cid)
        elif change["selection"] == "root-suggestion-cross-review":
            proposal = root_prop_map[cid]
            review = root_cross_map[cid]
            blind = blind_map[cid]
            need(change["sourceReviewRowSha256"] == root_prop_lines[cid] and change["reviewDecisionRowSha256"] == root_cross_lines[cid],
                 "root proposal/cross row hashes mismatch " + cid)
            need(review["decision"] == "accept" and review["finalTarget"] == change["finalTarget"],
                 "plan final target differs from root cross reviewer " + cid)
            need(review["finalTargetSha256"] == change["finalTargetSha256"] and review["integrity"]["candidateFreeRowSha256"] == candidate_raw_line_sha[cid],
                 "root cross hash mismatch " + cid)
            need(blind["decision"] == "hold" and blind["findingType"] == "semantic-review" and blind["directCallerBacked"] is True,
                 "root suggestion was not an eligible blind semantic hold " + cid)
            need(proposal["proposedTargetSha256"] == change["proposalTargetSha256"], "root suggestion hash mismatch " + cid)
        else:
            fail("unknown selected change source " + cid)
        need(candidate["callerReferenceCount"] > 0, "selected cell lacks caller context " + cid)
        structural = verify_structural(candidate, change["finalTarget"])
        # Primary cross review uses strict source-token parity; root cross review seals placeholders and caller context.
        if change["selection"] == "primary-cross-review":
            need(all(structural.values()), "selected primary target failed structural checks " + cid)
        else:
            need(structural["placeholder"], "selected root target failed placeholder checks " + cid)

    callerless_ids = {
        r["sourceKey"] + "::" + r["locale"] for r in blind_rows
        if r["decision"] == "hold" and r["findingType"] == "callerless-hold"
        and r["directCallerBacked"] is False and r["callerReferenceCount"] == 0
    }
    semantic_hold_ids = {
        r["sourceKey"] + "::" + r["locale"] for r in blind_rows
        if r["decision"] == "hold" and r["findingType"] == "semantic-review"
    }
    need(len(callerless_ids) == 48 and not (callerless_ids & set(plan_changes)), "callerless holds were selected")
    need(len(semantic_hold_ids) == 55 and semantic_hold_ids <= set(plan_changes), "semantic blind holds are not all adjudicated")
    hold_rows_raw, hold_rows = read_jsonl(primary_dir / "primary-review-holds.jsonl")
    need(len(hold_rows) == 48 and all(r["sourceTextIncluded"] is False and r["targetTextIncluded"] is False for r in hold_rows),
         "primary callerless holds are not hash-only")

    catalog_metas = {m["path"]: m for m in plan["catalogs"]}
    need(len(catalog_metas) == 12, "plan does not cover 12 pinned catalogs")
    changes_by_path = collections.defaultdict(list)
    for change in plan["changes"]:
        changes_by_path[change["targetFile"]].append(change)
    expected_changed_paths = set(changes_by_path)
    need(len(expected_changed_paths) == len(changes_by_path) and expected_changed_paths <= set(catalog_metas),
         "selected target paths exceed pinned catalog set")
    actual_readback = []
    changed_count = 0
    unchanged_count = 0
    for cid, candidate in ((r["sourceKey"] + "::" + r["locale"], r) for r in candidates):
        meta = catalog_metas[candidate["targetFile"]]
        data = json.loads((repo / candidate["targetFile"]).read_bytes())
        need(len(data) == meta["keyCount"] == 4165, "postimage catalog key count mismatch " + meta["locale"])
        order_sha = sha(json.dumps(list(data), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        need(order_sha == meta["keyOrderSha256"], "postimage catalog key order mismatch " + meta["locale"])
        need(candidate["sourceKey"] in data, "postimage target key missing " + cid)
        selected = plan_changes.get(cid)
        expected_text = selected["finalTarget"] if selected else candidate["currentTarget"]
        expected_hash = selected["finalTargetSha256"] if selected else candidate["currentTargetSha256"]
        observed_hash = stsha(data[candidate["sourceKey"]])
        need(observed_hash == expected_hash, "600-cell target readback mismatch " + cid)
        if selected:
            need(data[candidate["sourceKey"]] != candidate["currentTarget"], "selected cell did not change " + cid)
            changed_count += 1
        else:
            need(data[candidate["sourceKey"]] == candidate["currentTarget"], "unselected cell changed " + cid)
            unchanged_count += 1
        actual_readback.append({
            "sourceOrdinal": candidate["sourceOrdinal"],
            "locale": candidate["locale"],
            "cellIdentitySha256": IDENTITY_HASH(cid),
            "targetFile": candidate["targetFile"],
            "selected": selected is not None,
            "expectedTargetSha256": expected_hash,
            "observedTargetSha256": observed_hash,
            "matches": True,
        })
    need(len(actual_readback) == 600 and changed_count == 106 and unchanged_count == 494, "complete readback counts mismatch")
    need(changed_count + unchanged_count == 600, "readback total mismatch")

    catalog_readback = []
    for path, meta in sorted(catalog_metas.items(), key=lambda item: LOCALES.index(item[1]["locale"])):
        raw = (repo / path).read_bytes()
        data = json.loads(raw)
        order_sha = sha(json.dumps(list(data), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        need(order_sha == meta["keyOrderSha256"] and len(data) == meta["keyCount"], "catalog parity mismatch " + meta["locale"])
        catalog_readback.append({
            "locale": meta["locale"],
            "path": path,
            "preimageSha256": meta["preimageSha256"],
            "preimageGitBlob": meta["preimageGitBlob"],
            "postimageSha256": sha(raw),
            "keyCount": len(data),
            "keyOrderSha256": order_sha,
            "selectedCellCount": len(changes_by_path.get(path, [])),
        })
    (root / "all-cell-readback.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in actual_readback), encoding="utf-8")
    (root / "catalog-readback.json").write_text(json.dumps(catalog_readback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "result": "PASS",
        "sourcePin": {"head": HEAD, "tree": TREE},
        "candidateCells": len(actual_readback),
        "selectedChanges": changed_count,
        "unchangedCells": unchanged_count,
        "callerlessHashOnlyHoldsPreserved": len(callerless_ids),
        "blindSemanticHoldsAdjudicated": len(semantic_hold_ids),
        "callerlessHoldMismatches": 0,
        "unselectedCellMismatches": 0,
        "catalogs": len(catalog_readback),
        "changedCatalogFiles": len(expected_changed_paths),
        "changedCatalogPaths": sorted(expected_changed_paths),
        "keyCountPerCatalog": 4165,
        "keyOrderPreserved": True,
        "nativeSpeakerApproval": False,
    }
    (root / "application-verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.phase == "precommit":
        paths = set(git(repo, "diff", "--name-only").splitlines())
        status = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain=v1"], text=True).splitlines()
        status_paths = {line[3:] for line in status}
        need(paths == expected_changed_paths, "precommit diff contains paths outside selected locale catalogs")
        need(status_paths == expected_changed_paths, "precommit status contains paths outside selected locale catalogs")
    else:
        need(bool(args.product_commit), "product commit SHA is required after commit")
        product = args.product_commit
        parents = git(repo, "show", "-s", "--format=%P", product).split()
        need(parents == [HEAD], "product commit parent is not exact pinned head")
        product_paths = set(git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", product).splitlines())
        need(product_paths == expected_changed_paths, "product commit changes paths outside selected locale catalogs")
        for path in expected_changed_paths:
            need(git(repo, "rev-parse", product + ":" + path) == git(repo, "rev-parse", "HEAD:" + path),
                 "current checkout does not match product commit catalog " + path)
        (root / "product-commit-record.json").write_text(json.dumps({
            "productCommit": product,
            "parent": HEAD,
            "changedPaths": sorted(product_paths),
            "changedCatalogFiles": len(product_paths),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.phase == "delivered":
            need(bool(args.evidence_commit), "evidence commit SHA is required for delivered phase")
            evidence = args.evidence_commit
            need(git(repo, "rev-parse", "HEAD") == evidence, "current HEAD differs from evidence commit")
            evidence_parents = git(repo, "show", "-s", "--format=%P", evidence).split()
            need(evidence_parents == [product], "evidence commit parent is not product commit")
            evidence_paths = set(git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", evidence).splitlines())
            prefix = str(root.relative_to(repo)) + "/"
            need(evidence_paths and all(path.startswith(prefix) for path in evidence_paths),
                 "evidence commit changes files outside separate evidence directory")
            expected_evidence_paths = {str(p.relative_to(repo)) for p in root.rglob("*") if p.is_file()}
            need(evidence_paths == expected_evidence_paths, "evidence commit path set differs from packet evidence folder")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()

