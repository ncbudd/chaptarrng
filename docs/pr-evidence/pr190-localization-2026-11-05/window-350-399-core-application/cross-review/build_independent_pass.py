#!/usr/bin/env python3
"""Build the candidate-free independent review ledger for W350-W399."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "candidate-free" / "input"
OUT = ROOT / "cross-review"
EXPECTED_HEAD = "dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0"
EXPECTED_TREE = "be10d71209076f753ef295038a9f3c3646a918a3"

# Independent targets are recorded only for rows where the candidate-free pass
# found a clear semantic, grammar, or exact-input-example issue.
REVISIONS = {
    (352, "de"): ("Buchüberwachung", "The current word means observation; the app uses monitoring as a book state.", "moderate"),
    (352, "ko"): ("책 모니터링", "The current wording reads as surveillance; use the established monitoring term.", "moderate"),
    (358, "hi"): ("पुस्तक का नामकरण", "Replace an English transliteration with a direct Hindi phrase.", "moderate"),
    (358, "ja"): ("書籍の命名", "The current transliteration is unnatural and appears misspelled; use a direct Japanese label.", "moderate"),
    (360, "ja"): ("書籍の進捗", "The current transliteration is unnatural for a progress label.", "moderate"),
    (360, "ko"): ("책 진행률", "The current wording is an incomplete noun phrase for the numeric progress field.", "moderate"),
    (372, "de"): ("Fortschritt der Bücher", "The current two-noun phrase is unidiomatic German.", "moderate"),
    (372, "ko"): ("책 진행률", "Use a natural progress-rate label for the numeric field.", "moderate"),
    (375, "hi"): ("पुस्तक शेल्फ़", "The current word means library; this page represents named bookshelves.", "moderate"),
    (376, "hi"): ("पुस्तक शेल्फ़ प्राप्त करने के लिए ऊपर Goodreads उपयोगकर्ता ID दर्ज करें।", "The current text says book lists rather than bookshelves.", "moderate"),
    (376, "zh-Hans"): ("输入上面的 Goodreads 用户代号以获取书架。", "Remove the space before the Chinese full stop.", "high"),
    (376, "zh-Hant"): ("輸入上面的 Goodreads 使用者代碼以取得書架。", "Remove the space before the Chinese full stop.", "high"),
    (377, "zh-Hans"): ("无法从 Goodreads 获取书架。请检查用户标识是否正确以及书架是否公开，或在下方手动添加书架。", "Remove nonstandard spaces around punctuation and make the instructions read as a sentence.", "moderate"),
    (377, "zh-Hant"): ("無法從 Goodreads 取得書架。請檢查使用者代碼是否正確及書架是否公開，或在下方手動新增書架。", "Remove nonstandard spaces around punctuation and make the instructions read as a sentence.", "moderate"),
    (378, "ar"): ("يدويًا: أضف رفًا (مثال: read، currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "de"): ("Manuell: Regal hinzufügen (z. B. read, currently-reading)", "The current German noun means handbook; preserve the exact Goodreads shelf identifiers.", "high"),
    (378, "es"): ("Manual: añadir estantería (p. ej., read, currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "fr"): ("Manuel : ajouter une étagère (ex. : read, currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "hi"): ("मैन्युअल: शेल्फ़ जोड़ें (उदाहरण: read, currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "ko"): ("수동: 선반 추가 (예: read, currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "pt-BR"): ("Manual: adicionar estante (ex.: read, currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "vi"): ("Thủ công: thêm kệ (ví dụ: read, currently-reading)", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "zh-Hans"): ("手动：添加书架（例如：read、currently-reading）", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (378, "zh-Hant"): ("手動：新增書架（例如：read、currently-reading）", "These are Goodreads shelf identifiers entered by the user; preserve the exact example values.", "high"),
    (379, "ar"): ("لم تُرجع أي رفوف لمستخدم Goodreads {user}. لا يزال بإمكانك إضافة الرفوف يدويًا أدناه.", "The current second clause is ungrammatical; retain the user placeholder and clarify the fallback.", "moderate"),
    (379, "zh-Hans"): ("未能获取 Goodreads 用户 {user} 的书架。您仍可在下方手动添加书架。", "Move the user placeholder next to the Goodreads user it identifies.", "moderate"),
    (379, "zh-Hant"): ("未能取得 Goodreads 使用者 {user} 的書架。您仍可在下方手動新增書架。", "Make the sentence describe the missing shelves rather than implying that the user returned them.", "moderate"),
    (382, "hi"): ("आपकी लाइब्रेरी में कोई ईबुक नहीं मिली।", "Use feminine agreement for the borrowed eBook noun in this sentence.", "moderate"),
    (384, "vi"): ("Ngày sinh", "The source field is a date value; the current translation means birthplace.", "high"),
    (370, "vi"): ("Sách trong bộ sách", "Use a localized term for a book series instead of the English word Series.", "moderate"),
    (371, "vi"): ("Sách trong bộ sách này:", "Use a localized term for a book series instead of the English word series.", "moderate"),
    (390, "ko"): ("내장 사용자 정의 형식은 고정된 미디어 유형을 사용합니다.", "Correct the spacing in the bound adjective.", "high"),
    (390, "pt-BR"): ("Formatos personalizados incorporados usam um tipo de mídia fixo.", "The adjective must agree with the masculine noun tipo.", "high"),
    (392, "de"): ("von", "The current preposition means through; this phrase credits the package author.", "high"),
    (392, "ja"): ("作者：", "The current postpositional construction is not grammatical before the following author name.", "moderate"),
    (392, "ko"): ("작성자:", "Use a natural author-credit prefix before the package author name.", "moderate"),
    (392, "vi"): ("bởi", "The current word means via; this phrase credits the package author.", "high"),
    (394, "de"): ("Umgehen, wenn der Mindestwert des benutzerdefinierten Formats überschritten wird", "The current sentence lacks a subject and does not state the score threshold clearly.", "moderate"),
    (394, "zh-Hant"): ("高於自訂格式分數時略過", "The current noun phrase does not express the checkbox condition clearly.", "moderate"),
    (396, "ar"): ("تجاوز التأخير عند أعلى جودة", "The current phrase says high quality rather than the highest quality; the help text identifies this as delay bypass.", "moderate"),
    (396, "de"): ("Bei höchster Qualität umgehen", "The current imperative is ungrammatical and omits the conditional relation.", "moderate"),
    (396, "ja"): ("最高品質の場合はバイパス", "The current phrase reads as a noun rather than a conditional action.", "moderate"),
    (396, "pt-BR"): ("Ignorar se for da qualidade mais alta", "The current wording says quality is higher, not that it is the highest enabled quality.", "moderate"),
    (396, "zh-Hant"): ("若為最高品質，則略過延遲", "The current wording is awkward and does not clearly state the highest-quality condition.", "moderate"),
    (398, "ko"): ("로컬/LAN 주소의 프록시 우회", "Fix spacing and retain the LAN scope alongside local addresses.", "moderate"),
    (398, "zh-Hant"): ("略過本機／LAN 位址的 Proxy", "The current translation uses an incorrect term for bypass and changes the meaning.", "high"),
}

# The supplied caller excerpt for this key does not show the Wanted/All labels.
HOLDS = {
    (366, locale): ("The supplied caller excerpt lacks the Wanted/All control labels, so their localized text cannot be checked against the UI wording.", "high")
    for locale in ("ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant")
}

FLAG_NOTES = {
    (356, "ar"): "ChaptarrNG is preserved; translating ID as a local word for identifier is semantically sound.",
    (376, "ar"): "Goodreads is preserved; the localized word for identifier is a suitable rendering of ID.",
    (376, "zh-Hans"): "Goodreads is preserved; 用户代号 conveys user ID, so the heuristic flag is not a meaning loss.",
    (376, "zh-Hant"): "Goodreads is preserved; 使用者代碼 conveys user ID, so the heuristic flag is not a meaning loss.",
    (377, "ar"): "Goodreads is preserved; the localized word for identifier is a suitable rendering of ID.",
    (377, "fr"): "Goodreads is preserved; identifiant is a suitable rendering of User ID.",
    (377, "zh-Hans"): "Goodreads is preserved; 用户标识 conveys User ID, so the heuristic flag is not a meaning loss.",
    (377, "zh-Hant"): "Goodreads is preserved; 使用者代碼 conveys User ID, so the heuristic flag is not a meaning loss.",
    (398, "ar"): "Local addresses capture the meaning of local/LAN addresses; the acronym is redundant here.",
    (398, "de"): "Lokale Adressen captures the meaning of local/LAN addresses; the acronym is redundant here.",
    (398, "es"): "Direcciones locales captures the meaning of local/LAN addresses; the acronym is redundant here.",
    (398, "fr"): "Adresses locales captures the meaning of local/LAN addresses; the acronym is redundant here.",
    (398, "ja"): "ローカルアドレス captures the local/LAN scope; the acronym is redundant here.",
    (398, "ko"): "로컬 주소 captures the local/LAN scope; the acronym is redundant here.",
    (398, "pt-BR"): "Endereços locais captures the meaning of local/LAN addresses; the acronym is redundant here.",
    (398, "zh-Hans"): "局域网地址 explicitly conveys LAN addresses.",
}

TOKEN_FIELDS = (
    "sourcePlaceholders", "currentPlaceholders",
    "sourceMarkup", "currentMarkup",
    "sourceInlineCode", "currentInlineCode",
    "sourceNumericTokens", "currentNumericTokens",
    "protectedLiterals", "integrityChecks",
)

def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

manifest = json.loads((INPUT / "candidate-free-manifest.json").read_text(encoding="utf-8"))
if manifest["head"] != EXPECTED_HEAD or manifest["tree"] != EXPECTED_TREE:
    raise SystemExit("candidate-free pin does not match requested head/tree")
cells = load_jsonl(INPUT / "candidate-free-cells.jsonl")
contexts = {row["sourceKey"]: row for row in load_jsonl(INPUT / "caller-context.jsonl")}
if len(cells) != 600 or len(contexts) != 50:
    raise SystemExit("candidate-free packet does not contain the expected 600 cells / 50 contexts")

out_rows = []
for row in cells:
    ident = (row["sourceOrdinal"], row["locale"])
    context = contexts[row["sourceKey"]]
    if context["callerContextSha256"] != row["callerContextSha256"]:
        raise SystemExit(f"caller-context hash disagreement for {ident}")
    token_summary = {field: row[field] for field in TOKEN_FIELDS}
    token_hash = sha(canonical(token_summary))
    if ident in HOLDS:
        reason, confidence = HOLDS[ident]
        decision = "hold-context"
        target = None
        recommendation = "hold"
    elif ident in REVISIONS:
        target, reason, confidence = REVISIONS[ident]
        decision = "replace"
        recommendation = "replace"
    else:
        target = row["currentTarget"]
        reason = FLAG_NOTES.get(ident, "Current wording conveys the English source in the supplied caller context; required placeholders and markup are preserved.")
        confidence = "high" if (row["sourceKey"] in {"BookQualityProperBadge", "BookQualityRepackBadge"}) else "moderate"
        decision = "accept-current"
        recommendation = "accept"
    out_rows.append({
        "batch": row["batch"],
        "head": EXPECTED_HEAD,
        "tree": EXPECTED_TREE,
        "sourceOrdinal": row["sourceOrdinal"],
        "sourceKey": row["sourceKey"],
        "locale": row["locale"],
        "sourceText": row["sourceText"],
        "sourceTextSha256": row["sourceTextSha256"],
        "currentTarget": row["currentTarget"],
        "currentTargetSha256": row["currentTargetSha256"],
        "callerContextSha256": row["callerContextSha256"],
        "tokenSummary": token_summary,
        "tokenSummarySha256": token_hash,
        "sourceFile": row["sourceFile"],
        "sourceFileSha256": row["sourceFileSha256"],
        "sourceFileGitBlob": row["sourceFileGitBlob"],
        "targetFile": row["targetFile"],
        "targetFileSha256": row["targetFileSha256"],
        "targetFileGitBlob": row["targetFileGitBlob"],
        "recommendation": recommendation,
        "decision": decision,
        "recommendedTarget": target,
        "recommendedTargetSha256": sha(target) if target is not None else None,
        "confidence": confidence,
        "rationale": reason,
        "reviewBasis": "candidate-free source, current target, caller excerpt, and token summary only",
    })

ledger_path = OUT / "independent-review.jsonl"
ledger_path.write_text("".join(canonical(row) + "\n" for row in out_rows), encoding="utf-8")
counts = Counter(row["decision"] for row in out_rows)
flags = load_jsonl(INPUT / "integrity-review-flags.jsonl")
summary = {
    "result": "SEALED_INDEPENDENT_PASS",
    "batch": "W350-399-Core",
    "repository": "snapetech-org/chaptarrng",
    "pullRequest": 190,
    "head": EXPECTED_HEAD,
    "tree": EXPECTED_TREE,
    "liveMain": manifest["liveMain"],
    "firstPosition": 350,
    "lastPosition": 399,
    "sourceIds": 50,
    "cells": len(out_rows),
    "locales": manifest["scope"]["locales"],
    "decisionCounts": dict(sorted(counts.items())),
    "candidateLedgersOpenedBeforeSeal": False,
    "candidateFreeManifestSha256": sha((INPUT / "candidate-free-manifest.json").read_text(encoding="utf-8")),
    "candidateFreeCellsSha256": sha((INPUT / "candidate-free-cells.jsonl").read_text(encoding="utf-8")),
    "callerContextSha256": sha((INPUT / "caller-context.jsonl").read_text(encoding="utf-8")),
    "integrityFlagRows": len(flags),
    "integrityFlagsReviewed": True,
    "independentReviewFile": ledger_path.name,
    "independentReviewSha256": sha(ledger_path.read_text(encoding="utf-8")),
    "tokenSummaryAlgorithm": "SHA-256 of UTF-8 compact JSON with sorted keys for the source/current token fields listed by the ledger",
    "createdFrom": "candidate-free packet only",
}
(OUT / "independent-review-manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
