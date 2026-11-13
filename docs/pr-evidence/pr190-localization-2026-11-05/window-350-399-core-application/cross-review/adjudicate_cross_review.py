#!/usr/bin/env python3
"""Build the final hash-bound cross-adjudication for W350-W399."""
from __future__ import annotations
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
INPUT = TASK / "candidate-free" / "input"
PRIMARY = TASK / "primary-review"
BLIND = TASK / "blind-review"
OUT = TASK / "cross-review"
HEAD = "dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0"
TREE = "be10d71209076f753ef295038a9f3c3646a918a3"
TOKEN_FIELDS = (
    "sourcePlaceholders", "currentPlaceholders",
    "sourceMarkup", "currentMarkup",
    "sourceInlineCode", "currentInlineCode",
    "sourceNumericTokens", "currentNumericTokens",
    "protectedLiterals", "integrityChecks",
)
NUM = re.compile(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])")
INLINE = re.compile(r"`([^`]+)`")
MARKUP = re.compile(r"<[^>]+>")
PLACEHOLDER = re.compile(r"\{[^{}]+\}")

# Variants chosen after reading both proposal ledgers. Most candidate corrections
# are selected directly; these entries choose one of the equivalent variants.
VARIANT_OVERRIDES = {
    (378, "ar"): "يدويًا: أضف رفًا (مثال: read، currently-reading)",
    (378, "fr"): "Manuel : ajouter une étagère (par exemple : read, currently-reading)",
    (378, "hi"): "मैन्युअल रूप से: शेल्फ़ जोड़ें (उदाहरण: read, currently-reading)",
    (378, "pt-BR"): "Manual: adicione uma estante (ex.: read, currently-reading)",
    (396, "de"): "Bei höchster Qualität umgehen",
    (396, "zh-Hant"): "最高品質時略過延遲",
}
CROSS_ONLY_TARGETS = {
    (351, "ko"): ("책 {count}권", "The count is used for the singular branch too; Korean needs the book counter 권, as in the reviewed plural-count rows.", "moderate"),
}

# All rows marked replace in the sealed independent pass remain candidates unless
# a primary/blind proposal supplied a better exact variant.

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_text(text: str) -> str:
    return sha_bytes(text.encode("utf-8"))

def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def canon_line(value) -> bytes:
    return (canon(value) + "\n").encode("utf-8")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def token_summary(row):
    return {field: row[field] for field in TOKEN_FIELDS}

def target_tokens_match(source: str, target: str) -> bool:
    return (
        Counter(PLACEHOLDER.findall(source)) == Counter(PLACEHOLDER.findall(target))
        and INLINE.findall(source) == INLINE.findall(target)
        and MARKUP.findall(source) == MARKUP.findall(target)
        and NUM.findall(source) == NUM.findall(target)
    )

packet = read_json(INPUT / "candidate-free-manifest.json")
if packet["head"] != HEAD or packet["tree"] != TREE:
    raise SystemExit("candidate-free pin mismatch")
source_rows = read_jsonl(INPUT / "candidate-free-cells.jsonl")
context_rows = read_jsonl(INPUT / "caller-context.jsonl")
context_map = {row["sourceKey"]: row for row in context_rows}
independent_rows = read_jsonl(OUT / "independent-review.jsonl")
primary_cells = read_jsonl(PRIMARY / "primary-review-cells.jsonl")
primary_proposals = read_jsonl(PRIMARY / "primary-review-proposals.jsonl")
primary_holds = read_jsonl(PRIMARY / "primary-review-holds.jsonl")
blind_rows = read_jsonl(BLIND / "ledger.jsonl")
blind_context_rows = read_jsonl(BLIND / "caller-context-review.jsonl")

by_id = lambda rows, ordinal, locale: next((r for r in rows if r["sourceOrdinal"] == ordinal and r["locale"] == locale), None)
packet_map = {(r["sourceOrdinal"], r["locale"]): r for r in source_rows}
independent_map = {(r["sourceOrdinal"], r["locale"]): r for r in independent_rows}
primary_map = {(r["sourceOrdinal"], r["locale"]): r for r in primary_cells}
primary_proposal_map = {(r["sourceOrdinal"], r["locale"]): r for r in primary_proposals}
primary_hold_map = {(r["sourceOrdinal"], r["locale"]): r for r in primary_holds}
blind_map = {(r["sourceOrdinal"], r["locale"]): r for r in blind_rows}
blind_context_map = {r["sourceKey"]: r for r in blind_context_rows}
if any(len(m) != 600 for m in (packet_map, independent_map, primary_map, blind_map)):
    raise SystemExit("one or more full-cell ledgers do not contain 600 unique rows")

