#!/usr/bin/env python3
"""Portable structural verifier for the ChaptarrNG W50-W99 blind review packet."""
from __future__ import annotations
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'input'
DISPOSITIONS = ('accept-current', 'propose-correction', 'hold')
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def placeholders(text: str):
    return dict(sorted(collections.Counter(PLACEHOLDER_RE.findall(text)).items()))

def require(condition: bool, message: str):
    if not condition:
        raise SystemExit('FAIL: ' + message)

# Check every source packet file named by its checksum manifest, using only this copied input.
for line in (INPUT / 'candidate-free-SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    expected, rel = line.split(None, 1)
    rel = rel.lstrip('* ')
    path = (INPUT / rel).resolve()
    require(path.is_relative_to(INPUT.resolve()), 'input checksum path escapes copied packet')
    require(path.is_file() and digest(path.read_bytes()) == expected, 'input checksum mismatch: ' + rel)

attestation = read_json(INPUT / 'PR-attestation-before.json')
selection = read_json(INPUT / 'source-selection.json')
manifest = read_json(INPUT / 'candidate-free-manifest.json')
require(attestation['state'] == 'OPEN' and attestation['isDraft'] is True, 'PR state/draft pin')
require(attestation['exactHead'] == 'daa578eaa0d1c252e969d1f5891a364b13d50ec0', 'attested head')
require(attestation['exactTree'] == 'e0b306dc20596ad7004bdfb9ac2cc0a3021726c7', 'attested tree')
require(selection['exactHead'] == attestation['exactHead'] and selection['exactTree'] == attestation['exactTree'], 'selection pin')
require(manifest['exactHead'] == attestation['exactHead'] and manifest['exactTree'] == attestation['exactTree'], 'candidate-free manifest pin')
source_rows = read_jsonl(INPUT / 'candidate-free-cells.jsonl')
ledger = read_jsonl(ROOT / 'blind-review-ledger.jsonl')
proposals = read_jsonl(ROOT / 'proposals.jsonl')
holds = read_jsonl(ROOT / 'holds.jsonl')
summary = read_json(ROOT / 'summary.json')
require(len(source_rows) == 600 and len(ledger) == 600, '600-cell coverage')
require(len(selection['keys']) == 50 and len(selection['targetLocales']) == 12, 'source/locale selection size')
require(len({(r['sourceKey'], r['locale']) for r in source_rows}) == 600, 'candidate-free cell identities')
require([(r['sourceKey'], r['locale']) for r in ledger] == [(r['sourceKey'], r['locale']) for r in source_rows], 'ledger ordering/identity')
source_map = {(r['sourceKey'], r['locale']): r for r in source_rows}
counts = collections.Counter()
proposal_ids = []
hold_ids = []
for r in ledger:
    ident = (r['sourceKey'], r['locale'])
    src = source_map[ident]
    require(r['sourceSha256'] == src['sourceTextSha256'], 'source hash ' + repr(ident))
    require(r['currentSha256'] == src['currentTargetSha256'], 'current hash ' + repr(ident))
    require(r['callerContextSha256'] == src['callerContextSha256'], 'caller hash ' + repr(ident))
    require(r['callerReferenceCount'] == src['callerReferenceCount'], 'caller count ' + repr(ident))
    disposition = r['disposition']
    require(disposition in DISPOSITIONS, 'unknown disposition ' + repr(ident))
    counts[disposition] += 1
    if disposition == 'hold':
        hold_ids.append(ident)
        forbidden = {'sourceText', 'currentTarget', 'selectedTarget', 'proposal', 'proposedTarget', 'finalTarget'}
        require(not (forbidden & r.keys()), 'hold must be text-free ' + repr(ident))
        require(bool(r.get('holdReason')), 'hold missing reason ' + repr(ident))
        continue
    require(r.get('sourceText') == src['sourceText'], 'source text ' + repr(ident))
    require(r.get('currentTarget') == src['currentTarget'], 'current text ' + repr(ident))
    target = r.get('selectedTarget')
    require(isinstance(target, str), 'missing selected target ' + repr(ident))
    require(r.get('selectedTargetSha256') == digest(target.encode('utf-8')), 'selected target hash ' + repr(ident))
    require(placeholders(target) == src['sourcePlaceholders'], 'placeholder signature ' + repr(ident))
    require(all(literal in target for literal in src['protectedLiterals']), 'protected literal ' + repr(ident))
    if disposition == 'accept-current':
        require(target == src['currentTarget'], 'accept-current changed wording ' + repr(ident))
        require(r.get('rationale'), 'accept rationale ' + repr(ident))
    else:
        require(target != src['currentTarget'], 'proposal has no wording change ' + repr(ident))
        require(r.get('rationale'), 'proposal rationale ' + repr(ident))
        proposal_ids.append(ident)
require(counts == {'accept-current': 518, 'propose-correction': 58, 'hold': 24}, 'disposition counts')
require([(r['sourceKey'], r['locale']) for r in proposals] == proposal_ids, 'proposal file subset/order')
require([(r['sourceKey'], r['locale']) for r in holds] == hold_ids, 'hold file subset/order')
require(summary['exactHead'] == attestation['exactHead'] and summary['exactTree'] == attestation['exactTree'], 'summary pins')
require(summary['dispositionCounts'] == {d: counts[d] for d in DISPOSITIONS}, 'summary disposition counts')
require(summary['cellCount'] == 600 and summary['sourceKeys'] == 50, 'summary coverage')
require(summary['nativeSpeakerReview'] is False and summary['browserReview'] is False, 'review scope claims')
# Verify all files named by the output checksum manifest. The manifest intentionally does not hash itself.
for line in (ROOT / 'OUTPUT-SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    expected, rel = line.split(None, 1)
    rel = rel.lstrip('* ')
    path = (ROOT / rel).resolve()
    require(path.is_relative_to(ROOT.resolve()), 'output checksum path escapes packet')
    require(path.is_file() and digest(path.read_bytes()) == expected, 'output checksum mismatch: ' + rel)
print(json.dumps({'result':'PASS','exactHead':attestation['exactHead'],'exactTree':attestation['exactTree'],'cells':len(ledger),'counts':{d:counts[d] for d in DISPOSITIONS},'sourceInputChecksums':'PASS','outputChecksums':'PASS','textFreeHolds':'PASS','placeholdersAndProtectedLiterals':'PASS'},sort_keys=True))
