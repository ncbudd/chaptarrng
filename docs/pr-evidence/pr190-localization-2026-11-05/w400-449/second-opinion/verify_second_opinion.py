#!/usr/bin/env python3
"""Verify the W400–W449 second-opinion packet against pinned candidate-free inputs."""
from __future__ import annotations
import collections, hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
CF = TASK / 'candidate-free' / 'input'
CROSS = TASK / 'cross-review' / 'independent-semantic-review'
HEAD = '8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7'
TREE = '018e46cd14424204a01be46e13e5b50f9f26ce07'
ADJUSTED = {
    'CalibrePushDescriptionInterp::ar',
    'CalibrePushDescriptionInterp::es',
    'CalibrePushDescriptionInterp::hi',
    'CalibrePushDescriptionInterp::pt-BR',
    'EditionCatalog::ar',
    'EditionCatalog::vi',
}
PLACEHOLDER = re.compile(r'\{[^{}]+\}')
INLINE = re.compile(r'`([^`]+)`')
MARKUP = re.compile(r'<[^>]+>')
NUMBER = re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_text(value: str) -> str:
    return sha(value.encode('utf-8'))

def canon(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')

def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def need(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit('FAIL: ' + message)

def verify_output_sums() -> None:
    sums = HERE / 'SHA256SUMS.txt'
    need(sums.is_file(), 'missing SHA256SUMS.txt')
    listed = {}
    for line in sums.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split('  ', 1)
        path = Path(name)
        need(not path.is_absolute() and '..' not in path.parts, 'unsafe checksum path')
        need(name not in listed, 'duplicate checksum entry ' + name)
        need((HERE / path).is_file(), 'missing checksummed file ' + name)
        need(sha((HERE / path).read_bytes()) == digest, 'checksum mismatch ' + name)
        listed[name] = digest
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt'}
    need(set(listed) == actual, 'checksum inventory mismatch')

def token_parity(source: dict, target: str) -> bool:
    source_text = source['sourceText']
    return (
        collections.Counter(PLACEHOLDER.findall(source_text)) == collections.Counter(PLACEHOLDER.findall(target))
        and INLINE.findall(source_text) == INLINE.findall(target)
        and MARKUP.findall(source_text) == MARKUP.findall(target)
        and collections.Counter(NUMBER.findall(source_text)) == collections.Counter(NUMBER.findall(target))
        and all(literal in target for literal in source.get('protectedLiterals', []))
    )

def main() -> None:
    verify_output_sums()
    summary = read_json(HERE / 'summary.json')
    manifest = read_json(HERE / 'manifest.json')
    need(summary['exactHead'] == manifest['exactHead'] == HEAD, 'head pin')
    need(summary['exactTree'] == manifest['exactTree'] == TREE, 'tree pin')
    need(manifest['sealed'] is True, 'manifest seal flag')
    need(summary['nativeSpeakerApproval'] is False, 'native-speaker approval claim')
    need(summary['callerlessCellsIncludedInRecommendations'] is False, 'callerless inclusion claim')
    need(summary['hashOnlyHoldTextIncluded'] is False, 'hash-only text claim')

    input_paths = {
        'candidate-free/input/candidate-free-cells.jsonl': CF / 'candidate-free-cells.jsonl',
        'candidate-free/input/caller-context.jsonl': CF / 'caller-context.jsonl',
        'candidate-free/input/SHA256SUMS.txt': CF / 'SHA256SUMS.txt',
        'cross-review/independent-semantic-review/cross-review-ledger.jsonl': CROSS / 'cross-review-ledger.jsonl',
        'cross-review/independent-semantic-review/holds-hash-only.jsonl': CROSS / 'holds-hash-only.jsonl',
    }
    expected_inputs = {key: sha(path.read_bytes()) for key, path in input_paths.items()}
    need(summary['inputSha256'] == expected_inputs, 'input file pins')
    need(manifest['inputSha256'] == expected_inputs, 'manifest input pins')

    candidates = read_jsonl(CF / 'candidate-free-cells.jsonl')
    contexts = read_jsonl(CF / 'caller-context.jsonl')
    cross_rows = read_jsonl(CROSS / 'cross-review-ledger.jsonl')
    cross_holds = read_jsonl(CROSS / 'holds-hash-only.jsonl')
    ledger = read_jsonl(HERE / 'second-opinion-ledger.jsonl')
    output_holds = read_jsonl(HERE / 'hash-only-holds.jsonl')
    context_by_key = {row['sourceKey']: row for row in contexts}
    candidate_by_id = {(row['sourceKey'], row['locale']): row for row in candidates}
    cross_by_id = {row['cellId']: row for row in cross_rows if row.get('decision') == 'recommend-revision'}
    callerless_hashes = set()
    callerless_count = 0
    for candidate in candidates:
        context = context_by_key[candidate['sourceKey']]
        if candidate['literalCallCount'] == 0 and context['literalCallCount'] == 0:
            callerless_count += 1
            callerless_hashes.add(sha(canon(candidate)))
    need(callerless_count == len(cross_holds) == len(output_holds) == 12, 'callerless hold count')
    need(output_holds == cross_holds, 'hash-only holds differ from pinned cross-review records')
    held_text_fields = {'sourceKey', 'sourceOrdinal', 'sourceText', 'currentTarget', 'reviewedTarget', 'recommendedTarget', 'cellId'}
    for row in output_holds:
        need(not (held_text_fields & row.keys()), 'hash-only hold contains text or identity')
        need(row.get('sourceAndTargetTextOmitted') is True and row.get('recommendedTargetOmitted') is True, 'hold omission flags')

    need(len(cross_by_id) == len(ledger) == 140, 'recommendation count')
    need(len({row['cellId'] for row in ledger}) == 140, 'recommendation uniqueness')
    need(not any(row.get('candidateFreeRowSha256') in callerless_hashes for row in ledger), 'callerless row in recommendations')
    adjusted_seen = set()
    counts = collections.Counter()
    for row in ledger:
        cell_id = row['cellId']
        cross = cross_by_id.get(cell_id)
        need(cross is not None, 'unknown recommendation ' + cell_id)
        candidate = candidate_by_id.get((row['sourceKey'], row['locale']))
        need(candidate is not None, 'missing candidate-free cell ' + cell_id)
        context = context_by_key[row['sourceKey']]
        need(candidate['literalCallCount'] > 0 and context['literalCallCount'] > 0, 'callerless recommendation ' + cell_id)
        need(row['exactHead'] == HEAD and cross['exactHead'] == HEAD, 'row head ' + cell_id)
        need(row['exactTree'] == TREE and cross['exactTree'] == TREE, 'row tree ' + cell_id)
        need(row['sourceOrdinal'] == candidate['sourceOrdinal'] == cross['sourceOrdinal'], 'source ordinal ' + cell_id)
        need(row['sourceText'] == candidate['sourceText'] == cross['sourceText'], 'source text binding ' + cell_id)
        need(row['currentTarget'] == candidate['currentTarget'] == cross['currentTarget'], 'current target binding ' + cell_id)
        need(row['sourceTextSha256'] == candidate['sourceTextSha256'] == cross['sourceTextSha256'] if 'sourceTextSha256' in row else candidate['sourceTextSha256'] == cross['sourceTextSha256'], 'source hash ' + cell_id)
        need(row['sourceTextSha256'] if 'sourceTextSha256' in row else True, 'source hash field')
        need(row['sourceTextSha256'] == candidate['sourceTextSha256'] if 'sourceTextSha256' in row else True, 'source hash field binding')
        need(row['currentTargetSha256'] == candidate['currentTargetSha256'] == cross['currentTargetSha256'], 'current target hash ' + cell_id)
        need(row['callerContextSha256'] == candidate['callerContextSha256'] == context['callerContextSha256'] == cross['callerContextSha256'], 'caller context hash ' + cell_id)
        need(row['candidateFreeRowSha256'] == sha(canon(candidate)) == cross['candidateFreeRowSha256'], 'candidate-free row hash ' + cell_id)
        need(row['crossReviewRowSha256'] == sha(canon(cross)), 'cross-review row hash ' + cell_id)
        need(row['crossRecommendationTarget'] == cross['reviewedTarget'], 'cross-review target text ' + cell_id)
        need(row['crossRecommendationTargetSha256'] == cross['reviewedTargetSha256'] == sha_text(cross['reviewedTarget']), 'cross-review target hash ' + cell_id)
        need(row['finalTargetSha256'] == sha_text(row['finalTarget']), 'final target hash ' + cell_id)
        need(token_parity(candidate, row['finalTarget']), 'final target token parity ' + cell_id)
        need(row['nativeSpeakerApproval'] is False, 'native approval on row ' + cell_id)
        decision = row['decision']
        counts[decision] += 1
        if decision == 'accept-recommendation':
            need(row['finalTarget'] == cross['reviewedTarget'], 'accepted target changed ' + cell_id)
        elif decision == 'adjust':
            adjusted_seen.add(cell_id)
            need(row['finalTarget'] != cross['reviewedTarget'], 'adjustment equals recommendation ' + cell_id)
        else:
            need(decision == 'hold' and not row.get('finalTarget'), 'unexpected hold form ' + cell_id)
    need(adjusted_seen == ADJUSTED, 'adjusted cell set')
    expected_counts = {'accept-recommendation': 134, 'adjust': 6, 'hold': 0}
    actual_counts = {key: counts.get(key, 0) for key in expected_counts}
    need(actual_counts == expected_counts, 'decision counts')
    need(summary['decisionCounts'] == expected_counts, 'summary decision counts')
    need(summary['reviewedRecommendations'] == 140, 'summary coverage')
    need(manifest['counts']['recommendations'] == 140 and manifest['counts']['hashOnlyCallerlessHolds'] == 12, 'manifest coverage')
    print('PASS: 140 recommendations bound to candidate-free source/current/caller and cross-review hashes; 134 accepted, 6 adjusted, 0 held; 12 callerless cells remain hash-only.')

if __name__ == '__main__':
    main()
