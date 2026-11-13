#!/usr/bin/env python3
"""Verify a sealed W350–W399 candidate-free blind review ledger."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

HEAD = "dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0"
TREE = "be10d71209076f753ef295038a9f3c3646a918a3"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
DECISIONS = {"accept-current", "correction", "refinement", "hold"}
TOKEN = re.compile(r"\{(?:[A-Za-z_][A-Za-z0-9_]*|[0-9]+)\}")
NUMBER = re.compile(r"(?<![A-Za-z0-9_])[0-9]+(?![A-Za-z0-9_])")
ICU = re.compile(r"\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(plural|select|selectordinal)\s*,")


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_text(text: str) -> str:
    return digest_bytes(text.encode("utf-8"))


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_counts(text: str) -> dict[str, int]:
    return dict(sorted(collections.Counter(TOKEN.findall(text)).items()))


def number_tokens(text: str) -> list[str]:
    return NUMBER.findall(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, help="candidate-free/input directory (default: ../candidate-free/input)")
    ap.add_argument("--ledger", type=Path, help="ledger.jsonl path (default: sibling ledger.jsonl)")
    ap.add_argument("--contexts", type=Path, help="caller-context-review.jsonl path")
    ap.add_argument("--seal", type=Path, help="seal.json path")
    ap.add_argument("--checksums", type=Path, help="SHA256SUMS.txt path")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent
    inp = (args.input or out.parent / "candidate-free" / "input").resolve()
    ledger_path = (args.ledger or out / "ledger.jsonl").resolve()
    contexts_path = (args.contexts or out / "caller-context-review.jsonl").resolve()
    seal_path = (args.seal or out / "seal.json").resolve()
    sums_path = (args.checksums or out / "SHA256SUMS.txt").resolve()
    if not inp.is_dir(): fail(f"candidate-free input directory missing: {inp}")

    # Verify the complete candidate-free packet by its included manifest of hashes.
    expected_input = {}
    for line in (inp / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        parts = line.split(None, 1)
        if len(parts) != 2: fail("malformed candidate-free SHA256SUMS.txt")
        expected_input[parts[1].strip()] = parts[0]
    if not expected_input: fail("candidate-free input checksum list is empty")
    for rel, expected in expected_input.items():
        p = inp / rel
        if not p.is_file(): fail(f"candidate-free input file missing: {rel}")
        actual = digest_bytes(p.read_bytes())
        if actual != expected: fail(f"candidate-free input hash mismatch: {rel}")

    manifest = json.loads((inp / "candidate-free-manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((inp / "candidate-free-summary.json").read_text(encoding="utf-8"))
    if manifest.get("head") != HEAD or manifest.get("tree") != TREE: fail("candidate-free manifest head/tree mismatch")
    if summary.get("head") != HEAD or summary.get("tree") != TREE: fail("candidate-free summary head/tree mismatch")
    if manifest.get("candidateFreeOnly") is not True or summary.get("candidateFreeOnly") is not True: fail("candidate-free-only attestation missing")
    if manifest.get("scope", {}).get("locales") != LOCALES: fail("unexpected locale list/order")

    cells = jsonl(inp / "candidate-free-cells.jsonl")
    contexts = jsonl(inp / "caller-context.jsonl")
    ledger = jsonl(ledger_path)
    context_reviews = jsonl(contexts_path)
    if len(cells) != 600 or len(ledger) != 600: fail("expected exactly 600 candidate-free and ledger cells")
    if len(contexts) != 50 or len(context_reviews) != 50: fail("expected exactly 50 caller-context records")
    expected_keys = []
    for row in cells:
        if row["sourceKey"] not in expected_keys: expected_keys.append(row["sourceKey"])
    if len(expected_keys) != 50: fail("expected 50 unique source keys")
    if [r["sourceKey"] for r in context_reviews] != expected_keys: fail("caller-context review order differs from source order")
    context_by = {x["sourceKey"]: x for x in contexts}
    source_by = {}
    for x in cells: source_by.setdefault(x["sourceKey"], x)

    # Caller context is copied in full and hash-bound, so reviewers can audit the exact UI evidence.
    for original, reviewed in zip(contexts, context_reviews):
        if reviewed.get("callerContext") != original: fail(f"caller context content differs for {original['sourceKey']}")
        if reviewed.get("sourceKey") != original["sourceKey"]: fail("caller-context source key mismatch")
        raw = json.dumps(original, ensure_ascii=False, separators=(",", ":"))
        if reviewed.get("callerRecordSha256") != digest_text(raw): fail(f"caller-record hash mismatch: {original['sourceKey']}")
        if reviewed.get("sourceTextSha256") != source_by[original["sourceKey"]]["sourceTextSha256"]: fail("caller context source hash mismatch")

    protected_flag_rows = jsonl(inp / "integrity-review-flags.jsonl")
    flagged = {(x["sourceKey"], x["locale"]) for x in protected_flag_rows}
    if len(flagged) != 16: fail("expected 16 protected-literal heuristic flags")
    seen = set()
    actual_decisions = collections.Counter()
    locale_counts = {loc: collections.Counter() for loc in LOCALES}
    for source, review in zip(cells, ledger):
        ident = (source["sourceOrdinal"], source["sourceKey"], source["locale"])
        if ident in seen: fail(f"duplicate ledger cell: {ident}")
        seen.add(ident)
        for name, value in (("head", HEAD), ("tree", TREE)):
            if review.get(name) != value: fail(f"{name} pin mismatch at {ident}")
        fields = ["sourceOrdinal", "sourceKey", "sourceText", "sourceTextSha256", "sourceFile", "sourceFileGitBlob", "sourceFileSha256", "locale", "targetFile", "targetFileGitBlob", "targetFileSha256", "currentTarget", "currentTargetSha256", "callerContextSha256", "callerReferenceCount", "indirectKeyReferenceCount", "literalCallCount", "relatedDynamicTranslationCallsiteCount", "sourcePlaceholders", "currentPlaceholders", "sourceNumericTokens", "currentNumericTokens", "sourceInlineCode", "currentInlineCode", "sourceMarkup", "currentMarkup", "protectedLiterals", "integrityChecks"]
        for field in fields:
            if review.get(field) != source.get(field): fail(f"{field} differs from candidate-free source at {ident}")
        if review.get("callerContextRecordSha256") != digest_text(json.dumps(context_by[source["sourceKey"]], ensure_ascii=False, separators=(",", ":"))): fail(f"caller record pin mismatch at {ident}")
        if digest_text(source["sourceText"]) != source["sourceTextSha256"]: fail(f"source text hash mismatch at {ident}")
        if digest_text(source["currentTarget"]) != source["currentTargetSha256"]: fail(f"current target hash mismatch at {ident}")
        if token_counts(source["sourceText"]) != source["sourcePlaceholders"]: fail(f"source placeholder manifest mismatch at {ident}")
        if token_counts(source["currentTarget"]) != source["currentPlaceholders"]: fail(f"current placeholder manifest mismatch at {ident}")
        if number_tokens(source["sourceText"]) != source["sourceNumericTokens"]: fail(f"source numeric-token manifest mismatch at {ident}")
        if number_tokens(source["currentTarget"]) != source["currentNumericTokens"]: fail(f"current numeric-token manifest mismatch at {ident}")
        if any(k != "protectedLiteral" and v is not True for k, v in source["integrityChecks"].items()): fail(f"non-protected integrity check failed at {ident}")
        has_flag = (source["sourceKey"], source["locale"]) in flagged
        if has_flag != (source["integrityChecks"].get("protectedLiteral") is False): fail(f"protected-literal flag map mismatch at {ident}")
        icu_src = ICU.findall(source["sourceText"])
        icu_current = ICU.findall(source["currentTarget"])
        if icu_src != icu_current: fail(f"current ICU pattern mismatch at {ident}")

        decision = review.get("decision")
        if decision not in DECISIONS: fail(f"invalid decision at {ident}")
        if review.get("confidence") not in {"high", "moderate", "low", "unknown"}: fail(f"invalid confidence at {ident}")
        proposal = review.get("proposedTarget")
        proposal_hash = review.get("proposedTargetSha256")
        if decision in {"correction", "refinement"}:
            if not isinstance(proposal, str) or not proposal: fail(f"missing proposed target at {ident}")
            if digest_text(proposal) != proposal_hash: fail(f"proposed target hash mismatch at {ident}")
            if token_counts(proposal) != source["sourcePlaceholders"]: fail(f"proposal placeholder mismatch at {ident}")
            if number_tokens(proposal) != source["sourceNumericTokens"]: fail(f"proposal numeric-token mismatch at {ident}")
            if ICU.findall(proposal) != icu_src: fail(f"proposal ICU pattern mismatch at {ident}")
            if proposal == source["currentTarget"]: fail(f"proposal is identical to current target at {ident}")
        else:
            if proposal is not None or proposal_hash is not None: fail(f"unexpected proposal at {ident}")
        if decision == "hold" and not review.get("rationale"): fail(f"hold without rationale at {ident}")
        actual_decisions[decision] += 1
        locale_counts[source["locale"]][decision] += 1

    if len(seen) != 600: fail("ledger is not a full 600-cell matrix")
    if sorted({x["locale"] for x in ledger}) != sorted(LOCALES): fail("ledger locale set mismatch")
    if [x["locale"] for x in ledger[:12]] != LOCALES: fail("ledger locale order mismatch")

    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("head") != HEAD or seal.get("tree") != TREE: fail("seal head/tree mismatch")
    if seal.get("primaryFilesOpenedBeforeBlindCompletion") is not False: fail("seal must state primary files were not opened before blind completion")
    if seal.get("ledgerSha256") != digest_bytes(ledger_path.read_bytes()): fail("seal ledger hash mismatch")
    if seal.get("callerContextReviewSha256") != digest_bytes(contexts_path.read_bytes()): fail("seal caller-context review hash mismatch")
    if seal.get("decisionCounts") != dict(sorted(actual_decisions.items())): fail("seal decision counts mismatch")
    if seal.get("protectedLiteralHeuristicFlagsReviewed") != 16: fail("seal protected-literal review count mismatch")
    if seal.get("candidateFreeOnly") is not True: fail("seal candidate-free-only attestation missing")

    # Verify the portable output checksum list, including this verifier and the seal.
    sums = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        parts = line.split(None, 1)
        if len(parts) != 2: fail("malformed output SHA256SUMS.txt")
        sums[parts[1].strip()] = parts[0]
    required = {ledger_path.name, contexts_path.name, seal_path.name, Path(__file__).name, "README.md"}
    if set(sums) != required: fail("output checksum list does not contain exactly the required artifacts")
    for name, expected in sums.items():
        p = out / name
        if not p.is_file() or digest_bytes(p.read_bytes()) != expected: fail(f"output hash mismatch: {name}")
    if seal.get("verifierSha256") != digest_bytes(Path(__file__).read_bytes()): fail("seal verifier hash mismatch")
    print("PASS")
    print(f"PR head {HEAD}; tree {TREE}")
    print(f"{len(ledger)} cells; {len(context_reviews)} caller records; decisions {dict(sorted(actual_decisions.items()))}")
    print("candidate-free-only; primary files opened before blind completion: false")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        fail(str(exc))
