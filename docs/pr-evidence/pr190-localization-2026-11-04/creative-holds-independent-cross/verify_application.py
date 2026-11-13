#!/usr/bin/env python3
import hashlib, json, subprocess, sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
packet = evidence / "review-packet"
repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-fresh-exact-20261103/repo")
post = json.loads((evidence / "application-postflight.json").read_text(encoding="utf-8"))
read_jsonl = lambda p: [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]

def git(*args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, text=False).stdout

def sha(data):
    return hashlib.sha256(data).hexdigest()

def fail(msg):
    raise SystemExit("FAIL: " + msg)

base = post["baseHead"]
app_head = post["applicationHead"]
app_tree = post["applicationTree"]
if git("rev-parse", app_head).decode().strip() != app_head: fail("application commit missing")
if git("rev-parse", app_head + "^{tree}").decode().strip() != app_tree: fail("application tree mismatch")
if post["pullRequest"] != 190 or post["repository"] != "snapetech-org/ChaptarrNG": fail("wrong repository or PR")
if post["prState"] != "OPEN" or post["isDraft"] is not True or post["prHead"] != app_head: fail("PR postflight pin mismatch")
if post["deploymentsObserved"] != 0: fail("unexpected deployment")

cells = read_jsonl(packet / "candidate-free-input/current-target-cells.jsonl")
cross = read_jsonl(packet / "cross-review/root-cross-ledger.jsonl")
readback = json.loads((evidence / "application-readback.json").read_text(encoding="utf-8"))
key = lambda x: (x["sourceId"], x["locale"])
if len(cells) != 20 or len(cross) != 20 or len({key(x) for x in cells}) != 20: fail("scope is not 20 unique cells")
by_cross = {key(x): x for x in cross}
updates = {key(x): x for x in cross if x["crossDisposition"] != "hold"}
holds = {key(x): x for x in cross if x["crossDisposition"] == "hold"}
if len(updates) != 9 or len(holds) != 11: fail("expected nine updates and eleven holds")
if readback["applicationHead"] != app_head or readback["applicationTree"] != app_tree: fail("readback pin mismatch")
if len(readback["rows"]) != 20: fail("readback row count mismatch")
rb = { (x["sourceId"], x["locale"]): x for x in readback["rows"] }
if set(rb) != set(by_cross): fail("readback row keys mismatch")
files = sorted({r["targetFile"] for r in cells})
expected_changes = {(r["targetFile"], r["sourceId"]): by_cross[key(r)]["selectedTarget"] for r in cells if key(r) in updates}
actual_changes = []
for rel in files:
    base_bytes = git("show", f"{base}:{rel}")
    if sha(base_bytes) != next(r["targetFileSha256"] for r in cells if r["targetFile"] == rel): fail("candidate-free catalog hash drift: " + rel)
    head_bytes = git("show", f"{app_head}:{rel}")
    old = json.loads(base_bytes)
    new = json.loads(head_bytes)
    if set(old) != set(new): fail("catalog keys changed: " + rel)
    for k, value in old.items():
        if value != new[k]:
            actual_changes.append((rel, k))
            expected = expected_changes.get((rel, k))
            if expected is None or new[k] != expected: fail(f"unexpected catalog value delta: {rel}:{k}")
if set(actual_changes) != set(expected_changes): fail("catalog delta is not exactly the nine selected cells")
for row in cells:
    k = key(row)
    choice = by_cross[k]
    target = json.loads(git("show", f"{app_head}:{row['targetFile']}"))[row["sourceId"]]
    observed_hash = sha(target.encode("utf-8"))
    item = rb[k]
    if k in updates:
        expected = choice["selectedTarget"]
        if target != expected or item.get("selectedTarget") != expected: fail(f"selected value mismatch: {k}")
        if item.get("observedSha256") != observed_hash or item.get("selectedTargetSha256") != observed_hash: fail(f"selected hash mismatch: {k}")
        if item.get("crossDisposition") != choice["crossDisposition"]: fail(f"selected disposition mismatch: {k}")
    else:
        expected_hash = row["currentTargetSha256"]
        if observed_hash != expected_hash or item.get("observedSha256") != expected_hash or item.get("currentTargetSha256") != expected_hash: fail(f"hold hash mismatch: {k}")
        if any(field in item for field in ("expected", "observed", "selectedTarget", "currentTarget")): fail(f"hold row includes target text: {k}")
        if item.get("crossDisposition") != "hold": fail(f"hold disposition mismatch: {k}")

changed_paths = git("diff-tree", "--no-commit-id", "--name-only", "-r", base, app_head).decode().splitlines()
expected_paths = sorted({rel for rel, _ in actual_changes})
if sorted(changed_paths) != expected_paths: fail("application commit changed unexpected paths")
if any(p.startswith(".github/workflows/") for p in changed_paths): fail("workflow path changed")
print(json.dumps({"result": "PASS", "cells": 20, "selectedUpdates": 9, "textFreeHolds": 11, "changedCells": len(actual_changes), "changedFiles": expected_paths, "workflowChanges": []}, ensure_ascii=False))
