#!/usr/bin/env python3
import hashlib, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load_jsonl(path):
    return [json.loads(line) for line in path.open(encoding='utf-8') if line.strip()]
def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

rows = load_jsonl(ROOT / 'cross-review-cells.jsonl')
changes = load_jsonl(ROOT / 'selected-changes.jsonl')
assert len(rows) == 600, len(rows)
assert len({(r['sourceOrdinal'], r['locale']) for r in rows}) == 600
assert {r['sourceOrdinal'] for r in rows} == set(range(150, 200))
locales = {'ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'}
for ordinal in range(150, 200):
    assert {r['locale'] for r in rows if r['sourceOrdinal'] == ordinal} == locales
counts = Counter(r['crossDisposition'] for r in rows)
assert counts == Counter({'accept-current': 530, 'propose-change': 58, 'hold-text-free': 12}), counts
assert len(changes) == 58
change_ids = {r['cellId'] for r in changes}
assert change_ids == {r['cellId'] for r in rows if r['crossDisposition'] == 'propose-change'}
placeholders = re.compile(r'\{[^{}\n]+\}')
for r in rows:
    if r['crossDisposition'] == 'hold-text-free':
        forbidden = {'cellId','sourceKey','sourceText','currentTarget','recommendedTarget','finalReviewedTarget','blindCandidate','primaryCandidate'}
        assert not forbidden.intersection(r), r
        for field in ['cellIdSha256','sourceKeySha256','sourceTextSha256','currentTargetSha256']:
            assert re.fullmatch(r'[0-9a-f]{64}', r[field]), (field, r)
        continue
    assert r['sourceTextSha256'] == sha(r['sourceText'])
    assert r['currentTargetSha256'] == sha(r['currentTarget'])
    target = r.get('recommendedTarget', r.get('finalReviewedTarget'))
    target_hash = r.get('recommendedTargetSha256', r.get('finalReviewedTargetSha256'))
    assert target and target_hash == sha(target)
    assert placeholders.findall(r['sourceText']) == placeholders.findall(target), r['cellId']
    assert r['exactHead'] == '243f17465cc95fe84f16e17767db04a4a97ad040'
    assert r['exactTree'] == '25e7bd0f3adf871b9030081ebc7c49a28213c50f'
    for literal in r.get('protectedLiterals', []):
        assert literal in target, (r['cellId'], literal)
    assert r['candidateFreeRowSha256'] and r['primaryReviewRowSha256'] and r['blindReviewRowSha256']
for r in changes:
    assert r['recommendedTarget'] != r['currentTarget']
    assert r['recommendedTargetSha256'] == sha(r['recommendedTarget'])
market = [r for r in rows if r.get('sourceKey','').startswith('AudibleMarketplace') and r.get('sourceKey') != 'AudibleMarketplaceHelpText']
assert len(market) == 132
assert all(r['callerReferenceCount'] == 1 for r in market)
uk_id = next(r for r in changes if r['cellId'] == 'AudibleMarketplaceUk::id')
assert uk_id['recommendedTarget'] == 'Britania Raya (.co.uk)'
assert any(r['cellId'] == 'AudiobookConversionTagModeHelpText::hi' and r['selectedFrom'] == 'cross-review-custom' for r in changes)
print(json.dumps({'rows':len(rows),'counts':dict(counts),'changes':len(changes),'marketplaceCellsCallerBacked':len(market),'textFreeHolds':counts['hold-text-free']},sort_keys=True))
