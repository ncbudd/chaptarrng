#!/usr/bin/env python3
"""Portable verifier for this blind-review packet. Uses only files under this directory."""
from __future__ import annotations
import collections
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
INPUT = ROOT / "input"

def fail(message: str) -> None:
    print("FAIL:", message)
    raise SystemExit(1)

def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_jsonl(path: pathlib.Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def verify_sums(directory: pathlib.Path, manifest_name: str) -> set[str]:
    manifest_path = directory / manifest_name
    if not manifest_path.is_file():
        fail(f"missing {manifest_path.relative_to(ROOT)}")
    listed = set()
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        rel = rel.strip()
        rel_path = pathlib.PurePosixPath(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            fail(f"unsafe checksum path: {rel}")
        path = directory.joinpath(*rel_path.parts)
        if not path.is_file():
            fail(f"missing checksummed file: {rel}")
        if sha(path) != digest:
            fail(f"checksum mismatch: {rel}")
        listed.add(rel)
    return listed

input_listed = verify_sums(INPUT, "SHA256SUMS.txt")
if len(input_listed) != 6:
    fail(f"expected 6 input-file checksum entries, found {len(input_listed)}")

packet = json.loads((INPUT / "candidate-free-manifest.json").read_text(encoding="utf-8"))
verification = json.loads((INPUT / "candidate-free-verification.json").read_text(encoding="utf-8"))
for name, field in [
    ("candidate-free-cells.jsonl", "candidateFreeCellsSha256"),
    ("caller-context.jsonl", "callerContextSha256"),
    ("source-selection.json", "sourceSelectionSha256"),
]:
    if sha(INPUT / name) != packet[field]:
        fail(f"candidate-free manifest hash mismatch: {name}")
if (packet.get("exactHead"), packet.get("exactTree")) != (
    "7f5d99e24b054cf1437d135328c3dee565e6b318",
    "d39f2fe8cf91a39653679980c0832c5ca400a114",
):
    fail("pin mismatch")
if verification.get("result") != "PASS" or not verification.get("candidateFieldsAbsent"):
    fail("candidate-free verification record is not PASS")

cells = read_jsonl(INPUT / "candidate-free-cells.jsonl")
ledger = read_jsonl(ROOT / "blind-review-ledger.jsonl")
proposals = read_jsonl(ROOT / "blind-review-proposals.jsonl")
holds = read_jsonl(ROOT / "blind-review-holds.jsonl")
expected_locales = {"ar","de","es","fr","hi","id","ja","ko","pt-BR","vi","zh-Hans","zh-Hant"}
if len(cells) != 600 or len(ledger) != 600:
    fail("expected 600 input cells and 600 ledger rows")
if len({(r["sourceKey"],r["locale"]) for r in cells}) != 600:
    fail("input key/locale pairs are not unique")
if len({(r["sourceKey"],r["locale"]) for r in ledger}) != 600:
    fail("ledger key/locale pairs are not unique")
if len({r["sourceKey"] for r in cells}) != 50:
    fail("expected 50 keys")
if {r["locale"] for r in cells} != expected_locales:
    fail("unexpected locale set")
if not all(r.get("currentPlaceholders") == r.get("sourcePlaceholders") for r in cells):
    fail("input placeholder mismatch")
if not all(r.get("currentProtectedLiteralsPresent") is True for r in cells):
    fail("input protected literal missing")

cell_map={(r["sourceKey"],r["locale"]):r for r in cells}
for row in ledger:
    key=(row["sourceKey"],row["locale"])
    source=cell_map.get(key)
    if source is None:
        fail(f"ledger row not in input: {key}")
    for field in ("sourceText","currentTarget","sourcePlaceholders","currentPlaceholders","protectedLiterals"):
        if row.get(field) != source.get(field):
            fail(f"ledger disagrees with input for {key}: {field}")
    if row.get("disposition") not in {"accept","correct","hold"}:
        fail(f"unknown disposition for {key}")
    if not row.get("rationale"):
        fail(f"missing rationale for {key}")
    if row.get("disposition") == "correct":
        proposed=row.get("proposedTarget")
        if not isinstance(proposed,str) or not proposed:
            fail(f"missing proposed text for correction {key}")
        counts=collections.Counter(re.findall(r"\{[^{}]+\}",proposed))
        expected=collections.Counter(row["sourcePlaceholders"])
        if counts != expected:
            fail(f"proposal placeholder mismatch for {key}: {counts} != {expected}")
        if not all(literal in proposed for literal in row["protectedLiterals"]):
            fail(f"proposal changed protected literal for {key}")
    elif row.get("proposedTarget") is not None:
        fail(f"non-correction has proposed text for {key}")

counts=collections.Counter(r["disposition"] for r in ledger)
if counts != {"accept":525,"correct":27,"hold":48}:
    fail(f"unexpected disposition counts: {dict(counts)}")
if len(proposals) != 27 or any(r["disposition"] != "correct" for r in proposals):
    fail("proposal extract does not contain the 27 correction rows")
if len(holds) != 48 or any(r["disposition"] != "hold" or r.get("proposedTarget") is not None for r in holds):
    fail("hold extract does not contain 48 text-free holds")
expected_hold_keys={
    "AddAuthorMonitorNewAudiobooksHelpText",
    "AddAuthorMonitorNewEbooksHelpText",
    "AddAuthorWhichAudiobooksToMonitor",
    "AddAuthorWhichEbooksToMonitor",
}
if {r["sourceKey"] for r in holds} != expected_hold_keys:
    fail("hold key set mismatch")
output_listed=verify_sums(ROOT,"SHA256SUMS.txt")
expected_output={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p != ROOT / "SHA256SUMS.txt"}
if output_listed != expected_output:
    fail("output checksum manifest does not cover exactly all other output files")
print("PASS: input checksums, packet pins, 600-cell ledger, dispositions, proposals, holds, placeholders, protected literals, and output checksums")
print(json.dumps({"cells":len(ledger),"dispositions":dict(counts),"inputFiles":len(input_listed),"outputFiles":len(output_listed)},sort_keys=True))
