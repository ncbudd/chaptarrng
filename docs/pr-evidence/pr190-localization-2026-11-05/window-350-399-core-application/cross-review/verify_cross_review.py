#!/usr/bin/env python3
"""Portable verifier for the W350-W399 cross-review packet.

Usage: python3 verify_cross_review.py [task-root]
The task root must contain candidate-free/input, primary-review, blind-review,
and cross-review directories. Uses only the Python standard library and does
not access a repository.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

EXPECTED_HEAD = "dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0"
EXPECTED_TREE = "be10d71209076f753ef295038a9f3c3646a918a3"
TOKEN_FIELDS = (
    "sourcePlaceholders", "currentPlaceholders",
    "sourceMarkup", "currentMarkup",
    "sourceInlineCode", "currentInlineCode",
    "sourceNumericTokens", "currentNumericTokens",
    "protectedLiterals", "integrityChecks",
)
PLACEHOLDER = re.compile(r"\{[^{}]+\}")
INLINE = re.compile(r"`([^`]+)`")
MARKUP = re.compile(r"<[^>]+>")
NUM = re.compile(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])")

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_text(text: str) -> str:
    return sha_bytes(text.encode("utf-8"))

def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def verify_directory_checksums(directory: Path) -> None:
    sums_path = directory / "SHA256SUMS.txt"
    if not sums_path.exists():
        raise ValueError(f"missing SHA256SUMS.txt: {directory}")
    listed = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relpath = line.split(None, 1)
        relpath = relpath.lstrip("*")
        if relpath in listed:
            raise ValueError(f"duplicate checksum entry: {directory}/{relpath}")
        path = directory / relpath
        actual = sha_bytes(path.read_bytes())
        if actual != digest:
            raise ValueError(f"checksum mismatch: {directory}/{relpath}")
        listed[relpath] = digest
    actual_files = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    if set(listed) != actual_files:
        raise ValueError(f"checksum file set mismatch: {directory}")

def token_summary(row):
    return {field: row[field] for field in TOKEN_FIELDS}

def target_tokens_match(source: str, target: str) -> bool:
    return (
        Counter(PLACEHOLDER.findall(source)) == Counter(PLACEHOLDER.findall(target))
        and INLINE.findall(source) == INLINE.findall(target)
        and MARKUP.findall(source) == MARKUP.findall(target)
        and NUM.findall(source) == NUM.findall(target)
    )

def main() -> int:
    if len(sys.argv) > 2:
        raise SystemExit("usage: verify_cross_review.py [task-root]")
    task_root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parents[1]
    input_dir = task_root / "candidate-free" / "input"
    primary_dir = task_root / "primary-review"
    blind_dir = task_root / "blind-review"
    output_dir = task_root / "cross-review"
    for directory in (input_dir, primary_dir, blind_dir, output_dir):
        verify_directory_checksums(directory)

    packet = read_json(input_dir / "candidate-free-manifest.json")
    independent_manifest = read_json(output_dir / "independent-review-manifest.json")
    cross_summary = read_json(output_dir / "cross-review-summary.json")
    supplement = read_json(output_dir / "visibility-label-context.json")
    if packet["head"] != EXPECTED_HEAD or packet["tree"] != EXPECTED_TREE:
        raise ValueError("candidate-free packet pin mismatch")
    if independent_manifest["head"] != EXPECTED_HEAD or independent_manifest["tree"] != EXPECTED_TREE:
        raise ValueError("independent review pin mismatch")
    if cross_summary["head"] != EXPECTED_HEAD or cross_summary["tree"] != EXPECTED_TREE:
        raise ValueError("cross-review pin mismatch")
    if independent_manifest["candidateLedgersOpenedBeforeSeal"] is not False:
        raise ValueError("independent pass was not sealed before proposal access")

    candidate_path = input_dir / "candidate-free-cells.jsonl"
    context_path = input_dir / "caller-context.jsonl"
    candidate_rows = read_jsonl(candidate_path)
    context_rows = read_jsonl(context_path)
    context_map = {row["sourceKey"]: row for row in context_rows}
    candidate_map = {(row["sourceOrdinal"], row["locale"]): row for row in candidate_rows}
    if len(candidate_map) != 600 or len(context_map) != 50:
        raise ValueError("candidate-free input must contain 600 cells and 50 caller records")
    for key, expected in (
        ("candidateFreeCellsSha256", sha_bytes(candidate_path.read_bytes())),
        ("callerContextSha256", sha_bytes(context_path.read_bytes())),
        ("candidateFreeManifestSha256", sha_bytes((input_dir / "candidate-free-manifest.json").read_bytes())),
    ):
        if independent_manifest[key] != expected:
            raise ValueError(f"independent manifest input digest mismatch: {key}")

    independent_rows = read_jsonl(output_dir / "independent-review.jsonl")
    independent_map = {(row["sourceOrdinal"], row["locale"]): row for row in independent_rows}
    if len(independent_map) != 600 or independent_map.keys() != candidate_map.keys():
        raise ValueError("independent pass does not cover the 600 candidate-free cells exactly")
    independent_counts = Counter(row["decision"] for row in independent_rows)
    for ident, src in candidate_map.items():
        row = independent_map[ident]
        if row["head"] != EXPECTED_HEAD or row["tree"] != EXPECTED_TREE:
            raise ValueError(f"independent row pin mismatch: {ident}")
        for field in ("sourceKey", "sourceText", "sourceTextSha256", "currentTarget", "currentTargetSha256", "callerContextSha256", "sourceFile", "sourceFileSha256", "sourceFileGitBlob", "targetFile", "targetFileSha256", "targetFileGitBlob"):
            if row[field] != src[field]:
                raise ValueError(f"independent input binding mismatch: {ident}/{field}")
        tokens = token_summary(src)
        if row["tokenSummary"] != tokens or row["tokenSummarySha256"] != sha_text(canonical(tokens)):
            raise ValueError(f"independent token hash mismatch: {ident}")
        if row["decision"] == "hold-context":
            if row["recommendedTarget"] is not None:
                raise ValueError(f"independent hold contains text: {ident}")
        else:
            target = row["recommendedTarget"]
            if not isinstance(target, str) or row["recommendedTargetSha256"] != sha_text(target) or not target_tokens_match(src["sourceText"], target):
                raise ValueError(f"independent target/token mismatch: {ident}")
    if dict(sorted(independent_counts.items())) != independent_manifest["decisionCounts"]:
        raise ValueError("independent decision counts mismatch")
    independent_path = output_dir / "independent-review.jsonl"
    if sha_bytes(independent_path.read_bytes()) != independent_manifest["independentReviewSha256"]:
        raise ValueError("independent ledger seal digest mismatch")

    primary_cells = read_jsonl(primary_dir / "primary-review-cells.jsonl")
    primary_proposals = read_jsonl(primary_dir / "primary-review-proposals.jsonl")
    primary_holds = read_jsonl(primary_dir / "primary-review-holds.jsonl")
    blind_rows = read_jsonl(blind_dir / "ledger.jsonl")
    blind_context_rows = read_jsonl(blind_dir / "caller-context-review.jsonl")
    primary_map = {(row["sourceOrdinal"], row["locale"]): row for row in primary_cells}
    primary_proposal_map = {(row["sourceOrdinal"], row["locale"]): row for row in primary_proposals}
    primary_hold_map = {(row["sourceOrdinal"], row["locale"]): row for row in primary_holds}
    blind_map = {(row["sourceOrdinal"], row["locale"]): row for row in blind_rows}
    blind_context_map = {row["sourceKey"]: row for row in blind_context_rows}
    if any(len(mapping) != 600 for mapping in (primary_map, blind_map)):
        raise ValueError("primary and blind ledgers must each cover 600 unique cells")
    if len(primary_proposal_map) != 66 or sum(row["proposedTarget"] is not None for row in blind_rows) != 54:
        raise ValueError("proposal counts do not match the sealed proposal packets")

    cross_rows = read_jsonl(output_dir / "final-cross-review.jsonl")
    cross_map = {(row["sourceOrdinal"], row["locale"]): row for row in cross_rows}
    if len(cross_map) != 600 or cross_map.keys() != candidate_map.keys():
        raise ValueError("final cross review does not cover each cell exactly once")
    cross_counts = Counter(row["crossDisposition"] for row in cross_rows)
    proposal_primary_ids = set(primary_proposal_map)
    proposal_blind_ids = {ident for ident, row in blind_map.items() if row["proposedTarget"] is not None}
    proposal_union = proposal_primary_ids | proposal_blind_ids
    for ident, src in candidate_map.items():
        row = cross_map[ident]
        primary = primary_map[ident]
        blind = blind_map[ident]
        context = context_map[src["sourceKey"]]
        blind_context = blind_context_map[src["sourceKey"]]
        tokens = token_summary(src)
        token_hash = sha_text(canonical(tokens))
        candidate_free_row_hash = sha_bytes((canonical(src) + "\n").encode("utf-8"))
        context_record_hash = sha_text(canonical(context))
        if row["head"] != EXPECTED_HEAD or row["tree"] != EXPECTED_TREE:
            raise ValueError(f"final cross row pin mismatch: {ident}")
        for field in ("sourceKey", "sourceText", "sourceTextSha256", "currentTarget", "currentTargetSha256", "callerContextSha256", "sourceFile", "sourceFileSha256", "sourceFileGitBlob", "targetFile", "targetFileSha256", "targetFileGitBlob"):
            if row[field] != src[field]:
                raise ValueError(f"final cross candidate binding mismatch: {ident}/{field}")
        if row["tokenSummary"] != tokens or row["tokenSummarySha256"] != token_hash:
            raise ValueError(f"final cross token hash mismatch: {ident}")
        if row["callerContextRecordSha256"] != context_record_hash:
            raise ValueError(f"caller context record hash mismatch: {ident}")
        for field in ("sourceText", "sourceTextSha256", "currentTarget", "currentTargetSha256", "callerContextSha256"):
            if primary[field] != src[field] or blind[field] != src[field]:
                raise ValueError(f"reviewer source/current/context hash mismatch: {ident}/{field}")
        if primary["candidateFreeRowSha256"] != candidate_free_row_hash:
            raise ValueError(f"primary candidate-free row digest mismatch: {ident}")
        if {field: primary[field] for field in TOKEN_FIELDS} != tokens or {field: blind[field] for field in TOKEN_FIELDS} != tokens:
            raise ValueError(f"reviewer token summary mismatch: {ident}")
        if blind["callerContextRecordSha256"] != context_record_hash or blind_context["callerRecordSha256"] != context_record_hash:
            raise ValueError(f"blind caller record digest mismatch: {ident}")
        if not all(row["hashBindings"].values()):
            raise ValueError(f"false exact-hash binding flag: {ident}")
        pproposal = primary_proposal_map.get(ident)
        if pproposal:
            if pproposal["sourceTextSha256"] != src["sourceTextSha256"] or pproposal["currentTargetSha256"] != src["currentTargetSha256"] or pproposal["callerContextSha256"] != src["callerContextSha256"]:
                raise ValueError(f"primary proposal identity/hash mismatch: {ident}")
            if sha_text(pproposal["recommendedTarget"]) != pproposal["recommendedTargetSha256"]:
                raise ValueError(f"primary proposal target hash mismatch: {ident}")
        if blind["proposedTarget"] is not None and sha_text(blind["proposedTarget"]) != blind["proposedTargetSha256"]:
            raise ValueError(f"blind proposal target hash mismatch: {ident}")
        if row["primary"]["target"] != (pproposal["recommendedTarget"] if pproposal else None):
            raise ValueError(f"primary proposal missing or changed in final cross row: {ident}")
        if row["blind"]["target"] != blind["proposedTarget"]:
            raise ValueError(f"blind proposal missing or changed in final cross row: {ident}")
        target = row["recommendedTarget"]
        if target is not None:
            if row["recommendedTargetSha256"] != sha_text(target) or not target_tokens_match(src["sourceText"], target):
                raise ValueError(f"final target hash/token mismatch: {ident}")
        elif row["crossDisposition"] != "hold-source-copy":
            raise ValueError(f"text-free target outside explicit hold: {ident}")
        if row["recommendedTargetTokensVerified"] != (target_tokens_match(src["sourceText"], target) if target is not None else None):
            raise ValueError(f"final target token flag mismatch: {ident}")

    if dict(sorted(cross_counts.items())) != cross_summary["crossDecisionCounts"]:
        raise ValueError("cross decision counts mismatch")
    if cross_summary["proposalUnionCellCount"] != len(proposal_union):
        raise ValueError("proposal union count mismatch")
    if cross_summary["proposalIntersectionCellCount"] != len(proposal_primary_ids & proposal_blind_ids):
        raise ValueError("proposal intersection count mismatch")
    if cross_summary["allSourceCurrentCallerTokenBindingsExact"] is not True:
        raise ValueError("cross summary does not assert exact bindings")

    recommendations = read_jsonl(output_dir / "cross-recommendations.jsonl")
    holds = read_jsonl(output_dir / "cross-holds.jsonl")
    expected_recs = [row for row in cross_rows if row["crossDisposition"] == "recommend-revision"]
    expected_holds = [row for row in cross_rows if row["crossDisposition"] == "hold-source-copy"]
    if len(recommendations) != len(expected_recs) or len(holds) != len(expected_holds):
        raise ValueError("recommendation/hold extracts do not match the full cross ledger")
    if len(recommendations) != cross_summary["recommendationCount"] or len(holds) != cross_summary["holdCount"]:
        raise ValueError("recommendation/hold counts disagree with summary")
    for row, full in zip(recommendations, expected_recs):
        for field in ("sourceOrdinal", "sourceKey", "locale", "sourceTextSha256", "currentTargetSha256", "callerContextSha256", "tokenSummarySha256", "recommendedTarget", "recommendedTargetSha256"):
            if row[field] != full[field]:
                raise ValueError(f"recommendation extract mismatch: {field}")
    for row, full in zip(holds, expected_holds):
        for field in ("sourceOrdinal", "sourceKey", "locale", "sourceTextSha256", "currentTargetSha256", "callerContextSha256", "tokenSummarySha256"):
            if row[field] != full[field]:
                raise ValueError(f"hold extract mismatch: {field}")
        if row["recommendedTarget"] is not None:
            raise ValueError("hold extract contains target text")

    visibility_rows = [row for row in cross_rows if row["sourceOrdinal"] == 366]
    locales = packet["scope"]["locales"]
    if len(visibility_rows) != 12 or any(row["recommendedTarget"] is not None for row in visibility_rows):
        raise ValueError("BookVisibilityToggleHelpText must remain 12 text-free holds")
    if set(supplement["currentLocalizedControlLabels"]) != set(locales):
        raise ValueError("supplemental Library/All labels do not cover all locales")
    if supplement["source"]["componentRenders"] != ["translate('Library')", "translate('All')"]:
        raise ValueError("supplemental control labels do not match pinned source evidence")
    if "Wanted" not in supplement["source"]["englishSourceText"] or supplement["adjudication"]["targetTextSelected"] is not False:
        raise ValueError("supplemental source mismatch/hold decision missing")
    if cross_summary["visibilitySourceMismatch"]["allTargetsTextFree"] is not True:
        raise ValueError("visibility summary does not preserve text-free holds")

    print(json.dumps({
        "result": "PASS",
        "head": EXPECTED_HEAD,
        "tree": EXPECTED_TREE,
        "cells": len(cross_rows),
        "decisions": dict(sorted(cross_counts.items())),
        "primaryProposals": len(primary_proposals),
        "blindProposals": len(proposal_blind_ids),
        "proposalUnion": len(proposal_union),
        "exactHashBindings": True,
        "visibilityHolds": len(visibility_rows),
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
