#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

PACKET = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
EXPECTED_HEAD = "c66ef0bccc0635f047cebeda95b9aaa0ae8130a4"
EXPECTED_TREE = "e2142a119ce8d9d765927bb44a47f71364863995"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


assert git("rev-parse", "HEAD") == EXPECTED_HEAD
assert git("rev-parse", "HEAD^{tree}") == EXPECTED_TREE
status = git("status", "--porcelain", "--untracked-files=all").splitlines()
allowed = PACKET.relative_to(REPO).as_posix() + "/"
assert all(line[3:].startswith(allowed) for line in status), "only this new evidence packet may be dirty before apply"

primary = [json.loads(line) for line in (PACKET / "primary-review-cells.jsonl").read_text().splitlines()]
cross = [json.loads(line) for line in (PACKET / "independent-review/cross-review.jsonl").read_text().splitlines()]
assert len(primary) == len(cross) == 120
primary_by_cell = {(row["queuePosition"], row["locale"]): row for row in primary}
assert len(primary_by_cell) == 120
changes = [row for row in cross if row["finalDisposition"] in {"correction", "refinement"}]
assert len(changes) == 8

files_before = {}
catalogs = {}
for row in primary:
    path = row["targetFile"]
    if path not in files_before:
        raw = (REPO / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["targetFileSha256"], f"file hash mismatch: {path}"
        files_before[path] = raw
        catalogs[path] = json.loads(raw)
    p = primary_by_cell[(row["queuePosition"], row["locale"])]
    actual = catalogs[path][row["sourceId"]]
    assert actual == row["currentTarget"] == p["currentTarget"], (row["sourceId"], row["locale"])
    assert sha(actual) == row["currentTargetSha256"] == p["currentTargetSha256"]
    assert sha(row["source"]) == row["sourceSha256"] == p["sourceSha256"]

plans = []
files_updated = {}
for row in changes:
    p = primary_by_cell[(row["queuePosition"], row["locale"])]
    path = p["targetFile"]
    assert row["sourceId"] == p["sourceId"] and row["locale"] == p["locale"]
    assert row["sourceSha256"] == p["sourceSha256"]
    assert row["currentTargetSha256"] == p["currentTargetSha256"]
    current = row["currentTarget"]
    final = row["finalReviewedTarget"]
    assert sha(current) == row["currentTargetSha256"]
    assert sha(final) != sha(current)
    assert re.findall(r"\{[^{}]+\}", current) == re.findall(r"\{[^{}]+\}", final)
    for literal in p.get("protectedLiterals", []):
        assert literal in current and literal in final, (row["sourceId"], row["locale"], literal)
    raw = files_updated.get(path, files_before[path]).decode("utf-8")
    key = json.dumps(row["sourceId"], ensure_ascii=False)
    old = json.dumps(current, ensure_ascii=False)
    new = json.dumps(final, ensure_ascii=False)
    pattern = re.compile(r"(?m)^([ \t]*" + re.escape(key) + r"[ \t]*:[ \t]*)" + re.escape(old) + r"([ \t]*,?[ \t]*)$")
    raw, count = pattern.subn(lambda m: m.group(1) + new + m.group(2), raw)
    assert count == 1, (row["sourceId"], row["locale"], count)
    files_updated[path] = raw.encode("utf-8")
    plans.append({
        "queuePosition": row["queuePosition"],
        "sourceId": row["sourceId"],
        "locale": row["locale"],
        "targetFile": path,
        "sourceSha256": row["sourceSha256"],
        "expectedCurrentTargetSha256": row["currentTargetSha256"],
        "expectedCurrentTarget": current,
        "finalDisposition": row["finalDisposition"],
        "finalTarget": final,
        "finalTargetSha256": sha(final),
        "crossReviewNote": row["crossReviewNote"],
    })

for path, raw in files_updated.items():
    (REPO / path).write_bytes(raw)

readback = []
counts = Counter()
for row in cross:
    p = primary_by_cell[(row["queuePosition"], row["locale"])]
    path = p["targetFile"]
    data = json.loads((REPO / path).read_text())
    value = data[row["sourceId"]]
    expected = row["finalReviewedTarget"]
    assert value == expected, (row["queuePosition"], row["locale"])
    assert sha(value) == sha(expected)
    counts[row["finalDisposition"]] += 1
    readback.append({
        "queuePosition": row["queuePosition"],
        "sourceId": row["sourceId"],
        "locale": row["locale"],
        "targetFile": path,
        "finalDisposition": row["finalDisposition"],
        "finalTargetSha256": sha(value),
    })
for path in files_before:
    before = list(json.loads(files_before[path]).keys())
    after = list(json.loads((REPO / path).read_bytes()).keys())
    assert before == after, f"catalog key order changed: {path}"

(PACKET / "apply-plan.json").write_text(json.dumps({
    "repository": "snapetech-org/chaptarrng",
    "pullRequest": 190,
    "window": "W1200-W1209 exact-head re-review",
    "inputHead": EXPECTED_HEAD,
    "inputTree": EXPECTED_TREE,
    "inputCellCount": 120,
    "changeCount": len(plans),
    "changes": plans,
}, ensure_ascii=False, indent=2) + "\n")
(PACKET / "readback.json").write_text(json.dumps({
    "repository": "snapetech-org/chaptarrng",
    "pullRequest": 190,
    "window": "W1200-W1209 exact-head re-review",
    "inputHead": EXPECTED_HEAD,
    "inputTree": EXPECTED_TREE,
    "targetCells": len(readback),
    "changedCells": len(plans),
    "dispositions": dict(counts),
    "catalogKeyOrderPreserved": True,
    "targetFileCountChanged": len(files_updated),
    "readback": readback,
}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({
    "changedFiles": sorted(files_updated),
    "changedCells": len(plans),
    "dispositions": dict(counts),
    "targetCellsReadBack": len(readback),
}, ensure_ascii=False))
