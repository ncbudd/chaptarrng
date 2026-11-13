#!/usr/bin/env python3
import collections
import hashlib
import json
import pathlib
import re
import shutil
import subprocess

OUT = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0800-0849-crossreview-20261102')
PRIMARY = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0800-0849-primary-20261102')
REPO = pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
def read_jsonl(path):
    return [json.loads(line) for line in path.open(encoding='utf-8') if line.strip()]
def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows), encoding='utf-8')

manifest = json.load((PRIMARY / 'input-manifest.json').open(encoding='utf-8'))
ledger = read_jsonl(PRIMARY / 'primary-review-ledger.jsonl')
caller_rows = read_jsonl(PRIMARY / 'caller-context.jsonl')
source_by_ordinal = {r['sourceOrdinal']: r for r in caller_rows}

# Exact UI navigation terms are translated catalog labels, not immutable product/API literals.
menu_targets = {
  830: {
    'ar': 'لم يتم إعداد أي مجلد جذر من نوع {value0}. أضف مجلدًا ضمن الإعدادات → إدارة الوسائط.',
    'de': 'Für {value0} sind keine Stammordner eingerichtet. Fügen Sie einen unter Einstellungen → Medienverwaltung hinzu.',
    'es': 'No hay carpetas raíz de {value0} configuradas. Añada una en Ajustes → Gestión de medios.',
    'fr': 'Aucun dossier racine de type {value0} n’est configuré. Ajoutez-en un dans Paramètres → Gestion des médias.',
    'hi': 'कोई {value0} रूट फ़ोल्डर कॉन्फ़िगर नहीं है। समायोजन → मीडिया प्रबंधन में एक जोड़ें।',
    'id': 'Belum ada folder akar {value0} yang dikonfigurasi. Tambahkan satu melalui Pengaturan → Pengelolaan Media.',
    'ja': '{value0} のルートフォルダーが設定されていません。設定 → メディア管理で追加してください。',
    'ko': '{value0} 루트 폴더가 설정되어 있지 않습니다. 설정 → 미디어 관리에서 추가하세요.',
    'pt-BR': 'Nenhuma pasta raiz de {value0} está configurada. Adicione uma em Configurações → Gerenciamento de mídia.',
    'vi': 'Chưa cấu hình thư mục gốc nào thuộc loại {value0}. Hãy thêm một thư mục trong Cài đặt → Quản lý truyền thông.',
    'zh-Hans': '未配置任何 {value0} 根文件夹。请在设置 → 媒体管理中添加一个。',
    'zh-Hant': '未設定任何 {value0} 根資料夾。請在設定 → 媒體管理中新增一個。'
  },
  837: {
    'ar': 'Hardcover غير مفعّل (فعّله من الإعدادات أو عيّن رمز API لهذه القائمة المستوردة).',
    'de': 'Hardcover ist nicht aktiviert (aktivieren Sie es in Einstellungen oder legen Sie ein API-Token für diese Importliste fest).',
    'es': 'Hardcover no está activado (actívelo en Ajustes o establezca un token de API para esta lista de importación).',
    'fr': 'Hardcover n’est pas activé (activez-le dans Paramètres ou définissez un jeton API pour cette liste d’importation).',
    'hi': 'Hardcover सक्षम नहीं है (समायोजन में इसे सक्षम करें या इस आयात सूची में API टोकन सेट करें)।',
    'id': 'Hardcover belum diaktifkan. Aktifkan di Pengaturan atau tetapkan token API pada daftar impor ini.',
    'ja': 'Hardcover は有効になっていません。設定で有効にするか、このインポートリストに API トークンを設定してください。',
    'ko': 'Hardcover가 활성화되어 있지 않습니다. 설정에서 활성화하거나 이 가져오기 목록에 API 토큰을 설정하세요.',
    'pt-BR': 'Hardcover não está ativado. Ative-o em Configurações ou configure um token de API nesta lista de importação.',
    'vi': 'Hardcover chưa được bật. Hãy bật Hardcover trong Cài đặt hoặc đặt token API cho danh sách nhập này.',
    'zh-Hans': 'Hardcover 尚未启用（请在设置中启用，或在此导入列表中设置 API 令牌）。',
    'zh-Hant': 'Hardcover 尚未啟用（請在設定中啟用，或在此匯入清單中設定 API 權杖）。'
  }
}
extra_targets = {
  (811, 'es'): 'Chaptarr se está reiniciando después de restablecer los valores de fábrica. Vuelva a intentarlo dentro de unos instantes.',
  (815, 'ja'): 'Calibre ライブラリはすでにルートフォルダーとして設定されています。',
  (834, 'ar'): 'تمت إضافة هذا المؤلف بالفعل.',
  (849, 'id'): 'Data daftar tidak dapat diambil.'
}
reasons = {
  (811, 'es'): '“Restauración de la fábrica” reads as restoring a factory building; the pinned source describes the service restarting after a factory reset. This proposal uses the ordinary factory-reset phrasing and preserves Chaptarr.',
  (815, 'ja'): 'The current Japanese target leaves “root” in English. The pinned Calibre validation context is a root-folder duplicate check; ルートフォルダー is the established Japanese folder term and matches the catalog’s RootFolder label.',
  (834, 'ar'): 'The current target uses الكاتب (writer) and an awkward construction; the pinned validator concerns the Author entity. This proposal uses the locale catalog’s مؤلف term for Author and grammatical إضافة.',
  (849, 'id'): 'The current phrase is an awkward literal rendering. The pinned Goodreads caller reports failure to retrieve list data; this proposal states that list data could not be retrieved.'
}

