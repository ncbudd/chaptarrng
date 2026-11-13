#!/usr/bin/env python3
"""Verify the candidate-free inputs and sealed blind-review packet."""
from __future__ import annotations
import collections, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w400-449-20261105/candidate-free/input')
HEAD = '8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7'
TREE = '018e46cd14424204a01be46e13e5b50f9f26ce07'
LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH = re.compile(r'\{[^{}]+\}')
INLINE = re.compile(r'`([^`]+)`')
MARKUP = re.compile(r'<[^>]+>')
NUM = re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def shat(text: str) -> str:
    return sha(text.encode('utf-8'))

def readj(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def readjl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def require(condition, message):
    if not condition:
        raise SystemExit('FAIL: ' + message)

def token_ok(source: str, target: str, protected: list[str]) -> bool:
    return (
        collections.Counter(PH.findall(source)) == collections.Counter(PH.findall(target))
        and INLINE.findall(source) == INLINE.findall(target)
        and MARKUP.findall(source) == MARKUP.findall(target)
        and collections.Counter(NUM.findall(source)) == collections.Counter(NUM.findall(target))
        and all(token in target for token in protected)
    )

def verify_sums(directory: Path, sums_path: Path):
    listed = set()
    for line in sums_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        parts = line.split('  ', 1)
        require(len(parts) == 2, f'malformed checksum line in {sums_path}')
        expected, name = parts
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts, f'unsafe checksum path {name}')
        path = directory / rel
        require(path.is_file(), f'missing checksummed file {name}')
        require(sha(path.read_bytes()) == expected, f'checksum mismatch {name}')
        listed.add(name)
    return listed

# Verify the frozen candidate-free packet directly from its checksum list.
input_sums = INPUT / 'SHA256SUMS.txt'
input_list_sha = sha(input_sums.read_bytes())
require(input_list_sha == 'dc057678d73514d8ad08426a648571472b02ee9969cb0cf67b6c4f998e4a3d4f', 'candidate-free checksum-list pin')
input_listed = verify_sums(INPUT, input_sums)
input_manifest = readj(INPUT / 'candidate-free-manifest.json')
require(input_manifest['candidateFreeOnly'] is True, 'candidate-free-only input')
require(input_manifest['head'] == HEAD and input_manifest['tree'] == TREE, 'candidate-free exact head/tree')
require(input_manifest['scope']['firstPosition'] == 400 and input_manifest['scope']['lastPosition'] == 449, 'candidate-free ordinal scope')
require(input_manifest['scope']['cells'] == 600 and input_manifest['scope']['sourceIds'] == 50, 'candidate-free dimensions')
input_cells = readjl(INPUT / 'candidate-free-cells.jsonl')
require(len(input_cells) == 600, 'candidate-free cell count')

# Verify all output files listed in the sealed checksums, excluding only the checksum file itself.
out_sums = ROOT / 'SHA256SUMS.txt'
output_listed = verify_sums(ROOT, out_sums)
require('SHA256SUMS.txt' not in output_listed, 'checksum file must not checksum itself')
manifest = readj(ROOT / 'manifest.json')
require(manifest['exactHead'] == HEAD and manifest['exactTree'] == TREE, 'review manifest exact head/tree')
require(manifest['candidateFreeInputChecksumListSha256'] == input_list_sha, 'review manifest input pin')
for name, expected in manifest['files'].items():
    path = ROOT / name
    require(path.is_file() and sha(path.read_bytes()) == expected, f'manifest file hash {name}')
    require(name in output_listed, f'manifest file absent from output checksum list {name}')

ledger = readjl(ROOT / 'blind-ledger.jsonl')
proposals = readjl(ROOT / 'proposals.jsonl')
holds = readjl(ROOT / 'holds-hash-only.jsonl')
summary = readj(ROOT / 'summary.json')
require(len(ledger) == 600, 'blind ledger cell count')
require(len(proposals) == 76, 'proposal count')
require(len(holds) == 12, 'hash-only hold count')
require(summary['exactHead'] == HEAD and summary['exactTree'] == TREE, 'summary exact head/tree')
require(summary['candidateFreeInputChecksumListSha256'] == input_list_sha, 'summary input pin')
require(summary['cellsReviewed'] == 600 and summary['sourceIdsReviewed'] == 50, 'summary review dimensions')
require(summary['nativeSpeakerReview'] is False and summary['browserReview'] is False, 'review limitations')
require(summary['repoEdits'] is False and summary['prEdits'] is False and summary['workflowEdits'] is False, 'edit scope')
require(summary['testsBuildsScansCi'] is False, 'no project test/build/scan/CI')

input_map = {(r['sourceOrdinal'], r['locale']): r for r in input_cells}
ledger_map = {(r['sourceOrdinal'], r['locale']): r for r in ledger}
require(len(input_map) == len(ledger_map) == 600, 'unique cell identities')
require(list(ledger_map) == [(r['sourceOrdinal'], r['locale']) for r in ledger], 'unique ordered ledger')
require(list(input_map) == list(ledger_map), 'exact candidate-free coverage/order')
counts = collections.Counter(r['decision'] for r in ledger)
require(dict(counts) == summary['decisionCounts'], 'summary decision counts')
require(sum(counts.values()) == 600, 'decision total')
require(counts['accept-current'] == 512 and counts['correction'] == 32 and counts['refinement'] == 44 and counts['hold'] == 12, 'decision dimensions')

