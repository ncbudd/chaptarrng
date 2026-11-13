#!/usr/bin/env python3
"""Portable exact-head verifier for the ChaptarrNG W1187 no-op evidence."""
from pathlib import Path
import hashlib, json, subprocess

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def main():
    repo = Path(__file__).resolve().parents[4]
    rel = "docs/pr-evidence/pr190-localization-2026-11-03/w1187-fallback-hold-correction"
    evidence = repo / rel
    result = json.loads((evidence / "application-result.json").read_text())
    base = result["baseHead"]
    assert git(repo, "cat-file", "-t", base) == "commit"
    assert git(repo, "rev-parse", f"{base}^{{tree}}") == result["baseTree"]
    assert git(repo, "diff", "--quiet", base, "HEAD", "--", "src/NzbDrone.Core/Localization/Core") == "", "catalog changed since pinned audit head"
    assert not git(repo, "diff", "--name-only", base, "HEAD", "--", ".github/workflows")
    changed = git(repo, "diff", "--name-only", base, "HEAD").splitlines()
    assert changed and all(p.startswith(rel + "/") for p in changed), f"unexpected changes since audit head: {changed}"
    plan = [json.loads(line) for line in (evidence/"apply-plan.jsonl").read_text().splitlines() if line]
    assert len(plan) == 12 and len({r["locale"] for r in plan}) == 12
    assert all(r["sourceOrdinal"] == 1187 and r["sourceId"] == result["sourceId"] for r in plan)
    assert all(r["action"] == "no-op" and not r["apply"] and r["selectedDisposition"] == "accept-current" for r in plan)
    for r in plan:
        raw = subprocess.check_output(["git", "-C", str(repo), "show", f"{base}:{r['catalogPath']}"], text=True)
        value = json.loads(raw)[r["sourceId"]]
        assert hashlib.sha256(value.encode()).hexdigest() == r["currentTargetSha256"], f"target mismatch: {r['locale']}"
    reattested = [json.loads(line) for line in (evidence/"cross-audit/prior-hold-reattestation.jsonl").read_text().splitlines() if line]
    assert len(reattested) == 12
    assert result["priorHoldsReattested"] == result["priorHoldsCleared"] == 12
    assert result["updates"] == 0 and result["noOps"] == 12 and result["newHolds"] == 0
    assert result["m4bClassification"].startswith("dynamic placeholder fallback")
    print("PASS: W1187 12 stale holds cleared; 12 catalog values match exact pinned hashes; evidence-only diff; no workflow edits")

if __name__ == "__main__":
    main()