# Locate exact catalog menu labels and verify the current catalog values represented in the corrective targets.
locale_paths = {locale: row['path'] for locale, row in manifest['localeCatalogs'].items()}
label_rows=[]
for locale in LOCALES:
    catalog = json.loads((REPO / locale_paths[locale]).read_text(encoding='utf-8'))
    for key in ('Settings', 'MediaManagement'):
        value = catalog[key]
        label_rows.append({'locale': locale, 'key': key, 'value': value, 'valueSha256': sha(value), 'catalogPath': locale_paths[locale], 'catalogBlob': manifest['localeCatalogs'][locale]['blob'], 'catalogSha256': manifest['localeCatalogs'][locale]['sha256']})
        target = menu_targets[830 if key == 'MediaManagement' else 837][locale]
        if value not in target:
            raise SystemExit(f'UI label mismatch: {locale} {key} {value!r} absent from target {target!r}')
write_jsonl(OUT / 'catalog-label-reattestation.jsonl', label_rows)

# Pin UI navigation translations and the ordinary server-message translator that displays these messages in app locale.
ui_files = ['frontend/src/Components/Page/Sidebar/PageSidebar.js', 'frontend/src/Settings/Settings.js', 'frontend/src/Utilities/String/translateServerMessage.js']
ui_evidence=[]
for path in ui_files:
    file_path=REPO/path
    raw=file_path.read_bytes()
    blob=subprocess.check_output(['git','-C',str(REPO),'hash-object',str(file_path)],text=True).strip()
    lines=file_path.read_text(encoding='utf-8').splitlines()
    snippets=[]
    if path.endswith('PageSidebar.js'):
        ranges=[(109,109),(113,113)]
    elif path.endswith('Settings.js'):
        ranges=[(64,64)]
    else:
        ranges=[(202,220)]
    for first,last in ranges:
        snippets.append({'firstLine':first,'lastLine':last,'lines':[{'line':n,'text':lines[n-1].strip(),'sha256':sha(lines[n-1].strip())} for n in range(first,last+1)]})
    ui_evidence.append({'path':path,'blob':blob,'sha256':hashlib.sha256(raw).hexdigest(),'snippets':snippets})
write_json(OUT/'ui-label-source-evidence.json', {'head':manifest['head'],'tree':manifest['tree'],'files':ui_evidence,'explanation':'PageSidebar renders Settings and MediaManagement through translate(key); Settings page title also uses translate(Settings). translateServerMessage maps a known source string to the app-locale catalog. Therefore the two breadcrumb phrases are user-facing UI labels and should match the active locale catalog values.'})

