#!/usr/bin/env python3
"""Verify the independent ChaptarrNG PR #190 root cross-review packet."""
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "candidate-free-input"
PRIMARY = ROOT / "primary-review"
BLIND = ROOT / "independent-blind-review"
CROSS = ROOT / "cross-review"
HEAD = "28cdae837118a426ac867fb468a5e5a6937cbb9b"
TREE = "e6e7f1344d08eddbc421d339f91594847a625c10"


def jl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError("command failed: " + " ".join(args) + "\n" + result.stdout)
    return result.stdout


def main():
    run([sys.executable, str(CANDIDATE / "verify_packet.py")], CANDIDATE)
    run([sys.executable, str(PRIMARY / "verify_review.py")], PRIMARY)
    run([sys.executable, str(BLIND / "output" / "verify-ledger.py")], BLIND / "output")
    for folder, checksum in (
        (CANDIDATE, "SHA256SUMS.txt"),
        (ROOT / "input" / "candidate-free-input", "SHA256SUMS.txt"),
        (PRIMARY, "SHA256SUMS.txt"),
        (BLIND / "input" / "candidate-free-input", "SHA256SUMS.txt"),
        (BLIND / "output", "SHA256SUMS.txt"),
        (CROSS, "SHA256SUMS.txt"),
    ):
        run(["sha256sum", "-c", checksum], folder)

    manifest = json.loads((CANDIDATE / "manifest.json").read_text(encoding="utf-8"))
    if manifest["head"] != HEAD or manifest["tree"] != TREE:
        raise ValueError("candidate-free exact pins differ")
    current_rows = jl(CANDIDATE / "current-target-cells.jsonl")
    primary_rows = jl(PRIMARY / "review-ledger.jsonl")
    blind_rows = jl(BLIND / "output" / "reviewer-ledger.jsonl")
    cross_rows = jl(CROSS / "root-cross-ledger.jsonl")
    key = lambda row: (row["locale"], row["sourceId"])
    maps = [{key(row): row for row in rows} for rows in (current_rows, primary_rows, blind_rows, cross_rows)]
    if any(len(item) != 20 for item in maps) or not all(set(maps[0]) == set(item) for item in maps[1:]):
        raise ValueError("input and reviewer ledgers do not cover the same 20 cells")

    attestation = json.loads((CROSS / "PR-attestation.json").read_text(encoding="utf-8"))
    if attestation["headRefOid"] != HEAD or attestation["tree"] != TREE or attestation["state"] != "OPEN" or attestation["isDraft"] is not True or attestation["deploymentsForHead"] != []:
        raise ValueError("live PR/deployment attestation differs from review scope")

    dispositions = Counter()
    selected_sources = Counter()
    holds = 0
    updates = 0
    for cell in sorted(maps[0]):
        c, p, b, x = (item[cell] for item in maps)
        locale, source_id = cell
        if x["head"] != HEAD or x["tree"] != TREE or p["sourceSha256"] != c["sourceSha256"] or b["sourceSha256"] != c["sourceSha256"]:
            raise ValueError(f"pin or source hash mismatch at {cell}")
        if p["currentTargetSha256"] != c["currentTargetSha256"] or b["currentTargetSha256"] != c["currentTargetSha256"]:
            raise ValueError(f"review baseline mismatch at {cell}")
        if x["currentTargetSha256"] != c["currentTargetSha256"] or x["sourceSha256"] != c["sourceSha256"]:
            raise ValueError(f"cross baseline hash mismatch at {cell}")

        if source_id == "ui.loading.dodgeBooks":
            holds += 1
            for field in ("sourceText", "currentTarget", "primaryProposal", "independentBlindProposal", "selectedTarget", "selectedTargetSha256"):
                if x.get(field) is not None:
                    raise ValueError(f"text-bearing creative hold at {cell}: {field}")
            if x["crossDisposition"] != "hold" or "selectedDisposition" in x:
                raise ValueError(f"Dodge cell was not retained as a hold: {cell}")
        else:
            selected = x["selectedTarget"]
            if hashlib.sha256(selected.encode("utf-8")).hexdigest() != x["selectedTargetSha256"]:
                raise ValueError(f"selected target hash mismatch at {cell}")
            if selected == c["currentTarget"]:
                raise ValueError(f"non-hold selected value is a no-op at {cell}")
            if x["selectionSource"] == "independent-clean-blind":
                reviewer = b
            elif x["selectionSource"] == "primary":
                reviewer = p
            else:
                raise ValueError(f"unexpected selected source at {cell}")
            proposal = reviewer.get("proposedTarget")
            if proposal is None:
                proposal = reviewer.get("recommendedTargetText")
            if proposal != selected:
                raise ValueError(f"selected text is not the cited reviewer proposal: {cell}")
            if x["selectedDisposition"] not in ("correction", "refinement") or x["crossDisposition"] == "hold":
                raise ValueError(f"selected target disposition mismatch at {cell}")
            updates += 1
        dispositions["hold" if source_id == "ui.loading.dodgeBooks" else x["selectedDisposition"]] += 1
        selected_sources[x.get("selectionSource", "hold")] += 1

    if holds != 11 or updates != 9 or dispositions != {"hold": 11, "correction": 6, "refinement": 3}:
        raise ValueError(f"unexpected root outcomes: holds={holds}, updates={updates}, dispositions={dispositions}")
    if selected_sources != {"independent-clean-blind": 8, "primary": 1, "hold": 11}:
        raise ValueError(f"unexpected selection sources: {selected_sources}")
    summary = json.loads((CROSS / "summary.json").read_text(encoding="utf-8"))
    if summary["head"] != HEAD or summary["tree"] != TREE or summary["cells"] != 20 or summary["selectedTargets"] != 9 or summary["textFreeHolds"] != 11:
        raise ValueError("root cross summary differs")
    print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":20,"selectedUpdates":updates,"textFreeHolds":holds,"dispositions":dict(sorted(dispositions.items())),"selectedSources":dict(sorted(selected_sources.items()))},ensure_ascii=False,sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}",file=sys.stderr)
        raise SystemExit(1)
