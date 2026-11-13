#!/usr/bin/env python3
"""Build a read-only independent cross-review packet from the pinned PR and primary evidence."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path('/home/keith/Documents/code/chaptarrng')
HEAD = '015ff68d96340292b5e6a45d34496a5936ebf09c'
TREE = 'bbb59a14a50a4b63bc209663c1e4b873ead4fc10'
PRIMARY = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0550-0599-primary-20261102')
OUT = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0550-0599-crossreview-20261102')
REPO_SLUG = 'snapetech-org/chaptarrng'
LOCALES = ['es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']
LOCALE_FILES = {
    'es': 'es.json', 'zh-Hans': 'zh_CN.json', 'hi': 'hi.json', 'de': 'de.json',
    'ja': 'ja.json', 'fr': 'fr.json', 'pt-BR': 'pt_BR.json', 'ar': 'ar.json',
    'ko': 'ko.json', 'zh-Hant': 'zh_TW.json', 'vi': 'vi.json', 'id': 'id.json'
}
CATALOG_ROOT = 'src/NzbDrone.Core/Localization/Core/'
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}')
TAG_RE = re.compile(r'</?[A-Za-z][^>]*>')

# Independent caller-context notes checked against exact-head source lines and adjacent code.
CONTEXT = {
  550: 'API conversion returns a validation error when authorId is absent; authorId is an exact API field literal.',
  551: 'Root-folder validation rejects ebook settings on audiobook-only folders.',
  552: 'The proxy enum value ProxyEverything is supported; IndexerOnly is the recommended performance choice.',
  553: 'SABnzbd settings validation tells the user to disable the Date Sorting feature.',
  554: 'A series lookup failed for the substituted series identifier {value0}.',
  555: 'The operation failed to apply a narrator to every book in a series.',
  556: 'Metadata-server configuration requires a URL beginning with http:// or https://.',
  557: 'Metadata-refresh preflight failed while re-adding an author; the existing author was not deleted.',
  558: 'qBittorrent reports an error state on a torrent, surfaced as a warning.',
  559: 'An import-list connection failed; {value0} identifies the failing list and the log gives details.',
  560: 'The torrent client could not return its torrent list; {value0} is the client error detail.',
  561: 'NzbGet KeepHistory validation rejects values greater than 25000; the exact 25000 value is accepted by the pinned condition.',
  562: 'Root-folder validation rejects ebook-only folders for audiobook selection and directs users to Audiobook or Mixed roots.',
  563: 'Goodreads bookshelf retrieval requires the correct user ID and public shelves.',
  564: 'A configured host must be a host name/address without an http:// scheme.',
  565: 'The provider connection failure indicates SSL is required.',
  566: 'The application could not connect to the configured Subsonic server.',
  567: 'RSS sync interval accepts 0 to disable, or a value from 10 through 120 minutes.',
  568: 'The API requires between 1 and 500 positive sourceIds.',
  569: 'The API request requires an API token.',
  570: 'The configured uTorrent client is too old; API version 3.0 or later is needed.',
  571: 'The requested pattern field is required.',
  572: 'The route ID must equal the ID of the addressed resource.',
  573: 'The application could not connect to the configured Transmission server.',
  574: 'The configured folder path {value0} does not exist; create it or correct the path.',
  575: 'A valid absolute URL is required.',
  576: 'The configured folder does not exist.',
  577: 'The application failed to import an author from the selected provider.',
  578: 'Goodreads series data could not be retrieved.',
  579: 'The request body must not be empty.',
  580: 'The AuthorMediaMoveController moves author media; the instruction is to preview the move before starting it.',
  581: 'The supplied API key is incorrect.',
  582: 'entityType is restricted to the exact enum values Author, AuthorMetadata, Book, Edition, or BookFile.',
  583: 'The proxy test uses testUrl and reports its response status code; this is a network proxy, not a human agent.',
  584: 'Authentication failed; the caller advises checking both the API key and server type.',
  585: 'The metadata-server ping response could not be parsed as JSON; {value0} is the parse error detail.',
  586: 'Only Hardcover series identifiers are accepted, using the literal form hc:{id}.',
  587: 'Metadata-server configuration requires a URL.',
  588: 'Connection to Emby or Jellyfin failed; {value0} is the error detail.',
  589: 'The user must authenticate with Plex.tv before continuing.',
  590: 'Each selected book must carry a foreignAuthorId for the add-series operation.',
  591: 'The image download completed successfully.',
  592: 'The validation rule requires the exact substring chaptarr.',
  593: 'No image was found in the author metadata.',
  594: 'A configured metadata-server URL must begin with http:// or https://.',
  595: 'The image download is currently in progress.',
  596: 'selectedMediaType accepts the exact values audiobook or ebook.',
  597: 'The selected edition is checked against BookMediaType; the caller distinguishes audiobook from ebook.',
  598: 'The Kavita integration rejects an incorrect ApiKey; preserve its exact casing.',
  599: 'The application could not connect to SABnzbd.',
}

# Cross-review revisions and new findings. These remain proposals in scratch evidence only.
REVISIONS = {
  (555, 'id'): {
    'disposition': 'propose-correction',
    'target': 'Gagal menerapkan narator ke semua buku dalam seri.',
    'rationale': 'The primary candidate contains the Vietnamese word “trong” inside Indonesian text; “dalam” supplies the intended Indonesian “in”.'
  },
  (583, 'ar'): {
    'disposition': 'propose-correction',
    'target': 'فشل اختبار البروكسي عبر {value0} برمز الحالة {value1}.',
    'rationale': 'This caller tests a network proxy. “الوكيل” can mean an agent or representative; “البروكسي” is the clear networking term already used by the current Arabic target.'
  },
  (583, 'ko'): {
    'disposition': 'propose-correction',
    'target': '프록시 테스트가 실패했습니다. 테스트 URL: {value0}, 상태 코드: {value1}.',
    'rationale': 'The caller passes testUrl as {value0}; “테스트 URL” identifies the value precisely, while the primary candidate’s “relay address” is ambiguous.'
  },
  (574, 'ar'): {
    'disposition': 'propose-refinement',
    'target': 'المجلد "{value0}" غير موجود. يُرجى إنشاء الدليل أولًا أو التحقق من المسار.',
    'rationale': 'The current target joins the missing-folder statement and instruction without a sentence break. This wording separates them and preserves the folder placeholder.'
  },
  (580, 'de'): {
    'disposition': 'propose-correction',
    'target': 'Zeigen Sie vor dem Start eine Vorschau der Verschiebung an.',
    'rationale': 'The current target says to preview a generic operation. The pinned caller moves media, so the target should name the move.'
  },
  (580, 'ja'): {
    'disposition': 'propose-correction',
    'target': '移動を開始する前に、移動内容をプレビューしてください。',
    'rationale': 'The current target says to preview a generic operation. The pinned caller moves media, so the target should name the move.'
  },
  (580, 'fr'): {
    'disposition': 'propose-correction',
    'target': 'Prévisualisez le déplacement avant de le lancer.',
    'rationale': 'The current target says to preview a generic operation. The pinned caller moves media, so the target should name the move.'
  },
  (580, 'pt-BR'): {
    'disposition': 'propose-correction',
    'target': 'Confira a prévia da movimentação antes de iniciá-la.',
    'rationale': 'The current target says to preview a generic operation. The pinned caller moves media, so the target should name the move.'
  },
  (580, 'ar'): {
    'disposition': 'propose-correction',
    'target': 'اعرض معاينة لعملية النقل قبل بدء تنفيذها.',
    'rationale': 'The current target says to preview a generic operation. The pinned caller moves media, so the target should name the move.'
  },
  (597, 'vi'): {
    'disposition': 'propose-refinement',
    'target': 'Phiên bản được chọn không khớp với loại sách được yêu cầu.',
    'rationale': 'The current phrase for “media type” is literal and awkward. The caller compares audiobook and ebook editions, so “loại sách” states the relevant book type more naturally.'
  },
}

# W561 is held because its English source and runtime threshold differ at exactly 25000.
# These behavior-based alternatives are recorded for parent review, not accepted as final targets.
W561_OPTIONS = {
  'es': 'El valor de KeepHistory en NzbGet no debe superar 25000.',
  'zh-Hans': 'NzbGet 的 KeepHistory 设置不得超过 25000。',
  'hi': 'NzbGet में KeepHistory सेटिंग 25000 से अधिक नहीं होनी चाहिए。',
  'de': 'Der Wert der NzbGet-Einstellung KeepHistory darf 25000 nicht überschreiten.',
  'ja': 'NzbGet の KeepHistory 設定値は 25000 を超えてはいけません。',
  'fr': 'La valeur du paramètre KeepHistory dans NzbGet ne doit pas dépasser 25000.',
  'pt-BR': 'O valor da configuração KeepHistory no NzbGet não pode exceder 25000.',
  'ar': 'يجب ألا تتجاوز قيمة إعداد KeepHistory في NzbGet 25000.',
  'ko': 'NzbGet의 KeepHistory 설정값은 25000을 초과하면 안 됩니다.',
  'zh-Hant': 'NzbGet 的 KeepHistory 設定不得超過 25000。',
  'vi': 'Giá trị cài đặt KeepHistory trong NzbGet không được vượt quá 25000.',
  'id': 'Nilai pengaturan KeepHistory di NzbGet tidak boleh melebihi 25000.',
}


def run(args, *, cwd=None, binary=False):
    return subprocess.check_output(args, cwd=cwd, text=not binary)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def jbytes(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def save_json(path, obj):
    (OUT / path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_jsonl(path, rows):
    (OUT / path).write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def git_blob(path):
    return run(['git', 'show', f'{HEAD}:{path}'], cwd=REPO, binary=True)


def git_blob_id(path):
    return run(['git', 'rev-parse', f'{HEAD}:{path}'], cwd=REPO).strip()


def placeholders(text):
    return sorted(set(PLACEHOLDER_RE.findall(text)))


def markup(text):
    if re.fullmatch(r'<[^<>/]+>', text):
        return []
    return TAG_RE.findall(text)


def check_refs(refs):
    result = []
    for ref in refs:
        data = git_blob(ref['file'])
        blob = git_blob_id(ref['file'])
        text = data.decode('utf-8')
        lines = text.splitlines()
        line_no = ref.get('currentLine')
        idx = line_no - 1 if isinstance(line_no, int) else -1
        exact = 0 <= idx < len(lines) and lines[idx] == ref.get('currentLineText')
        line_sha_ok = exact and sha(lines[idx].encode('utf-8')) == ref.get('currentLineSha256')
        actual_before = lines[max(0, idx - len(ref.get('contextBefore', []))):idx] if idx >= 0 else []
        actual_after = lines[idx + 1:idx + 1 + len(ref.get('contextAfter', []))] if idx >= 0 else []
        context_ok = exact and actual_before == ref.get('contextBefore', []) and actual_after == ref.get('contextAfter', [])
        result.append({
            'file': ref['file'], 'kind': ref.get('kind'), 'currentLine': line_no,
            'currentLineText': ref.get('currentLineText'), 'currentLineSha256': ref.get('currentLineSha256'),
            'liveLineSha256': sha(lines[idx].encode('utf-8')) if exact else None,
            'lineExactAtRecordedNumber': exact, 'lineHashMatches': line_sha_ok, 'adjacentContextMatches': context_ok,
            'currentFileBlob': blob, 'expectedFileBlob': ref.get('currentFileBlob'),
            'fileBlobMatches': blob == ref.get('currentFileBlob'), 'currentFileSha256': sha(data),
            'expectedFileSha256': ref.get('currentFileSha256'), 'fileSha256Matches': sha(data) == ref.get('currentFileSha256'),
            'passed': exact and line_sha_ok and context_ok and blob == ref.get('currentFileBlob') and sha(data) == ref.get('currentFileSha256')
        })
    return result


def protected_checks(source, target, literals):
    return [{'literal': lit, 'presentInSource': lit in source, 'presentInTarget': (lit in target) if target is not None else None}
            for lit in literals]


def token_checks(source, target):
    source_ph, target_ph = placeholders(source), placeholders(target) if target is not None else None
    source_markup, target_markup = markup(source), markup(target) if target is not None else None
    # Compare multiplicity as well as token spelling/order; this is stricter than the primary set check.
    ph_ok = target is not None and collections.Counter(PLACEHOLDER_RE.findall(source)) == collections.Counter(PLACEHOLDER_RE.findall(target))
    markup_ok = target is not None and source_markup == target_markup
    return {
        'sourcePlaceholders': source_ph, 'targetPlaceholders': target_ph, 'placeholderParity': ph_ok,
        'sourceMarkup': source_markup, 'targetMarkup': target_markup, 'markupParity': markup_ok
    }


def live_pr_state():
    pr = json.loads(run(['gh', 'api', f'repos/{REPO_SLUG}/pulls/190']))
    commit = json.loads(run(['gh', 'api', f'repos/{REPO_SLUG}/commits/{pr["head"]["sha"]}']))
    return {
        'repository': REPO_SLUG, 'number': pr['number'], 'state': pr['state'], 'draft': pr['draft'],
        'head': pr['head']['sha'], 'headRef': pr['head']['ref'], 'baseRef': pr['base']['ref'],
        'tree': commit['commit']['tree']['sha'], 'url': pr['html_url'],
        'exactExpectedHead': pr['head']['sha'] == HEAD, 'exactExpectedTree': commit['commit']['tree']['sha'] == TREE,
        'passed': pr['number'] == 190 and pr['state'] == 'open' and pr['draft'] is True and pr['head']['sha'] == HEAD and commit['commit']['tree']['sha'] == TREE
    }


def verify_primary_checksums():
    checked_packet = 0
    for line in (PRIMARY / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if sha((PRIMARY / name).read_bytes()) != digest:
            raise SystemExit(f'primary packet checksum mismatch: {name}')
        checked_packet += 1
    checked_repo = 0
    for line in (PRIMARY / 'INPUT-SHA256SUMS').read_text().splitlines():
        digest, path = line.split('  ', 1)
        if sha(git_blob(path)) != digest:
            raise SystemExit(f'primary input hash mismatch at exact head: {path}')
        checked_repo += 1
    return {'primaryPacketFilesChecked': checked_packet, 'pinnedRepositoryInputsChecked': checked_repo}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    allowed_existing = {'build_crossreview.py', 'README.md', 'SHA256SUMS', 'manifest.json', 'live-pr-state.json',
                        'live-cell-hash-reattestation.jsonl', 'caller-reattestation.jsonl',
                        'caller-reference-reattestation.jsonl', 'W549-boundary-reattestation.jsonl',
                        'candidate-cross-review.jsonl', 'full-cell-final-dispositions.jsonl',
                        'revisions-and-holds.json', 'summary.json'}
    if any(p.name not in allowed_existing for p in OUT.iterdir()):
        raise SystemExit(f'refusing to overwrite unexpected output in task directory: {OUT}')
    if run(['git', 'rev-parse', f'{HEAD}^{{tree}}'], cwd=REPO).strip() != TREE:
        raise SystemExit('pinned commit tree mismatch')

    pr = live_pr_state()
    if not pr['passed']:
        raise SystemExit('live PR is not open/draft at the pinned head/tree: ' + json.dumps(pr))

    checksum_result = verify_primary_checksums()
    cells = load_jsonl(PRIMARY / 'review-cells.jsonl')
    candidates = load_jsonl(PRIMARY / 'correction-candidates.jsonl')
    caller_rows = load_jsonl(PRIMARY / 'caller-context.jsonl')
    prior549 = [r for r in load_jsonl(PRIMARY / 'prior-context-dispositions.jsonl') if r.get('contextSourceOrdinal') == 549]
    if len(cells) != 600 or len(candidates) != 271 or len(caller_rows) != 50 or len(prior549) != 12:
        raise SystemExit('primary packet row count drift')
    cell_by_key = {(r['sourceOrdinal'], r['locale']): r for r in cells}
    cand_by_key = {(r['sourceOrdinal'], r['locale']): r for r in candidates}
    if len(cell_by_key) != 600 or set(cand_by_key) != {k for k, r in cell_by_key.items() if r['disposition'] in ('propose-correction', 'propose-refinement')}:
        raise SystemExit('primary candidate/cell correspondence mismatch')
    followup = json.loads(git_blob('docs/localization/source-followup-20261101.json'))
    source_ids = list(dict.fromkeys(r['sourceId'] for r in cells))
    expected_ids = followup['currentMissingIds'][550:600]
    if len(followup['currentMissingIds']) != 1210 or len(set(followup['currentMissingIds'])) != 1210 or source_ids != expected_ids:
        raise SystemExit('W550–599 source IDs do not match the exact source-followup list slice')
    expected_keys = [(ordinal, locale) for ordinal in range(550, 600) for locale in LOCALES]
    if [(r['sourceOrdinal'], r['locale']) for r in cells] != expected_keys:
        raise SystemExit('primary cell order or locale coverage mismatch')
    primary_counts = collections.Counter(r['disposition'] for r in cells)
    if primary_counts != collections.Counter({'accept-current': 329, 'propose-correction': 240, 'propose-refinement': 31}):
        raise SystemExit(f'primary disposition counts mismatch: {dict(primary_counts)}')
    if any(r['exactHead'] != HEAD or r['exactTree'] != TREE for r in cells + candidates):
        raise SystemExit('primary row exact-head/tree mismatch')

    source_path = 'src/NzbDrone.Core/Localization/Core/en.json'
    source_data = git_blob(source_path)
    source_catalog = json.loads(source_data)
    catalogs = {}
    catalog_info = {}
    for locale, file in LOCALE_FILES.items():
        path = CATALOG_ROOT + file
        raw = git_blob(path)
        catalogs[locale] = json.loads(raw)
        catalog_info[locale] = {'path': path, 'blob': git_blob_id(path), 'sha256': sha(raw), 'bytes': len(raw)}

    reattest = []
    final_rows = []
    candidate_rows = []
    pcounts = collections.Counter()
    verdict_counts = collections.Counter()
    candidate_verdict_counts = collections.Counter()
    token_mismatch_counts = collections.Counter()
    protected_mismatch_counts = collections.Counter()
    for row in cells:
        key = (row['sourceOrdinal'], row['locale'])
        ordinal, locale = key
        sid = row['sourceId']
        candidate = cand_by_key.get(key)
        source_live = source_catalog.get(sid)
        current_live = catalogs[locale].get(sid)
        if source_live != row['source'] or current_live != row['currentTarget']:
            raise SystemExit(f'catalog value drift at {ordinal}|{locale}')
        if sha(source_live.encode()) != row['sourceTextSha256'] or sha(current_live.encode()) != row['currentTargetSha256']:
            raise SystemExit(f'source/current string hash mismatch at {ordinal}|{locale}')
        if sha(sid.encode()) != row['sourceKeySha256']:
            raise SystemExit(f'source key hash mismatch at {ordinal}|{locale}')
        if git_blob_id(row['sourceFile']) != row['sourceFileBlob'] or sha(git_blob(row['sourceFile'])) != row['sourceFileSha256']:
            raise SystemExit(f'source file blob/hash mismatch at {ordinal}|{locale}')
        if git_blob_id(row['targetFile']) != row['targetFileBlob'] or sha(git_blob(row['targetFile'])) != row['targetFileSha256']:
            raise SystemExit(f'target file blob/hash mismatch at {ordinal}|{locale}')
        if row['callerContextSha256'] != sha(jbytes(row['callerRefs'])):
            raise SystemExit(f'primary caller-context digest mismatch at {ordinal}|{locale}')
        caller = next(c for c in caller_rows if c['sourceOrdinal'] == ordinal)
        if caller['sourceId'] != sid or caller['callerContextSha256'] != sha(jbytes(caller['callerRefs'])) or caller['callerContextSha256'] != row['callerContextSha256']:
            raise SystemExit(f'caller context row mismatch at {ordinal}|{locale}')
        if row['callerRefs'] != caller['callerRefs']:
            raise SystemExit(f'caller reference payload mismatch at {ordinal}|{locale}')

        primary_target = candidate['recommendedTarget'] if candidate else None
        primary_target_hash = candidate['recommendedTargetSha256'] if candidate else None
        if candidate and (primary_target is None or sha(primary_target.encode()) != primary_target_hash):
            raise SystemExit(f'primary candidate hash mismatch at {ordinal}|{locale}')
        if candidate and (candidate['source'] != source_live or candidate['currentTarget'] != current_live or
                          candidate['sourceTextSha256'] != row['sourceTextSha256'] or
                          candidate['currentTargetSha256'] != row['currentTargetSha256'] or
                          candidate['callerContextSha256'] != row['callerContextSha256']):
            raise SystemExit(f'candidate source/current/caller row mismatch at {ordinal}|{locale}')
        current_tokens = token_checks(source_live, current_live)
        current_literals = protected_checks(source_live, current_live, row['protectedLiterals'])
        if not current_tokens['placeholderParity']:
            token_mismatch_counts['currentPlaceholder'] += 1
        if not current_tokens['markupParity']:
            token_mismatch_counts['currentMarkup'] += 1
        if any(not c['presentInSource'] or not c['presentInTarget'] for c in current_literals):
            protected_mismatch_counts['current'] += 1
        if not current_tokens['placeholderParity'] or not current_tokens['markupParity'] or any(not c['presentInSource'] or not c['presentInTarget'] for c in current_literals):
            raise SystemExit(f'current target placeholder/markup/protected-literal mismatch at {ordinal}|{locale}')
        primary_tokens = token_checks(source_live, primary_target) if primary_target is not None else None
        primary_literals = protected_checks(source_live, primary_target, row['protectedLiterals']) if primary_target is not None else None
        if primary_tokens and not primary_tokens['placeholderParity']:
            token_mismatch_counts['primaryCandidatePlaceholder'] += 1
        if primary_tokens and not primary_tokens['markupParity']:
            token_mismatch_counts['primaryCandidateMarkup'] += 1
        if primary_literals and any(not c['presentInSource'] or not c['presentInTarget'] for c in primary_literals):
            protected_mismatch_counts['primaryCandidate'] += 1
        if primary_tokens and (not primary_tokens['placeholderParity'] or not primary_tokens['markupParity'] or any(not c['presentInSource'] or not c['presentInTarget'] for c in primary_literals)):
            raise SystemExit(f'primary candidate placeholder/markup/protected-literal mismatch at {ordinal}|{locale}')
        final_disposition = row['disposition']
        final_target = primary_target if candidate else current_live
        verdict = 'accept-primary-candidate' if candidate else 'retain-primary-accept-current'
        context_note = CONTEXT[ordinal]
        reason = (f'The pinned caller confirms this context: {context_note} Compared the {locale} candidate with the English source and current target; it conveys the intended message and preserves required placeholders, markup, and technical literals.'
                  if candidate else f'The pinned caller confirms this context: {context_note} Compared the current {locale} target with the English source; it conveys the intended message without a material terminology or meaning issue.')
        alternate = None
        if key in REVISIONS:
            change = REVISIONS[key]
            final_disposition, final_target = change['disposition'], change['target']
            verdict = 'revise-primary-candidate' if candidate else 'new-review-finding'
            reason = change['rationale']
        elif ordinal == 561:
            final_disposition = 'hold'
            final_target = None
            verdict = 'hold-primary-candidate'
            alternate = W561_OPTIONS[locale]
            reason = ('Hold: the English source says “should be less than 25000,” while the pinned Nzbget.cs branch rejects only values greater than 25000 and accepts exactly 25000. The primary below-25000 wording would make the same stricter claim as the English source and does not match the caller behavior. Keep this locale on hold until the English wording is resolved; the optional behavior-based target states that the value must not exceed 25000.')
        elif key in REVISIONS:
            pass

        if final_target is not None:
            checks = token_checks(source_live, final_target)
            protected = protected_checks(source_live, final_target, row['protectedLiterals'])
            if not checks['placeholderParity'] or not checks['markupParity'] or any(not c['presentInSource'] or not c['presentInTarget'] for c in protected):
                raise SystemExit(f'final token/markup/protected-literal mismatch at {ordinal}|{locale}')
        else:
            checks = {'sourcePlaceholders': placeholders(source_live), 'targetPlaceholders': None,
                      'placeholderParity': None, 'sourceMarkup': markup(source_live), 'targetMarkup': None,
                      'markupParity': None, 'status': 'held-no-approved-target'}
            protected = protected_checks(source_live, None, row['protectedLiterals'])
        option_checks = token_checks(source_live, alternate) if alternate else None
        option_literals = protected_checks(source_live, alternate, row['protectedLiterals']) if alternate else None
        if alternate and (not option_checks['placeholderParity'] or not option_checks['markupParity'] or any(not c['presentInSource'] or not c['presentInTarget'] for c in option_literals)):
            raise SystemExit(f'behavior option token/markup/protected-literal mismatch at {ordinal}|{locale}')

        ref_checks = check_refs(row['callerRefs'])
        if not all(x['passed'] for x in ref_checks):
            raise SystemExit(f'caller ref reattestation failed at {ordinal}|{locale}')
        caller_digest = row['callerContextSha256']
        # Ensure final proposals that change a row retain exact runtime/API literal spelling.
        source_line_files = sorted({x['file'] for x in ref_checks})
        entry = {
            'repository': REPO_SLUG, 'pullRequest': 190, 'exactHead': HEAD, 'exactTree': TREE,
            'sourceOrdinal': ordinal, 'sourceId': sid, 'locale': locale, 'source': source_live,
            'sourceTextSha256': sha(source_live.encode()), 'sourceKeySha256': sha(sid.encode()),
            'sourceFile': row['sourceFile'], 'sourceFileBlob': git_blob_id(row['sourceFile']), 'sourceFileSha256': sha(git_blob(row['sourceFile'])),
            'targetFile': row['targetFile'], 'targetFileBlob': git_blob_id(row['targetFile']), 'targetFileSha256': sha(git_blob(row['targetFile'])),
            'currentTarget': current_live, 'currentTargetSha256': sha(current_live.encode()),
            'primaryDisposition': row['disposition'], 'primaryTarget': primary_target, 'primaryTargetSha256': primary_target_hash,
            'crossReviewVerdict': verdict, 'finalDisposition': final_disposition, 'finalTarget': final_target,
            'finalTargetSha256': sha(final_target.encode()) if final_target is not None else None,
            'behaviorBasedOption': alternate, 'behaviorBasedOptionSha256': sha(alternate.encode()) if alternate else None,
            'confidence': 'moderate', 'independentRationale': reason, 'sourceCallerContextSummary': context_note, 'callerRefs': row['callerRefs'],
            'callerContextSha256': caller_digest, 'callerRefFiles': source_line_files, 'callerRefReattestations': ref_checks,
            'currentTokenChecks': current_tokens, 'currentProtectedLiteralChecks': current_literals,
            'primaryCandidateTokenChecks': primary_tokens, 'primaryCandidateProtectedLiteralChecks': primary_literals,
            'finalTokenChecks': checks, 'finalProtectedLiteralChecks': protected,
            'behaviorOptionTokenChecks': option_checks, 'behaviorOptionProtectedLiteralChecks': option_literals,
            'nativeSpeakerApproval': False
        }
        pcounts[final_disposition] += 1
        verdict_counts[verdict] += 1
        if candidate:
            candidate_verdict_counts[verdict] += 1
        reattest.append({
            'sourceOrdinal': ordinal, 'sourceId': sid, 'locale': locale,
            'sourceFile': row['sourceFile'], 'expectedSourceFileBlob': row['sourceFileBlob'], 'liveSourceFileBlob': git_blob_id(row['sourceFile']),
            'sourceFileBlobMatches': git_blob_id(row['sourceFile']) == row['sourceFileBlob'],
            'sourceFileSha256Matches': sha(git_blob(row['sourceFile'])) == row['sourceFileSha256'],
            'sourceValueMatches': source_live == row['source'], 'sourceTextSha256': sha(source_live.encode()),
            'targetFile': row['targetFile'], 'expectedTargetFileBlob': row['targetFileBlob'], 'liveTargetFileBlob': git_blob_id(row['targetFile']),
            'targetFileBlobMatches': git_blob_id(row['targetFile']) == row['targetFileBlob'],
            'targetFileSha256Matches': sha(git_blob(row['targetFile'])) == row['targetFileSha256'],
            'currentTargetMatches': current_live == row['currentTarget'], 'currentTargetSha256': sha(current_live.encode()),
            'primaryCandidatePresent': candidate is not None, 'primaryCandidateSha256': primary_target_hash,
            'primaryCandidateHashMatches': (candidate is None or sha(primary_target.encode()) == primary_target_hash),
            'finalDisposition': final_disposition, 'finalTargetSha256': entry['finalTargetSha256'],
            'currentPlaceholderParity': current_tokens['placeholderParity'], 'currentMarkupParity': current_tokens['markupParity'],
            'primaryCandidatePlaceholderParity': primary_tokens['placeholderParity'] if primary_tokens else None,
            'primaryCandidateMarkupParity': primary_tokens['markupParity'] if primary_tokens else None,
            'currentProtectedLiteralParity': all(c['presentInSource'] and c['presentInTarget'] for c in current_literals),
            'primaryCandidateProtectedLiteralParity': all(c['presentInSource'] and c['presentInTarget'] for c in primary_literals) if primary_literals else None,
            'passed': True
        })
        final_rows.append(entry)
        if candidate:
            candidate_rows.append(entry.copy())

    # Exact production caller attestations: one source-level row and one detailed row per callsite.
    caller_summary = []
    caller_ref_rows = []
    total_refs = 0
    unique_files = set()
    for caller in caller_rows:
        refs = caller['callerRefs']
        checked = check_refs(refs)
        if caller['callerContextSha256'] != sha(jbytes(refs)) or not all(x['passed'] for x in checked):
            raise SystemExit(f'caller source attestation failed at {caller["sourceOrdinal"]}')
        total_refs += len(refs)
        unique_files.update(r['file'] for r in refs)
        caller_summary.append({
            'sourceOrdinal': caller['sourceOrdinal'], 'sourceId': caller['sourceId'], 'sourceText': caller['sourceText'],
            'callerReferenceStatus': caller['callerReferenceStatus'], 'callerContextSha256': caller['callerContextSha256'],
            'callerRefCount': len(refs), 'callerRefs': checked, 'passed': True
        })
        for ref, result in zip(refs, checked):
            caller_ref_rows.append({
                'sourceOrdinal': caller['sourceOrdinal'], 'sourceId': caller['sourceId'], 'callerContextSha256': caller['callerContextSha256'],
                'reference': ref, 'reattestation': result
            })
    if len(caller_rows) != 50 or total_refs != 69 or len(unique_files) != 42:
        raise SystemExit('caller inventory count mismatch')

    # Adjacent W549 boundary: compare its prior decisions with the exact current PR catalogs and caller.
    boundary_rows = []
    for prior in prior549:
        locale = prior['locale']
        sid = prior['sourceId']
        live_source = source_catalog.get(sid)
        target_path = CATALOG_ROOT + LOCALE_FILES[locale]
        live_target = catalogs[locale].get(sid)
        if live_source != prior['source'] or sha(live_source.encode()) != prior['sourceTextSha256']:
            raise SystemExit(f'W549 live source mismatch for {locale}')
        refs = prior.get('liveCallerRefs') or prior.get('priorCallerRefs') or []
        checked = check_refs(refs)
        if not refs or not all(x['passed'] for x in checked):
            raise SystemExit(f'W549 caller reattestation failed for {locale}')
        old_current_match = live_target == prior['priorCurrentTarget']
        old_recommendation_match = prior['priorRecommendedTarget'] is not None and live_target == prior['priorRecommendedTarget']
        boundary_rows.append({
            'contextSourceOrdinal': 549, 'sourceId': sid, 'locale': locale,
            'source': live_source, 'sourceTextSha256': sha(live_source.encode()), 'sourceMatchesPrior': True,
            'priorPrimaryHead': prior['priorPrimaryPacketHead'], 'priorPrimaryTree': prior['priorPrimaryPacketTree'],
            'priorDisposition': prior['priorDisposition'], 'priorCurrentTarget': prior['priorCurrentTarget'],
            'priorCurrentTargetSha256': prior['priorCurrentTargetSha256'], 'priorRecommendedTarget': prior['priorRecommendedTarget'],
            'priorRecommendedTargetSha256': prior['priorRecommendedTargetSha256'], 'liveCurrentTarget': live_target,
            'liveCurrentTargetSha256': sha(live_target.encode()), 'liveTargetFile': target_path,
            'liveTargetFileBlob': git_blob_id(target_path), 'liveTargetFileSha256': sha(git_blob(target_path)),
            'priorCurrentTargetMatchesLive': old_current_match, 'priorRecommendationMatchesLive': old_recommendation_match,
            'callerRefs': checked, 'callerContextSha256': prior['callerContextSha256'],
            'passed': True
        })
    old_match_count = sum(r['priorCurrentTargetMatchesLive'] for r in boundary_rows)
    rec_match_count = sum(r['priorRecommendationMatchesLive'] for r in boundary_rows)
    if len(boundary_rows) != 12 or old_match_count != 8 or rec_match_count != 4:
        raise SystemExit('W549 boundary counts differ from primary packet claim')

    save_json('live-pr-state.json', pr)
    save_jsonl('live-cell-hash-reattestation.jsonl', reattest)
    save_jsonl('caller-reattestation.jsonl', caller_summary)
    save_jsonl('caller-reference-reattestation.jsonl', caller_ref_rows)
    save_jsonl('W549-boundary-reattestation.jsonl', boundary_rows)
    save_jsonl('candidate-cross-review.jsonl', candidate_rows)
    save_jsonl('full-cell-final-dispositions.jsonl', final_rows)

    revised_rows = [r for r in final_rows if r['crossReviewVerdict'] in ('revise-primary-candidate', 'new-review-finding')]
    held_rows = [r for r in final_rows if r['finalDisposition'] == 'hold']
    findings = {
      'candidateTextRevisions': [
        {'sourceOrdinal': r['sourceOrdinal'], 'sourceId': r['sourceId'], 'locale': r['locale'], 'primaryTarget': r['primaryTarget'], 'recommendedTarget': r['finalTarget'], 'rationale': r['independentRationale']}
        for r in revised_rows if r['crossReviewVerdict'] == 'revise-primary-candidate'
      ],
      'newFindingsOnPrimaryAcceptCurrent': [
        {'sourceOrdinal': r['sourceOrdinal'], 'sourceId': r['sourceId'], 'locale': r['locale'], 'currentTarget': r['currentTarget'], 'recommendedTarget': r['finalTarget'], 'finalDisposition': r['finalDisposition'], 'rationale': r['independentRationale']}
        for r in revised_rows if r['crossReviewVerdict'] == 'new-review-finding'
      ],
      'holds': [
        {'sourceOrdinal': r['sourceOrdinal'], 'sourceId': r['sourceId'], 'locale': r['locale'], 'primaryTarget': r['primaryTarget'], 'behaviorBasedOption': r['behaviorBasedOption'], 'rationale': r['independentRationale']}
        for r in held_rows
      ]
    }
    save_json('revisions-and-holds.json', findings)

    summary = {
      'schemaVersion': 1, 'task': 'Independent read-only cross-review of ChaptarrNG PR #190 W550-599 primary packet',
      'repository': REPO_SLUG, 'pullRequest': 190, 'exactHead': HEAD, 'exactTree': TREE,
      'livePrState': {'state': pr['state'], 'draft': pr['draft'], 'head': pr['head'], 'tree': pr['tree'], 'passed': pr['passed']},
      'primaryPacket': str(PRIMARY), 'primaryChecksums': checksum_result,
      'scope': {'positions': [550, 599], 'sourceIds': 50, 'locales': LOCALES, 'cells': 600,
                'candidateRows': len(candidates), 'callerSourceRows': len(caller_rows), 'callerReferences': total_refs, 'callerFiles': len(unique_files)},
      'primaryDispositionCounts': dict(primary_counts),
      'finalDispositions': dict(pcounts), 'allCellCrossReviewVerdicts': dict(verdict_counts),
      'candidateCrossReviewVerdicts': dict(candidate_verdict_counts),
      'primaryCandidates': {'acceptedAsProposed': candidate_verdict_counts['accept-primary-candidate'],
                            'revised': candidate_verdict_counts['revise-primary-candidate'], 'held': candidate_verdict_counts['hold-primary-candidate']},
      'additionalFindingsOnAcceptedCurrent': len([r for r in revised_rows if r['crossReviewVerdict'] == 'new-review-finding']),
      'W549Boundary': {'rows': len(boundary_rows), 'priorCurrentTargetsStillLive': old_match_count,
                       'priorRecommendationsNowLive': rec_match_count, 'allSourceHashesMatch': True, 'allCallerRefsReattested': True},
      'mechanicalIntegrity': {'all600SourceAndCurrentTargetsReattested': len(reattest) == 600,
                              'allCallerContextHashesMatch': True, 'all69CallerRefsReattested': len(caller_ref_rows) == 69,
                              'tokenParityMismatches': dict(token_mismatch_counts),
                              'protectedLiteralMismatchCells': dict(protected_mismatch_counts),
                              'finalProposalProtectedLiteralMismatches': sum(1 for r in final_rows if r['finalTarget'] is not None and not all(c['presentInSource'] and c['presentInTarget'] for c in r['finalProtectedLiteralChecks'])),
                              'candidateCurrentHashMismatches': 0},
      'heldIssue': {'sourceOrdinal': 561, 'affectedLocales': LOCALES,
                    'runtimeBehavior': 'Nzbget.cs rejects value > 25000; value 25000 passes.',
                    'englishSource': 'NzbGet setting KeepHistory should be less than 25000',
                    'resolution': 'Hold all 12 targets until English source wording is decided; record behavior-based “must not exceed 25000” options separately.'},
      'semanticReview': {'confidence': 'moderate', 'nativeSpeakerApproval': False, 'browserReview': False,
                         'findings': findings},
      'constraints': {'repositoryCatalogEdits': False, 'pullRequestWrites': False, 'testsBuildsScansCi': False,
                     'browserActions': False, 'workflowEdits': False, 'releases': False},
      'repositoryStatus': run(['git', 'status', '--short', '--branch'], cwd=REPO).strip()
    }
    save_json('summary.json', summary)
    (OUT / 'README.md').write_text(f'''# ChaptarrNG PR #190 W550–599 independent cross-review

- Exact PR state reattested as open/draft at `{HEAD}` / tree `{TREE}`.
- Scope: 50 source strings × 12 locales = 600 exact source/current/candidate cells. The primary packet manifest and all its listed source/catalog inputs were independently checksum-verified.
- Primary disposition counts reattested: 329 accept-current, 240 corrections, and 31 refinements.
- Exact source and current catalog values were re-read from the pinned commit. All 600 source/current hashes, candidate hashes, caller-context hashes, placeholders (including multiplicity), markup, and protected literals were checked.
- Caller review: {len(caller_rows)}/50 source rows, {total_refs} references across {len(unique_files)} files, reattested against exact line text, adjacent context, blob IDs, and file SHA-256.
- Primary candidate outcomes: {verdict_counts['accept-primary-candidate']} retained, {verdict_counts['revise-primary-candidate']} revised, {verdict_counts['hold-primary-candidate']} held. There are {len(revised_rows) - verdict_counts['revise-primary-candidate']} new findings on cells the primary marked accept-current.
- Final cell dispositions: {dict(pcounts)}.
- Revised candidates: `555|id`, `583|ar`, `583|ko`. New current-target findings: `574|ar`, `580|de`, `580|ja`, `580|fr`, `580|pt-BR`, `580|ar`, `597|vi`.
- Hold: all 12 W561 cells. The English source says KeepHistory “should be less than 25000,” while the pinned caller rejects only values above 25000 and accepts exactly 25000. Locale options that say “must not exceed 25000” are recorded separately in `revisions-and-holds.json`; they are not accepted targets until the English source wording is decided.
- W549 boundary: 12 source/locale rows and caller context reattested; 8 older current targets still match, and 4 prior recommendations now match the live catalog.
- This is a model cross-review, not native-speaker approval. No catalog edits, PR writes, tests/builds/scans/CI, browser actions, workflow edits, or releases were performed.

Detailed records are in `candidate-cross-review.jsonl`, `full-cell-final-dispositions.jsonl`, `live-cell-hash-reattestation.jsonl`, `caller-reattestation.jsonl`, `caller-reference-reattestation.jsonl`, and `W549-boundary-reattestation.jsonl`. `SHA256SUMS` checksums every packet file except itself.
''', encoding='utf-8')

    # Capture packet inventory and checksums; manifest is included in the checksum set.
    inventory = []
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name not in ('manifest.json', 'SHA256SUMS'):
            raw = path.read_bytes()
            inventory.append({'path': path.name, 'bytes': len(raw), 'sha256': sha(raw)})
    manifest = {'schemaVersion': 1, 'repository': REPO_SLUG, 'pullRequest': 190, 'head': HEAD, 'tree': TREE,
                'outputDirectory': str(OUT), 'files': inventory}
    save_json('manifest.json', manifest)
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    (OUT / 'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files), encoding='utf-8')
    for line in (OUT / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if sha((OUT / name).read_bytes()) != digest:
            raise SystemExit(f'output checksum failure: {name}')
    final_pr = live_pr_state()
    if not final_pr['passed']:
        raise SystemExit('PR moved while packet was built; inspect live-pr-state and preserve this evidence')
    print(json.dumps({'packet': str(OUT), 'head': HEAD, 'tree': TREE, 'cells': len(final_rows),
                      'candidateRows': len(candidate_rows), 'finalDispositions': dict(pcounts),
                      'candidateVerdicts': dict(candidate_verdict_counts), 'callerRefs': total_refs, 'callerFiles': len(unique_files),
                      'W549PriorCurrentStillLive': old_match_count, 'W549PriorRecommendationsNowLive': rec_match_count,
                      'packetFiles': len(files) + 1, 'packetBytes': sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),
                      'checksumManifestSha256': sha((OUT / 'SHA256SUMS').read_bytes())}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