# Establish selected target texts: independent pass first, then proposal targets,
# then the explicit cross-adjudicated variants above.
chosen = {}
for ident, src in packet_map.items():
    ind = independent_map[ident]
    chosen[ident] = ind["recommendedTarget"]
for ident, p in primary_proposal_map.items():
    chosen[ident] = p["recommendedTarget"]
for ident, b in blind_map.items():
    if b["proposedTarget"] is not None and ident not in primary_proposal_map:
        chosen[ident] = b["proposedTarget"]
for ident, target in VARIANT_OVERRIDES.items():
    chosen[ident] = target
for ident, (target, _reason, _confidence) in CROSS_ONLY_TARGETS.items():
    chosen[ident] = target
for ident in primary_hold_map:
    chosen[ident] = None

# Supplied exact localized label values are cross-only context and never revise
# the independent pass or the 12 text-free target holds.
visibility_path = OUT / "visibility-label-context.json"
visibility = read_json(visibility_path)
if visibility["head"] != HEAD or visibility["tree"] != TREE:
    raise SystemExit("supplemental visibility context pin mismatch")
if set(visibility["currentLocalizedControlLabels"]) != set(packet["scope"]["locales"]):
    raise SystemExit("supplemental visibility context does not cover all locales")

cross_rows = []
proposal_ids_primary = set(primary_proposal_map)
proposal_ids_blind = {ident for ident, row in blind_map.items() if row["proposedTarget"] is not None}
for ident, src in packet_map.items():
    ordinal, locale = ident
    ind = independent_map[ident]
    p = primary_map[ident]
    pprop = primary_proposal_map.get(ident)
    phold = primary_hold_map.get(ident)
    b = blind_map[ident]
    bctx = blind_context_map[src["sourceKey"]]
    context = context_map[src["sourceKey"]]
    tokens = token_summary(src)
    token_hash = sha_text(canon(tokens))
    primary_tokens = {field: p[field] for field in TOKEN_FIELDS}
    blind_tokens = {field: b[field] for field in TOKEN_FIELDS}
    candidate_free_row_hash = sha_bytes(canon_line(src))
    context_record_hash = sha_text(canon(context))
    checks = {
        "sourceTextValue": p["sourceText"] == src["sourceText"] == b["sourceText"],
        "sourceTextSha256": p["sourceTextSha256"] == src["sourceTextSha256"] == b["sourceTextSha256"] and sha_text(src["sourceText"]) == src["sourceTextSha256"],
        "currentTargetValue": p["currentTarget"] == src["currentTarget"] == b["currentTarget"],
        "currentTargetSha256": p["currentTargetSha256"] == src["currentTargetSha256"] == b["currentTargetSha256"] and sha_text(src["currentTarget"]) == src["currentTargetSha256"],
        "callerContextSha256": p["callerContextSha256"] == src["callerContextSha256"] == b["callerContextSha256"] == context["callerContextSha256"],
        "primaryCandidateFreeRowSha256": p["candidateFreeRowSha256"] == candidate_free_row_hash,
        "primaryTokenSummary": primary_tokens == tokens,
        "blindTokenSummary": blind_tokens == tokens,
        "blindCallerContextRecordSha256": b["callerContextRecordSha256"] == context_record_hash == bctx["callerRecordSha256"],
        "headTree": p["exactHead"] == b["head"] == HEAD and p["exactTree"] == b["tree"] == TREE,
    }
    if not all(checks.values()):
        bad = [key for key, ok in checks.items() if not ok]
        raise SystemExit(f"proposal/candidate hash binding failed for {ident}: {bad}")
    if pprop:
        for field, expected in (("sourceTextSha256", src["sourceTextSha256"]), ("currentTargetSha256", src["currentTargetSha256"]), ("callerContextSha256", src["callerContextSha256"])):
            if pprop[field] != expected:
                raise SystemExit(f"primary proposal binding failed for {ident}: {field}")
        if pprop["recommendedTarget"] != p["recommendedTarget"] or pprop["recommendedTargetSha256"] != p["recommendedTargetSha256"] or sha_text(pprop["recommendedTarget"]) != pprop["recommendedTargetSha256"]:
            raise SystemExit(f"primary proposal target hash failed for {ident}")
    if phold and (phold["recommendedTarget"] is not None or phold["recommendedTargetSha256"] is not None):
        raise SystemExit(f"primary hold is not text-free for {ident}")
    if b["proposedTarget"] is not None and (sha_text(b["proposedTarget"]) != b["proposedTargetSha256"]):
        raise SystemExit(f"blind proposal target hash failed for {ident}")
    target = chosen[ident]
    is_visibility_hold = ordinal == 366
    if is_visibility_hold:
        if target is not None or p["primaryDisposition"] != "hold-text-free" or b["decision"] != "hold":
            raise SystemExit("visibility help rows must remain text-free holds")
        cross_disposition = "hold-source-copy"
        rationale = "The pinned UI renders Library/All, while the English source says Wanted/All. Treat this as an English source-copy mismatch; keep all locale targets text-free until the source is aligned, then review the corrected source in a focused follow-up."
        confidence = "high"
        target_basis = ["cross-only supplemental source/control evidence"]
    elif (ordinal, locale) in CROSS_ONLY_TARGETS:
        cross_disposition = "recommend-revision"
        rationale, confidence = CROSS_ONLY_TARGETS[(ordinal, locale)][1:]
        target_basis = ["cross-adjudication"]
    elif target == src["currentTarget"]:
        cross_disposition = "accept-current"
        rationale = "No material issue remained after the independent, primary, and blind reviews; the current wording is retained."
        confidence = "moderate"
        target_basis = ["current target"]
    else:
        cross_disposition = "recommend-revision"
        target_hash = sha_text(target)
        target_basis = []
        if ind["recommendedTarget"] == target:
            target_basis.append("sealed independent review")
            rationale = ind["rationale"]
            confidence = ind["confidence"]
        if pprop and pprop["recommendedTarget"] == target:
            target_basis.append("primary proposal")
            rationale = pprop["decisionRationale"]
            confidence = pprop["reviewConfidence"]
        if b["proposedTarget"] == target:
            target_basis.append("blind proposal")
            rationale = b["rationale"]
            confidence = b["confidence"]
        if not target_basis:
            target_basis = ["cross-adjudicated variant"]
            rationale = "The selected wording combines the reviewed correction with the exact caller context."
            confidence = "moderate"
        if pprop and b["proposedTarget"] is not None and pprop["recommendedTarget"] != b["proposedTarget"] and target not in {pprop["recommendedTarget"], b["proposedTarget"]}:
            rationale = "Both reviews identify a correction; the cross target uses a concise equivalent that preserves the same meaning."
        if not target_tokens_match(src["sourceText"], target):
            raise SystemExit(f"selected target changes source placeholder/markup/inline-code/numeric tokens for {ident}")
    target_hash = sha_text(target) if target is not None else None

    def proposal_record(kind, record, proposed, proposed_sha, proposal_reason, proposal_confidence):
        if proposed is None:
            return {"status": "not-proposed", "target": None, "targetSha256": None, "rationale": None, "confidence": None, "sourceTextSha256": src["sourceTextSha256"], "currentTargetSha256": src["currentTargetSha256"], "callerContextSha256": src["callerContextSha256"], "tokenSummarySha256": token_hash}
        if target is None:
            status = "held-pending-source-copy"
        elif target == proposed:
            status = "selected-exact-target"
        else:
            status = "correction-adopted-with-alternative-target" if target != src["currentTarget"] else "proposal-not-selected-current-retained"
        return {"status": status, "target": proposed, "targetSha256": proposed_sha, "rationale": proposal_reason, "confidence": proposal_confidence, "sourceTextSha256": src["sourceTextSha256"], "currentTargetSha256": src["currentTargetSha256"], "callerContextSha256": src["callerContextSha256"], "tokenSummarySha256": token_hash, "targetSha256Verified": sha_text(proposed) == proposed_sha}

    primary_record = proposal_record("primary", pprop, pprop["recommendedTarget"] if pprop else None, pprop["recommendedTargetSha256"] if pprop else None, pprop["decisionRationale"] if pprop else None, pprop["reviewConfidence"] if pprop else None)
    blind_record = proposal_record("blind", b, b["proposedTarget"], b["proposedTargetSha256"], b["rationale"] if b["proposedTarget"] is not None else None, b["confidence"] if b["proposedTarget"] is not None else None)
    if pprop is None and p["primaryDisposition"] == "accept-current":
        primary_record["fullCellDisposition"] = "accept-current"
    elif phold:
        primary_record["fullCellDisposition"] = "hold-text-free"
    else:
        primary_record["fullCellDisposition"] = p["primaryDisposition"]
    primary_record["candidateFreeRowSha256"] = p["candidateFreeRowSha256"]
    blind_record["decision"] = b["decision"]
    blind_record["callerContextRecordSha256"] = b["callerContextRecordSha256"]

    cross_rows.append({
        "batch": src["batch"],
        "head": HEAD,
        "tree": TREE,
        "sourceOrdinal": ordinal,
        "sourceKey": src["sourceKey"],
        "locale": locale,
        "sourceText": src["sourceText"],
        "sourceTextSha256": src["sourceTextSha256"],
        "currentTarget": src["currentTarget"],
        "currentTargetSha256": src["currentTargetSha256"],
        "callerContextSha256": src["callerContextSha256"],
        "callerContextRecordSha256": context_record_hash,
        "tokenSummary": tokens,
        "tokenSummarySha256": token_hash,
        "sourceFile": src["sourceFile"],
        "sourceFileSha256": src["sourceFileSha256"],
        "sourceFileGitBlob": src["sourceFileGitBlob"],
        "targetFile": src["targetFile"],
        "targetFileSha256": src["targetFileSha256"],
        "targetFileGitBlob": src["targetFileGitBlob"],
        "independent": {"decision": ind["decision"], "recommendedTarget": ind["recommendedTarget"], "recommendedTargetSha256": ind["recommendedTargetSha256"], "confidence": ind["confidence"], "rationale": ind["rationale"]},
        "primary": primary_record,
        "blind": blind_record,
        "hashBindings": checks,
        "crossDisposition": cross_disposition,
        "recommendedTarget": target,
        "recommendedTargetSha256": target_hash,
        "targetBasis": target_basis,
        "confidence": confidence,
        "rationale": rationale,
        "supplementalContextId": "visibility-label-context.json#Library-All" if ordinal == 366 else None,
        "recommendedTargetTokensVerified": target_tokens_match(src["sourceText"], target) if target is not None else None,
    })

