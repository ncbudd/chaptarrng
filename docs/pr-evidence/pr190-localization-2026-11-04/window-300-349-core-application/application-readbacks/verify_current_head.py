#!/usr/bin/env python3
"""Exact-hash W300–W349 catalog readback for a specified Git head."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CODE_EXTS = {".js", ".jsx", ".ts", ".tsx", ".cs"}
DYNAMIC_CALL = re.compile(r"\b(?:translate|GetLocalizedString)\s*\(\s*([^,)\n]+)")


def git(repo: Path, *args: str, binary: bool = False):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=not binary)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def catalog(repo: Path, rev: str, path: str):
    return json.loads(git(repo, "show", f"{rev}:{path}", binary=True))


def scan_contexts(repo: Path, rev: str, keys: list[str]):
    tree = git(repo, "ls-tree", "-rz", rev, binary=True)
    entries = []
    for row in tree.split(b"\0"):
        if not row:
            continue
        meta, raw_path = row.split(b"\t", 1)
        _, kind, blob = meta.decode().split()
        path = raw_path.decode()
        if kind != "blob" or Path(path).suffix not in CODE_EXTS:
            continue
        parts = Path(path).parts
        basename = Path(path).name.lower()
        test_project = any(
            part.lower() in ("test", "tests", "__tests__")
            or part.lower().endswith((".test", ".tests", "-test", "-tests"))
            for part in parts[:-1]
        )
        test_file = basename.endswith((".test.js", ".test.jsx", ".test.ts", ".test.tsx", ".spec.js", ".spec.jsx", ".spec.ts", ".spec.tsx", ".test.cs", ".tests.cs"))
        if test_project or test_file:
            continue
        data = git(repo, "cat-file", "blob", blob, binary=True)
        try:
            lines = data.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        entries.append((path, blob, data, lines))
    entries.sort(key=lambda item: item[0])
    contexts = {}
    for key in keys:
        rx = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(key) + r"(?![A-Za-z0-9_])")
        refs, dyn = [], []
        for path, blob, data, lines in entries:
            hits = []
            for index, line in enumerate(lines):
                if not rx.search(line):
                    continue
                comment = line.lstrip().startswith(("//", "/*", "*", "#"))
                front = bool(re.search(r"\btranslate\s*\(\s*(['\"])" + re.escape(key) + r"\1", line))
                server = bool(re.search(r"\bGetLocalizedString\s*\(\s*(['\"])" + re.escape(key) + r"\1", line))
                kind = "literal-translate-call" if front else "literal-server-call" if server else "indirect-key-literal-reference"
                refs.append({
                    "referenceKind": kind, "isComment": comment, "isRuntimeReference": not comment,
                    "path": path, "line": index + 1, "lineText": line, "lineSha256": sha(line.encode()),
                    "fileSha256": sha(data), "fileGitBlob": blob,
                    "contextBefore": lines[max(0, index - 2):index], "contextAfter": lines[index + 1:index + 4],
                })
                hits.append(index)
            if hits:
                for index, line in enumerate(lines):
                    for match in DYNAMIC_CALL.finditer(line):
                        arg = match.group(1).strip()
                        if arg.startswith(("'", '"', "`")) or line.lstrip().startswith(("//", "/*", "*")):
                            continue
                        dyn.append({
                            "path": path, "line": index + 1, "lineText": line, "lineSha256": sha(line.encode()),
                            "callExpression": match.group(0).strip(), "argumentExpression": arg,
                            "fileSha256": sha(data), "fileGitBlob": blob,
                            "contextBefore": lines[max(0, index - 2):index], "contextAfter": lines[index + 1:index + 3],
                        })
        refs.sort(key=lambda item: (item["path"], item["line"], item["referenceKind"]))
        dyn.sort(key=lambda item: (item["path"], item["line"], item["callExpression"]))
        actual = [item for item in refs if item["isRuntimeReference"]]
        body = {"sourceKey": key, "literalAndIndirectReferences": refs, "relatedDynamicTranslationCallsites": dyn}
        contexts[key] = {
            "sourceKey": key,
            "callerContextSha256": sha(canonical(body).rstrip(b"\n")),
            "callerReferenceCount": len(actual),
            "literalCallCount": sum(item["referenceKind"] != "indirect-key-literal-reference" for item in actual),
            "indirectKeyReferenceCount": sum(item["referenceKind"] == "indirect-key-literal-reference" for item in actual),
            "relatedDynamicTranslationCallsiteCount": len(dyn),
        }
    return contexts


def verify_checksums(directory: Path):
    result = subprocess.run(["sha256sum", "-c", "SHA256SUMS.txt"], cwd=directory, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f"Checksum verification failed in {directory}: {result.stderr}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True, help="Git repository/worktree containing the exact revisions")
    parser.add_argument("--evidence-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--head", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--product", required=True)
    args = parser.parse_args()
    repo, evidence = args.repo.resolve(), args.evidence_root.resolve()
    source_packet = evidence / "source-packets/candidate-free/input"
    plan = json.loads((evidence / "application-plan/apply-plan.json").read_text(encoding="utf-8"))
    cells = read_jsonl(source_packet / "candidate-free-cells.jsonl")
    baseline_contexts = {row["sourceKey"]: row for row in read_jsonl(source_packet / "caller-context.jsonl")}
    keys = list(dict.fromkeys(row["sourceKey"] for row in cells))
    tree = git(repo, "rev-parse", f"{args.head}^{{tree}}").strip()
    current_source = catalog(repo, args.head, "src/NzbDrone.Core/Localization/Core/en.json")
    contexts = scan_contexts(repo, args.head, keys)
    selected = {item["cellId"]: item for item in plan["changes"]}
    catalog_data, catalog_checks = {}, []
    for meta in plan["catalogs"]:
        data = catalog(repo, args.head, meta["path"])
        key_order = sha(json.dumps(list(data), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if len(data) != meta["keyCount"] or key_order != meta["keyOrderSha256"]:
            raise SystemExit(f"Catalog key count/order mismatch: {meta['path']}")
        catalog_data[meta["path"]] = data
        catalog_checks.append({"path": meta["path"], "locale": meta["locale"], "keyCount": len(data), "keyOrderSha256": key_order})
    rows, mismatches = [], []
    for cell in cells:
        key, locale = cell["sourceKey"], cell["locale"]
        cell_id = key + "::" + locale
        value = catalog_data[cell["targetFile"]][key]
        observed_target = sha(value.encode("utf-8"))
        expected = selected[cell_id]["finalTargetSha256"] if cell_id in selected else cell["currentTargetSha256"]
        source_hash = sha(current_source[key].encode("utf-8"))
        context_hash = contexts[key]["callerContextSha256"]
        matches = observed_target == expected and source_hash == cell["sourceTextSha256"]
        if not matches:
            mismatches.append(cell_id)
        rows.append({
            "sourceOrdinal": cell["sourceOrdinal"], "sourceKey": key, "locale": locale,
            "cellIdSha256": sha(cell_id.encode("utf-8")), "targetFile": cell["targetFile"],
            "selected": cell_id in selected, "sourceTextSha256": source_hash,
            "expectedTargetSha256": expected, "observedTargetSha256": observed_target,
            "callerContextSha256": context_hash, "matches": matches,
        })
    context_rows = []
    changed_contexts = []
    for key in keys:
        previous, current = baseline_contexts[key], contexts[key]
        changed = previous["callerContextSha256"] != current["callerContextSha256"]
        if changed:
            changed_contexts.append(key)
        context_rows.append({
            "sourceKey": key, "priorContextSha256": previous["callerContextSha256"],
            "currentContextSha256": current["callerContextSha256"], "contextChanged": changed,
            "callerReferenceCount": current["callerReferenceCount"], "literalCallCount": current["literalCallCount"],
            "indirectKeyReferenceCount": current["indirectKeyReferenceCount"],
            "relatedDynamicTranslationCallsiteCount": current["relatedDynamicTranslationCallsiteCount"],
        })
    selected_context_changes = sorted(row["sourceKey"] + "::" + row["locale"] for row in cells
        if row["sourceKey"] in changed_contexts and row["sourceKey"] + "::" + row["locale"] in selected)
    root_dir = evidence / "review-supplements/root-manual-review"
    review_dir = evidence / "review-supplements/fresh-review-packets/BookMatchingStrictness-id-merge-4688c998"
    verify_checksums(root_dir)
    verify_checksums(review_dir)
    reviewer_verify = subprocess.run(["python3", "verify-sealed-review-decision.py"], cwd=review_dir, capture_output=True, text=True)
    if reviewer_verify.returncode:
        raise SystemExit("Fresh reviewer seal check failed: " + reviewer_verify.stderr)
    root_review = json.loads((root_dir / "fresh-context-adjudication-4688c998.json").read_text(encoding="utf-8"))
    reviewer = json.loads((review_dir / "sealed-review-decision.json").read_text(encoding="utf-8"))
    id_target = catalog_data["src/NzbDrone.Core/Localization/Core/id.json"]["BookMatchingStrictness"]
    reviewer_artifact_sha = sha((review_dir / "sealed-review-decision.json").read_bytes())
    review_pins_ok = (
        root_review["currentHead"] == args.head and root_review["currentTree"] == tree
        and root_review["cellId"] == "BookMatchingStrictness::id"
        and root_review["currentContextSha256"] == contexts["BookMatchingStrictness"]["callerContextSha256"]
        and root_review["sourceSha256"] == sha(current_source["BookMatchingStrictness"].encode("utf-8"))
        and root_review["currentTargetSha256"] == sha(id_target.encode("utf-8"))
        and root_review["currentTarget"] == "Mode pencocokan"
        and root_review["rootDecision"] == "accept-current"
        and root_review["freshIndependentReviewerDecision"] == "accept"
        and root_review["freshReviewerArtifactSha256"] == reviewer_artifact_sha
        and reviewer["pins"]["head"] == args.head and reviewer["pins"]["tree"] == tree
        and reviewer["hashes"]["currentContextSha256"] == contexts["BookMatchingStrictness"]["callerContextSha256"]
        and reviewer["decision"]["disposition"] == "accept"
    )
    if not review_pins_ok:
        raise SystemExit("Fresh root/reviewer decision does not pin to this exact head/context")
    product_record = json.loads((evidence / "application-plan/product-commit-record.json").read_text(encoding="utf-8"))
    product_paths = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", args.product).splitlines()
    expected_product_paths = product_record["changedPaths"]
    if sorted(product_paths) != sorted(expected_product_paths) or any(not p.startswith("src/NzbDrone.Core/Localization/Core/") for p in product_paths):
        raise SystemExit("Product commit path list differs from the sealed catalog list")
    workflow_diff = git(repo, "diff", "--name-only", args.main, args.head, "--", ".github/workflows").splitlines()
    if workflow_diff:
        raise SystemExit("Workflow paths changed against the latest main: " + repr(workflow_diff))
    if len(cells) != 600 or len(keys) != 50 or len(selected) != 106 or len(context_rows) != 50 or mismatches:
        raise SystemExit(f"Readback mismatch: cells={len(cells)} keys={len(keys)} selected={len(selected)} mismatches={mismatches[:10]}")
    out = evidence / "application-readbacks"
    out.mkdir(parents=True, exist_ok=True)
    (out / "current-head-600-cell-readback.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
    (out / "current-head-50-context-readback.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in context_rows), encoding="utf-8")
    result = {
        "result": "PASS", "head": args.head, "tree": tree, "latestMain": args.main,
        "candidateCells": len(rows), "selectedChanges": len(selected), "unchangedCells": len(rows) - len(selected),
        "targetReadbackMismatches": len(mismatches), "sourceKeys": len(keys), "sourceTextChanges": 0,
        "contextChangedKeysFromCandidateFree": changed_contexts,
        "selectedCellsWithChangedSourceOrContext": selected_context_changes,
        "catalogCount": len(catalog_checks), "keyCountPerCatalog": 4165,
        "catalogs": catalog_checks, "keyOrderChecked": True,
        "productCommit": args.product, "productCommitPaths": product_paths,
        "workflowPathsAgainstLatestMain": workflow_diff,
        "freshCellReview": {
            "cellId": root_review["cellId"], "target": root_review["currentTarget"],
            "contextSha256": root_review["currentContextSha256"],
            "reviewerDecision": root_review["freshIndependentReviewerDecision"],
            "reviewerConfidence": root_review["freshIndependentReviewerConfidence"],
            "rootDecision": root_review["rootDecision"], "rootConfidence": root_review["rootConfidence"],
            "nativeSpeakerSignoff": root_review["nativeSpeakerSignoff"],
        },
    }
    (out / "current-head-final-verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result["result"], "head": args.head, "tree": tree, "cells": len(rows), "selected": len(selected), "unchanged": len(rows)-len(selected), "mismatches": len(mismatches), "sourceKeys": len(keys), "changedContexts": changed_contexts, "selectedCellsWithChangedSourceOrContext": selected_context_changes, "workflowPaths": workflow_diff}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
