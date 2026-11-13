#!/usr/bin/env python3
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path('/home/keith/Documents/code/task-scratch')
OUT = BASE / 'chaptarrng-pr190-w200-249-cross-20261104'
PRIMARY = BASE / 'chaptarrng-pr190-w200-249-primary-20261104/primary-review'
CANDIDATE = BASE / 'chaptarrng-pr190-w200-249-primary-20261104/candidate-free/input'
BLIND = BASE / 'chaptarrng-pr190-w200-249-blind-20261104'
HEAD = 'dc91bdcdf60ba422bb176cc7c58b9b1cab27facd'
TREE = 'ffae435c871360ba958098bc0398a1f251f8b1e8'
LOCALES = {'ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'}
CALLERLESS = 'AuthorsLabel'
PLACEHOLDER = re.compile(r'\{[^{}]+\}')
INLINE = re.compile(r'`([^`]+)`')
MARKUP = re.compile(r'<[^>]+>')
NUMBER = re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def load_jsonl(path):
    return [json.loads(line) for line in path.open(encoding='utf-8') if line.strip()]

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def row_sha(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')))

def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')

selections = json.loads((OUT / 'review-selections.json').read_text(encoding='utf-8'))
blind_selected = set(selections['blindSelectedCells'])
custom_targets = selections['customTargets']
rationales = {int(k): v for k, v in selections['rationalesByOrdinal'].items()}

candidate_rows = load_jsonl(CANDIDATE / 'candidate-free-cells.jsonl')
primary_rows = load_jsonl(PRIMARY / 'primary-review-cells.jsonl')
primary_proposals = {r['cellId']: r for r in load_jsonl(PRIMARY / 'primary-review-proposals.jsonl')}
blind_rows = load_jsonl(BLIND / 'decisions.jsonl')
blind_proposals = {r['sourceKey'] + '::' + r['locale']: r for r in load_jsonl(BLIND / 'proposals.jsonl')}
attestation = json.loads((OUT / 'live-pr-attestation.json').read_text(encoding='utf-8'))

if len(candidate_rows) != 600 or len(primary_rows) != 600 or len(blind_rows) != 600:
    raise SystemExit('expected 600 candidate-free, primary, and blind rows')
if len(primary_proposals) != 96 or len(blind_proposals) != 34:
    raise SystemExit('input proposal counts differ from sealed manifests')
if attestation['pr']['headSha'] != HEAD or attestation['branchApi']['sha'] != HEAD or attestation['pullRef']['sha'] != HEAD:
    raise SystemExit('live PR, branch, and pull refs do not align with the pinned head')
if attestation['sourceWorktree']['head'] != HEAD or attestation['sourceWorktree']['tree'] != TREE or not attestation['sourceWorktree']['clean']:
    raise SystemExit('source worktree does not match the exact clean pin')

primary_by_id = {(r['sourceOrdinal'], r['locale']): r for r in primary_rows}
blind_by_id = {(r['sourceOrdinal'], r['locale']): r for r in blind_rows}
if len(primary_by_id) != 600 or len(blind_by_id) != 600:
    raise SystemExit('duplicate review rows')
rows = []
changes = []
for c in sorted(candidate_rows, key=lambda r: (r['sourceOrdinal'], r['locale'])):
    cid = c['sourceKey'] + '::' + c['locale']
    cell_key = (c['sourceOrdinal'], c['locale'])
    p = primary_by_id[cell_key]
    b = blind_by_id[cell_key]
    pp = primary_proposals.get(cid)
    bp = blind_proposals.get(cid)
    if p['exactHead'] != HEAD or p['exactTree'] != TREE:
        raise SystemExit(f'primary pin mismatch: {cid}')
    if p['candidateFreeRowSha256'] != row_sha(c):
        raise SystemExit(f'primary candidate-free linkage mismatch: {cid}')
    if b['currentTargetSha256'] != c['currentTargetSha256'] or b['callerContextSha256'] != c['callerContextSha256']:
        raise SystemExit(f'blind source/caller linkage mismatch: {cid}')
    if c['sourceOrdinal'] not in range(200, 250) or c['locale'] not in LOCALES:
        raise SystemExit(f'out-of-scope cell: {cid}')

    lineage = {
        'candidateFreeRowSha256': row_sha(c),
        'primaryReviewRowSha256': row_sha(p),
        'blindReviewRowSha256': row_sha(b),
        'sourceFileGitBlob': c.get('sourceFileGitBlob'),
        'sourceFileSha256': c.get('sourceFileSha256'),
        'targetFileGitBlob': c.get('targetFileGitBlob'),
        'targetFileSha256': c.get('targetFileSha256'),
    }

    if c.get('callerReferenceCount', 0) == 0:
        if c['sourceKey'] != CALLERLESS or pp or bp or p.get('primaryDisposition') not in ('hold', 'hold-text-free', 'hash-only-hold') or b.get('decision') != 'hash-only-hold':
            raise SystemExit(f'unexpected callerless disposition: {cid}')
        row = {
            'batch': c['batch'],
            'cellIdSha256': sha(cid),
            'sourceOrdinal': c['sourceOrdinal'],
            'locale': c['locale'],
            'sourceKeySha256': sha(c['sourceKey']),
            'sourceTextSha256': c['sourceTextSha256'],
            'currentTargetSha256': c['currentTargetSha256'],
            'exactHead': HEAD,
            'exactTree': TREE,
            'crossDisposition': 'hold-text-free',
            'primaryDisposition': p.get('primaryDisposition'),
            'blindDecision': b.get('decision'),
            'callerReferenceCount': 0,
            'callerContextSha256': c['callerContextSha256'],
            'crossRationale': 'The pinned caller audit has zero source references. Keep this cell as a text-free hold; do not expose or infer source, current-target, or candidate wording.',
            'nativeSpeakerReviewOutstanding': True,
        }
        row.update(lineage)
        rows.append(row)
        continue

    selected = c['currentTarget']
    selected_from = 'both-reviews-accept-current'
    if cid in custom_targets:
        selected = custom_targets[cid]
        selected_from = 'cross-review-custom'
    elif cid in blind_selected:
        if not bp:
            raise SystemExit(f'blind override does not have a blind proposal: {cid}')
        selected = bp['selectedTarget']
        selected_from = 'blind'
    elif pp and bp:
        if pp['recommendedTarget'] == bp['selectedTarget']:
            selected = pp['recommendedTarget']
            selected_from = 'primary+blind-agree'
        else:
            selected = pp['recommendedTarget']
            selected_from = 'primary'
    elif pp:
        selected = pp['recommendedTarget']
        selected_from = 'primary'
    elif bp:
        selected = bp['selectedTarget']
        selected_from = 'blind'

    disposition = 'propose-change' if selected != c['currentTarget'] else 'accept-current'
    reason = rationales.get(c['sourceOrdinal'], 'Both independent reviews retained the exact current target; no correction proposal was raised for this cell.')
    if cid == '207::es' or cid == '209::es':
        reason += ' The blind wording keeps the catalog’s existing formal “usted” register.'
    elif cid == '220::ja':
        reason += ' The blind candidate matches the catalog’s established “メディアタイプ” terminology.'
    elif cid == '212::id':
        reason += ' A cross-review refinement makes the eligible authors the clear subject of the monitored-book clause.'
    elif cid == '212::zh-Hans':
        reason += ' A cross-review refinement keeps the source relation explicit while avoiding the awkward possessive construction in both candidates.'
    elif cid == '233::pt-BR':
        reason += ' A cross-review refinement combines the clearer server-match clause with a direct default-folder instruction.'
    elif cid == '248::id':
        reason += ' “Peralihan” expresses switching between releases; the blind “penggantian” can imply replacement only.'

    if (c['sourceOrdinal'], c['locale']) in {(233, 'ja'), (235, 'ja')}:
        reason += ' The Japanese 「1つ」 is an equivalent rendering of spelled-out “one” in the source; the count is preserved.'

    selected_placeholders = dict(Counter(PLACEHOLDER.findall(selected)))
    selected_inline = INLINE.findall(selected)
    selected_markup = MARKUP.findall(selected)
    selected_numeric = NUMBER.findall(selected)

    chosen_hash = sha(selected)
    base = {
        'batch': c['batch'],
        'cellId': cid,
        'sourceOrdinal': c['sourceOrdinal'],
        'sourceKey': c['sourceKey'],
        'locale': c['locale'],
        'sourceText': c['sourceText'],
        'sourceTextSha256': c['sourceTextSha256'],
        'currentTarget': c['currentTarget'],
        'currentTargetSha256': c['currentTargetSha256'],
        'exactHead': HEAD,
        'exactTree': TREE,
        'crossDisposition': disposition,
        'primaryDisposition': p.get('primaryDisposition'),
        'blindDecision': b.get('decision'),
        'primaryCandidate': pp.get('recommendedTarget') if pp else None,
        'blindCandidate': bp.get('selectedTarget') if bp else None,
        'selectedFrom': selected_from,
        'reviewConfidence': 'moderate',
        'crossRationale': reason,
        'callerReferenceCount': c.get('callerReferenceCount', 0),
        'callerContextSha256': c.get('callerContextSha256'),
        'callerRefs': c.get('callerRefs', []),
        'relatedDynamicTranslationCallsiteCount': c.get('relatedDynamicTranslationCallsiteCount', 0),
        'sourceFile': c.get('sourceFile'),
        'targetFile': c.get('targetFile'),
        'sourcePlaceholders': c.get('sourcePlaceholders', {}),
        'currentPlaceholders': c.get('currentPlaceholders', {}),
        'selectedPlaceholders': selected_placeholders,
        'sourceNumericTokens': c.get('sourceNumericTokens', []),
        'selectedNumericTokens': selected_numeric,
        'sourceMarkup': c.get('sourceMarkup', []),
        'selectedMarkup': selected_markup,
        'sourceInlineCode': c.get('sourceInlineCode', []),
        'selectedInlineCode': selected_inline,
        'protectedLiterals': c.get('protectedLiterals', []),
        'nativeSpeakerApproval': False,
        'nativeSpeakerReviewOutstanding': True,
    }
    if disposition == 'propose-change':
        base['numericTokenDisposition'] = 'exact'
        base['recommendedTarget'] = selected
        base['recommendedTargetSha256'] = chosen_hash
        changes.append({
            'cellId': cid,
            'sourceOrdinal': c['sourceOrdinal'],
            'sourceKey': c['sourceKey'],
            'locale': c['locale'],
            'sourceTextSha256': c['sourceTextSha256'],
            'currentTargetSha256': c['currentTargetSha256'],
            'recommendedTarget': selected,
            'recommendedTargetSha256': chosen_hash,
            'selectedFrom': selected_from,
            'primaryCandidate': pp.get('recommendedTarget') if pp else None,
            'blindCandidate': bp.get('selectedTarget') if bp else None,
            'crossRationale': reason,
            'callerContextSha256': c.get('callerContextSha256'),
            'candidateFreeRowSha256': row_sha(c),
            'primaryReviewRowSha256': row_sha(p),
            'blindReviewRowSha256': row_sha(b),
            'exactHead': HEAD,
            'exactTree': TREE,
            'nativeSpeakerApproval': False,
            'nativeSpeakerReviewOutstanding': True,
        })
    else:
        base['numericTokenDisposition'] = 'semantic-equivalent-spelled-number' if (c['sourceOrdinal'], c['locale']) in {(233, 'ja'), (235, 'ja')} else 'exact'
        base['finalReviewedTarget'] = selected
        base['finalReviewedTargetSha256'] = chosen_hash
    base.update(lineage)
    rows.append(base)

rows.sort(key=lambda r: (r['sourceOrdinal'], r['locale']))
changes.sort(key=lambda r: (r['sourceOrdinal'], r['locale']))
counts = Counter(r['crossDisposition'] for r in rows)
if len(rows) != 600 or len({(r['sourceOrdinal'], r['locale']) for r in rows}) != 600:
    raise SystemExit('cross output does not contain exactly one row per source-locale cell')
if counts != Counter({'propose-change': 99, 'accept-current': 489, 'hold-text-free': 12}):
    raise SystemExit(f'unexpected cross dispositions: {counts}')
if len(changes) != 99:
    raise SystemExit(f'expected 99 selected recommendations, got {len(changes)}')

write_jsonl(OUT / 'cross-review-cells.jsonl', rows)
write_jsonl(OUT / 'selected-changes.jsonl', changes)
primary_ids = set(primary_proposals)
blind_ids = set(blind_proposals)
summary = {
    'repository': 'snapetech-org/chaptarrng',
    'pullRequest': 190,
    'batch': 'W200-W249',
    'head': HEAD,
    'tree': TREE,
    'apiBaseAtReview': attestation['pr']['baseSha'],
    'currentMainAtReview': attestation['currentMain'],
    'baseDiffersFromLiveMain': attestation['apiBaseDiffersFromMain'],
    'baseDriftReconciliation': {
        'compareBase': attestation['pr']['baseSha'],
        'compareHead': attestation['currentMain'],
        'aheadBy': 8,
        'changedFiles': [
            '.github/workflows/bookshelfng-standalone-macos-acceptance.yml',
            '.github/workflows/standalone-asset-validation.yml',
            'AGENTS.md',
            'docs/BOOKSHELFNG_RETIREMENT.md',
            'packaging/scripts/test-bookshelf-legacy-channels.mjs',
            'scripts/test_workflow_runner_policy.py'
        ],
        'localizationSourceOrCatalogChanges': False,
        'verifiedBy': 'GitHub compare API at 2026-11-04T16:19:50Z'
    },
    'scope': '50 source IDs × 12 direct locales = 600 cells',
    'primaryProposalCells': len(primary_ids),
    'blindProposalCells': len(blind_ids),
    'proposalOverlap': len(primary_ids & blind_ids),
    'uniqueProposalCellsCrossReviewed': len(primary_ids | blind_ids),
    'selectedChangeCells': len(changes),
    'dispositions': dict(counts),
    'callerBackedKeys': 49,
    'callerlessSourceKeys': [CALLERLESS],
    'textFreeHolds': counts['hold-text-free'],
    'nativeSpeakerApproval': 0,
    'nativeSpeakerReviewOutstanding': 600,
    'recommendationsOnly': True,
    'appliedToCatalogs': False,
    'repositoryOrPRChanged': False,
    'testsBuildsCI': 'not run',
    'candidateFreeManifestSha256': json.loads((CANDIDATE / 'candidate-free-manifest.json').read_text())['manifestSha256'] if 'manifestSha256' in json.loads((CANDIDATE / 'candidate-free-manifest.json').read_text()) else sha((CANDIDATE / 'candidate-free-manifest.json').read_text()),
    'sourceWorktreeClean': True
}
(OUT / 'cross-review-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'rows': len(rows), 'changes': len(changes), 'dispositions': dict(counts), 'overlap': len(primary_ids & blind_ids)}, ensure_ascii=False, sort_keys=True))
