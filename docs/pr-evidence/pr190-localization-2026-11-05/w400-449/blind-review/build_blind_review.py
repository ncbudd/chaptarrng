#!/usr/bin/env python3
"""Build the sealed independent blind-review packet for ChaptarrNG W400-W449."""
from __future__ import annotations
import collections, hashlib, json, re
from datetime import datetime, timezone
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

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_text(text: str) -> str:
    return sha_bytes(text.encode('utf-8'))

def canon(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')

def readj(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def readjl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def token_report(source: str, target: str, row: dict) -> dict:
    source_ph = dict(sorted(collections.Counter(PH.findall(source)).items()))
    target_ph = dict(sorted(collections.Counter(PH.findall(target)).items()))
    src_inline, dst_inline = INLINE.findall(source), INLINE.findall(target)
    src_markup, dst_markup = MARKUP.findall(source), MARKUP.findall(target)
    src_nums = collections.Counter(NUM.findall(source))
    dst_nums = collections.Counter(NUM.findall(target))
    protected = row['protectedLiterals']
    return {
        'placeholderParity': source_ph == target_ph,
        'inlineCodeParity': src_inline == dst_inline,
        'markupParity': src_markup == dst_markup,
        'numericTokenParity': src_nums == dst_nums,
        'protectedLiteralParity': all(token in target for token in protected),
        'sourcePlaceholders': source_ph,
        'targetPlaceholders': target_ph,
        'sourceInlineCode': src_inline,
        'targetInlineCode': dst_inline,
        'sourceMarkup': src_markup,
        'targetMarkup': dst_markup,
        'sourceNumericTokens': sorted(NUM.findall(source)),
        'targetNumericTokens': sorted(NUM.findall(target)),
        'protectedLiterals': protected,
    }

# Suggestions are limited to clear semantic, grammar, or UI-string defects found in the current cells.
# The rest of the 600 cells were reviewed and retained as acceptable.
PROPOSALS = {
 (403,'hi'): ('correction', 'Calibre Content Server (Calibre Web नहीं) का उपयोग करने से Chaptarr आपकी Calibre लाइब्रेरी में पुस्तकें जोड़ सकता है और प्रारूपों के बीच रूपांतरण शुरू कर सकता है।', 'The current Hindi verb प्रेरित करना means “inspire/induce”; शुरू करना conveys triggering conversions.'),
 (404,'ar'): ('refinement', 'مضيف Calibre', 'The current word order and feminine form are awkward for the settings label “Calibre Host”.'),
 (408,'hi'): ('correction', 'Chaptarr Calibre के Content Server के साथ इंटरफ़ेस कर सकता है। यह Calibre-Web का उपयोग नहीं कर सकता, क्योंकि वह असंबंधित सॉफ़्टवेयर है।', 'The current first clause uses a plural verb for the singular product and conflicts with the singular second clause.'),
 (413,'ar'): ('correction', 'إرسال إلى Calibre', 'The current wording reads as “pushing Calibre”; the toolbar action sends metadata to Calibre.'),
 (413,'es'): ('correction', 'Enviar a Calibre', 'Empujar Calibre is an unnatural literal rendering and does not clearly say to send the item to Calibre.'),
 (413,'id'): ('refinement', 'Kirim ke Calibre', 'The current label leaves the action in English; this is a concise Indonesian action label.'),
 (413,'vi'): ('refinement', 'Gửi đến Calibre', 'The current wording can read as pushing Calibre itself; this makes the destination explicit.'),
 (414,'hi'): ('refinement', 'Calibre में {0} पुस्तकों के लिए लिखे जाने वाले फ़ील्ड चुनें। जिन फ़ील्ड का चयन नहीं किया गया है, वे Calibre में अपरिवर्तित रहेंगी।', 'This avoids translating “left unticked” as literally untouched while preserving the field-selection instruction and count placeholder.'),
 (416,'es'): ('correction', 'Consejo: Para previsualizar los campos de metadatos, seleccione «Cancelar», luego seleccione cualquier libro y utilice el', 'The quoted button label should be the Spanish “Cancelar”, matching the localized Cancel control.'),
 (422,'hi'): ('correction', 'क्या आप कतार में प्रतीक्षारत और चल रहे सभी कार्यों को रद्द करना चाहते हैं?', 'The current Hindi leaves “queued” in English and omits the explicit confirmation question.'),
 (422,'zh-Hans'): ('refinement', '取消所有排队和正在运行的任务？', 'Removes the stray ASCII space before the question mark and clarifies “queued”.'),
 (422,'zh-Hant'): ('refinement', '要取消所有排隊和執行中的工作嗎？', 'Removes the stray space before punctuation and renders queued work as waiting in the queue.'),
 (424,'es'): ('refinement', '¿Seguro que quieres cancelar esta tarea pendiente?', 'Adds the required opening Spanish question mark.'),
 (424,'fr'): ('correction', 'Êtes-vous sûr de vouloir annuler cette tâche en attente ?', 'Corrects the missing circumflex in sûr and uses the natural confirmation phrasing.'),
 (424,'ko'): ('refinement', '대기 중인 작업을 취소하시겠습니까?', 'Corrects Korean spacing and renders pending as waiting.'),
 (424,'zh-Hant'): ('correction', '您確定要取消此待處理工作嗎？', '待辦 means a to-do item; 待處理 expresses a pending task, and the punctuation is corrected.'),
 (425,'es'): ('refinement', 'Cancelar tarea en curso', 'Tarea de ejecución is awkward; en curso is the concise task-status wording.'),
 (426,'ar'): ('refinement', 'تم إلغاء {count} من الأوامر', 'Adds a natural plural construction for the count of cancelled commands.'),
 (426,'de'): ('correction', '{count} Befehle abgebrochen', 'Storniert is normally used for cancelling bookings/contracts; abgebrochen fits commands.'),
 (426,'hi'): ('correction', 'कमांड रद्द किए गए: {count}', 'The current phrase is an infinitive fragment and does not read as a completed cancellation message.'),
 (426,'ja'): ('correction', 'コマンド {count} 件をキャンセルしました', 'The current text is a noun fragment; this expresses that the commands were cancelled.'),
 (426,'ko'): ('refinement', '명령 {count}개를 취소했습니다', 'The current fragment omits the completed action; this reads as a cancellation notification.'),
 (427,'ar'): ('correction', 'جارٍ الإلغاء', 'The current noun means cancellation; the caller uses this as an in-progress queue status.'),
 (427,'de'): ('correction', 'Wird abgebrochen', 'The caller displays an ongoing status, while the current noun means cancellation.'),
 (427,'es'): ('correction', 'Cancelando', 'The caller displays an ongoing status; this is the Spanish progressive form.'),
 (427,'fr'): ('correction', 'Annulation en cours', 'The caller displays an ongoing status, not the name of the cancellation action.'),
 (427,'hi'): ('correction', 'रद्द किया जा रहा है', 'The caller displays an ongoing status; the current infinitive is not progressive.'),
 (427,'id'): ('correction', 'Sedang dibatalkan', 'The caller displays an ongoing status; the current form names the action rather than its progress.'),
 (427,'ja'): ('correction', 'キャンセル中', 'The caller displays an ongoing status; this form explicitly means cancellation in progress.'),
 (427,'zh-Hans'): ('correction', '正在取消', 'The current term can mean cancellation or cancel; the caller displays cancellation in progress.'),
 (427,'zh-Hant'): ('correction', '正在取消', 'The current term can mean cancellation or cancel; the caller displays cancellation in progress.'),
 (428,'de'): ('refinement', 'Nur einige Dateien einer Edition sind ausgewählt. Wenn Sie fortfahren, wird diese Edition auf mehrere Autorenordner verteilt.', 'Makes “only some files” and the split across multiple author folders explicit.'),
 (428,'es'): ('refinement', 'Solo se han seleccionado algunos archivos de una edición. Si continúas, esa edición quedará repartida entre las carpetas de los autores.', 'The current second sentence is awkward and less clear about the consequence of continuing.'),
 (428,'hi'): ('correction', 'किसी संस्करण की केवल कुछ फ़ाइलें चुनी गई हैं। जारी रखने पर वह संस्करण अलग-अलग लेखकों के फ़ोल्डरों में बँट जाएगा।', 'The current wording says the edition is split into an author folder, losing the across-folders meaning.'),
 (428,'ja'): ('correction', 'エディションの一部のファイルのみが選択されています。続行すると、そのエディションが複数の著者フォルダーに分かれます。', 'The current first sentence says only edition files are selected, omitting “some”; the warning concerns splitting across author folders.'),
 (428,'vi'): ('correction', 'Chỉ một số tệp của một ấn bản được chọn. Nếu tiếp tục, ấn bản đó sẽ bị phân tách giữa các thư mục tác giả.', 'The current second sentence is ungrammatical and obscures the split across author folders.'),
 (428,'zh-Hans'): ('refinement', '仅选择了某个版本的部分文件。继续操作会使该版本分散到多个作者文件夹中。', 'Makes the selection partial and the distribution across multiple author folders explicit.'),
 (428,'zh-Hant'): ('refinement', '只選取了某個版本的部分檔案。繼續會使該版本分散到多個作者資料夾中。', 'Makes the selection partial and the distribution across multiple author folders explicit.'),
 (429,'hi'): ('correction', 'प्रदाता IDs उपलब्ध नहीं होने के कारण {format} नहीं जोड़ा जा सकता', 'The current wording says “not found {format}” instead of “cannot add {format}”; the corrected text retains the protected ID token.'),
 (429,'id'): ('correction', 'Tidak dapat menambahkan {format}: ID penyedia tidak ada', 'The current “hilang ID penyedia” is ungrammatical; the replacement states that provider IDs are absent.'),
 (429,'ja'): ('correction', 'プロバイダー ID が不足しているため、{format}を追加できません', 'Reorders the fragment into a clear “cannot add because provider IDs are missing” message.'),
 (429,'zh-Hans'): ('correction', '无法添加 {format}：缺少提供者 ID', '身份 means identity rather than provider ID; the replacement preserves the ID token.'),
 (429,'zh-Hant'): ('refinement', '無法新增 {format}：缺少提供者 ID', 'Uses ID for the missing provider identifiers instead of the less precise “code”.'),
 (432,'vi'): ('refinement', 'Danh mục', 'Danh mục is the usual Vietnamese label for selectable categories; Loại means type.'),
 (434,'de'): ('correction', 'Ändert, wie streng HTTPS-Zertifikate geprüft werden. Ändern Sie dies nur, wenn Sie die Risiken verstehen.', 'The current text refers to validation of HTTPS certification; the setting controls certificate validation.'),
 (434,'es'): ('correction', 'Cambia el nivel de rigor con el que se valida el certificado HTTPS. No lo cambies a menos que entiendas los riesgos.', 'The setting validates an HTTPS certificate, not an HTTPS certification.'),
 (434,'fr'): ('correction', 'Modifie le niveau d’exigence de la validation du certificat HTTPS. Ne le modifiez pas si vous ne comprenez pas les risques.', 'The current wording says certification validation; the setting concerns the HTTPS certificate.'),
 (434,'pt-BR'): ('correction', 'Altera o rigor da validação do certificado HTTPS. Não altere a menos que compreenda os riscos.', 'The setting validates an HTTPS certificate, not an HTTPS certification.'),
 (436,'ar'): ('refinement', 'يغيّر فئة التنزيل في عميل التنزيل إلى «فئة ما بعد الاستيراد»', 'Makes clear that this action changes the download’s category within the download client.'),
 (437,'ar'): ('refinement', 'يغيّر فئات التنزيلات في عميل التنزيل إلى «فئة ما بعد الاستيراد»', 'Makes clear that this action changes download categories within the download client.'),
 (436,'de'): ('refinement', 'Ändert die Kategorie des Downloads im Download-Client in „Kategorie nach dem Import“.', 'Clarifies that the category is changed inside the client.'),
 (437,'de'): ('refinement', 'Ändert die Kategorien der Downloads im Download-Client in „Kategorie nach dem Import“.', 'Clarifies that the categories of downloads are changed inside the client.'),
 (436,'es'): ('refinement', 'Cambia la categoría de la descarga en el cliente de descargas a «Categoría posterior a la importación».', 'Clarifies that the download’s category is changed inside the client.'),
 (437,'es'): ('refinement', 'Cambia las categorías de las descargas en el cliente de descargas a «Categoría posterior a la importación».', 'Clarifies that the categories of downloads are changed inside the client.'),
 (436,'fr'): ('refinement', 'Modifie la catégorie du téléchargement dans le client de téléchargement en « Catégorie après importation ».', 'Clarifies that the download’s category is changed inside the client.'),
 (437,'fr'): ('refinement', 'Modifie les catégories des téléchargements dans le client de téléchargement en « Catégorie après importation ».', 'Clarifies that the categories of downloads are changed inside the client.'),
 (437,'hi'): ('refinement', 'डाउनलोड क्लाइंट में डाउनलोड की श्रेणियों को “आयात के बाद की श्रेणी” में बदलता है।', 'The current text names only a singular download category for the plural-key hint.'),
 (436,'id'): ('refinement', 'Mengubah kategori unduhan di klien unduhan menjadi "Kategori Pasca-Impor".', 'Clarifies that the category is changed inside the download client.'),
 (437,'id'): ('refinement', 'Mengubah kategori unduhan di klien unduhan menjadi "Kategori Pasca-Impor".', 'Clarifies that the categories of downloads are changed inside the download client.'),
 (436,'ja'): ('refinement', 'ダウンロードクライアント内のダウンロードカテゴリを「インポート後カテゴリ」に変更します。', 'The current text leaves the named category in English and is unclear about what is being changed.'),
 (437,'ja'): ('refinement', 'ダウンロードクライアント内のダウンロードカテゴリを「インポート後カテゴリ」に変更します。', 'The current text leaves the named category in English and is unclear about what is being changed.'),
 (436,'pt-BR'): ('refinement', 'Altera a categoria do download no cliente de download para "Categoria pós-importação".', 'Clarifies that the download’s category is changed inside the client.'),
 (437,'pt-BR'): ('refinement', 'Altera a categoria dos downloads no cliente de download para "Categoria pós-importação".', 'Clarifies that the categories of downloads are changed inside the client.'),
 (436,'vi'): ('refinement', 'Đổi danh mục của tải xuống trong ứng dụng khách tải xuống thành "Danh mục sau khi nhập".', 'Clarifies that the download’s category is changed inside the client.'),
 (437,'vi'): ('refinement', 'Đổi danh mục của các mục tải xuống trong ứng dụng khách tải xuống thành "Danh mục sau khi nhập".', 'Clarifies that the categories of downloads are changed inside the client.'),
 (436,'zh-Hans'): ('refinement', '将下载客户端中的下载类别设为“导入后类别”。', 'Clarifies that the download category is assigned within the download client.'),
 (437,'zh-Hans'): ('refinement', '将下载客户端中的下载类别设为“导入后类别”。', 'Clarifies that the categories of downloads are assigned within the download client.'),
 (436,'zh-Hant'): ('refinement', '將下載用戶端中的下載類別設為「匯入後類別」。', 'Clarifies that the download category is assigned within the download client.'),
 (437,'zh-Hant'): ('refinement', '將下載用戶端中的下載類別設為「匯入後類別」。', 'Clarifies that the categories of downloads are assigned within the download client.'),
 (440,'ar'): ('refinement', 'موجز تقويم Chaptarr', 'موجز تقويم is the usual sense of a subscribable calendar feed; تغذية reads more literally as feeding.'),
 (440,'vi'): ('correction', 'Nguồn cấp lịch Chaptarr', 'Bộ nạp lịch means a calendar loader; nguồn cấp lịch conveys a calendar feed.'),
 (444,'fr'): ('refinement', 'Chaptarr prend en charge plusieurs listes pour importer des livres et des auteurs dans la base de données.', 'Removes unnecessary capitalization from common nouns.'),
 (444,'ko'): ('refinement', 'Chaptarr는 책과 저자를 데이터베이스로 가져오기 위한 여러 목록을 지원합니다.', 'Corrects spacing in 가져오기 and uses a natural conjunction.'),
 (448,'ar'): ('refinement', 'الإصدارات والتسجيلات الصوتية', 'The caller describes edition entries with narration details; التسجيلات الصوتية is clearer than “narrative” for recorded narration.'),
 (448,'hi'): ('refinement', 'संस्करण और वाचन', 'वाचन conveys spoken narration more clearly than the English-derived नैरेटिव.'),
 (448,'vi'): ('refinement', 'Các phiên bản và phần thuyết minh', 'The caller describes editions with narration details; this denotes narration rather than the narrator as a person.'),
}

manifest = readj(INPUT / 'candidate-free-manifest.json')
attestation = readj(INPUT / 'PR-attestation.json')
assert manifest['head'] == attestation['headSha'] == HEAD
assert manifest['tree'] == attestation['headTree'] == TREE
assert manifest['scope']['firstPosition'] == 400 and manifest['scope']['lastPosition'] == 449
assert manifest['scope']['cells'] == 600 and manifest['candidateFreeOnly']
assert sha_bytes((INPUT / 'SHA256SUMS.txt').read_bytes()) == 'dc057678d73514d8ad08426a648571472b02ee9969cb0cf67b6c4f998e4a3d4f'
cells = readjl(INPUT / 'candidate-free-cells.jsonl')
assert len(cells) == 600
rows = []
for src in cells:
    ordinal, locale, key = src['sourceOrdinal'], src['locale'], src['sourceKey']
    if key == 'CatalogNumber':
        assert ordinal == 431 and src['literalCallCount'] == 0
        rows.append({
            'batch': src['batch'], 'exactHead': HEAD, 'exactTree': TREE,
            'sourceOrdinal': ordinal, 'locale': locale,
            'decision': 'hold', 'reasonCode': 'zero-literal-caller-hash-only',
            'reason': 'No literal runtime translation caller exists in the pinned caller scan; retain a hash-only hold.',
            'confidence': 'high', 'sourceKeySha256': sha_text(key),
            'sourceTextSha256': src['sourceTextSha256'],
            'currentTargetSha256': src['currentTargetSha256'],
            'callerContextSha256': src['callerContextSha256'],
            'callerReferenceCount': src['callerReferenceCount'],
            'literalCallCount': src['literalCallCount'],
            'indirectKeyReferenceCount': src['indirectKeyReferenceCount'],
            'relatedDynamicTranslationCallsiteCount': src['relatedDynamicTranslationCallsiteCount'],
            'sourceFileSha256': src['sourceFileSha256'], 'targetFileSha256': src['targetFileSha256'],
            'sourceFileGitBlob': src['sourceFileGitBlob'], 'targetFileGitBlob': src['targetFileGitBlob'],
            'integrityChecks': src['integrityChecks'],
            'textIncluded': False,
        })
        continue
    proposal = PROPOSALS.get((ordinal, locale))
    current_token_report = token_report(src['sourceText'], src['currentTarget'], src)
    assert all(current_token_report[k] for k in ('placeholderParity','inlineCodeParity','markupParity','numericTokenParity','protectedLiteralParity'))
    row = {
        'batch': src['batch'], 'exactHead': HEAD, 'exactTree': TREE,
        'sourceOrdinal': ordinal, 'sourceKey': key, 'sourceKeySha256': sha_text(key),
        'sourceText': src['sourceText'], 'sourceTextSha256': src['sourceTextSha256'],
        'locale': locale, 'decision': proposal[0] if proposal else 'accept-current',
        'currentTarget': src['currentTarget'], 'currentTargetSha256': src['currentTargetSha256'],
        'callerContextSha256': src['callerContextSha256'],
        'callerReferenceCount': src['callerReferenceCount'], 'literalCallCount': src['literalCallCount'],
        'indirectKeyReferenceCount': src['indirectKeyReferenceCount'],
        'relatedDynamicTranslationCallsiteCount': src['relatedDynamicTranslationCallsiteCount'],
        'sourceFileSha256': src['sourceFileSha256'], 'targetFileSha256': src['targetFileSha256'],
        'sourceFileGitBlob': src['sourceFileGitBlob'], 'targetFileGitBlob': src['targetFileGitBlob'],
        'integrityChecks': src['integrityChecks'], 'tokenEvidence': current_token_report,
        'confidence': 'moderate' if locale in {'ar','hi','id','ja','ko','vi','zh-Hans','zh-Hant'} else 'high',
    }
    if proposal:
        kind, target, rationale = proposal
        checks = token_report(src['sourceText'], target, src)
        assert all(checks[k] for k in ('placeholderParity','inlineCodeParity','markupParity','numericTokenParity','protectedLiteralParity')), (ordinal, locale, checks)
        row['proposedTarget'] = target
        row['proposalSha256'] = sha_text(target)
        row['rationale'] = rationale
        row['proposalTokenChecks'] = checks
    else:
        row['rationale'] = 'Current wording conveys the source meaning in the pinned caller context; retained after semantic, grammar, and protected-token review.'
    rows.append(row)

assert len(rows) == 600
assert len(PROPOSALS) == len([r for r in rows if r['decision'] in {'correction','refinement'}])
# Preserve the candidate-free row order: source ordinal, then pinned locale order.
rows.sort(key=lambda r: (r['sourceOrdinal'], LOCALES.index(r['locale'])))
(ROOT / 'blind-ledger.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows), encoding='utf-8')
proposals = [r for r in rows if r['decision'] in {'correction','refinement'}]
holds = [r for r in rows if r['decision'] == 'hold']
(ROOT / 'proposals.jsonl').write_text(''.join(json.dumps({k:v for k,v in r.items() if k not in {'tokenEvidence','integrityChecks'}}, ensure_ascii=False, sort_keys=True) + '\n' for r in proposals), encoding='utf-8')
(ROOT / 'holds-hash-only.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in holds), encoding='utf-8')
counts = collections.Counter(r['decision'] for r in rows)
by_locale = {loc: dict(collections.Counter(r['decision'] for r in rows if r['locale']==loc)) for loc in LOCALES}
summary = {
    'schemaVersion': 1, 'result': 'PASS', 'batch': 'W400-449-Core',
    'repository': 'snapetech-org/chaptarrng', 'pullRequest': 190,
    'exactHead': HEAD, 'exactTree': TREE,
    'sourceIdsReviewed': 50, 'cellsReviewed': 600, 'locales': LOCALES,
    'decisionCounts': dict(counts), 'byLocale': by_locale,
    'proposalCount': len(proposals), 'hashOnlyHoldCount': len(holds),
    'hashOnlyHeldSourceKeyCount': 1,
    'hashOnlyHoldSourceKeySha256': sha_text('CatalogNumber'),
    'allCurrentTokenChecksPass': all(all(r['tokenEvidence'][k] for k in ('placeholderParity','inlineCodeParity','markupParity','numericTokenParity','protectedLiteralParity')) for r in rows if r['decision']!='hold'),
    'allProposalTokenChecksPass': all(all(r['proposalTokenChecks'][k] for k in ('placeholderParity','inlineCodeParity','markupParity','numericTokenParity','protectedLiteralParity')) for r in proposals),
    'candidateFreeInputChecksumListSha256': sha_bytes((INPUT / 'SHA256SUMS.txt').read_bytes()),
    'candidateFreeManifestSha256': sha_bytes((INPUT / 'candidate-free-manifest.json').read_bytes()),
    'callerContextSha256': manifest['callerContext']['sha256'],
    'candidateFreeCellsSha256': manifest['candidateFreeCells']['sha256'],
    'nativeSpeakerReview': False, 'browserReview': False,
    'repoEdits': False, 'prEdits': False, 'workflowEdits': False,
    'testsBuildsScansCi': False,
    'livePrStateAtReview': {'state':'open','draft':True,'headSha':HEAD,'headTree':TREE},
    'createdAtUtc': datetime.now(timezone.utc).isoformat(),
}
(ROOT / 'summary.json').write_bytes(canon(summary))

print(json.dumps({'rows':len(rows),'decisions':dict(counts),'proposals':len(proposals),'holds':len(holds),'head':HEAD,'tree':TREE}, indent=2))
