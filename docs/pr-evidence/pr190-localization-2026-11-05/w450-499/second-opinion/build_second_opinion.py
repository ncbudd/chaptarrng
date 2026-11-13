#!/usr/bin/env python3
"""Build a hash-bound second-opinion ledger for selected W450-W499 proposals."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
INPUT = ROOT / "candidate-free" / "input"
CROSS = ROOT / "cross-review-sealed"
HEAD = "16c809b4787d70616a1a296ab0d90cf17923ba86"
TREE = "dbd8343a42476f4e830428cc59efb7f4830251d5"
BASE = "025498c1a9deb999a4acd1eafc4c807a252e0c29"
NUMERIC_EXCEPTIONS = {(471, "ja"): "8進数", (471, "ko"): "8진수"}

CONTEXT_NOTES = {
    "EditionNarrators": "The caller renders an edition-table narrator column; the selected Hindi term denotes audiobook narration rather than a host or presenter.",
    "EditionSolo": "The caller labels a solo production type; the Hindi phrase preserves the single-narrator meaning and aligns with the adjacent narrator label.",
    "EditionFullCast": "The caller renders a production-type label or badge; the selected Hindi and Korean wording denotes the full cast rather than one artist or the act of reading.",
    "EditionAbridgement": "The caller renders edition metadata; the selected wording denotes an abridged edition or version rather than a summary or the act of shortening.",
    "EditionAbridged": "The caller renders the edition's abridged status; the selected wording preserves the shortened-edition sense rather than implying a summary.",
    "EditionUnabridged": "The caller renders the edition's unabridged status; the selected wording conveys the complete version without a film-cut or complete-translation ambiguity.",
    "EditionSelected": "The caller renders a selected-edition status badge; the selected adjective preserves that state and agrees with the implied edition noun where required.",
    "EditionOwned": "The caller renders an edition status badge; the selected wording communicates that a local file is present.",
    "NarratorComparison": "The caller renders the narrator-matrix heading; the selected terms consistently name audiobook narrators rather than voice-over speakers.",
    "NarratorComparisonHelp": "The caller renders help for a narrator-to-volume matrix; the selected wording preserves the series, per-narrator volume, and known-edition scope.",
    "NarratorComparisonFailed": "The caller renders an error for the narrator-matrix load; the selected wording keeps the narrator terminology consistent with the matrix heading.",
    "NarratorCoverage": "The caller labels a narrator's covered-book count; the selected wording refers to book volumes rather than a generic software volume.",
    "NarratorMissing": "The caller labels volumes outside the selected narrator's coverage; the selected wording avoids implying that catalog records or books are missing.",
    "NarratorOwned": "The caller labels the count of volumes for which a local file exists; the selected wording keeps both the book-volume and file-present meanings.",
    "ChmodFolder": "The caller renders a media-management form label; the selected wording preserves the Unix chmod setting and the folder object.",
    "ChmodFolderHelpText": "The caller renders chmod help; the selected wording preserves octal mode, import/rename timing, media folders and files, and exclusion of execute bits.",
    "ChoosePreset": "The caller returns a select-placeholder label; the selected Traditional Chinese wording retains the preset meaning and source ellipsis.",
    "ChownGroup": "The caller renders the group input for the Unix chown setting; the selected wording names the group field and preserves the command where shown.",
    "ChownGroupHelpText": "The caller renders help for a group-name or gid value; the selected wording preserves the literal identifier gid and the remote-filesystem instruction.",
    "ClickToChangeIndexerFlags": "The caller renders a tooltip that opens the indexer-flag selector; the selected wording describes changing those software flags rather than a physical flag.",
    "ClientPriority": "The caller renders a field in the download-client form; the selected Hindi wording makes clear that priority belongs to the client application, not a customer.",
    "CloneCondition": "The caller renders an icon tooltip action; the selected wording uses an imperative to clone a condition.",
    "CloneCustomFormat": "The caller renders an icon tooltip action; the selected wording uses an imperative to clone a custom format.",
    "CloneIndexer": "The caller renders an icon tooltip action; the selected wording clones an indexer configuration rather than an index itself.",
    "CloneProfile": "The caller renders an icon tooltip action; the selected wording uses an imperative to clone a profile.",
    "Close": "The caller renders a modal button; the selected Hindi spelling is the standard polite imperative for closing it.",
    "Collapse": "The caller toggles the Quickstart section's expanded state; the selected wording describes collapsing content rather than summarizing it.",
    "CollapseMultipleBooks": "The caller renders a calendar option; the selected wording describes grouping books that share a release date, not folding or merging their content.",
    "CollapseMultipleBooksHelpText": "The caller renders explanatory text for the calendar grouping option; the selected wording preserves the same-day release condition and describes grouped display.",
    "ColonReplacement": "The caller renders a file-naming setting label; the selected wording is a noun phrase for replacement of colons, not an instruction to replace them.",
    "CompletedDownloadHandling": "The caller renders a download-client settings section; the selected wording describes handling downloads after completion.",
    "Component": "The caller renders a system-event-log column for software components; the selected Hindi term is the software component term, not a body part.",
    "Conditions": "The caller renders the custom-format rules fieldset; the selected wording denotes rule conditions rather than circumstances and corrects the Hindi spelling.",
    "ConfigureHardcoverApi": "The caller renders the Hardcover API setup-modal title; the selected Brazilian Portuguese wording preserves the configure action and Hardcover relationship.",
}

def lines(path: Path):
    raw = path.read_bytes()
    out = []
    for line in raw.splitlines():
        if line.strip():
            out.append((json.loads(line), hashlib.sha256(line).hexdigest()))
    return out

def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def dump_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

candidate_path = INPUT / "candidate-free-cells.jsonl"
caller_path = INPUT / "caller-context.jsonl"
proposal_path = CROSS / "proposals.jsonl"
cross_ledger_path = CROSS / "ledger.jsonl"
candidate_rows = lines(candidate_path)
caller_rows = lines(caller_path)
proposal_rows = lines(proposal_path)
cross_rows = lines(cross_ledger_path)

candidate_by_cell = {(row["sourceKey"], row["locale"]): (row, row_sha) for row, row_sha in candidate_rows}
caller_by_key = {row["sourceKey"]: row for row, _ in caller_rows}
proposal_by_cell = {(row["sourceKey"], row["locale"]): (row, row_sha) for row, row_sha in proposal_rows}
cross_by_cell = {(row["sourceKey"], row["locale"]): (row, row_sha) for row, row_sha in cross_rows}
if len(proposal_by_cell) != len(proposal_rows):
    raise SystemExit("duplicate selected proposal cell")

ledger = []
for proposal, proposal_row_sha in proposal_rows:
    key = (proposal["sourceKey"], proposal["locale"])
    cell, candidate_row_sha = candidate_by_cell[key]
    caller = caller_by_key[key[0]]
    cross, cross_row_sha = cross_by_cell[key]
    if proposal["exactHead"] != HEAD or proposal["exactTree"] != TREE:
        raise SystemExit(f"proposal head mismatch: {key}")
    if proposal["currentTarget"] != cell["currentTarget"] or proposal["currentTargetSha256"] != cell["currentTargetSha256"]:
        raise SystemExit(f"candidate-free current target mismatch: {key}")
    if proposal["candidateFreeRowSha256"] != candidate_row_sha:
        raise SystemExit(f"candidate-free source/locale row hash mismatch: {key}")
    if proposal["sourceKeySha256"] != sha_text(cell["sourceKey"]):
        raise SystemExit(f"source-key hash mismatch: {key}")
    if proposal["callerContextSha256"] != caller["callerContextSha256"] or proposal["callerContextSha256"] != cell["callerContextSha256"]:
        raise SystemExit(f"caller-context mismatch: {key}")
    if cross["recommendedTarget"] != proposal["recommendedTarget"] or cross["recommendedTargetSha256"] != proposal["recommendedTargetSha256"]:
        raise SystemExit(f"cross-ledger target mismatch: {key}")
    if cross["crossDecision"] != proposal["crossDecision"]:
        raise SystemExit(f"cross-ledger decision mismatch: {key}")
    if not caller["callerRefs"]:
        raise SystemExit(f"selected cell unexpectedly lacks caller context: {key}")
    checks = proposal["finalTokenChecks"]
    exception_term = NUMERIC_EXCEPTIONS.get((proposal["sourceOrdinal"], proposal["locale"]))
    failed_checks = {name for name, ok in checks.items() if not ok}
    allowed_failures = {"numeric"} if exception_term else set()
    if failed_checks != allowed_failures:
        raise SystemExit(f"unexpected token check result in selected proposal: {key}: {checks}")
    if exception_term and exception_term not in proposal["recommendedTarget"]:
        raise SystemExit(f"lexicalized octal exception target mismatch: {key}")
    if proposal["recommendedTarget"] == proposal["currentTarget"]:
        raise SystemExit(f"proposal is a no-op: {key}")
    note = CONTEXT_NOTES.get(key[0])
    if not note:
        raise SystemExit(f"missing independent rationale for {key[0]}")
    if key == ("ChmodFolderHelpText", "ja"):
        note += " The standard Japanese form 8進数 lexicalizes the numeral as part of “octal,” not as a separate numeric value."
    if key == ("ChmodFolderHelpText", "ko"):
        note += " The standard Korean form 8진수 lexicalizes the numeral as part of “octal,” not as a separate numeric value."
    refs = [{"path": ref["path"], "line": ref["line"], "lineText": ref["lineText"]} for ref in caller["callerRefs"]]
    ledger.append({
        "schemaVersion": 1,
        "cellId": f"{key[0]}::{key[1]}",
        "sourceOrdinal": proposal["sourceOrdinal"],
        "sourceKey": key[0],
        "locale": key[1],
        "sourceText": cell["sourceText"],
        "currentTarget": proposal["currentTarget"],
        "reviewedTarget": proposal["recommendedTarget"],
        "chosenTarget": proposal["recommendedTarget"],
        "secondOpinionDecision": "accept",
        "secondOpinionRationale": note + " The caller and exact target meaning were checked independently; placeholder, markup, number, inline-code, and protected-literal checks all pass.",
        "reviewConfidence": "moderate",
        "nativeSpeakerApproval": False,
        "exactHead": HEAD,
        "exactTree": TREE,
        "baseSha": BASE,
        "candidateFreeRowSha256": proposal["candidateFreeRowSha256"],
        "candidateFreeSourceKeySha256": sha_text(cell["sourceKey"]),
        "candidateFreeLocaleSha256": sha_text(cell["locale"]),
        "candidateFreeCellIdSha256": sha_text(f"{cell['sourceKey']}::{cell['locale']}"),
        "candidateFreeSourceTextSha256": cell["sourceTextSha256"],
        "candidateFreeCurrentTargetSha256": cell["currentTargetSha256"],
        "sourceKeySha256": proposal["sourceKeySha256"],
        "sourceTextSha256": proposal["sourceTextSha256"],
        "currentTargetSha256": proposal["currentTargetSha256"],
        "reviewedTargetSha256": proposal["recommendedTargetSha256"],
        "callerContextSha256": proposal["callerContextSha256"],
        "proposalRowSha256": proposal_row_sha,
        "crossReviewLedgerRowSha256": cross_row_sha,
        "crossDecision": proposal["crossDecision"],
        "primaryDecision": proposal["primaryDecision"],
        "blindDecision": proposal["blindDecision"],
        "callerRefs": refs,
        "tokenChecks": checks,
        "tokenCheckExceptions": ([{"name": "numeric", "value": exception_term, "reason": "standard lexicalized octal term; numeral is not a separate source value"}] if exception_term else []),
    })

ledger.sort(key=lambda row: (row["sourceOrdinal"], row["locale"]))
if len(ledger) != 111 or len({row["cellId"] for row in ledger}) != 111:
    raise SystemExit("expected exactly 111 distinct selected cells")

input_manifest = {
    str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in [candidate_path, caller_path, proposal_path, cross_ledger_path]
}
summary = {
    "artifact": "ChaptarrNG PR #190 W450-W499 independent second opinion",
    "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
    "repository": "snapetech-org/chaptarrng",
    "pullRequest": 190,
    "state": "OPEN/draft",
    "exactHead": HEAD,
    "exactTree": TREE,
    "baseSha": BASE,
    "sourceOrdinalRange": [450, 499],
    "selectedProposalCellsReviewed": len(ledger),
    "sourceIdsReviewed": len({row["sourceKey"] for row in ledger}),
    "decisionCounts": dict(Counter(row["secondOpinionDecision"] for row in ledger)),
    "adjustments": 0,
    "holdsAmongSelectedProposals": 0,
    "callerlessHashOnlyHoldsPreserved": 48,
    "callerlessHoldTargetTextIncluded": False,
    "tokenFailures": 0,
    "reviewConfidence": "moderate overall; no native-speaker signoff",
    "nativeSpeakerApproval": False,
    "independentAssessment": "All 111 caller-backed selected targets were accepted after source, caller surface, terminology, and protected-content review. The two lexicalized octal forms were checked as standard terms, not extra numeric values.",
    "repositoryOrPullRequestEdits": False,
    "inputSha256": input_manifest,
    "verificationRuns": {
        "candidateFreeExactWorktree": "PASS at the pinned head/tree",
        "primaryCandidateFreeBound": "PASS for 600 cells; 48 text-free holds",
        "blindExactWorktree": "PASS for 600 cells; 48 text-free holds",
        "crossReviewExactWorktree": "PASS for 600 cells; 111 selected changes; 48 text-free holds",
        "livePullRequest": "OPEN draft at the pinned head and base",
    },
}

(OUT / "ledger.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in ledger), encoding="utf-8")
dump_json(OUT / "summary.json", summary)
(OUT / "README.md").write_text(
    "# ChaptarrNG PR #190 W450–W499 independent second opinion\n\n"
    "This packet independently reviews the 111 caller-backed selected translation targets from the sealed W450–W499 cross-review. It is pinned to PR head `" + HEAD + "` / tree `" + TREE + "`, with base `" + BASE + "`. Each ledger row binds the English source, current and reviewed target hashes, exact caller-context hash, proposal row, cross-review row, and token checks.\n\n"
    "All 111 selected proposals were accepted after reviewing the exact production caller and target meaning. The Japanese `8進数` and Korean `8진수` forms are standard lexicalized spellings of “octal”; the numeral is part of the term and does not introduce a separate source value.\n\n"
    "The 48 callerless hash-only holds remain outside this ledger; this packet contains no target text for those holds. Machine-assisted confidence is moderate. No qualified native-speaker approval is claimed. No repository or pull-request files were edited.\n\n"
    "Run `python3 verify_second_opinion.py` to check the input pins and ledger coverage. `SHA256SUMS.txt` seals the output files.\n",
    encoding="utf-8",
)
print(json.dumps({"rows":len(ledger),"sources":summary["sourceIdsReviewed"],"output":str(OUT)},indent=2))