ledger_path = OUT / "final-cross-review.jsonl"
ledger_path.write_bytes(b"".join(canon_line(row) for row in cross_rows))
recommendation_rows = [row for row in cross_rows if row["crossDisposition"] == "recommend-revision"]
hold_rows = [row for row in cross_rows if row["crossDisposition"] == "hold-source-copy"]
recommendations_path = OUT / "cross-recommendations.jsonl"
holds_path = OUT / "cross-holds.jsonl"
recommendations_path.write_bytes(b"".join(canon_line({
    "sourceOrdinal": row["sourceOrdinal"], "sourceKey": row["sourceKey"], "locale": row["locale"],
    "sourceTextSha256": row["sourceTextSha256"], "currentTarget": row["currentTarget"],
    "currentTargetSha256": row["currentTargetSha256"], "callerContextSha256": row["callerContextSha256"],
    "tokenSummarySha256": row["tokenSummarySha256"], "recommendedTarget": row["recommendedTarget"],
    "recommendedTargetSha256": row["recommendedTargetSha256"], "targetBasis": row["targetBasis"],
    "confidence": row["confidence"], "rationale": row["rationale"]
}) for row in recommendation_rows))
holds_path.write_bytes(b"".join(canon_line({
    "sourceOrdinal": row["sourceOrdinal"], "sourceKey": row["sourceKey"], "locale": row["locale"],
    "sourceTextSha256": row["sourceTextSha256"], "currentTarget": row["currentTarget"],
    "currentTargetSha256": row["currentTargetSha256"], "callerContextSha256": row["callerContextSha256"],
    "tokenSummarySha256": row["tokenSummarySha256"], "recommendedTarget": None,
    "recommendedTargetSha256": None, "rationale": row["rationale"],
    "supplementalContextId": row["supplementalContextId"]
}) for row in hold_rows))
counts = Counter(row["crossDisposition"] for row in cross_rows)
by_locale = Counter(row["locale"] for row in recommendation_rows)
by_source = Counter(row["sourceKey"] for row in recommendation_rows)
selected_primary = sum(row["primary"]["status"] == "selected-exact-target" for row in cross_rows)
selected_blind = sum(row["blind"]["status"] == "selected-exact-target" for row in cross_rows)
variant_primary = sum(row["primary"]["status"] == "correction-adopted-with-alternative-target" for row in cross_rows)
variant_blind = sum(row["blind"]["status"] == "correction-adopted-with-alternative-target" for row in cross_rows)
proposal_union = proposal_ids_primary | proposal_ids_blind
summary = {
    "result": "PASS",
    "batch": "W350-399-Core",
    "repository": "snapetech-org/chaptarrng",
    "pullRequest": 190,
    "head": HEAD,
    "tree": TREE,
    "liveMain": packet["liveMain"],
    "sourceIds": 50,
    "cells": len(cross_rows),
    "locales": packet["scope"]["locales"],
    "independentLedgerSha256": sha_bytes((OUT / "independent-review.jsonl").read_bytes()),
    "primaryLedgerSha256": sha_bytes((PRIMARY / "primary-review-cells.jsonl").read_bytes()),
    "primaryProposalCount": len(primary_proposals),
    "blindLedgerSha256": sha_bytes((BLIND / "ledger.jsonl").read_bytes()),
    "blindProposalCount": len(proposal_ids_blind),
    "proposalUnionCellCount": len(proposal_union),
    "proposalIntersectionCellCount": len(proposal_ids_primary & proposal_ids_blind),
    "proposalSameTargetIntersectionCount": sum(primary_proposal_map[ident]["recommendedTarget"] == blind_map[ident]["proposedTarget"] for ident in proposal_ids_primary & proposal_ids_blind),
    "primaryExactTargetsSelected": selected_primary,
    "blindExactTargetsSelected": selected_blind,
    "primaryAlternativeCorrectionsSelected": variant_primary,
    "blindAlternativeCorrectionsSelected": variant_blind,
    "crossDecisionCounts": dict(sorted(counts.items())),
    "allSourceCurrentCallerTokenBindingsExact": all(all(row["hashBindings"].values()) for row in cross_rows),
    "allSelectedTargetsPreserveSourceTokens": all(row["recommendedTargetTokensVerified"] is not False for row in cross_rows),
    "protectedLiteralHeuristicRowsReviewed": len(read_jsonl(INPUT / "integrity-review-flags.jsonl")),
    "visibilitySourceMismatch": {
        "holdCount": 12,
        "labels": "Library/All",
        "sourceCopyRecommendation": visibility["adjudication"]["sourceCopyRecommendation"],
        "allTargetsTextFree": all(row["recommendedTarget"] is None for row in cross_rows if row["sourceOrdinal"] == 366),
        "supplementalContextSha256": sha_bytes(visibility_path.read_bytes()),
    },
    "repositoryOrCatalogEdited": False,
    "nativeSpeakerClaims": False,
    "finalCrossReviewFile": ledger_path.name,
    "finalCrossReviewSha256": sha_bytes(ledger_path.read_bytes()),
    "recommendationsFile": recommendations_path.name,
    "recommendationsSha256": sha_bytes(recommendations_path.read_bytes()),
    "recommendationCount": len(recommendation_rows),
    "recommendationCountByLocale": dict(sorted(by_locale.items())),
    "recommendationCountBySourceKey": dict(sorted(by_source.items())),
    "holdsFile": holds_path.name,
    "holdsSha256": sha_bytes(holds_path.read_bytes()),
    "holdCount": len(hold_rows),
}
(OUT / "cross-review-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