for current, reviewed in zip(input_cells, ledger):
    k = (current['sourceOrdinal'], current['locale'])
    require(reviewed['sourceOrdinal'] == current['sourceOrdinal'] and reviewed['locale'] == current['locale'], f'cell identity {k}')
    require(reviewed['exactHead'] == HEAD and reviewed['exactTree'] == TREE, f'cell pin {k}')
    require(reviewed['sourceTextSha256'] == current['sourceTextSha256'], f'source hash {k}')
    require(reviewed['currentTargetSha256'] == current['currentTargetSha256'], f'current target hash {k}')
    require(reviewed['callerContextSha256'] == current['callerContextSha256'], f'caller hash {k}')
    require(reviewed['callerReferenceCount'] == current['callerReferenceCount'], f'caller reference count {k}')
    require(reviewed['literalCallCount'] == current['literalCallCount'], f'literal caller count {k}')
    require(reviewed['integrityChecks'] == current['integrityChecks'], f'current integrity record {k}')
    require(all(current['integrityChecks'].values()), f'candidate-free token checks {k}')
    if current['sourceKey'] == 'CatalogNumber':
        require(reviewed['decision'] == 'hold', f'callerless key held {k}')
        forbidden = {'sourceKey','sourceText','currentTarget','proposedTarget'}
        require(not (forbidden & set(reviewed)), f'hold row contains raw text {k}')
        require(reviewed['sourceKeySha256'] == shat(current['sourceKey']), f'held key hash {k}')
        require(reviewed['sourceTextSha256'] == current['sourceTextSha256'], f'held source hash {k}')
        require(reviewed['currentTargetSha256'] == current['currentTargetSha256'], f'held target hash {k}')
        require(reviewed['literalCallCount'] == 0 and reviewed['reasonCode'] == 'zero-literal-caller-hash-only', f'hold reason {k}')
        require(reviewed['textIncluded'] is False, f'hold text flag {k}')
        serialized = json.dumps(reviewed, ensure_ascii=False)
        require('CatalogNumber' not in serialized and 'Catalog Number' not in serialized, f'hold key leaked {k}')
        continue
    require(reviewed['decision'] in {'accept-current','correction','refinement'}, f'non-hold decision {k}')
    require(reviewed['sourceKey'] == current['sourceKey'] and reviewed['sourceKeySha256'] == shat(current['sourceKey']), f'key pin {k}')
    require(reviewed['sourceText'] == current['sourceText'] and shat(reviewed['sourceText']) == current['sourceTextSha256'], f'source text/hash {k}')
    require(reviewed['currentTarget'] == current['currentTarget'] and shat(reviewed['currentTarget']) == current['currentTargetSha256'], f'current text/hash {k}')
    require(token_ok(current['sourceText'], current['currentTarget'], current['protectedLiterals']), f'current token parity {k}')
    require(reviewed['tokenEvidence']['placeholderParity'] and reviewed['tokenEvidence']['inlineCodeParity'] and reviewed['tokenEvidence']['markupParity'] and reviewed['tokenEvidence']['numericTokenParity'] and reviewed['tokenEvidence']['protectedLiteralParity'], f'current token evidence {k}')
    if reviewed['decision'] in {'correction','refinement'}:
        require(isinstance(reviewed.get('proposedTarget'), str) and reviewed.get('rationale'), f'proposal details {k}')
        require(shat(reviewed['proposedTarget']) == reviewed['proposalSha256'], f'proposal text hash {k}')
        require(token_ok(current['sourceText'], reviewed['proposedTarget'], current['protectedLiterals']), f'proposal token parity {k}')
        checks = reviewed['proposalTokenChecks']
        require(all(checks[n] for n in ('placeholderParity','inlineCodeParity','markupParity','numericTokenParity','protectedLiteralParity')), f'proposal token evidence {k}')
    else:
        require('proposedTarget' not in reviewed and 'proposalTokenChecks' not in reviewed, f'unexpected proposal {k}')

proposal_keys = [(r['sourceOrdinal'],r['locale']) for r in proposals]
expected_proposals = [(r['sourceOrdinal'],r['locale']) for r in ledger if r['decision'] in {'correction','refinement'}]
require(proposal_keys == expected_proposals, 'proposal set/order')
for row in proposals:
    base = ledger_map[(row['sourceOrdinal'],row['locale'])]
    require(row['decision'] == base['decision'] and row['proposedTarget'] == base['proposedTarget'], 'proposal ledger parity')
    require(row['proposalSha256'] == base['proposalSha256'] and row['callerContextSha256'] == base['callerContextSha256'], 'proposal hash/context parity')
hold_keys = [(r['sourceOrdinal'],r['locale']) for r in holds]
require(hold_keys == [(r['sourceOrdinal'],r['locale']) for r in ledger if r['decision']=='hold'], 'hold set/order')
require(all(not ({'sourceKey','sourceText','currentTarget','proposedTarget'} & set(r)) for r in holds), 'hold artifact contains hashes only')
require(summary['allCurrentTokenChecksPass'] is True and summary['allProposalTokenChecksPass'] is True, 'summary token status')

print(json.dumps({
    'result':'PASS','exactHead':HEAD,'exactTree':TREE,
    'candidateFreeChecksumListSha256':input_list_sha,
    'cells':len(ledger),'decisions':dict(counts),'proposals':len(proposals),'hashOnlyHolds':len(holds),
    'inputFilesVerified':len(input_listed),'outputFilesVerified':len(output_listed),
}, indent=2))
