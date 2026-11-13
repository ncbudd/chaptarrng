#!/usr/bin/env python3
"""Verify the portable ChaptarrNG PR #190 W0–W49 cross-audit bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HEAD = "7f5d99e24b054cf1437d135328c3dee565e6b318"
TREE = "d39f2fe8cf91a39653679980c0832c5ca400a114"
HOLD_KEYS = {
    "AddAuthorMonitorNewAudiobooksHelpText",
    "AddAuthorMonitorNewEbooksHelpText",
    "AddAuthorWhichAudiobooksToMonitor",
    "AddAuthorWhichEbooksToMonitor",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha(text.encode("utf-8"))


def read_jsonl(path: Path):
    data = []
    hashes = []
    for raw in path.read_bytes().splitlines(keepends=True):
        data.append(json.loads(raw))
        hashes.append(sha(raw.rstrip(b"\n")))
    return data, hashes


def cell_key(row):
    return (row["sourceKey"], row["locale"])


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def verify_manifest(folder: Path, filename: str) -> int:
    manifest = folder / filename
    require(manifest.exists(), f"missing checksum manifest: {manifest.relative_to(ROOT)}")
    seen = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        require(len(parts) == 2, f"malformed checksum line in {manifest}")
        expected, rel = parts
        target = (folder / rel).resolve()
        require(target.is_relative_to(folder.resolve()), f"checksum path escapes its packet: {rel}")
        require(target.is_file(), f"checksum target missing: {target}")
        actual = sha(target.read_bytes())
        require(actual == expected, f"checksum mismatch: {target}")
        require(rel not in seen, f"duplicate checksum entry: {rel}")
        seen.add(rel)
    return len(seen)


def verify_bundle_checksums() -> int:
    manifest = ROOT / "SHA256SUMS.txt"
    require(manifest.exists(), "missing top-level SHA256SUMS.txt")
    listed = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        require(rel not in listed, f"duplicate top-level checksum entry: {rel}")
        target = (ROOT / rel).resolve()
        require(target.is_relative_to(ROOT.resolve()), f"top-level checksum path escapes bundle: {rel}")
        require(target.is_file(), f"top-level checksum target missing: {rel}")
        require(sha(target.read_bytes()) == digest, f"top-level checksum mismatch: {rel}")
        listed[rel] = digest
    actual = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and p != manifest
    }
    require(actual == set(listed), f"top-level checksum file set differs (unlisted={sorted(actual-set(listed))}, stale={sorted(set(listed)-actual)})")
    return len(listed)


def verify_source_checkout(worktree: Path, candidates) -> dict:
    worktree = worktree.resolve()
    require(worktree.is_dir(), f"source worktree not found: {worktree}")

    def git(*args):
        return subprocess.check_output(["git", "-C", str(worktree), *args], text=True).strip()

    actual_head = git("rev-parse", "HEAD")
    actual_tree = git("show", "-s", "--format=%T", "HEAD")
    status = git("status", "--porcelain")
    require(actual_head == HEAD, f"source HEAD mismatch: {actual_head}")
    require(actual_tree == TREE, f"source tree mismatch: {actual_tree}")
    require(not status, f"source worktree is not clean: {status}")

    catalogs = {}
    for row in candidates:
        for role, path_field, sha_field, blob_field in (
            ("source", "sourceFile", "sourceFileSha256", "sourceFileGitBlob"),
            ("target", "targetFile", "targetFileSha256", "targetFileGitBlob"),
        ):
            rel = row[path_field]
            expected = (row[sha_field], row[blob_field])
            if rel in catalogs:
                require(catalogs[rel] == expected, f"inconsistent catalog manifest metadata: {rel}")
            else:
                catalogs[rel] = expected
    for rel, (expected_sha, expected_blob) in catalogs.items():
        path = worktree / rel
        content = path.read_bytes()
        require(sha(content) == expected_sha, f"catalog file SHA mismatch: {rel}")
        actual_blob = git("hash-object", rel)
        require(actual_blob == expected_blob, f"catalog Git blob mismatch: {rel}")
        parsed = json.loads(content)
        for row in candidates:
            if row["sourceFile"] == rel:
                require(parsed.get(row["sourceKey"]) == row["sourceText"], f"English source differs in {rel}: {row['sourceKey']}")
            if row["targetFile"] == rel:
                require(parsed.get(row["sourceKey"]) == row["currentTarget"], f"current locale value differs in {rel}: {row['sourceKey']}/{row['locale']}")

    caller_files = {}
    caller_refs = 0
    for row in candidates:
        require(row["callerReferenceCount"] == len(row["callerRefs"]), f"caller reference count mismatch: {cell_key(row)}")
        for ref in row["callerRefs"]:
            rel = ref["path"]
            path = worktree / rel
            content = path.read_bytes()
            expected_meta = (ref["fileSha256"], ref["fileGitBlob"])
            if rel in caller_files:
                require(caller_files[rel] == expected_meta, f"inconsistent caller metadata: {rel}")
            else:
                caller_files[rel] = expected_meta
            require(sha(content) == ref["fileSha256"], f"caller file SHA mismatch: {rel}")
            require(git("hash-object", rel) == ref["fileGitBlob"], f"caller Git blob mismatch: {rel}")
            lines = content.decode("utf-8").splitlines()
            require(1 <= ref["line"] <= len(lines), f"caller line out of range: {rel}:{ref['line']}")
            actual_line = lines[ref["line"] - 1]
            require(actual_line == ref["lineText"], f"caller line text mismatch: {rel}:{ref['line']}")
            require(sha_text(actual_line) == ref["lineSha256"], f"caller line SHA mismatch: {rel}:{ref['line']}")
            caller_refs += 1
    return {"head": actual_head, "tree": actual_tree, "clean": True, "catalogFiles": len(catalogs), "callerFiles": len(caller_files), "callerRefs": caller_refs}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-worktree", type=Path, help="also verify catalogs and caller lines against the exact checkout")
    args = ap.parse_args()

    top_files = verify_bundle_checksums()
    primary_root = ROOT / "input" / "candidate-primary"
    blind_root = ROOT / "input" / "blind"
    checks = {
        "candidatePrimary": verify_manifest(primary_root, "SHA256SUMS"),
        "blindPacket": verify_manifest(blind_root, "SHA256SUMS.txt"),
        "blindNestedInput": verify_manifest(blind_root / "input", "SHA256SUMS.txt"),
    }
    candidates, candidate_hashes = read_jsonl(primary_root / "candidate-free-cells.jsonl")
    primary, primary_hashes = read_jsonl(primary_root / "primary-review-cells.jsonl")
    blind, blind_hashes = read_jsonl(blind_root / "blind-review-ledger.jsonl")
    reviewer_a, reviewer_hashes = read_jsonl(ROOT / "work" / "reviewer-a.jsonl")
    ledger, _ = read_jsonl(ROOT / "cross-ledger.jsonl")
    proposals, _ = read_jsonl(ROOT / "selected-proposals.jsonl")
    holds, _ = read_jsonl(ROOT / "cross-audit-holds.jsonl")
    summary = json.loads((ROOT / "summary.json").read_text(encoding="utf-8"))

    require(len(candidates) == len(primary) == len(blind) == len(ledger) == 600, "expected 600 input and cross-ledger rows")
    require(len(reviewer_a) == 300, "expected exactly 300 ordinals 0–24 reviewer rows")
    require(len(proposals) == 38, "expected 38 selected revisions")
    require(len(holds) == 48, "expected 48 text-free holds")
    keys = [cell_key(row) for row in candidates]
    require(len(set(keys)) == 600, "candidate cells are not unique")
    cand = {cell_key(row): (row, candidate_hashes[i]) for i, row in enumerate(candidates)}
    prim = {cell_key(row): (row, primary_hashes[i]) for i, row in enumerate(primary)}
    blind_map = {cell_key(row): (row, blind_hashes[i]) for i, row in enumerate(blind)}
    review_map = {cell_key(row): (row, reviewer_hashes[i]) for i, row in enumerate(reviewer_a)}
    ledger_map = {cell_key(row): row for row in ledger}
    require(set(cand) == set(prim) == set(blind_map) == set(ledger_map), "cell sets differ across source, reviews, and ledger")
    require(set(review_map) == {k for k, (r, _) in cand.items() if r["sourceOrdinal"] < 25}, "reviewer coverage differs from ordinals 0–24")

    for ident, (c, ch) in cand.items():
        p, ph = prim[ident]
        b, bh = blind_map[ident]
        x = ledger_map[ident]
        require(p["candidateFreeRowSha256"] == ch, f"primary candidate-free row link mismatch: {ident}")
        require(x["candidateFreeInputRowSha256"] == ch and x["primaryInputRowSha256"] == ph and x["blindInputRowSha256"] == bh, f"input row linkage mismatch: {ident}")
        require(x["sourceTextSha256"] == c["sourceTextSha256"] and x["currentTargetSha256"] == c["currentTargetSha256"], f"source/current hash link mismatch: {ident}")
        require(c["sourceTextSha256"] == sha_text(c["sourceText"]) and c["currentTargetSha256"] == sha_text(c["currentTarget"]), f"input source/current text hashes invalid: {ident}")
        require(x["primaryDisposition"] == p["primaryDisposition"] and x["blindDisposition"] == b["disposition"], f"review disposition link mismatch: {ident}")
        require(x["primaryProposalSha256"] == (sha_text(p["finalReviewedTarget"]) if p["primaryDisposition"] == "revise-current" else None), f"primary proposal hash mismatch: {ident}")
        require(x["blindProposalSha256"] == (sha_text(b["proposedTarget"]) if b.get("proposedTarget") else None), f"blind proposal hash mismatch: {ident}")
        require(x["callerContextSha256"] == c["callerContextSha256"] and x["callerReferenceCount"] == c["callerReferenceCount"], f"caller context link mismatch: {ident}")
        require(x["exactHead"] == HEAD and x["exactTree"] == TREE, f"source pin mismatch in cross ledger: {ident}")
        if c["sourceKey"] in HOLD_KEYS:
            require(x["crossDisposition"] == "hold", f"callerless cell not held: {ident}")
            require("sourceText" not in x and "currentTarget" not in x and x["callerRefs"] == [], f"held cross-ledger row contains text/context: {ident}")
            require(c["callerReferenceCount"] == 0, f"held cell unexpectedly has callers: {ident}")
        else:
            require(x.get("sourceText") == c["sourceText"] and x.get("currentTarget") == c["currentTarget"], f"non-held text missing or changed: {ident}")
        if ident in review_map:
            r, rh = review_map[ident]
            require(x["independentReviewerA"]["inputRowSha256"] == rh, f"reviewer row hash mismatch: {ident}")
        else:
            require(x["independentReviewerA"] is None, f"unexpected reviewer A row: {ident}")

    proposal_map = {cell_key(row): row for row in proposals}
    require(len(proposal_map) == len(proposals), "duplicate selected proposals")
    hold_map = {cell_key(row): row for row in holds}
    require(len(hold_map) == len(holds), "duplicate holds")
    require(set(proposal_map) == {k for k, x in ledger_map.items() if x["crossDisposition"] == "revise-current"}, "proposal set does not match ledger revisions")
    require(set(hold_map) == {k for k, x in ledger_map.items() if x["crossDisposition"] == "hold"}, "hold set does not match ledger holds")
    for ident, proposal in proposal_map.items():
        c, _ = cand[ident]
        x = ledger_map[ident]
        p, _ = prim[ident]
        b, _ = blind_map[ident]
        expected_target = p["finalReviewedTarget"] if proposal["selectedFrom"] == "primary" else b["proposedTarget"]
        require(proposal["selectedTarget"] == expected_target, f"selected target differs from reviewed proposal: {ident}")
        require(proposal["selectedTargetSha256"] == sha_text(proposal["selectedTarget"]) == x["selectedTargetSha256"], f"selected target hash mismatch: {ident}")
        placeholders = {m: len(re.findall(re.escape(m), proposal["selectedTarget"])) for m in c["sourcePlaceholders"]}
        require(placeholders == c["sourcePlaceholders"], f"selected target placeholder mismatch: {ident}")
        require(all(literal in proposal["selectedTarget"] for literal in c["protectedLiterals"]), f"selected target protected literal mismatch: {ident}")
        require(proposal["sourceTextSha256"] == c["sourceTextSha256"] and proposal["currentTargetSha256"] == c["currentTargetSha256"], f"proposal source/current hash mismatch: {ident}")
    for ident, hold in hold_map.items():
        require(hold["proposedTarget"] is None, f"hold has a proposal string: {ident}")
        forbidden = {"sourceText", "currentTarget", "proposedTargetText", "selectedTarget", "targetText"}
        require(not (forbidden & set(hold)), f"hold row contains text fields: {ident}")
        require(hold["callerReferenceCount"] == 0 and hold["sourceKey"] in HOLD_KEYS, f"invalid hold context: {ident}")
        require(hold["sourceTextSha256"] == cand[ident][0]["sourceTextSha256"] and hold["currentTargetSha256"] == cand[ident][0]["currentTargetSha256"], f"hold source/current hash mismatch: {ident}")

    counts = Counter(row["crossDisposition"] for row in ledger)
    require(counts == Counter({"accept-current": 514, "revise-current": 38, "hold": 48}), f"unexpected cross counts: {counts}")
    require(summary["crossDispositionCounts"] == dict(counts), "summary cross counts mismatch")
    require(summary["cellsReviewed"] == 600 and summary["selectedProposalCount"] == len(proposals) and summary["textFreeHoldCount"] == len(holds), "summary totals mismatch")
    require(summary["nativeSpeakerApproval"] is False and summary["repoOrPrModified"] is False, "approval or modification claim incorrect")
    source_result = verify_source_checkout(args.source_worktree, candidates) if args.source_worktree else None
    print(json.dumps({"result": "PASS", "head": HEAD, "tree": TREE, "bundleFilesChecksummed": top_files, "inputPackets": checks, "cells": 600, "selected": len(proposals), "holds": len(holds), "counts": dict(counts), "sourceCheckout": source_result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
