#!/usr/bin/env python3
"""Build the pinned ChaptarrNG PR #190 W250-W299 independent cross-review packet."""
from __future__ import annotations
import collections
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TASK = Path('/home/keith/Documents/code/task-scratch')
OUT = TASK / 'chaptarrng-pr190-w250-299-cross-20261104'
CANDIDATE = TASK / 'chaptarrng-pr190-w250-299-core-20261104/candidate-free/input'
PRIMARY = TASK / 'chaptarrng-pr190-w250-299-core-20261104/primary-review'
BLIND = TASK / 'chaptarrng-pr190-w250-299-independent-blind-20261104'
REPO = Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-next-window')
HEAD = '2a9995a2bf63f06814bd8780736305f16bd6b33a'
TREE = 'f6ae6530b73bf581c1fbc5a8c13eacd7342e9172'
MAIN = '9a44e91c96cd9f2eac1a351b1366f63c26b2ffc3'
API_BASE = '17bde320915af42de73b8646ad56f8ba2ccebf4e'
BRANCH = 'codex/chaptarrng-localization-complete-20261031'
LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH = re.compile(r'\{[^{}]+\}')
INLINE = re.compile(r'`([^`]+)`')
MARKUP = re.compile(r'<[^>]+>')
NUMBER = re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

CUSTOM = {
    'AutomaticUpdatesDisabledDocker::id': {
        'selectedTarget': 'Anda perlu memperbarui gambar kontainer di luar {appName} atau menggunakan skrip.',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F001'],
        'reviewConfidence': 'high',
        'rationale': 'The current Indonesian coordinates “harus memperbarui” with the imperative “gunakan.” “Atau menggunakan” keeps the source alternatives parallel and leaves the {appName} placeholder intact.'
    },
    'BlocklistReleaseHelpText::de': {
        'selectedTarget': 'Verhindert, dass Chaptarr diese Dateien automatisch erneut herunterlädt.',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F003'],
        'reviewConfidence': 'moderate',
        'rationale': 'The exact caller is the queue-removal blocklist setting. Here “erneut erfasst” can mean recorded; “erneut herunterlädt” states that automatic downloads are prevented.'
    },
    'BackupsContainUnencryptedCredentials::ar': {
        'selectedTarget': 'تشمل النسخ الاحتياطية الكاملة بيانات الاعتماد. بدون ملف سري مُثبّت ومُهيأ عبر CHAPTARR_BACKUP_ENCRYPTION_KEY_FILE، تُخزَّن النسخ الاحتياطية كملفات ZIP عادية. تظل النسخة الاحتياطية لإعدادات البدء السريع تصديرًا منفصلًا مشفرًا بعبارة مرور.',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F005'],
        'reviewConfidence': 'moderate',
        'rationale': 'The current final clause renders the named Settings Backup as “quick settings support.” This wording names the Quickstart settings backup as a separate export. It also states explicitly that the backups, rather than the credentials, are stored as ZIP files. The environment identifier is preserved.'
    },
    'BackupsContainUnencryptedCredentials::fr': {
        'selectedTarget': 'Les sauvegardes complètes incluent les identifiants. Sans fichier secret monté et configuré via CHAPTARR_BACKUP_ENCRYPTION_KEY_FILE, les sauvegardes sont stockées sous forme de fichiers ZIP non chiffrés. La sauvegarde des paramètres du démarrage rapide reste un export distinct chiffré à l’aide d’une phrase de passe.',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F006'],
        'reviewConfidence': 'moderate',
        'rationale': 'The current masculine pronoun “ils” has the nearby masculine plural “identifiants” as an antecedent and can say credentials are stored as ZIP files. Repeating “les sauvegardes” makes the stored object explicit and preserves the environment identifier.'
    },
    'BindAddress::de': {
        'selectedTarget': 'Bind-Adresse',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F008'],
        'reviewConfidence': 'moderate',
        'rationale': 'The caller is a server host setting whose help text accepts an IP address, localhost, or all interfaces. “Bind-Adresse” is a noun field label; the current “Adresse binden” is an action phrase.'
    },
    'BindAddress::es': {
        'selectedTarget': 'Dirección de escucha',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F008'],
        'reviewConfidence': 'moderate',
        'rationale': 'The caller is a server host setting whose help text accepts an IP address, localhost, or all interfaces. “Dirección de escucha” identifies the server listening address; “dirección de enlace” can be read as a link address.'
    },
    'BindAddress::pt-BR': {
        'selectedTarget': 'Endereço de escuta',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F008'],
        'reviewConfidence': 'moderate',
        'rationale': 'The caller is a server host setting whose help text accepts an IP address, localhost, or all interfaces. “Endereço de escuta” names the server listening address; the current wording is an imperative.'
    },
    'BlocklistAndSearchMultipleHint::de': {
        'selectedTarget': 'Nach dem Hinzufügen zur Sperrliste mit der Suche nach Alternativen beginnen.',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F009'],
        'reviewConfidence': 'moderate',
        'rationale': 'This hint is selected when multiple queue items are selected. The current sentence refers to one alternative and one item; this wording describes starting a search for alternatives after adding items to the blocklist.'
    },
    'BlocklistAndSearchMultipleHint::zh-Hans': {
        'selectedTarget': '将这些项目列入黑名单后，开始搜索替代资源。',
        'selectedFrom': 'cross-review-new-from-blind-finding', 'basisFindingIds': ['F009'],
        'reviewConfidence': 'moderate',
        'rationale': 'The caller selects this hint for multiple queue items. The current “搜索替换” reads as the search-and-replace operation; this wording says to search for replacement resources after blocklisting the items.'
    },
    'BlocklistAndSearchMultipleHint::vi': {
        'selectedTarget': 'Sau khi đưa các mục vào danh sách chặn, hãy bắt đầu tìm kiếm các bản phát hành thay thế.',
        'selectedFrom': 'cross-review-refinement-of-primary', 'basisFindingIds': ['F009'],
        'reviewConfidence': 'moderate',
        'rationale': 'The primary correction fixes the unnatural blocklisting phrase. I refined it to name replacement releases, which matches the queue caller and avoids the broader “replacement items.”'
    },
    'EncryptedBackupPassphraseHelpText::vi': {
        'selectedTarget': 'Sử dụng ít nhất 16 ký tự và giữ cụm từ mật khẩu riêng biệt với bản sao lưu. Chaptarr không thể khôi phục cụm từ mật khẩu đã mất.',
        'selectedFrom': 'cross-review-locale-convention-refinement', 'basisFindingIds': [],
        'reviewConfidence': 'high',
        'rationale': 'The primary proposal distinguishes a passphrase from a password, but the pinned Vietnamese catalog already uses “Cụm từ mật khẩu” for SettingsBackupPassphrase and SettingsBackupConfirmPassphrase. This matches that established term and retains the 16-character requirement and Chaptarr brand.'
    },
    'EncryptedBackupPassphraseMismatch::vi': {
        'selectedTarget': 'Các cụm từ mật khẩu không khớp nhau.',
        'selectedFrom': 'cross-review-locale-convention-refinement', 'basisFindingIds': [],
        'reviewConfidence': 'high',
        'rationale': 'The primary proposal distinguishes passphrases from passwords. I used the exact established Vietnamese catalog term “cụm từ mật khẩu” from SettingsBackupPassphrase and SettingsBackupPassphrasesDoNotMatch.'
    },
    'EncryptedBackupRestoreHelpText::vi': {
        'selectedTarget': 'Nhập cụm từ mật khẩu đã dùng khi tạo bản sao lưu này. Bản sao lưu sẽ được khôi phục và Chaptarr sẽ khởi động lại.',
        'selectedFrom': 'cross-review-locale-convention-refinement', 'basisFindingIds': [],
        'reviewConfidence': 'high',
        'rationale': 'The primary proposal distinguishes a passphrase from a password. I used the established Vietnamese catalog term “cụm từ mật khẩu” from SettingsBackupPassphrase and retained the restore and restart behavior.'
    }
}

