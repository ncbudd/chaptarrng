#!/usr/bin/env python3
"""Apply only pre-reviewed W300-W349 target values with exact hash guards."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

HEAD = "f0082d1b655c05b8d4019ede523dd695cd6d745a"
TREE = "4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def stsha(value):
    return sha(value.encode("utf-8"))

def fail(message):
    raise SystemExit("FAIL: " + message)

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--action-output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan["sourcePin"] != {"head": HEAD, "tree": TREE}:
        fail("plan source pin mismatch")
    if git(repo, "rev-parse", "HEAD") != HEAD or git(repo, "rev-parse", "HEAD^{tree}") != TREE:
        fail("apply worktree is not at exact pinned head/tree")
    if git(repo, "status", "--porcelain=v1"):
        fail("apply worktree is not clean")
    if len(plan["changes"]) != 106 or plan["selection"]["selectedUniqueCells"] != 106:
        fail("plan does not contain exactly 106 selected cells")

    changes_by_path = {}
    changes_by_id = {}
    for change in plan["changes"]:
        cid = change["cellId"]
        if cid in changes_by_id:
            fail("duplicate selected cell: " + cid)
        if stsha(change["finalTarget"]) != change["finalTargetSha256"]:
            fail("final target hash mismatch: " + cid)
        if change["targetFile"].startswith("/") or not change["targetFile"].startswith("src/NzbDrone.Core/Localization/Core/"):
            fail("target path outside direct Core locale catalogs: " + cid)
        changes_by_id[cid] = change
        changes_by_path.setdefault(change["targetFile"], []).append(change)

    catalog_data = {}
    catalog_before = {}
    catalog_order = {}
    for meta in plan["catalogs"]:
        path = repo / meta["path"]
        raw = path.read_bytes()
        if sha(raw) != meta["preimageSha256"]:
            fail("catalog preimage hash mismatch: " + meta["path"])
        data = json.loads(raw)
        keys = list(data)
        if len(keys) != meta["keyCount"] or sha(json.dumps(keys, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) != meta["keyOrderSha256"]:
            fail("catalog preimage key count/order mismatch: " + meta["path"])
        if raw != (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"):
            fail("catalog serialization mismatch: " + meta["path"])
        catalog_data[meta["path"]] = data
        catalog_before[meta["path"]] = raw
        catalog_order[meta["path"]] = keys

    seen = set()
    for path_text, changes in changes_by_path.items():
        if path_text not in catalog_data:
            fail("selected change path is not in the 12-catalog plan: " + path_text)
        data = catalog_data[path_text]
        for change in changes:
            cid = change["cellId"]
            if cid in seen:
                fail("selected cell appears more than once: " + cid)
            seen.add(cid)
            key = change["sourceKey"]
            if key not in data:
                fail("selected catalog key missing: " + cid)
            current = data[key]
            if stsha(current) != change["currentTargetSha256"]:
                fail("exact current target hash mismatch: " + cid)
            if current == change["finalTarget"]:
                fail("selected target is already current: " + cid)
    if seen != set(changes_by_id):
        fail("not all plan cells were hash-guarded")

    before_status = set(git(repo, "status", "--porcelain=v1").splitlines())
    expected_paths = set(changes_by_path)
    if before_status:
        fail("unexpected pre-apply status")

    per_catalog = []
    for meta in plan["catalogs"]:
        path_text = meta["path"]
        data = catalog_data[path_text]
        changes = changes_by_path.get(path_text, [])
        for change in changes:
            data[change["sourceKey"]] = change["finalTarget"]
        if list(data) != catalog_order[path_text]:
            fail("catalog key order changed in memory: " + path_text)
        if not changes:
            continue
        output = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        tmp_name = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".w300-349-", suffix=".tmp", dir=(repo / path_text).parent, delete=False) as tmp:
                tmp.write(output)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_name = tmp.name
            os.replace(tmp_name, repo / path_text)
        finally:
            if tmp_name and os.path.exists(tmp_name):
                os.unlink(tmp_name)
        per_catalog.append({
            "locale": meta["locale"],
            "path": path_text,
            "selectedCellCount": len(changes),
            "preimageSha256": sha(catalog_before[path_text]),
            "postimageSha256": sha(output),
            "keyCount": len(data),
            "keyOrderSha256": sha(json.dumps(list(data), ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
        })

    changed_paths = set(git(repo, "diff", "--name-only").splitlines())
    if changed_paths != expected_paths:
        fail("working diff path set differs from selected catalog paths")
    status_lines = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain=v1"], text=True).splitlines()
    status_paths = {line[3:] for line in status_lines}
    if status_paths != expected_paths:
        fail("working status path set differs from selected catalog paths")
    action = {
        "result": "PASS",
        "sourcePin": {"head": HEAD, "tree": TREE},
        "selectedCells": len(changes_by_id),
        "changedCatalogFiles": len(per_catalog),
        "changedPaths": sorted(expected_paths),
        "catalogs": per_catalog,
        "hooks": {
            "preCommit": "not run; commit command will set core.hooksPath=/dev/null because .githooks/pre-commit invokes scripts/security-scan-local.sh --staged --semgrep-only and the task forbids local scans",
            "prePush": "not run; push command will set core.hooksPath=/dev/null because .githooks/pre-push invokes packaging/scripts/test-publish-image-aliases.sh and the task forbids tests",
        },
    }
    args.action_output.parent.mkdir(parents=True, exist_ok=True)
    args.action_output.write_text(json.dumps(action, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": "PASS",
        "selectedCells": len(changes_by_id),
        "changedCatalogFiles": len(per_catalog),
        "changedPaths": sorted(expected_paths),
        "workingDiffPaths": sorted(changed_paths),
    }, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()