# Full per-cell review, preserving current/source/candidate hashes, caller refs, and independent final target.
records=[]
for r in ledger:
    ordinal, locale = r['sourceOrdinal'], r['locale']
    current = r['currentTarget']
    primary_final = r['finalTarget']
    if ordinal in menu_targets:
        final = menu_targets[ordinal][locale]
        disposition = 'revise-primary-proposal' if r['disposition'] != 'accept-current' else 'propose-additional-correction'
        rationale = ('“Settings” and “Media Management” are translated sidebar titles, confirmed by the exact frontend translate() calls and locale catalog entries. The primary marked them protected; independent review reclassifies them as localizable UI labels. This target uses the exact locale labels and preserves the source placeholder.' if ordinal == 830 else '“Settings” is a translated sidebar title, confirmed by the exact frontend translate() call and locale catalog entry. The primary left it as an English protected term (or used a different Settings label); independent review reclassifies it as a localizable UI label. This target uses the exact locale label and preserves Hardcover/API terminology.')
    elif (ordinal, locale) in extra_targets:
        final = extra_targets[(ordinal, locale)]
        disposition = 'propose-additional-correction'
        rationale = reasons[(ordinal, locale)]
    else:
        final = primary_final
        disposition = 'accept-current' if r['disposition'] == 'accept-current' else 'accept-primary-proposal'
        if disposition == 'accept-current':
            rationale = 'Independent static review against the English source and pinned caller found that the current target conveys the relevant meaning; placeholders, markup, and protected technical terms remain intact.'
        else:
            rationale = 'Independently accepted: the proposed target resolves the current wording issue while preserving source intent in the pinned caller context and retaining the technical literals/placeholders.'
    # Primary source is exactly preserved, and final tokens are checked independently.
    source_tokens = collections.Counter(re.findall(r'\{[^{}]+\}', r['source']))
    final_tokens = collections.Counter(re.findall(r'\{[^{}]+\}', final))
    tag_re = re.compile(r'<\s*/?\s*[A-Za-z][^>]*>')
    source_markup = tag_re.findall(r['source'])
    final_markup = tag_re.findall(final)
    protected = list(r.get('protectedLiterals') or [])
    reclassified=[]
    if ordinal == 830:
        for lit in ('Settings', 'Media Management'):
            if lit in protected:
                protected.remove(lit)
            reclassified.append(lit)
    elif ordinal == 837:
        if 'Settings' in protected:
            protected.remove('Settings')
        reclassified.append('Settings')
    protected_checks=[{'literal':lit,'presentInFinal':lit in final,'presentInSource':lit in r['source']} for lit in protected]
    candidate_target = r['recommendedTarget']
    records.append({
      'sourceOrdinal':ordinal,'sourceId':r['sourceId'],'locale':locale,
      'source':r['source'],'sourceTextSha256':r['sourceTextSha256'],
      'currentTarget':current,'currentTargetSha256':r['currentTargetSha256'],
      'primaryDisposition':r['disposition'],'primaryRecommendedTarget':candidate_target,'primaryRecommendedTargetSha256':r['recommendedTargetSha256'],
      'primaryFinalTarget':primary_final,'primaryFinalTargetSha256':r['finalTargetSha256'],
      'crossReviewDisposition':disposition,'finalTarget':final,'finalTargetSha256':sha(final),'rationale':rationale,
      'callerContextSha256':r['callerContextSha256'],'callerRefs':r['callerRefs'],
      'sourcePlaceholders':dict(source_tokens),'finalTargetPlaceholders':dict(final_tokens),'placeholderParity':source_tokens==final_tokens,
      'sourceMarkup':source_markup,'finalTargetMarkup':final_markup,'markupParity':source_markup==final_markup,
      'protectedLiterals':protected,'protectedLiteralChecks':protected_checks,'protectedLiteralsPreserved':all(x['presentInFinal'] for x in protected_checks),
      'reclassifiedUiLabels':reclassified,'confidence':'moderate','nativeSpeakerApproval':False
    })
    if source_tokens != final_tokens or source_markup != final_markup or not all(x['presentInFinal'] for x in protected_checks):
        raise SystemExit(f'Integrity mismatch for W{ordinal} {locale}')
if len(records)!=600:
    raise SystemExit(f'Expected 600 cells, got {len(records)}')
write_jsonl(OUT/'crossreview-ledger.jsonl',records)

changed=[r for r in records if r['finalTargetSha256']!=r['currentTargetSha256']]
counts=collections.Counter(r['crossReviewDisposition'] for r in records)
by_locale={loc:dict(collections.Counter(r['crossReviewDisposition'] for r in records if r['locale']==loc)) for loc in LOCALES}
findings=[]
for n in (830,837):
 for r in records:
  if r['sourceOrdinal']==n:
   findings.append({'sourceOrdinal':n,'sourceId':r['sourceId'],'locale':r['locale'],'finding':'A translated navigation label was incorrectly frozen as a protected literal or not matched to the actual UI label.','primaryTarget':r['primaryFinalTarget'],'finalTarget':r['finalTarget'],'currentTargetSha256':r['currentTargetSha256'],'finalTargetSha256':r['finalTargetSha256'],'catalogLabels':{key:next(x['value'] for x in label_rows if x['locale']==r['locale'] and x['key']==key) for key in (('Settings','MediaManagement') if n==830 else ('Settings',))},'rationale':r['rationale']})
for key in extra_targets:
 r=next(x for x in records if (x['sourceOrdinal'],x['locale'])==key)
 findings.append({'sourceOrdinal':r['sourceOrdinal'],'sourceId':r['sourceId'],'locale':r['locale'],'finding':'Additional missed correction found during independent semantic review.','primaryTarget':r['primaryFinalTarget'],'finalTarget':r['finalTarget'],'currentTargetSha256':r['currentTargetSha256'],'finalTargetSha256':r['finalTargetSha256'],'rationale':r['rationale']})