FINDING_ADJUDICATIONS = [
    {'findingId':'F001','disposition':'accept-and-correct','cells':['AutomaticUpdatesDisabledDocker::id'],'rationale':'Indonesian verb coordination is uneven; the cross candidate coordinates both alternatives.'},
    {'findingId':'F002','disposition':'accept-and-correct','cells':['BackfillAuthorRootFoldersHelpText::id'],'rationale':'The current Indonesian means newly/recently assigned, while the helper selects authors with a root for only one format. Use the primary correction.'},
    {'findingId':'F003','disposition':'accept-and-correct','cells':['BlocklistReleaseHelpText::de','BlocklistReleaseHelpText::es','BlocklistReleaseHelpText::fr','BlocklistReleaseHelpText::id'],'rationale':'In the pinned queue caller, grabbing means downloading/fetching files again. Use primary targets for es/fr/id and a cross target for de.'},
    {'findingId':'F004','disposition':'accept-and-correct','cells':['BackupRetentionHelpText::id'],'rationale':'“Periode penahanan” means detention; use the primary retention-period correction.'},
    {'findingId':'F005','disposition':'accept-and-correct','cells':['BackupsContainUnencryptedCredentials::ar'],'rationale':'The final clause changes the named Settings Backup export into “support”; the cross candidate names the backup and states its separate passphrase encryption.'},
    {'findingId':'F006','disposition':'accept-and-correct','cells':['BackupsContainUnencryptedCredentials::fr'],'rationale':'The masculine plural pronoun can refer to credentials; the cross candidate explicitly names the backups as the stored object.'},
    {'findingId':'F007','disposition':'accept-and-correct','cells':['DownloadEncryptedBackup::vi'],'rationale':'The primary correction gives the Vietnamese button a natural verb-object order.'},
    {'findingId':'F008','disposition':'accept-and-correct','cells':['BindAddress::de','BindAddress::es','BindAddress::hi','BindAddress::pt-BR'],'rationale':'The setting is the server listening/bind address. Use a technical noun label in de, es, pt-BR, and the primary Hindi correction.'},
    {'findingId':'F009','disposition':'accept-and-correct','cells':['BlocklistAndSearchMultipleHint::de','BlocklistAndSearchMultipleHint::vi','BlocklistAndSearchMultipleHint::zh-Hans'],'rationale':'The multiple-selection caller requires plural alternatives and an unambiguous post-blocklist search. Use cross targets in de/zh-Hans and refine the primary Vietnamese target.'},
    {'findingId':'F010','disposition':'accept-and-correct','cells':['BlocklistOnlyHint::vi'],'rationale':'The current Vietnamese calls the replacement a person; use the primary release/item wording.'},
    {'findingId':'F011','disposition':'reject-false-positive','cells':['Book::ar','Book::de','Book::es','Book::fr','Book::hi','Book::id','Book::ja','Book::ko','Book::pt-BR','Book::vi','Book::zh-Hans','Book::zh-Hant'],'rationale':'The pinned literal caller uses Book as the history table column for each book, and AuthorHistoryRow renders its book title. All 12 current targets are lexical book labels, not count labels (Chinese and Japanese forms are number-neutral); the separate BookCount source key names the numeric count. Keep the current targets.'}
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_text(text: str) -> str:
    return sha_bytes(text.encode('utf-8'))

def row_sha(row: dict) -> str:
    return sha_text(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')))

def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')

def write_jsonl(path: Path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')

def token_counts(rx, text):
    return collections.Counter(rx.findall(text))

def number_counts(text):
    return token_counts(NUMBER, PH.sub('', text))

def main():
    if not OUT.is_dir():
        raise SystemExit(f'cross output directory was not pre-created: {OUT}')
    owned = {'build_cross_review.py','verify_cross_review.py','README.md','SHA256SUMS.txt','base-drift-comparison.json','caller-evidence.json','cross-review-cells.jsonl','cross-review-summary.json','decision-reconciliation.json','live-pr-attestation.json','manifest.json','review-selections.json','selected-changes.jsonl'}
    unexpected = [p.name for p in OUT.iterdir() if p.name not in owned]
    if unexpected:
        raise SystemExit(f'unexpected task-scratch files in cross output directory: {unexpected}')

    # Verify the exact local source worktree pin and cleanliness.
    head = subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'], text=True).strip()
    tree = subprocess.check_output(['git','-C',str(REPO),'show','-s','--format=%T',HEAD], text=True).strip()
    dirty = subprocess.check_output(['git','-C',str(REPO),'status','--porcelain=v1'], text=True).strip()
    if (head, tree, dirty) != (HEAD, TREE, ''):
        raise SystemExit(f'exact source worktree mismatch: {head} {tree} dirty={bool(dirty)}')

    crows = read_jsonl(CANDIDATE/'candidate-free-cells.jsonl')
    prows = read_jsonl(PRIMARY/'primary-review-cells.jsonl')
    bkeys = read_jsonl(BLIND/'blind-cell-review.jsonl')
    pproposals = read_jsonl(PRIMARY/'primary-review-proposals.jsonl')
    findings = read_json(BLIND/'findings.json')
    caller_rows = read_jsonl(CANDIDATE/'caller-context.jsonl')
    candidate_summary = read_json(CANDIDATE/'candidate-free-summary.json')
    primary_summary = read_json(PRIMARY/'primary-review-summary.json')
    blind_summary = read_json(BLIND/'summary.json')
    blind_manifest = read_json(BLIND/'manifest.json')
    if len(crows) != 600 or len(prows) != 600 or len(bkeys) != 600:
        raise SystemExit('expected 600 rows from each input packet')
    if len(pproposals) != 33 or primary_summary['counts']['proposals'] != 33:
        raise SystemExit('primary proposal count mismatch')
    if blind_summary['dispositions'] != {'accept-current':570,'hold':30}:
        raise SystemExit('blind input counts mismatch')
    if any(r['exactHead'] != HEAD or r['exactTree'] != TREE for r in prows):
        raise SystemExit('primary exact pin mismatch')
    if candidate_summary['exactHead'] != HEAD or candidate_summary['exactTree'] != TREE:
        raise SystemExit('candidate-free exact pin mismatch')
    if primary_summary['exactHead'] != HEAD or primary_summary['exactTree'] != TREE:
        raise SystemExit('primary summary pin mismatch')
    if blind_manifest['sourceRefs']['head'] != HEAD or blind_manifest['sourceRefs']['tree'] != TREE:
        raise SystemExit('blind manifest exact pin mismatch')

    c_by = {(r['sourceOrdinal'],r['locale']):r for r in crows}
    p_by = {(r['sourceOrdinal'],r['locale']):r for r in prows}
    b_by = {(r['sourceOrdinal'],r['locale']):r for r in bkeys}
    pp_by = {r['cellId']:r for r in pproposals}
    f_by = {f['findingId']:f for f in findings}
    if len(c_by) != 600 or len(p_by) != 600 or len(b_by) != 600:
        raise SystemExit('duplicate input cell identity')
    ids = {r['sourceKey']+'::'+r['locale'] for r in crows}
    if set(CUSTOM) - ids:
        raise SystemExit('custom target outside this window: '+repr(sorted(set(CUSTOM)-ids)))
    if set(pp_by) - ids:
        raise SystemExit('primary proposal outside this window')
    if any(r['callerReferenceCount'] <= 0 for r in crows):
        raise SystemExit('callerless cell in this window; stop and do not draft a text-bearing recommendation')
    ordinals = sorted({r['sourceOrdinal'] for r in crows})
    if ordinals != list(range(250,300)):
        raise SystemExit('source-order window has a gap/overlap')
    keys_by_ordinal = {o:{r['sourceKey'] for r in crows if r['sourceOrdinal']==o} for o in ordinals}
    if any(len(keys_by_ordinal[o]) != 1 for o in ordinals):
        raise SystemExit('source ordinal maps to multiple keys')
    if any(sum(r['sourceOrdinal']==o for r in crows) != 12 for o in ordinals):
        raise SystemExit('a source key is not represented by all 12 locales')
    if set(r['locale'] for r in crows) != set(LOCALES):
        raise SystemExit('locale set mismatch')

    # Check the reviewer-to-candidate-free joins before adjudicating.
    for key, c in c_by.items():
        p = p_by[key]
        b = b_by[key]
        if p['candidateFreeRowSha256'] != row_sha(c):
            raise SystemExit(f'primary candidate-free row hash mismatch: {key}')
        if (b['currentTargetSha256'] != c['currentTargetSha256'] or b.get('sourceTextSha256') != c['sourceTextSha256']
                or b.get('callerReferenceCount') != c['callerReferenceCount'] or b.get('callerBacked') is not True
                or b.get('sourceKey') != c['sourceKey'] or b.get('locale') != c['locale']):
            raise SystemExit(f'blind current/source/caller linkage mismatch: {key}')
        if c['sourceTextSha256'] != sha_text(c['sourceText']) or c['currentTargetSha256'] != sha_text(c['currentTarget']):
            raise SystemExit(f'candidate-free text hash mismatch: {key}')

    # Fresh filtered live PR/ref attestation captured during this review; no PR body/object body read.
    attestation = {
        'repository':'snapetech-org/ChaptarrNG', 'pullRequest':190,
        'verifiedWindowUTC':['2026-11-04T22:04:52Z','2026-11-04T22:04:56Z'],
        'filteredQueriesOnly':True, 'fullPullRequestBodyRetrieved':False,
        'pr':{'state':'OPEN','draft':True,'headRefName':BRANCH,'headSha':HEAD,'baseRefName':'main','baseSha':API_BASE,'url':'https://github.com/snapetech-org/chaptarrng/pull/190'},
        'branchApi':{'ref':BRANCH,'sha':HEAD}, 'pullRef':{'ref':'refs/pull/190/head','sha':HEAD},
        'remoteHeads':{'refs/heads/main':MAIN}, 'currentMain':MAIN,
        'sourceWorktree':{'path':str(REPO),'head':head,'tree':tree,'clean':True}
    }
    compare_files = [
        '.github/workflows/bookshelfng-api-differential.yml','.github/workflows/bookshelfng-standalone-macos-acceptance.yml','.github/workflows/standalone-asset-validation.yml','AGENTS.md','docs/BOOKSHELFNG_RETIREMENT.md','docs/localization/provider-field-sources.json','docs/localization/provider-option-sources.json','docs/localization/server-message-sources.json','integration/README.md','integration/bookshelfng-api-contract.mjs','integration/bookshelfng-api-differential.compose.yml','integration/bookshelfng-api-differential.mjs','integration/normalize-bookshelfng-api-differential-fixture.py','integration/run-bookshelfng-api-differential.sh','integration/test-bookshelfng-api-contract.mjs','packaging/scripts/test-bookshelf-legacy-channels.mjs','packaging/scripts/test-bookshelf-standalone-handoff.py','packaging/scripts/test-docker-bookshelf-compatibility-defaults.sh','scripts/test_bookshelfng_helm_install_handoff.sh','scripts/test_workflow_runner_policy.py','src/Chaptarr.Api.V1/Author/AuthorController.cs','src/Chaptarr.Api.V1/Author/AuthorResource.cs','src/Chaptarr.Api.V1/Books/BookController.cs','src/Chaptarr.Api.V1/Books/BookControllerWithSignalR.cs','src/Chaptarr.Api.V1/Books/BookEditorController.cs','src/Chaptarr.Api.V1/Books/BookResource.cs','src/Chaptarr.Api.V1/Books/ReadarrFacadeEditionIdentity.cs','src/Chaptarr.Api.V1/History/HistoryController.cs','src/Chaptarr.Api.V1/History/HistoryResource.cs','src/Chaptarr.Api.V1/Profiles/Quality/QualityProfileController.cs','src/Chaptarr.Api.V1/ProviderControllerBase.cs','src/Chaptarr.Api.V1/ProviderResource.cs','src/Chaptarr.Core.Test/Api/AuthorControllerMediaStatisticsFixture.cs','src/Chaptarr.Core.Test/Api/AuthorResourceBookshelfCompatibilityFixture.cs','src/Chaptarr.Core.Test/Api/BookControllerPagedResourceFixture.cs','src/Chaptarr.Core.Test/Api/BookControllerSiblingDeleteInfoFixture.cs','src/Chaptarr.Core.Test/Api/BookEditorControllerCompatibilityFixture.cs','src/Chaptarr.Core.Test/Api/ProviderResourceCompatibilityProjectionFixture.cs','src/Chaptarr.Core.Test/Api/Wanted/WantedMonitoringFilterFixture.cs','src/Chaptarr.Core.Test/AuthorStats/AuthorStatisticsImportDeferralFixture.cs','src/Chaptarr.Core.Test/AuthorStats/AuthorStatisticsRepositoryFixture.cs','src/Chaptarr.Core.Test/AuthorStats/AuthorStatisticsServiceFixture.cs','src/Chaptarr.Core.Test/Books/BookResourceMapperFixture.cs','src/Chaptarr.Core.Test/Datastore/BookshelfDatabaseImporterFixture.cs','src/Chaptarr.Core.Test/Datastore/Fixtures/BookshelfNG.PopulatedMigration158.sql','src/Chaptarr.Core.Test/History/HistoryResourceMapperFixture.cs','src/Chaptarr.Core.Test/Indexers/DirectDownloadSettingsFixture.cs','src/Chaptarr.Core.Test/Indexers/MyAnonaMouseSeedTimeFixture.cs','src/Chaptarr.Core.Test/MediaFiles/BookImport/CatalogIdentificationFallbackFixture.cs','src/Chaptarr.Core.Test/Profiles/Quality/QualityProfileControllerFixture.cs','src/Chaptarr.Http/ClientSchema/SchemaBuilder.cs','src/NzbDrone.Core/AuthorStats/AuthorStatisticsRepository.cs','src/NzbDrone.Core/AuthorStats/AuthorStatisticsService.cs','src/NzbDrone.Core/Books/BookFileStatisticsSql.cs','src/NzbDrone.Core/Books/Model/Author.cs','src/NzbDrone.Core/Books/Services/AuthorService.cs','src/NzbDrone.Core/Datastore/BookshelfDatabaseImporter.cs','src/NzbDrone.Core/Datastore/Migration/125_add_bookshelf_legacy_author_quality_profile_ids.cs','src/NzbDrone.Core/Indexers/MyAnonaMouse/MyAnonaMouseSettings.cs'
    ]
    drift = {'apiBase':API_BASE,'currentMain':MAIN,'status':'ahead','aheadBy':26,'behindBy':0,'changedFiles':compare_files,
             'containsCoreLocalizationSourceOrCatalogChanges':False,
             'assessment':'PR API base is behind live main. The compare file list contains no src/NzbDrone.Core/Localization/Core language catalog or English Core source file; it does contain server/API source and localization reference documentation changes. This review remains pinned to the requested PR head/tree.'}
    write_json(OUT/'live-pr-attestation.json',attestation)
    write_json(OUT/'base-drift-comparison.json',drift)

    # Deduplicate exact direct runtime localization callsites as caller evidence.
    caller_by_key = {r['sourceKey']:r for r in caller_rows}
    caller_evidence = {}
    for key in sorted(keys_by_ordinal[o].pop() for o in ordinals):
        cr = caller_by_key[key]
        cells = [r for r in crows if r['sourceKey']==key]
        contexts = sorted({r['callerContextSha256'] for r in cells})
        if len(contexts) != 1:
            raise SystemExit('caller context hash differs by locale for '+key)
        refs = cr.get('callerRefs',[])
        direct = [x for x in refs if x.get('isRuntimeReference') and x.get('referenceKind')=='literal-translate-call']
        caller_evidence[key] = {
            'callerContextSha256':contexts[0], 'callerReferenceCount':cr.get('callerReferenceCount',0),
            'literalCallCount':cr.get('literalCallCount',0), 'directRuntimeTranslationCallsites':direct
        }
    write_json(OUT/'caller-evidence.json',caller_evidence)

    finding_by_cell = collections.defaultdict(list)
    for f in findings:
        for blind_id in f['affectedCells']:
            # Blind identity is ordinal:key:locale.
            _, key, locale = blind_id.split(':',2)
            finding_by_cell[key+'::'+locale].append(f['findingId'])

    selected = []
    out_rows = []
    selections = {
        'batch':'W250-299-Core','head':HEAD,'tree':TREE,
        'primaryProposals':len(pp_by), 'primaryProposalCellsSelected':len(pp_by),
        'customTargets':CUSTOM,
        'findingAdjudications':FINDING_ADJUDICATIONS,
        'policy':'Select a primary target when independently corroborated or semantically sound; use cross-review refinements where existing locale conventions or exact caller context support a clearer target. Reconcile every blind hold; do not carry a hold without an evidence gap.'
    }
    write_json(OUT/'review-selections.json',selections)

    for key in sorted(c_by):
        c = c_by[key]
        p = p_by[key]
        b = b_by[key]
        cid = c['sourceKey']+'::'+c['locale']
        pp = pp_by.get(cid)
        custom = CUSTOM.get(cid)
        blind_fids = sorted(finding_by_cell.get(cid,[]))
        if custom:
            target = custom['selectedTarget']
            selected_from = custom['selectedFrom']
            rationale = custom['rationale']
            confidence = custom['reviewConfidence']
        elif pp:
            target = pp['recommendedTarget']
            selected_from = 'primary-review-candidate'
            rationale = pp['decisionRationale']
            confidence = pp['reviewConfidence']
        else:
            target = c['currentTarget']
            selected_from = 'accept-current'
            if 'F011' in blind_fids:
                rationale = FINDING_ADJUDICATIONS[-1]['rationale']
                confidence = 'high'
            elif c['sourceKey']=='BackupIntervalHelpText' and c['locale'] in {'ar','es','fr','pt-BR','zh-Hans','zh-Hant'}:
                rationale = 'The scanner flags DB because the translation expands it as the localized term for database; Chaptarr is preserved. In the backup interval caller, this expansion preserves meaning and does not drop a required identifier.'
                confidence = 'high'
            elif p['primaryDisposition']=='accept-current' and b['disposition']=='accept-current':
                rationale = 'Both the primary and blind reviews accepted this exact current target. The source, current-target, caller-context, placeholder, markup, inline-code, numeric, and protected-literal records are linked by the verified input hashes.'
                confidence = 'moderate'
            else:
                rationale = 'The exact pinned source and caller were rechecked; no target change is warranted after reconciling the primary and blind evidence.'
                confidence = 'moderate'

        if pp and custom:
            selected_from += '; primary proposal refined by cross-review'
        disposition = 'propose-change' if target != c['currentTarget'] else 'accept-current'
        target_sha = sha_text(target)
        placeholder_sig = token_counts(PH,target)
        inline_sig = token_counts(INLINE,target)
        markup_sig = token_counts(MARKUP,target)
        numeric_sig = number_counts(target)
        if placeholder_sig != token_counts(PH,c['sourceText']):
            raise SystemExit(f'placeholder parity failure: {cid}')
        if inline_sig != token_counts(INLINE,c['sourceText']):
            raise SystemExit(f'inline code parity failure: {cid}')
        if markup_sig != token_counts(MARKUP,c['sourceText']):
            raise SystemExit(f'markup parity failure: {cid}')
        if numeric_sig != number_counts(c['sourceText']):
            raise SystemExit(f'numeric token parity failure: {cid}')
        exceptions = []
        missing_literals = [lit for lit in c.get('protectedLiterals',[]) if lit not in target]
        if missing_literals:
            expected_db_expansion = c['sourceKey']=='BackupIntervalHelpText' and c['locale'] in {'ar','es','fr','pt-BR','zh-Hans','zh-Hant'} and missing_literals==['DB'] and target==c['currentTarget']
            if not expected_db_expansion:
                raise SystemExit(f'protected literal loss: {cid} {missing_literals}')
            exceptions.append({'literal':'DB','assessment':'expanded as the localized term for database; Chaptarr remains present'})
        row = {
            'batch':c['batch'],'cellId':cid,'sourceOrdinal':c['sourceOrdinal'],'sourceKey':c['sourceKey'],'locale':c['locale'],
            'sourceText':c['sourceText'],'sourceTextSha256':c['sourceTextSha256'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
            'recommendedTarget':target,'recommendedTargetSha256':target_sha,'exactHead':HEAD,'exactTree':TREE,
            'crossDisposition':disposition,'selectedFrom':selected_from,'crossRationale':rationale,'reviewConfidence':confidence,
            'primaryDisposition':p['primaryDisposition'],'blindDisposition':b['disposition'],'findingIds':blind_fids,
            'primaryCandidate':pp['recommendedTarget'] if pp else None,
            'primaryCandidateSha256':pp['recommendedTargetSha256'] if pp else None,
            'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,
            'callerReferenceCount':c['callerReferenceCount'],'literalCallCount':c['literalCallCount'],'callerContextSha256':c['callerContextSha256'],
            'callerEvidenceId':c['sourceKey'],'callerPaths':p.get('callerPaths',[]),
            'sourceFile':c['sourceFile'],'sourceFileGitBlob':c['sourceFileGitBlob'],'sourceFileSha256':c['sourceFileSha256'],
            'targetFile':c['targetFile'],'targetFileGitBlob':c['targetFileGitBlob'],'targetFileSha256':c['targetFileSha256'],
            'candidateFreeRowSha256':row_sha(c),'primaryReviewRowSha256':row_sha(p),'blindReviewRowSha256':row_sha(b),
            'sourcePlaceholders':c['sourcePlaceholders'],'currentPlaceholders':c['currentPlaceholders'],'recommendedPlaceholders':dict(placeholder_sig),
            'sourceInlineCode':c['sourceInlineCode'],'recommendedInlineCode':list(inline_sig.elements()),
            'sourceMarkup':c['sourceMarkup'],'recommendedMarkup':list(markup_sig.elements()),
            'sourceNumericTokens':c['sourceNumericTokens'],'recommendedNumericTokens':sorted(numeric_sig.elements()),
            'protectedLiterals':c['protectedLiterals'],'protectedLiteralExceptions':exceptions,
            'placeholderParity':True,'inlineCodeParity':True,'markupParity':True,'numericTokenParity':True
        }
        out_rows.append(row)
        if disposition=='propose-change':
            change = {k:row[k] for k in ['batch','cellId','sourceOrdinal','sourceKey','locale','sourceTextSha256','currentTarget','currentTargetSha256','recommendedTarget','recommendedTargetSha256','selectedFrom','crossRationale','reviewConfidence','findingIds','callerContextSha256','candidateFreeRowSha256','primaryReviewRowSha256','blindReviewRowSha256','exactHead','exactTree']}
            selected.append(change)

    counts = collections.Counter(r['crossDisposition'] for r in out_rows)
    primary_ids = set(pp_by)
    blind_holds = {c['sourceKey']+'::'+c['locale'] for (ord_,loc),b in b_by.items() if b['disposition']=='hold' for c in [c_by[(ord_,loc)]]}
    overlap = primary_ids & blind_holds
    if len(overlap)!=9 or len(blind_holds)!=30 or len(selected)!=42 or counts != {'accept-current':558,'propose-change':42}:
        raise SystemExit(f'adjudication count mismatch overlap={len(overlap)} blind={len(blind_holds)} selected={len(selected)} counts={counts}')
    if sum(1 for x in CUSTOM.values()) != 13:
        raise SystemExit('custom target count mismatch')
    if any(r['sourceKey']=='Book' and r['crossDisposition']!='accept-current' for r in out_rows):
        raise SystemExit('Book false-positive adjudication changed a current target')
    if any(r['sourceKey']=='Book' and 'F011' not in r['findingIds'] for r in out_rows):
        raise SystemExit('Book finding coverage mismatch')

    write_jsonl(OUT/'cross-review-cells.jsonl',out_rows)
    write_jsonl(OUT/'selected-changes.jsonl',selected)
    caller_book = caller_evidence['Book']['directRuntimeTranslationCallsites']
    if not any(x.get('path')=='frontend/src/Author/History/AuthorHistoryTableContent.js' and x.get('line')==22 for x in caller_book):
        raise SystemExit('Book history-table direct caller missing from caller evidence')

    overlap_ids=sorted(overlap)
    f011_cells=FINDING_ADJUDICATIONS[-1]['cells']
    technical_mismatches = [r['cellId'] for r in out_rows if r['protectedLiteralExceptions']]
    decisions = {
        'findingAdjudications':FINDING_ADJUDICATIONS,
        'primaryBlindProposalHoldOverlap':{'cells':overlap_ids,'count':len(overlap_ids)},
        'blindOnlyHoldCells':sorted(blind_holds-primary_ids),
        'rejectedF011FalsePositiveCells':f011_cells,
        'protectedLiteralScannerExceptions':{'cells':technical_mismatches,'count':len(technical_mismatches),'decision':'accept-current','rationale':'DB is expanded as a localized term for database; the Chaptarr brand remains intact and the source meaning is preserved.'},
        'placeholderReordering':{'cells':blind_summary['numericPlaceholderReordering']['cells'],'locales':blind_summary['numericPlaceholderReordering']['locales'],'assessment':blind_summary['numericPlaceholderReordering']['assessment'],'crossCheck':'Placeholder identifiers and occurrence counts are preserved; order may follow locale grammar.'},
        'blindReviewerDisclosure':blind_manifest['accidentalExposure']
    }
    write_json(OUT/'decision-reconciliation.json',decisions)

    cfmanifest = CANDIDATE/'candidate-free-manifest.json'
    input_hashes = {
        'candidateFreeManifestSha256':sha_bytes(cfmanifest.read_bytes()),
        'candidateFreeCellsSha256':sha_bytes((CANDIDATE/'candidate-free-cells.jsonl').read_bytes()),
        'candidateFreeCallerContextSha256':sha_bytes((CANDIDATE/'caller-context.jsonl').read_bytes()),
        'primaryCellsSha256':sha_bytes((PRIMARY/'primary-review-cells.jsonl').read_bytes()),
        'primaryProposalsSha256':sha_bytes((PRIMARY/'primary-review-proposals.jsonl').read_bytes()),
        'blindCellsSha256':sha_bytes((BLIND/'blind-cell-review.jsonl').read_bytes()),
        'blindFindingsSha256':sha_bytes((BLIND/'findings.json').read_bytes())
    }
    summary = {
        'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'batch':'W250-W299-Core','head':HEAD,'tree':TREE,
        'scope':{'firstPosition':250,'lastPosition':299,'sourceKeys':50,'locales':12,'cells':600},
        'primaryProposalCells':33,'blindHoldCells':30,'primaryBlindOverlap':9,
        'blindOnlyHoldCells':21,'crossCustomTargetCells':13,'selectedChangeCells':42,
        'dispositions':dict(counts),'findingGroups':11,'rejectedFalsePositiveFindingCells':12,
        'callerBackedKeys':50,'callerlessKeys':0,'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600,
        'recommendationsOnly':True,'catalogsChanged':False,'repositoryOrPRChanged':False,'testsBuildsCIWorkflowsRun':False,
        'sourceWorktreeClean':True,'candidateFreePriorLineage':primary_summary.get('priorLineage'),
        'inputHashes':input_hashes,
        'liveBaseDrift':{'apiBase':API_BASE,'currentMain':MAIN,'aheadBy':26,'containsCoreLocalizationSourceOrCatalogChanges':False}
    }
    write_json(OUT/'cross-review-summary.json',summary)

    readme = f'''# ChaptarrNG PR #190 W250–W299 Core cross-review\n\nThis packet adjudicates all 600 cells across 50 English Core keys and 12 locales, pinned to PR head `{HEAD}` and tree `{TREE}`.\n\n## Result\n\n- Accept 558 current targets and recommend 42 target changes.\n- Reconcile 33 primary proposals against 30 blind holds; 9 cells overlap.\n- Add 9 changes for blind-only findings and refine 4 primary candidates using pinned caller or locale terminology evidence.\n- Reject blind finding F011 for all 12 `Book` cells: the exact callers use this key as a book-title column, and every current translation is a direct book noun label, while the separate BookCount key names the number.\n- Accept the six protected-literal scanner exceptions for `BackupIntervalHelpText`: each translation expands DB as “database” and retains Chaptarr.\n- Keep native-speaker review outstanding for every cell. These are review recommendations, not native signoff.\n\n## Pin and scope\n\nLive filtered PR metadata at {attestation['verifiedWindowUTC'][0]}–{attestation['verifiedWindowUTC'][1]} showed PR #190 open/draft, branch and pull refs at `{HEAD}`, and exact clean source worktree tree `{TREE}`. The API base is `{API_BASE}` while live main is `{MAIN}` (26 commits ahead). The compare file list contains no Core English or target localization catalogs; review evidence remains pinned to the specified PR head/tree. No PR body was retrieved.\n\nThe blind reviewer disclosed only aggregate prior-window counts from the candidate-free verifier and sibling directory filenames from a top-level listing; it did not inspect prior translations, historical per-cell rows, or W250 primary results.\n\n## Files\n\n- `cross-review-cells.jsonl`: all 600 cell decisions, current and recommended target hashes, input-row hashes, caller links, and token checks.\n- `selected-changes.jsonl`: the 42 proposed target changes.\n- `caller-evidence.json`: deduplicated exact runtime translation callsites by source key.\n- `decision-reconciliation.json`: finding-by-finding reconciliation, overlap, the rejected F011 claim, literal scanner exceptions, and blind reviewer disclosure.\n- `review-selections.json`: the 13 cross-review target refinements/new targets and full adjudication map.\n- `live-pr-attestation.json`, `base-drift-comparison.json`: filtered live refs and base/main file-list comparison.\n- `build_cross_review.py`, `verify_cross_review.py`: deterministic packet builder and verifier.\n- `manifest.json`, `SHA256SUMS.txt`: packet seal and checksums.\n\nVerify from this directory with `sha256sum -c SHA256SUMS.txt` and `python3 verify_cross_review.py`. The verifier rechecks the three sealed input packets and this output’s exact source-worktree pin; it does not run product tests, builds, or CI.\n'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')

    # Seal the packet; manifest lists byte hashes for every artifact except itself and the checksum file.
    artifacts = sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in {'manifest.json','SHA256SUMS.txt'})
    manifest = {
        'result':'PASS','createdAtUTC':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'batch':'W250-W299-Core','head':HEAD,'tree':TREE,
        'scope':{'sourceKeys':50,'locales':12,'cells':600},'dispositions':dict(counts),'selectedChangeCells':42,
        'inputHashes':input_hashes,'artifacts':{p.name:sha_bytes(p.read_bytes()) for p in artifacts},
        'sourceWorktree':{'path':str(REPO),'head':head,'tree':tree,'clean':True},
        'scopeControls':{'catalogEdits':False,'PRBodyRead':False,'PRWrites':False,'testsBuildsCIWorkflowRuns':False}
    }
    write_json(OUT/'manifest.json',manifest)
    sums=[]
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name!='SHA256SUMS.txt':
            sums.append(f'{sha_bytes(p.read_bytes())}  {p.name}')
    (OUT/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    print(json.dumps({'result':'PASS','out':str(OUT),'cells':len(out_rows),'selectedChanges':len(selected),'acceptCurrent':counts['accept-current'],'primaryProposalCells':len(pp_by),'blindHoldCells':len(blind_holds),'overlap':len(overlap),'customTargets':len(CUSTOM),'head':HEAD,'tree':TREE},sort_keys=True))

if __name__=='__main__': main()
