#!/usr/bin/env python3
"""Build a read-only independent cross-review of ChaptarrNG PR #190 W600–649."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

OUT = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0600-0649-crossreview-independent-20261102')
PRIMARY = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0600-0649-primary-20261102')
PRIOR = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0550-0599-primary-20261102')
REPO = OUT / 'source-copy'
OWNER_REPO = 'snapetech-org/chaptarrng'
PR_NUMBER = 190
HEAD = 'f405a6256c2661e48e412ac4471ce70411baf98c'
TREE = 'fe3272572b68460f1d8c8083a5dcc44cd3307b74'
LOCALES = ['es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']
CATALOG_PATHS = {
    'es': 'src/NzbDrone.Core/Localization/Core/es.json',
    'zh-Hans': 'src/NzbDrone.Core/Localization/Core/zh_CN.json',
    'hi': 'src/NzbDrone.Core/Localization/Core/hi.json',
    'de': 'src/NzbDrone.Core/Localization/Core/de.json',
    'ja': 'src/NzbDrone.Core/Localization/Core/ja.json',
    'fr': 'src/NzbDrone.Core/Localization/Core/fr.json',
    'pt-BR': 'src/NzbDrone.Core/Localization/Core/pt_BR.json',
    'ar': 'src/NzbDrone.Core/Localization/Core/ar.json',
    'ko': 'src/NzbDrone.Core/Localization/Core/ko.json',
    'zh-Hant': 'src/NzbDrone.Core/Localization/Core/zh_TW.json',
    'vi': 'src/NzbDrone.Core/Localization/Core/vi.json',
    'id': 'src/NzbDrone.Core/Localization/Core/id.json',
}
SOURCE_PATH = 'src/NzbDrone.Core/Localization/Core/en.json'
FOLLOWUP_PATH = 'docs/localization/source-followup-20261101.json'
REGISTRY_PATH = 'docs/localization/provider-field-sources.json'
EXPECTED_INPUT_SUMS_SHA = 'ff07d87007bc797b249eb424ee212893fe5f5551d36cf7e1e287bd530d26e415'
EXPECTED_PRIMARY_SUMS_SHA = '953d11509d8fbec61b361b3306f0a4f2cf1b3f51af3559bd823b3d6d2351e42f'
PH_RE = re.compile(r'\{[^{}]+\}')
MARKUP_RE = re.compile(r'</?[A-Za-z][^>]*>')

# The caller pins this as a qBittorrent warning when no audiobook category is set.
# The primary alternatives are unrelated monitoring-choice questions; replace with
# short, context-accurate recommendations to specify a category.
W621_REPLACEMENTS = {
    (621, 'es'): ('Se recomienda especificar una categoría.', 'The pinned caller emits a qBittorrent warning when no audiobook category is provided. The primary target changes the meaning to an unrelated question about monitoring books.'),
    (621, 'ja'): ('カテゴリの指定をお勧めします。', 'The pinned caller emits a qBittorrent warning when no audiobook category is provided. The primary target changes the meaning to an unrelated question about monitoring books.'),
    (621, 'vi'): ('Nên chỉ định danh mục.', 'The pinned caller emits a qBittorrent warning when no audiobook category is provided. The primary target changes the meaning to an unrelated question about monitoring books.'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def value_sha(value):
    if isinstance(value, str):
        return sha(value.encode('utf-8'))
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8'))


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_jsonl(name, rows):
    (OUT / name).write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def git(args, *, binary=False):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=not binary)


def git_blob(path):
    return git(['show', f'{HEAD}:{path}'], binary=True)


def blob_id(path):
    return git(['rev-parse', f'{HEAD}:{path}']).strip()


def live_pr_state():
    pr = json.loads(subprocess.check_output(['gh', 'api', f'repos/{OWNER_REPO}/pulls/{PR_NUMBER}'], text=True))
    commit = json.loads(subprocess.check_output(['gh', 'api', f'repos/{OWNER_REPO}/commits/{pr["head"]["sha"]}'], text=True))
    tree = commit['commit']['tree']['sha']
    return {
        'repository': OWNER_REPO, 'number': pr['number'], 'state': pr['state'], 'draft': pr['draft'],
        'head': pr['head']['sha'], 'headRef': pr['head']['ref'], 'baseRef': pr['base']['ref'],
        'tree': tree, 'url': pr['html_url'],
        'passed': pr['number'] == PR_NUMBER and pr['state'] == 'open' and pr['draft'] is True and
                  pr['head']['sha'] == HEAD and tree == TREE,
    }


def verify_sums(directory, sums_name, expected_file_sha=None):
    sums_path = directory / sums_name
    sums_sha = sha(sums_path.read_bytes())
    if expected_file_sha and sums_sha != expected_file_sha:
        raise RuntimeError(f'{sums_name} checksum-file digest mismatch: {sums_sha}')
    results = []
    for line in sums_path.read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        actual = sha((directory / name).read_bytes())
        if actual != digest:
            raise RuntimeError(f'checksum failure in {sums_name}: {name}')
        results.append({'file': name, 'sha256': actual, 'passed': True})
    return {'checksumFileSha256': sums_sha, 'entries': results}


def check_context(lines, ref):
    n = ref['currentLine']
    if n < 1 or n > len(lines):
        raise RuntimeError(f'caller line out of range: {ref["file"]}:{n}')
    line = lines[n - 1]
    before = lines[max(0, n - 3):n - 1]
    after = lines[n:min(len(lines), n + 2)]
    checks = {
        'lineTextMatches': line == ref['currentLineText'],
        'lineSha256Matches': sha(line.encode('utf-8')) == ref['currentLineSha256'],
        'contextBeforeMatches': before == ref['contextBefore'],
        'contextAfterMatches': after == ref['contextAfter'],
    }
    if ref.get('lineMatchMethod') == 'exact-source-id':
        checks['sourceIdPresent'] = ref['matchedSourceId'] in line
    elif ref.get('lineMatchMethod') == 'source-text-exact':
        checks['sourceTextPresent'] = ref['matchedSourceText'] in line
    elif ref.get('lineMatchMethod') == 'source-text-fragment':
        window = '\n'.join(lines[max(0, n - 3):min(len(lines), n + 2)])
        string_literals = ''.join(re.findall(r'"((?:\\.|[^"\\])*)"', window))
        checks['sourceFragmentPresent'] = (ref['matchedSourceText'] in string_literals or
                                           ref['matchedSourceText'] in window)
    if not all(checks.values()):
        raise RuntimeError(f'caller line/context mismatch: {ref["file"]}:{n}: {checks}')
    return line, before, after, checks


def text_checks(source, target, protected, casefold_literals=None):
    casefold_literals = set(casefold_literals or [])
    src_ph = collections.Counter(PH_RE.findall(source))
    target_ph = collections.Counter(PH_RE.findall(target)) if isinstance(target, str) else collections.Counter()
    source_markup = MARKUP_RE.findall(source)
    target_markup = MARKUP_RE.findall(target) if isinstance(target, str) else []
    literal_checks = {}
    for lit in protected:
        if lit in casefold_literals:
            literal_checks[lit] = lit.casefold() in target.casefold()
        else:
            literal_checks[lit] = lit in target
    return {
        'placeholderParity': src_ph == target_ph,
        'sourcePlaceholders': dict(src_ph), 'targetPlaceholders': dict(target_ph),
        'markupParity': source_markup == target_markup,
        'sourceMarkup': source_markup, 'targetMarkup': target_markup,
        'protectedLiteralsPreserved': all(literal_checks.values()),
        'protectedLiteralChecks': literal_checks,
    }


def main():
    allowed = {
        'build_crossreview.py', 'README.md', 'SHA256SUMS', 'manifest.json', 'summary.json',
        'live-pr-state.json', 'primary-input-integrity.json', 'source-attestation.jsonl',
        'live-cell-reattestation.jsonl', 'caller-ref-reattestation.jsonl',
        'boundary-reattestation.jsonl', 'candidate-cross-review.jsonl',
        'current-protected-literal-mismatches.jsonl', 'final-dispositions.jsonl',
        'missed-issues.jsonl', 'source-copy',
    }
    if any(path.name not in allowed for path in OUT.iterdir()):
        raise RuntimeError(f'refusing to overwrite unexpected files in {OUT}')
    if git(['rev-parse', 'HEAD']).strip() != HEAD or git(['show', '-s', '--format=%T', 'HEAD']).strip() != TREE:
        raise RuntimeError('source-copy does not contain the exact requested head/tree')
    pr_state = live_pr_state()
    if not pr_state['passed']:
        raise RuntimeError('live PR moved or is no longer open/draft: ' + json.dumps(pr_state))
    primary_sums = verify_sums(PRIMARY, 'SHA256SUMS', EXPECTED_PRIMARY_SUMS_SHA)
    input_sums_file_sha = sha((PRIMARY / 'INPUT-SHA256SUMS').read_bytes())
    if input_sums_file_sha != EXPECTED_INPUT_SUMS_SHA:
        raise RuntimeError(f'INPUT-SHA256SUMS checksum-file digest mismatch: {input_sums_file_sha}')
    manifest = json.loads((PRIMARY / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['head'] != HEAD or manifest['tree'] != TREE:
        raise RuntimeError('primary manifest pin differs from requested head/tree')

    # Exact source and catalog content from the PR commit via a sparse task-owned clone.
    source_raw = git_blob(SOURCE_PATH)
    follow_raw = git_blob(FOLLOWUP_PATH)
    registry_raw = git_blob(REGISTRY_PATH)
    source_catalog = json.loads(source_raw)
    followup = json.loads(follow_raw)
    source_ids = followup['currentMissingIds']
    if len(source_ids) != 1210 or len(set(source_ids)) != 1210:
        raise RuntimeError('source ID inventory count or uniqueness mismatch')
    source_list_hash = sha(compact(source_ids))
    if source_list_hash != manifest['sourceListSha256']:
        raise RuntimeError('source ID list hash does not match primary manifest')
    source_slice = load_jsonl(PRIMARY / 'source-slice.jsonl')
    expected_slice = source_ids[600:650]
    if len(source_slice) != 50 or [r['sourceId'] for r in source_slice] != expected_slice:
        raise RuntimeError('primary source slice differs from exact current 1210-ID ordered inventory')

    catalogs = {}
    catalog_raw = {}
    catalog_meta = {}
    for locale, path in CATALOG_PATHS.items():
        raw = git_blob(path)
        catalog_raw[locale] = raw
        catalogs[locale] = json.loads(raw)
        catalog_meta[locale] = {'path': path, 'blob': blob_id(path), 'sha256': sha(raw), 'bytes': len(raw)}
        if set(catalogs[locale]) != set(source_catalog):
            raise RuntimeError(f'{locale} catalog key inventory differs from en.json')
    source_info = {'path': SOURCE_PATH, 'blob': blob_id(SOURCE_PATH), 'sha256': sha(source_raw), 'bytes': len(source_raw)}
    follow_info = {'path': FOLLOWUP_PATH, 'blob': blob_id(FOLLOWUP_PATH), 'sha256': sha(follow_raw), 'bytes': len(follow_raw)}
    registry_info = {'path': REGISTRY_PATH, 'blob': blob_id(REGISTRY_PATH), 'sha256': sha(registry_raw), 'bytes': len(registry_raw)}
    input_manifest_checks = []
    exact_bytes = {SOURCE_PATH: source_raw, FOLLOWUP_PATH: follow_raw, REGISTRY_PATH: registry_raw}
    exact_bytes.update({CATALOG_PATHS[loc]: catalog_raw[loc] for loc in LOCALES})
    for line in (PRIMARY / 'INPUT-SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, path = line.split('  ', 1)
        if path not in exact_bytes:
            exact_bytes[path] = git_blob(path)
        actual = sha(exact_bytes[path])
        if actual != digest:
            raise RuntimeError(f'input checksum differs from exact-head file {path}')
        input_manifest_checks.append({'path': path, 'sha256': actual, 'passed': True})

    source_rows_by_ordinal = {r['sourceOrdinal']: r for r in source_slice}
    source_rows = []
    for row in source_slice:
        ordinal, sid = row['sourceOrdinal'], row['sourceId']
        live_source = source_catalog.get(sid)
        if live_source != row['source'] or sha(sid.encode('utf-8')) != row['sourceKeySha256'] or sha(live_source.encode('utf-8')) != row['sourceTextSha256']:
            raise RuntimeError(f'source row mismatch at {ordinal}/{sid}')
        if row['sourceFileBlob'] != source_info['blob'] or row['sourceFileSha256'] != source_info['sha256']:
            raise RuntimeError(f'source file pin mismatch at {ordinal}/{sid}')
        if row['sourceFollowupBlob'] != follow_info['blob'] or row['sourceFollowupSha256'] != follow_info['sha256']:
            raise RuntimeError(f'source follow-up pin mismatch at {ordinal}/{sid}')
        if row['sourceIdListSha256'] != source_list_hash or row['sourceIdListCount'] != len(source_ids):
            raise RuntimeError(f'source list pin mismatch at {ordinal}/{sid}')
        source_rows.append({
            'sourceOrdinal': ordinal, 'sourceId': sid, 'source': live_source,
            'sourceKeySha256': sha(sid.encode('utf-8')), 'sourceTextSha256': sha(live_source.encode('utf-8')),
            'sourceListPositionMatches': source_ids[ordinal] == sid,
            'sourceListSha256': source_list_hash, 'sourceListCount': len(source_ids),
            'sourceFile': source_info, 'sourceFollowup': follow_info,
            'registryFile': registry_info if row.get('registryPath') else None,
            'callerCount': len(row['callerRefs']), 'callerContextSha256': row['callerContextSha256'],
        })

    # Verify all caller references against exact live blob, line, two-line context and byte hash.
    ref_file_bytes = {}
    caller_rows = []
    for source in source_slice:
        refs = source['callerRefs']
        if sha(compact(refs)) != source['callerContextSha256']:
            raise RuntimeError(f'caller-context digest mismatch for {source["sourceId"]}')
        for ref in refs:
            path = ref['file']
            if path not in ref_file_bytes:
                raw = git_blob(path)
                ref_file_bytes[path] = {'bytes': raw, 'lines': raw.decode('utf-8').splitlines(),
                                        'blob': blob_id(path), 'sha256': sha(raw)}
            info = ref_file_bytes[path]
            if info['blob'] != ref['currentFileBlob'] or info['sha256'] != ref['currentFileSha256']:
                raise RuntimeError(f'caller file blob/hash mismatch {path}')
            line, before, after, checks = check_context(info['lines'], ref)
            caller_rows.append({
                'sourceOrdinal': source['sourceOrdinal'], 'sourceId': source['sourceId'],
                'file': path, 'fileBlob': info['blob'], 'fileSha256': info['sha256'],
                'kind': ref['kind'], 'line': ref['currentLine'], 'lineText': line,
                'lineSha256': ref['currentLineSha256'], 'contextBefore': before, 'contextAfter': after,
                'checks': checks, 'callerContextSha256': source['callerContextSha256'],
            })
    if len(caller_rows) != 64:
        raise RuntimeError(f'expected 64 caller references, found {len(caller_rows)}')

    cells = load_jsonl(PRIMARY / 'review-cells.jsonl')
    input_cells = load_jsonl(PRIMARY / 'input-cells.jsonl')
    candidates = load_jsonl(PRIMARY / 'correction-candidates.jsonl')
    literals = load_jsonl(PRIMARY / 'protected-literal-integrity.jsonl')
    if (len(cells), len(input_cells), len(candidates), len(literals)) != (600, 600, 201, 600):
        raise RuntimeError('primary row counts do not match 600 cells / 201 candidates')
    input_by_key = {(r['sourceOrdinal'], r['locale']): r for r in input_cells}
    literal_by_key = {(r['sourceOrdinal'], r['locale']): r for r in literals}
    primary_cell_by_key = {(r['sourceOrdinal'], r['locale']): r for r in cells}
    cell_by_key = {}
    live_cells = []
    current_literal_mismatch_rows = []
    candidate_by_key = {(r['sourceOrdinal'], r['locale']): r for r in candidates}

    for r in cells:
        ordinal, sid, locale = r['sourceOrdinal'], r['sourceId'], r['locale']
        if locale not in catalogs or source_rows_by_ordinal[ordinal]['sourceId'] != sid:
            raise RuntimeError(f'cell is outside exact source/locale inventory: {ordinal}/{sid}/{locale}')
        live_target = catalogs[locale].get(sid)
        live_source = source_catalog.get(sid)
        target_hash = value_sha(live_target) if live_target is not None else None
        inp = input_by_key[(ordinal, locale)]
        if live_target is None or live_target != r['currentTarget'] or target_hash != r['currentTargetSha256']:
            raise RuntimeError(f'live current target mismatch: {ordinal}/{sid}/{locale}')
        if live_source != r['source'] or sha(live_source.encode('utf-8')) != r['sourceTextSha256']:
            raise RuntimeError(f'live source text mismatch: {ordinal}/{sid}/{locale}')
        meta = catalog_meta[locale]
        if (r['targetFile'] != meta['path'] or r['targetFileBlob'] != meta['blob'] or r['targetFileSha256'] != meta['sha256'] or
            inp['targetFileBlob'] != meta['blob'] or inp['targetFileSha256'] != meta['sha256']):
            raise RuntimeError(f'target catalog identity mismatch: {locale}')
        if (inp['currentTarget'] != live_target or inp['currentTargetSha256'] != target_hash or inp['source'] != live_source or
            inp['callerContextSha256'] != r['callerContextSha256']):
            raise RuntimeError(f'input-cell mismatch at {ordinal}/{locale}')
        protected = r['protectedLiterals']
        casefold = {check['literal'] for check in r['protectedLiteralChecks'] if check['matchMode'] == 'case-insensitive'}
        current_checks = text_checks(live_source, live_target, protected, casefold)
        if not current_checks['placeholderParity'] or not current_checks['markupParity']:
            raise RuntimeError(f'current target structural mismatch {ordinal}/{locale}')
        literal_row = literal_by_key[(ordinal, locale)]
        if literal_row['currentTarget'] != live_target or literal_row['currentTargetSha256'] != target_hash:
            raise RuntimeError(f'protected-literal current target mismatch {ordinal}/{locale}')
        missing_current = [lit for lit, ok in current_checks['protectedLiteralChecks'].items() if not ok]
        if missing_current:
            current_literal_mismatch_rows.append({'sourceOrdinal': ordinal, 'sourceId': sid, 'locale': locale,
                                                  'missing': missing_current, 'currentTarget': live_target,
                                                  'currentTargetSha256': target_hash})
        candidate = candidate_by_key.get((ordinal, locale))
        if candidate:
            if candidate['currentTarget'] != live_target or candidate['currentTargetSha256'] != target_hash:
                raise RuntimeError(f'candidate current-target mismatch {ordinal}/{locale}')
            if value_sha(candidate['recommendedTarget']) != candidate['recommendedTargetSha256']:
                raise RuntimeError(f'candidate target hash mismatch {ordinal}/{locale}')
            proposed = candidate['recommendedTarget']
            proposed_checks = text_checks(live_source, proposed, protected, casefold)
            if not all(proposed_checks[k] for k in ['placeholderParity', 'markupParity', 'protectedLiteralsPreserved']):
                raise RuntimeError(f'candidate structural check failed {ordinal}/{locale}: {proposed_checks}')
        else:
            candidate = None
            proposed = None
            proposed_checks = None
        live = {
            'sourceOrdinal': ordinal, 'sourceId': sid, 'locale': locale,
            'source': live_source, 'sourceTextSha256': sha(live_source.encode('utf-8')),
            'currentTarget': live_target, 'currentTargetSha256': target_hash,
            'targetFile': meta['path'], 'targetFileBlob': meta['blob'], 'targetFileSha256': meta['sha256'],
            'primaryDisposition': r['disposition'], 'primaryRecommendedTarget': r['recommendedTarget'],
            'primaryRecommendedTargetSha256': r['recommendedTargetSha256'],
            'liveCallerContextSha256': r['callerContextSha256'],
            'sourceAndCatalogHashesMatch': True, 'currentTextChecks': current_checks,
            'recommendedTextChecks': proposed_checks,
        }
        live_cells.append(live)
        cell_by_key[(ordinal, locale)] = live
    if len(current_literal_mismatch_rows) != 15:
        raise RuntimeError(f'expected 15 protected-literal mismatch cells, found {len(current_literal_mismatch_rows)}')
    save_jsonl('source-attestation.jsonl', source_rows)
    save_jsonl('caller-ref-reattestation.jsonl', caller_rows)
    save_jsonl('live-cell-reattestation.jsonl', live_cells)
    save_jsonl('current-protected-literal-mismatches.jsonl', current_literal_mismatch_rows)

    # Independently review all candidate recommendations. Reject/replace the three
    # W621 texts that switch to a different source question.
    candidate_reviews = []
    for candidate in candidates:
        key = (candidate['sourceOrdinal'], candidate['locale'])
        replacement = W621_REPLACEMENTS.get(key)
        if replacement:
            target, rationale = replacement
            verdict = 'reject-primary-proposal-replace-with-corrected-target'
            checks = text_checks(candidate['source'], target, candidate['protectedLiterals'])
        else:
            target = candidate['recommendedTarget']
            rationale = ('Independent review accepts the proposed meaning and preserves the pinned caller context, placeholders, markup, and protected literals. Native-speaker validation remains outstanding.')
            verdict = 'accept-primary-proposal'
            checks = text_checks(candidate['source'], target, candidate['protectedLiterals'])
        if not all(checks[k] for k in ['placeholderParity', 'markupParity', 'protectedLiteralsPreserved']):
            raise RuntimeError(f'cross-review final target structural mismatch {key}')
        candidate_reviews.append({
            'sourceOrdinal': candidate['sourceOrdinal'], 'sourceId': candidate['sourceId'],
            'locale': candidate['locale'], 'source': candidate['source'],
            'currentTarget': candidate['currentTarget'], 'currentTargetSha256': candidate['currentTargetSha256'],
            'primaryDisposition': candidate['disposition'], 'primaryRecommendedTarget': candidate['recommendedTarget'],
            'primaryRecommendedTargetSha256': candidate['recommendedTargetSha256'],
            'crossReviewVerdict': verdict, 'crossReviewTarget': target,
            'crossReviewTargetSha256': value_sha(target), 'rationale': rationale,
            'textChecks': checks, 'callerRefs': candidate['callerRefs'],
            'nativeSpeakerApproval': False,
        })
    if len(candidate_reviews) != 201:
        raise RuntimeError('not all 201 candidates adjudicated')
    save_jsonl('candidate-cross-review.jsonl', candidate_reviews)

    # Reattest W599 from its previous primary packet, plus both edges of this slice.
    prior_sums_check = None
    prior_rows = []
    prior_readback_by_locale = {}
    if (PRIOR / 'SHA256SUMS').exists():
        prior_sums_check = verify_sums(PRIOR, 'SHA256SUMS')
    previous_cells = load_jsonl(PRIOR / 'review-cells.jsonl')
    w599_previous = {r['locale']: r for r in previous_cells if r['sourceOrdinal'] == 599}
    previous_id = source_ids[599]
    if set(w599_previous) != set(LOCALES):
        raise RuntimeError('previous W599 packet does not cover 12 locales')
    w599_source = source_catalog[previous_id]
    w599_caller_hashes = {}
    for locale, prev in w599_previous.items():
        current = catalogs[locale][previous_id]
        current_hash = value_sha(current)
        source_match = prev['source'] == w599_source and prev['sourceTextSha256'] == sha(w599_source.encode('utf-8'))
        current_match = current_hash == prev['currentTargetSha256'] and current == prev['currentTarget']
        recommendation_match = bool(prev['recommendedTarget']) and current_hash == prev['recommendedTargetSha256'] and current == prev['recommendedTarget']
        # Validate the old packet's pinned caller refs at the current exact commit as well.
        old_ref_checks = []
        for ref in prev['callerRefs']:
            path = ref['file']
            if path not in ref_file_bytes:
                raw = git_blob(path)
                ref_file_bytes[path] = {'bytes': raw, 'lines': raw.decode('utf-8').splitlines(),
                                        'blob': blob_id(path), 'sha256': sha(raw)}
            info = ref_file_bytes[path]
            if info['blob'] != ref['currentFileBlob'] or info['sha256'] != ref['currentFileSha256']:
                raise RuntimeError(f'W599 caller pin drift in {path}')
            _, _, _, checks = check_context(info['lines'], ref)
            old_ref_checks.append(all(checks.values()))
        if not source_match or not all(old_ref_checks):
            raise RuntimeError(f'W599 source/caller context failed for {locale}')
        prior_rows.append({
            'sourceOrdinal': 599, 'sourceId': previous_id, 'locale': locale,
            'previousPrimaryHead': prev['exactHead'], 'previousPrimaryTree': prev['exactTree'],
            'previousDisposition': prev['disposition'],
            'previousTarget': prev['currentTarget'], 'previousTargetSha256': prev['currentTargetSha256'],
            'previousRecommendation': prev['recommendedTarget'], 'previousRecommendationSha256': prev['recommendedTargetSha256'],
            'liveSource': w599_source, 'liveSourceSha256': sha(w599_source.encode('utf-8')),
            'liveTarget': current, 'liveTargetSha256': current_hash,
            'sourceMatches': source_match, 'previousTargetMatchesLive': current_match,
            'previousRecommendationMatchesLive': recommendation_match,
            'callerRefCount': len(prev['callerRefs']), 'callerRefsAllReattested': all(old_ref_checks),
        })
    if sum(x['previousTargetMatchesLive'] for x in prior_rows) != 6 or sum(x['previousRecommendationMatchesLive'] for x in prior_rows) != 6:
        raise RuntimeError('W599 boundary does not match expected 6 old targets / 6 applied recommendations')
    save_jsonl('boundary-reattestation.jsonl', prior_rows)

    next_ordinal = 650
    next_id = source_ids[next_ordinal]
    next_source = source_catalog[next_id]
    next_boundary = [{'sourceOrdinal': 650, 'sourceId': next_id, 'locale': loc,
                      'source': next_source, 'sourceTextSha256': sha(next_source.encode('utf-8')),
                      'liveTarget': catalogs[loc][next_id], 'liveTargetSha256': value_sha(catalogs[loc][next_id]),
                      'targetFile': catalog_meta[loc]['path'], 'targetFileBlob': catalog_meta[loc]['blob'],
                      'targetFileSha256': catalog_meta[loc]['sha256'], 'nextSourceOnlyContext': True}
                     for loc in LOCALES]
    save_jsonl('boundary-next-source-650.jsonl', next_boundary)

    # Final one-row-per-cell cross-review result.
    candidate_review_by_key = {(r['sourceOrdinal'], r['locale']): r for r in candidate_reviews}
    final_rows = []
    for cell in live_cells:
        key = (cell['sourceOrdinal'], cell['locale'])
        adjudicated = candidate_review_by_key.get(key)
        if adjudicated:
            verdict = adjudicated['crossReviewVerdict']
            target = adjudicated['crossReviewTarget']
            reason = adjudicated['rationale']
        else:
            verdict = 'accept-current'
            target = cell['currentTarget']
            reason = 'Current translation independently retained after exact source, catalog, caller, placeholder, markup, and protected-literal reattestation.'
        primary_cell = primary_cell_by_key[key]
        casefold = {check['literal'] for check in primary_cell['protectedLiteralChecks'] if check['matchMode'] == 'case-insensitive'}
        final_checks = text_checks(cell['source'], target, primary_cell['protectedLiterals'], casefold)
        if not all(final_checks[k] for k in ['placeholderParity', 'markupParity', 'protectedLiteralsPreserved']):
            raise RuntimeError(f'final target structural/literal failure {key}: {final_checks}')
        final_rows.append({
            'sourceOrdinal': cell['sourceOrdinal'], 'sourceId': cell['sourceId'], 'locale': cell['locale'],
            'sourceTextSha256': cell['sourceTextSha256'], 'currentTarget': cell['currentTarget'],
            'currentTargetSha256': cell['currentTargetSha256'], 'primaryDisposition': cell['primaryDisposition'],
            'crossReviewDisposition': verdict, 'finalTarget': target, 'finalTargetSha256': value_sha(target),
            'rationale': reason, 'callerContextSha256': cell['liveCallerContextSha256'],
            'finalTextChecks': final_checks,
            'exactHead': HEAD, 'exactTree': TREE,
        })
    save_jsonl('final-dispositions.jsonl', final_rows)
    missed = [{
        'sourceOrdinal': ordinal, 'sourceId': next(x['sourceId'] for x in source_slice if x['sourceOrdinal'] == ordinal),
        'locale': locale, 'type': 'wrong-source-semantics-in-primary-proposal',
        'primaryTarget': next(x['recommendedTarget'] for x in candidates if x['sourceOrdinal'] == ordinal and x['locale'] == locale),
        'replacementTarget': target, 'rationale': rationale,
        'callerEvidence': next(x['callerRefs'] for x in source_slice if x['sourceOrdinal'] == ordinal),
        'primaryProposalRejected': True,
    } for (ordinal, locale), (target, rationale) in W621_REPLACEMENTS.items()]
    save_jsonl('missed-issues.jsonl', missed)

    primary_counts = collections.Counter(x['disposition'] for x in cells)
    candidate_counts = collections.Counter(x['crossReviewVerdict'] for x in candidate_reviews)
    final_counts = collections.Counter(x['crossReviewDisposition'] for x in final_rows)
    summary = {
        'task': 'ChaptarrNG PR #190 W600–649 independent cross-review',
        'repository': OWNER_REPO, 'pullRequest': PR_NUMBER, 'livePrState': pr_state,
        'head': HEAD, 'tree': TREE, 'sourceOrdinalRange': [600, 649],
        'sourceIdCount': len(source_rows), 'localeCount': len(LOCALES), 'liveCellsReattested': len(live_cells),
        'callerReferencesReattested': len(caller_rows), 'callerFilesReattested': len(ref_file_bytes),
        'candidateRowsAdjudicated': len(candidate_reviews), 'primaryDispositionCounts': dict(primary_counts),
        'candidateVerdicts': dict(candidate_counts), 'finalDispositionCounts': dict(final_counts),
        'proposalsAccepted': candidate_counts['accept-primary-proposal'],
        'proposalsRejectedAndReplaced': candidate_counts['reject-primary-proposal-replace-with-corrected-target'],
        'holds': 0, 'replacementTargetsProvided': len(missed), 'missedIssueCount': len(missed),
        'candidateTargetHashMismatches': 0, 'currentTargetHashMismatches': 0,
        'sourceTextHashMismatches': 0, 'callerLineOrBlobMismatches': 0,
        'placeholderParityFailures': 0, 'markupParityFailures': 0,
        'currentProtectedLiteralMismatchCells': len(current_literal_mismatch_rows),
        'finalProtectedLiteralMismatchCells': 0,
        'sourceIdListCount': len(source_ids), 'sourceIdListSha256': source_list_hash,
        'w599PriorTargetMatchesLive': sum(x['previousTargetMatchesLive'] for x in prior_rows),
        'w599PriorRecommendationsMatchLive': sum(x['previousRecommendationMatchesLive'] for x in prior_rows),
        'w599CallerRefsReattested': sum(x['callerRefCount'] for x in prior_rows),
        'w650BoundaryRows': len(next_boundary), 'nativeSpeakerApproval': False,
        'repositoryOrPrModified': False,
        'testsBuildsScansCiBrowserWorkflowsReleasesRun': False,
        'limitations': ['Machine-assisted independent review; native-speaker approval remains outstanding.',
                        'Three primary W621 proposals were rejected as unrelated to the pinned source/caller and replaced with context-accurate suggestions.'],
    }
    input_sums = {'checksumFileSha256': input_sums_file_sha, 'entries': input_manifest_checks}
    save_json('live-pr-state.json', pr_state)
    save_json('primary-input-integrity.json', {
        'primaryPath': str(PRIMARY), 'primaryChecksumManifestSha256': primary_sums['checksumFileSha256'],
        'primaryFilesVerified': primary_sums['entries'], 'inputChecksumManifestSha256': input_sums['checksumFileSha256'],
        'exactHeadInputFilesVerified': input_manifest_checks, 'sourceFile': source_info,
        'sourceFollowupFile': follow_info, 'registryFile': registry_info, 'localeCatalogs': catalog_meta,
        'priorW599PacketChecksum': prior_sums_check,
    })
    save_json('summary.json', summary)
    readme = f'''# ChaptarrNG PR #190 W600–649 independent cross-review\n\nPinned to live PR #{PR_NUMBER} at `{HEAD}` / tree `{TREE}`; PR state remains open/draft. The primary packet’s supplied `SHA256SUMS` digest is `{primary_sums['checksumFileSha256']}` and all listed files verify. Its exact-head source/catalog input hashes also verify.\n\n## Findings\n\n- Reattested all 600 current source/target cells, 64 caller references across {len(ref_file_bytes)} exact C# files, and each of the 201 candidate recommendation hashes.\n- Rebuilt and checked the 1,210-ID ordered source list; positions 600–649 match the primary slice.\n- Rechecked the W599 previous-window edge: the source/callers match; 6 current targets still match the older primary values and 6 match that packet’s recommendations after application. Reattested the next source W650 across 12 locales.\n- Candidate outcomes: {candidate_counts['accept-primary-proposal']} primary proposals accepted; {candidate_counts['reject-primary-proposal-replace-with-corrected-target']} rejected and replaced; no holds.\n- The three W621 primary targets for “Category is recommended” instead ask which books to monitor when adding discovered authors. The pinned caller is a qBittorrent warning for an absent audiobook category. Replacements are recorded in `missed-issues.jsonl`.\n- Rechecked placeholders, markup, protected literals, and hashes. The primary has 15 current protected-literal misses; all proposed and cross-review final targets preserve them.\n- The repository and PR were not modified. No tests, builds, scans, CI, browser actions, workflow edits, releases, or tags were run. Native-speaker approval remains outstanding.\n\n## Packet files\n\n- `live-cell-reattestation.jsonl` — 600 exact-head source/current catalog rows and hashes.\n- `caller-ref-reattestation.jsonl` — 64 line, context, blob, and file hash checks.\n- `boundary-reattestation.jsonl` and `boundary-next-source-650.jsonl` — W599 and W650 edges.\n- `candidate-cross-review.jsonl` — independent disposition of all 201 proposals.\n- `missed-issues.jsonl` — three rejected W621 targets and replacements.\n- `final-dispositions.jsonl` — one final decision for each of 600 cells.\n\nAll packet files are checksummed in `SHA256SUMS`.\n'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')
    manifest_out = {
        'schemaVersion': 1, 'task': summary['task'], 'repository': OWNER_REPO, 'pullRequest': PR_NUMBER,
        'attestedHead': HEAD, 'attestedTree': TREE, 'primaryPacket': str(PRIMARY),
        'rows': {'sources': len(source_rows), 'cells': len(live_cells), 'callerReferences': len(caller_rows),
                 'candidateReviews': len(candidate_reviews), 'w599Boundary': len(prior_rows),
                 'w650Boundary': len(next_boundary), 'missedIssues': len(missed), 'finalDispositions': len(final_rows)},
        'repositoryOrPrModified': False,
    }
    save_json('manifest.json', manifest_out)
    sums = []
    for path in sorted(OUT.iterdir()):
        if path.name == 'SHA256SUMS' or not path.is_file():
            continue
        sums.append(f'{sha(path.read_bytes())}  {path.name}')
    (OUT / 'SHA256SUMS').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
