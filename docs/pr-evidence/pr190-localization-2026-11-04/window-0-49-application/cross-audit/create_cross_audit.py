#!/usr/bin/env python3
"""Build the portable ChaptarrNG PR #190 W0–W49 cross-audit bundle."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIMARY = ROOT / "input" / "candidate-primary"
BLIND = ROOT / "input" / "blind"
REVIEWER_A = ROOT / "work" / "reviewer-a.jsonl"
HEAD = "7f5d99e24b054cf1437d135328c3dee565e6b318"
TREE = "d39f2fe8cf91a39653679980c0832c5ca400a114"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha(text.encode("utf-8"))


def rows(path: Path):
    raw_rows = path.read_bytes().splitlines(keepends=True)
    result = []
    for raw in raw_rows:
        result.append((json.loads(raw), sha(raw.rstrip(b"\n"))))
    return result


def dump_jsonl(path: Path, records) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")


def key(row):
    return (row["sourceKey"], row["locale"])

# Targets are copied from the primary or blind proposal after this independent adjudication.
# The cross rationale records why the evidence supports the change.
SPECS = {
    ("AbsLibraryModeAudioOnly", "de"): ("primary", "The caller uses this only for an AudioBookShelf library flagged audiobooksOnly and contrasts it with audio plus eBooks; naming audiobooks removes ambiguity.", "high"),
    ("AbsLibraryModeAudioOnly", "es"): ("primary", "The caller uses this only for an AudioBookShelf library flagged audiobooksOnly and contrasts it with audio plus eBooks; naming audiobooks removes ambiguity.", "high"),
    ("AbsLibraryModeAudioOnly", "fr"): ("primary", "The caller uses this only for an AudioBookShelf library flagged audiobooksOnly and contrasts it with audio plus eBooks; naming audiobooks removes ambiguity.", "high"),
    ("AbsLibraryModeAudioOnly", "hi"): ("primary", "The caller uses this only for an AudioBookShelf library flagged audiobooksOnly and contrasts it with audio plus eBooks; naming audiobooks removes ambiguity.", "moderate"),
    ("AbsLibraryModeAudioOnly", "pt-BR"): ("primary", "The caller uses this only for an AudioBookShelf library flagged audiobooksOnly and contrasts it with audio plus eBooks; naming audiobooks removes ambiguity.", "high"),
    ("AbsMappingsAbsLibraryHeader", "zh-Hant"): ("blind", "This column names AudioBookShelf media libraries; 媒體庫 means media library, while 資料庫 suggests a database.", "high"),
    ("AbsMappingsHelpText", "de"): ("blind", "The caller asks which ABS folder can see the same files as each Chaptarr root. The current German says the folder contains those files, which changes the relationship; access wording is faithful.", "moderate"),
    ("AbsMappingsLegacyWarning", "zh-Hant"): ("blind", "The caller is mapping AudioBookShelf media libraries, not databases. The proposed terminology corrects that referent in the warning.", "high"),
    ("AbsMappingsLoadLibraries", "zh-Hant"): ("blind", "This button loads AudioBookShelf media libraries; 媒體庫 names that object, while 資料庫 means database.", "high"),
    ("AbsMappingsLoadLibrariesError", "zh-Hant"): ("blind", "This error is about loading AudioBookShelf media libraries, not databases; the proposed term matches the caller.", "high"),
    ("AbsMappingsLoadLibrariesFirst", "zh-Hant"): ("blind", "The disabled option requires the AudioBookShelf media libraries to be loaded first; the proposed term matches that object.", "high"),
    ("AbsMappingsLoadingLibraries", "zh-Hant"): ("blind", "This loading status is for AudioBookShelf media libraries, not databases; the proposed term matches the caller.", "high"),
    ("AbsMappingsNoRootFolders", "zh-Hant"): ("blind", "The warning refers to mapping Chaptarr root folders to AudioBookShelf media libraries; the proposed term corrects the referent.", "high"),
    ("AbsMappingsWatcherRequirement", "zh-Hant"): ("blind", "This helper explains per-library watcher behavior and fallback full scans. 媒體庫 accurately identifies those objects, and the target preserves the named setting and restart condition.", "high"),
    ("Adopt", "id"): ("blind", "The caller is a confirmation action for taking an already-running torrent into ChaptarrNG management; Ambil alih expresses taking it over more directly than the loanword Adopsi.", "moderate"),
    ("Adopt", "vi"): ("primary", "The confirmation action takes an existing torrent into management; Tiếp nhận distinguishes that from simply receiving it.", "moderate"),
    ("AdoptExistingTorrent", "id"): ("blind", "The modal title names taking an existing torrent into ChaptarrNG management; Ambil alih expresses that action.", "moderate"),
    ("AdoptExistingTorrent", "vi"): ("primary", "The modal title names taking an existing torrent into ChaptarrNG management; Tiếp nhận is clearer than Nhận (receive) in this context.", "moderate"),
    ("AdoptExistingTorrentMessageText", "hi"): ("blind", "The confirmation assures the user that another download will not start. कोई और expresses ‘another’ clearly; the placeholder and remaining meaning stay intact.", "moderate"),
    ("AdoptExistingTorrentMessageText", "id"): ("blind", "The modal describes tracking and importing the current torrent without starting another download. Ambil alih consistently names the management action.", "moderate"),
    ("AdoptExistingTorrentMessageText", "vi"): ("blind", "The modal describes tracking and importing the current torrent without starting another download. Tiếp nhận consistently names the management action and the wording retains the assurance.", "moderate"),
    ("Actions", "ar"): ("primary", "The current Arabic has the wrong initial hamza; إجراءات is the standard spelling for this action heading.", "high"),
    ("Actions", "zh-Hans"): ("blind", "Callers use this string for row-action columns and health actions; 操作 is the established UI term for operations, while 动作 suggests physical actions.", "high"),
    ("Actions", "zh-Hant"): ("blind", "Callers use this string for row-action columns and health actions; 操作 is the established UI term for operations, while 動作 suggests physical actions.", "high"),
    ("AddAnotherDownloadClient", "de"): ("primary", "The Quickstart caller selects this label only when a download client already exists, so the German must retain ‘another’.", "high"),
    ("AddAnotherDownloadClient", "ko"): ("blind", "The Quickstart caller selects this label only when a download client already exists; 하나 더 explicitly says to add one more.", "high"),
    ("AddAnotherDownloadClient", "vi"): ("primary", "The Quickstart caller selects this label only when a download client already exists; the target retains ‘another’ and uses a natural app term.", "moderate"),
    ("AddAuthorAudiobookRootFolderHelpText", "es"): ("blind", "Carpeta raíz is the natural Spanish construction for a root folder; removing de fixes the awkward wording.", "moderate"),
    ("AddAuthorAudiobookRootFolderHelpText", "fr"): ("primary", "The help text describes an audiobook root folder; the target uses natural French for audiobook files and preserves the format literals.", "moderate"),
    ("AddAuthorAudiobookRootFolderHelpText", "id"): ("primary", "The current Indonesian says audio files generally and drops audiobook; buku audio restores the source distinction while preserving the formats.", "moderate"),
    ("AddAuthorEbookRootFolderHelpText", "es"): ("blind", "Carpeta raíz is the natural Spanish construction, and libros electrónicos translates ebook instead of leaving it in English.", "moderate"),
    ("AddAuthorEbookRootFolderHelpText", "fr"): ("primary", "The help text describes eBook files; the target uses natural French for electronic books and preserves the format literals.", "moderate"),
    ("AddAuthorEbookRootFolderHelpText", "id"): ("primary", "The current Indonesian leaves ebook in English; buku elektronik supplies a localized term and the target preserves all format literals.", "moderate"),
    ("AddAuthorUsingExistingFolder", "vi"): ("blind", "This helper says the author folder is already present. hiện có is natural for ‘existing’; tồn tại is awkward in this phrase.", "moderate"),
    ("AddCustomFormatNameToFileNames", "hi"): ("blind", "This checkbox refers to files after they have been renamed; बदली गई describes renamed files, unlike the current ongoing-action wording.", "moderate"),
    ("AddCustomFilter", "de"): ("primary", "This button adds a user-defined filter. The current Eigener uses the wrong grammatical case in this object position and is less precise; Benutzerdefinierten is accurate.", "moderate"),
    ("AddCustomFilter", "vi"): ("primary", "tùy chỉnh means custom; tự chọn means self-selected and changes the filter meaning.", "moderate"),
    ("AddDownloadClient", "vi"): ("primary", "This is a button to add a download-client application; the current ứng dụng khách tải xuống is a literal, awkward calque, while ứng dụng tải xuống is natural software wording.", "moderate"),
}

HOLD_KEYS = {
    "AddAuthorMonitorNewAudiobooksHelpText",
    "AddAuthorMonitorNewEbooksHelpText",
    "AddAuthorWhichAudiobooksToMonitor",
    "AddAuthorWhichEbooksToMonitor",
}


def write_summary(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    candidates_with_hash = rows(PRIMARY / "candidate-free-cells.jsonl")
    primary_with_hash = rows(PRIMARY / "primary-review-cells.jsonl")
    blind_with_hash = rows(BLIND / "blind-review-ledger.jsonl")
    reviewer_with_hash = rows(REVIEWER_A)
    candidate = {key(r): (r, h) for r, h in candidates_with_hash}
    primary = {key(r): (r, h) for r, h in primary_with_hash}
    blind = {key(r): (r, h) for r, h in blind_with_hash}
    reviewer = {key(r): (r, h) for r, h in reviewer_with_hash}
    if not (len(candidate) == len(primary) == len(blind) == 600):
        raise SystemExit("Expected 600 unique candidate, primary, and blind rows")
    if len(reviewer) != 300:
        raise SystemExit("Expected 300 candidate-free reviewer rows")
    if set(candidate) != set(primary) or set(candidate) != set(blind):
        raise SystemExit("Input cell sets do not match")
    if set(reviewer) != {k for k, (r, _) in candidate.items() if r["sourceOrdinal"] < 25}:
        raise SystemExit("Independent reviewer coverage is not exactly ordinals 0–24")
    if set(SPECS) & HOLD_KEYS:
        raise SystemExit("A held key must not have a selected target")

    ledger = []
    selected = []
    holds = []
    counters = Counter()
    for ident, (c, c_hash) in sorted(candidate.items(), key=lambda item: (item[1][0]["sourceOrdinal"], item[0][1])):
        p, p_hash = primary[ident]
        b, b_hash = blind[ident]
        r, r_hash = reviewer[ident] if ident in reviewer else (None, None)
        if p["candidateFreeRowSha256"] != c_hash:
            raise SystemExit(f"Primary/candidate row link mismatch: {ident}")
        if p["currentTargetSha256"] != c["currentTargetSha256"] or b["currentTargetSha256"] != c["currentTargetSha256"]:
            raise SystemExit(f"Current translation hash mismatch: {ident}")
        if p["callerContextSha256"] != c["callerContextSha256"] or b["callerContextSha256"] != c["callerContextSha256"]:
            raise SystemExit(f"Caller context hash mismatch: {ident}")
        if c["sourceTextSha256"] != sha_text(c["sourceText"]) or c["currentTargetSha256"] != sha_text(c["currentTarget"]):
            raise SystemExit(f"Candidate source/current text hash mismatch: {ident}")
        if r and (r["exactHead"] != HEAD or r["exactTree"] != TREE or r["currentTargetSha256"] != c["currentTargetSha256"]):
            raise SystemExit(f"Independent reviewer pin/current mismatch: {ident}")

        is_hold = c["sourceKey"] in HOLD_KEYS
        spec = SPECS.get(ident)
        if is_hold:
            if c["callerReferenceCount"] != 0:
                raise SystemExit(f"Unexpected caller evidence for held key: {ident}")
            final_disp = "hold"
            selected_text = None
            selected_hash = None
            cross_reason = "No exact frontend caller context is supplied for this key. The UI role and relationship are not grounded well enough to recommend wording; hold without proposed text."
            cross_confidence = "low"
        elif spec:
            proposal_source, cross_reason, cross_confidence = spec
            if proposal_source == "primary":
                selected_text = p["finalReviewedTarget"]
            else:
                if b["disposition"] != "correct" or not b["proposedTarget"]:
                    raise SystemExit(f"Chosen blind proposal missing: {ident}")
                selected_text = b["proposedTarget"]
            if not selected_text or selected_text == c["currentTarget"]:
                raise SystemExit(f"Selected proposal is empty or unchanged: {ident}")
            final_disp = "revise-current"
            selected_hash = sha_text(selected_text)
            if {m: selected_text.count(m) for m in c["sourcePlaceholders"]} != c["sourcePlaceholders"]:
                raise SystemExit(f"Selected proposal placeholder mismatch: {ident}")
            missing = [lit for lit in c["protectedLiterals"] if lit not in selected_text]
            if missing:
                raise SystemExit(f"Selected proposal misses protected literals {missing}: {ident}")
            selected.append({
                "batch": c["batch"], "sourceOrdinal": c["sourceOrdinal"], "sourceKey": c["sourceKey"], "locale": c["locale"],
                "sourceText": c["sourceText"], "sourceTextSha256": c["sourceTextSha256"],
                "currentTarget": c["currentTarget"], "currentTargetSha256": c["currentTargetSha256"],
                "selectedTarget": selected_text, "selectedTargetSha256": selected_hash,
                "selectedFrom": proposal_source,
                "primaryDisposition": p["primaryDisposition"],
                "primaryProposalSha256": sha_text(p["finalReviewedTarget"]) if p["primaryDisposition"] == "revise-current" else None,
                "blindDisposition": b["disposition"],
                "blindProposalSha256": sha_text(b["proposedTarget"]) if b.get("proposedTarget") else None,
                "sourceFile": c["sourceFile"], "sourceFileSha256": c["sourceFileSha256"], "sourceFileGitBlob": c["sourceFileGitBlob"],
                "targetFile": c["targetFile"], "targetFileSha256": c["targetFileSha256"], "targetFileGitBlob": c["targetFileGitBlob"],
                "sourcePlaceholders": c["sourcePlaceholders"], "protectedLiterals": c["protectedLiterals"],
                "callerContextSha256": c["callerContextSha256"], "callerReferenceCount": c["callerReferenceCount"], "callerRefs": c["callerRefs"],
                "crossRationale": cross_reason, "crossConfidence": cross_confidence,
                "nativeSpeakerApproval": False,
            })
        else:
            selected_text = None
            selected_hash = None
            final_disp = "accept-current"
            cross_confidence = r["confidence"] if r else "moderate"
            if ident == ("AddCustomFilter", "es"):
                cross_reason = "The current Spanish accurately translates the button. Añadir is a valid alternative to Agregar, and the supplied context does not establish a required verb style; this is preference rather than a supported correction."
            elif c["callerReferenceCount"] == 0:
                cross_reason = "No exact caller context is available, but neither reviewed packet supports a correction to this protected literal. Keep the existing value unchanged pending caller context."
            elif r and r["disposition"] == "accept-current":
                cross_reason = "The current target preserves the source meaning and supplied caller use; the candidate-free reviewer found no clear translation or literal defect."
            else:
                cross_reason = "The current target preserves the source meaning and supplied caller use; no primary or blind proposal provides a supported correction for this cell."
        counters[final_disp] += 1

        row = {
            "batch": c["batch"], "exactHead": HEAD, "exactTree": TREE,
            "sourceOrdinal": c["sourceOrdinal"], "sourceKey": c["sourceKey"], "locale": c["locale"],
            "sourceTextSha256": c["sourceTextSha256"], "currentTargetSha256": c["currentTargetSha256"],
            "sourceFile": c["sourceFile"], "sourceFileSha256": c["sourceFileSha256"], "sourceFileGitBlob": c["sourceFileGitBlob"],
            "targetFile": c["targetFile"], "targetFileSha256": c["targetFileSha256"], "targetFileGitBlob": c["targetFileGitBlob"],
            "callerContextSha256": c["callerContextSha256"], "callerReferenceCount": c["callerReferenceCount"],
            "callerRefs": [] if is_hold else c["callerRefs"],
            "candidateFreeInputRowSha256": c_hash, "primaryInputRowSha256": p_hash, "blindInputRowSha256": b_hash,
            "primaryDisposition": p["primaryDisposition"],
            "primaryProposalSha256": sha_text(p["finalReviewedTarget"]) if p["primaryDisposition"] == "revise-current" else None,
            "primaryProposalIncluded": (p["primaryDisposition"] == "revise-current" and not is_hold),
            "primaryRationale": p.get("decisionRationale"),
            "blindDisposition": b["disposition"],
            "blindProposalSha256": sha_text(b["proposedTarget"]) if b.get("proposedTarget") else None,
            "blindProposalIncluded": bool(b.get("proposedTarget")) and not is_hold,
            "blindRationale": b.get("rationale"),
            "independentReviewerA": None if not r else {
                "inputRowSha256": r_hash, "disposition": r["disposition"], "confidence": r["confidence"], "rationale": r["rationale"]
            },
            "crossDisposition": final_disp,
            "selectedTargetSha256": selected_hash,
            "crossRationale": cross_reason,
            "crossConfidence": cross_confidence,
            "nativeSpeakerApproval": False,
        }
        if not is_hold:
            row["sourceText"] = c["sourceText"]
            row["currentTarget"] = c["currentTarget"]
        ledger.append(row)
        if is_hold:
            holds.append({
                "batch": c["batch"], "exactHead": HEAD, "exactTree": TREE,
                "sourceOrdinal": c["sourceOrdinal"], "sourceKey": c["sourceKey"], "locale": c["locale"],
                "sourceTextSha256": c["sourceTextSha256"], "currentTargetSha256": c["currentTargetSha256"],
                "sourceFile": c["sourceFile"], "sourceFileSha256": c["sourceFileSha256"],
                "targetFile": c["targetFile"], "targetFileSha256": c["targetFileSha256"],
                "callerContextSha256": c["callerContextSha256"], "callerReferenceCount": c["callerReferenceCount"],
                "primaryDisposition": p["primaryDisposition"],
                "primaryProposalSha256": sha_text(p["finalReviewedTarget"]) if p["primaryDisposition"] == "revise-current" else None,
                "blindDisposition": b["disposition"],
                "holdReason": cross_reason,
                "proposedTarget": None,
            })

    if set(SPECS) != {key(r) for r in selected}:
        missing = set(SPECS) - {key(r) for r in selected}
        extra = {key(r) for r in selected} - set(SPECS)
        raise SystemExit(f"Selected proposal set mismatch; missing={missing}, extra={extra}")
    if len(holds) != 48 or len(selected) != 38 or counters != Counter({"accept-current": 514, "revise-current": 38, "hold": 48}):
        raise SystemExit(f"Unexpected result counts: {counters}, selected={len(selected)}, holds={len(holds)}")
    dump_jsonl(ROOT / "cross-ledger.jsonl", ledger)
    dump_jsonl(ROOT / "selected-proposals.jsonl", selected)
    dump_jsonl(ROOT / "cross-audit-holds.jsonl", holds)

    summary = {
        "objective": "Independent third-party cross-audit of ChaptarrNG PR #190 W0–W49 localization cells",
        "exactHead": HEAD, "exactTree": TREE,
        "cellsReviewed": 600,
        "primaryDispositionCounts": dict(Counter(r["primaryDisposition"] for r, _ in primary_with_hash)),
        "blindDispositionCounts": dict(Counter(r["disposition"] for r, _ in blind_with_hash)),
        "primaryBlindProposalOverlap": len({k for k, (r, _) in primary.items() if r["primaryDisposition"] == "revise-current"} & {k for k, (r, _) in blind.items() if r["disposition"] == "correct"}),
        "crossDispositionCounts": dict(counters),
        "selectedProposalCount": len(selected),
        "textFreeHoldCount": len(holds),
        "primaryProposalsWithheldForNoCallerContext": sum(1 for h in holds if h["primaryDisposition"] == "revise-current"),
        "candidateFreeIndependentReviewer": {"coveredOrdinals": "0–24", "cells": len(reviewer), "dispositionCounts": dict(Counter(r["disposition"] for r, _ in reviewer_with_hash)), "confidenceCounts": dict(Counter(r["confidence"] for r, _ in reviewer_with_hash))},
        "inputPacketChecksumsVerified": True,
        "exactSourceCheckoutVerifiedSeparately": True,
        "nativeSpeakerApproval": False,
        "repoOrPrModified": False,
        "notes": [
            "The four author-monitor keys lack exact frontend caller context. Their 48 locale cells are held with no wording proposal, including 11 cells with primary proposals.",
            "Spanish AddCustomFilter remains at its current valid wording: Añadir versus Agregar is a style choice, not an evidenced defect.",
            "Selected revisions preserve source placeholders and listed protected literals. Confidence is the cross-reviewer's assessment, not native-speaker approval."
        ],
    }
    write_summary(ROOT / "summary.json", summary)
    return summary


if __name__ == "__main__":
    summary = main()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