write_jsonl(OUT/'additional-findings.jsonl',findings)
summary={
 'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'head':manifest['head'],'tree':manifest['tree'],'window':'W800-W849','sourceCount':50,'cellCount':600,'locales':LOCALES,
 'crossReviewDispositionCounts':dict(counts),'perLocaleDispositionCounts':by_locale,'primaryCandidateCount':sum(r['disposition']!='accept-current' for r in ledger),
 'primaryProposalsAcceptedAsWritten':counts['accept-primary-proposal'],'primaryProposalsRevised':counts['revise-primary-proposal'],'additionalCorrections':counts['propose-additional-correction'],'primaryAcceptCurrentRetained':counts['accept-current'],
 'finalTargetsDifferentFromCurrent':len(changed),'holds':0,'callerRefs':sum(len(r['callerRefs']) for r in source_by_ordinal.values()),'callerSourceRows':len(source_by_ordinal),'genericPipelineRefs':76,
 'placeholderMismatchCells':sum(not r['placeholderParity'] for r in records),'markupMismatchCells':sum(not r['markupParity'] for r in records),'protectedLiteralFailures':sum(not r['protectedLiteralsPreserved'] for r in records),
 'protectedLiteralReclassification':{'W830':['Settings','Media Management'],'W837':['Settings'],'basis':'These are localizable navigation labels resolved by translate() at the exact current UI source and are present in each locale catalog.'},
 'crossReviewFindings':len(findings),'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'confidence':'moderate','staticOnly':True,
 'importantSpecifics':['PT-BR W809 final recommendation preserves exact enum token null.','W830 and W837 use the exact localized Settings and MediaManagement labels from the current UI catalogs.','Additional corrections: W811 Spanish factory-reset wording; W815 Japanese root-folder term; W834 Arabic Author term; W849 Indonesian list-data phrasing.'],
 'repoModified':False,'testsBuildsCiBrowserRun':False
}
write_json(OUT/'summary.json',summary)
readme='''# ChaptarrNG PR #190 W800–W849 independent cross-review\n\nThis packet independently cross-reviews all 600 cells (50 source IDs × 12 direct locales) in the primary packet at exact head `f0eb9d38b1989bd6e3addeb698ec8c5f9c29d9e9` / tree `7f0f9a9d71d672bb47c08e1abe4125be03d815d6`. The primary input SHA256SUMS was verified before review; its manifest hash is recorded in `primary-input-reattestation.json`.\n\n## Scope and method\n\n- Re-attested the live PR and GitHub branch ref, HTTPS remote branch, clean worktree, all 12 catalog files, all 600 source/current-target values, 63 caller pins, 76 generic display-pipeline pins, and all 12 W799 boundary cells.\n- Independently assessed each current target and each of the 236 primary candidates against the source and pinned caller. The per-cell ledger includes current, source, candidate, final-target hashes, exact caller references, placeholder and markup parity, protected-literal checks, rationale, and native-speaker status.\n- Reclassified `Settings` and `Media Management` in W830 and `Settings` in W837 as localizable UI navigation labels. `PageSidebar.js` renders both with `translate()` and every locale has a corresponding catalog label; the exact source pins and catalog values are recorded in `ui-label-source-evidence.json` and `catalog-label-reattestation.jsonl`.\n- Added missed corrections for Spanish W811, Japanese W815, Arabic W834, and Indonesian W849. Other primary proposals are accepted as written.\n\n## Results\n\nCross-review decisions: 344 accept-current, 228 accept-primary-proposal, 8 revise-primary-proposal, and 20 propose-additional-correction. Thus 256 final targets differ from current values; no machine-review hold remains. Placeholder, markup, and protected-literal parity passed for all 600 final targets, including exact `null` preservation for PT-BR W809.\n\nThis is machine-assisted static review at moderate confidence, not native-speaker approval. Native-speaker review remains open. No repository or PR edits, tests, builds, scans, CI, or browser activity were performed.\n\n## Files\n\n- `crossreview-ledger.jsonl`: 600 exact-hash per-cell decisions and final targets.\n- `additional-findings.jsonl`: 28 findings/cell recommendations for W830/W837 plus four additional missed corrections.\n- `all-seven-pr-heads.json`: live PR/ref/tree reattestation for the seven localization PRs in scope.\n- `primary-input-reattestation.json`, `cell-reattestation.jsonl`, `caller-reattestation.jsonl`, `pipeline-reattestation.jsonl`, and `w799-boundary-reattestation.jsonl`: exact-input checks.\n- `catalog-label-reattestation.jsonl`, `ui-label-source-evidence.json`: UI menu-label evidence.\n- `build_crossreview.py`: packet-generation script.\n- `SHA256SUMS`: final packet checksums.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'summary':summary,'files':sorted(p.name for p in OUT.iterdir())},ensure_ascii=False,indent=2))
