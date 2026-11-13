#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
HEAD='daa578eaa0d1c252e969d1f5891a364b13d50ec0'
TREE='e0b306dc20596ad7004bdfb9ac2cc0a3021726c7'
TARGET_LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PLACEHOLDER_RE=re.compile(r'\{[^{}]+\}')
PROTECTED_RE=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
PROTECTED_BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
HOLD_KEYS={
 'AddMissing',
 'AddRootFolderInlineIntroAllMediaType',
 'AddRootFolderInlineIntroPrefix',
 'AddRootFolderInlineIntroSuffix',
 'AddRootFolderInlineRootFolderLabel',
}
REVISIONS={
 ('AddFormatSetupRequired','ar'):'قبل الإضافة، حدّد مجلدًا جذريًا وملف تعريف الجودة لكل تنسيق محدد.',
 ('AddImportListExclusionHelpText','ar'):'يمنع إضافة الكتاب إلى Chaptarr عبر قوائم الاستيراد أو عند تحديث المؤلف.',
 ('AddImportListExclusionHelpText','de'):'Verhindert, dass das Buch über Importlisten oder eine Autorenaktualisierung zu Chaptarr hinzugefügt wird.',
 ('AddImportListExclusionHelpText','es'):'Evita que el libro se añada a Chaptarr mediante las listas de importación o al actualizar el autor.',
 ('AddImportListExclusionHelpText','id'):'Mencegah buku ditambahkan ke Chaptarr melalui daftar impor atau penyegaran penulis.',
 ('AddImportListExclusionHelpText','ja'):'インポートリストや著者の更新によって、書籍がChaptarrに追加されないようにします。',
 ('AddImportListExclusionHelpText','ko'):'가져오기 목록이나 작가 새로 고침을 통해 책이 Chaptarr에 추가되지 않도록 합니다.',
 ('AddImportListExclusionHelpText','pt-BR'):'Impede que o livro seja adicionado ao Chaptarr por meio das listas de importação ou da atualização do autor.',
 ('AddImportListExclusionHelpText','vi'):'Ngăn sách được thêm vào Chaptarr thông qua danh sách nhập hoặc thao tác làm mới tác giả.',
 ('AddImportListExclusionHelpText','zh-Hans'):'防止书籍通过导入列表或作者刷新功能添加到 Chaptarr。',
 ('AddImportListExclusionHelpText','zh-Hant'):'防止圖書透過匯入清單或作者更新功能新增至 Chaptarr。',
 ('AddIndexer','ar'):'إضافة مفهرس',
 ('AddIndexer','fr'):'Ajouter un indexeur',
 ('AddIndexer','hi'):'इंडेक्सर जोड़ें',
 ('AddIndexer','id'):'Tambah pengindeks',
 ('AddIndexer','ja'):'インデクサーを追加',
 ('AddIndexer','ko'):'인덱서 추가',
 ('AddIndexer','vi'):'Thêm bộ lập chỉ mục',
 ('AddList','es'):'Añadir lista',
 ('AddList','fr'):'Ajouter une liste',
 ('AddList','vi'):'Thêm danh sách',
 ('AddListAudiobooksAndEbooks','id'):'Tambah daftar (buku audio + buku elektronik)',
 ('AddListAudiobooksAndEbooks','ja'):'リストを追加（オーディオブック + 電子書籍）',
 ('AddListEbooks','id'):'Tambah daftar (buku elektronik)',
 ('AddListEbooks','ja'):'リストを追加（電子書籍）',
 ('AddListEbooks','vi'):'Thêm danh sách (sách điện tử)',
 ('AddListExclusion','ar'):'إضافة استبعاد لقائمة الاستيراد',
 ('AddListExclusion','de'):'Ausschluss aus der Importliste hinzufügen',
 ('AddListExclusion','es'):'Añadir una exclusión de la lista de importación',
 ('AddListExclusion','fr'):'Ajouter une exclusion à la liste d’importation',
 ('AddListExclusion','hi'):'आयात सूची से बहिष्करण जोड़ें',
 ('AddListExclusion','id'):'Tambah pengecualian daftar impor',
 ('AddListExclusion','ja'):'インポートリストの除外を追加',
 ('AddListExclusion','ko'):'가져오기 목록 제외 항목 추가',
 ('AddListExclusion','pt-BR'):'Adicionar exclusão da lista de importação',
 ('AddListExclusion','vi'):'Thêm mục loại trừ khỏi danh sách nhập',
 ('AddListExclusion','zh-Hans'):'添加导入列表排除项',
 ('AddListExclusion','zh-Hant'):'新增匯入清單排除項',
 ('AddNew','ar'):'أضف جديدًا',
 ('AddNew','de'):'Neu hinzufügen',
 ('AddNew','id'):'Tambah baru',
 ('AddNew','zh-Hant'):'新增項目',
 ('AddNewItem','ar'):'إضافة عنصر جديد',
 ('AddNewItem','de'):'Neuen Eintrag hinzufügen',
 ('AddNewItem','es'):'Añadir elemento nuevo',
 ('AddNewSeries','vi'):'Thêm bộ sách mới',
 ('AddNewSeries','zh-Hans'):'添加新系列',
 ('AddNewSeries','zh-Hant'):'新增系列',
 ('AddProxy','fr'):'Ajouter un proxy',
 ('AddProxy','ko'):'프록시 추가',
 ('AddProxy','pt-BR'):'Adicionar proxy',
 ('AddSelected','ar'):'إضافة العناصر المحددة',
 ('AddSelected','es'):'Añadir selección',
 ('AddSelected','ja'):'選択した項目を追加',
 ('AddSelected','pt-BR'):'Adicionar seleção',
 ('AddSelected','zh-Hant'):'新增選取項目',
 ('AddToDownloadedQueue','de'):'Zur Download-Warteschlange hinzufügen',
 ('AddedToDownloadedQueue','de'):'Zur Download-Warteschlange hinzugefügt',
 ('AddToDownloadedQueue','es'):'Añadir a la cola de descargas',
 ('AddedToDownloadedQueue','es'):'Añadido a la cola de descargas',
 ('AddToDownloadedQueue','fr'):'Ajouter à la file de téléchargement',
 ('AddedToDownloadedQueue','fr'):'Ajouté à la file de téléchargement',
 ('AddToDownloadedQueue','hi'):'डाउनलोड कतार में जोड़ें',
 ('AddedToDownloadedQueue','hi'):'डाउनलोड कतार में जोड़ा गया',
 ('AddToDownloadedQueue','id'):'Tambahkan ke antrean unduhan',
 ('AddedToDownloadedQueue','id'):'Ditambahkan ke antrean unduhan',
 ('AddToDownloadedQueue','ja'):'ダウンロードキューに追加',
 ('AddedToDownloadedQueue','ja'):'ダウンロードキューに追加されました',
 ('AddToDownloadedQueue','pt-BR'):'Adicionar à fila de downloads',
 ('AddedToDownloadedQueue','pt-BR'):'Adicionado à fila de downloads',
 ('AddToDownloadedQueue','zh-Hans'):'添加到下载队列',
 ('AddToDownloadedQueue','zh-Hant'):'加入下載佇列',
 ('AddedToDownloadedQueue','zh-Hant'):'已加入下載佇列',
 ('AddToLibrary','ko'):'라이브러리에 추가',
 ('AddToLibrary','zh-Hans'):'添加到书库',
 ('AddToLibrary','zh-Hant'):'新增至書庫',
 ('AddedAuthorSettings','ar'):'إعدادات المؤلفين المضافين',
 ('AddedAuthorSettings','de'):'Einstellungen für hinzugefügte Autoren',
 ('AddedAuthorSettings','es'):'Configuración para autores añadidos',
 ('AddedAuthorSettings','fr'):'Paramètres pour les auteurs ajoutés',
 ('AddedAuthorSettings','hi'):'जोड़े गए लेखकों की सेटिंग्स',
 ('AddedAuthorSettings','id'):'Pengaturan untuk penulis yang ditambahkan',
 ('AddedAuthorSettings','ja'):'追加された作者の設定',
 ('AddedAuthorSettings','ko'):'추가된 저자 설정',
 ('AddedAuthorSettings','pt-BR'):'Configurações para autores adicionados',
 ('AddedAuthorSettings','vi'):'Thiết lập cho tác giả đã thêm',
 ('AddedAuthorSettings','zh-Hans'):'新增作者的设置',
 ('AddedAuthorSettings','zh-Hant'):'新增作者的設定',
 ('AddingTag','de'):'Tag wird hinzugefügt',
 ('AddingTag','es'):'Añadiendo etiqueta',
 ('AddingTag','hi'):'टैग जोड़ा जा रहा है',
 ('AddingTag','id'):'Menambahkan tag',
 ('AddingTag','ja'):'タグを追加中',
 ('AddingTag','ko'):'태그 추가 중',
 ('AddingTag','pt-BR'):'Adicionando etiqueta',
 ('AddingTag','vi'):'Đang thêm thẻ',
 ('AddingTag','zh-Hans'):'正在添加标签',
 ('AddingTag','zh-Hant'):'正在新增標籤',
 ('AdjustEbookConversionSettings','hi'):'ई-बुक रूपांतरण सेटिंग्स समायोजित करें',
 ('AgeWhenGrabbed','ar'):'عمر الإصدار عند تنزيله',
 ('AgeWhenGrabbed','de'):'Alter beim Abruf',
 ('AgeWhenGrabbed','es'):'Antigüedad al obtenerlo',
 ('AgeWhenGrabbed','fr'):'Âge au moment de la récupération',
 ('AgeWhenGrabbed','hi'):'डाउनलोड के समय की आयु',
 ('AgeWhenGrabbed','id'):'Usia saat diambil',
 ('AgeWhenGrabbed','pt-BR'):'Idade no momento da obtenção',
 ('AgeWhenGrabbed','vi'):'Độ tuổi của bản phát hành khi tải về',
 ('AgeWhenGrabbed','zh-Hans'):'抓取时的年龄',
 ('AgeWhenGrabbed','zh-Hant'):'抓取時的發行年齡',
 ('Agenda','ar'):'جدول المواعيد',
 ('Agenda','de'):'Terminübersicht',
 ('Agenda','es'):'Agenda',
 ('Agenda','fr'):'Agenda',
 ('Agenda','ja'):'予定一覧',
 ('Agenda','vi'):'Lịch trình',
 ('Agenda','zh-Hans'):'日程',
 ('Agenda','zh-Hant'):'日程',
 ('AllExpandedCollapseAll','es'):'Contraer todo',
 ('AllExpandedCollapseAll','vi'):'Thu gọn tất cả',
 ('AllExpandedExpandAll','ar'):'توسيع الكل',
 ('AllExpandedExpandAll','ja'):'すべて展開',
 ('AllowFingerprinting','de'):'Fingerabdruckabgleich erlauben',
 ('AllowFingerprintingHelpText','de'):'Fingerabdrücke verwenden, um die Genauigkeit der Buchzuordnung zu verbessern.',
 ('AllowFingerprinting','es'):'Permitir la identificación por huella digital',
 ('AllowFingerprintingHelpText','es'):'Usar huellas digitales para mejorar la precisión de la coincidencia de libros.',
 ('AllowFingerprinting','fr'):'Autoriser l’identification par empreinte',
 ('AllowFingerprintingHelpText','fr'):'Utiliser l’identification par empreinte pour améliorer la précision de la correspondance des livres.',
 ('AllowFingerprinting','hi'):'फ़िंगरप्रिंट मिलान की अनुमति दें',
 ('AllowFingerprintingHelpText','hi'):'पुस्तक मिलान की सटीकता बढ़ाने के लिए फ़िंगरप्रिंट मिलान का उपयोग करें।',
 ('AllowFingerprinting','id'):'Izinkan pencocokan sidik jari berkas',
 ('AllowFingerprintingHelpText','id'):'Gunakan sidik jari berkas untuk meningkatkan akurasi pencocokan buku.',
 ('AllowFingerprinting','ja'):'フィンガープリント照合を許可する',
 ('AllowFingerprintingHelpText','ja'):'フィンガープリント照合を使用して、書籍のマッチング精度を高めます。',
 ('AllowFingerprinting','ko'):'파일 지문 인식을 허용',
 ('AllowFingerprintingHelpText','ko'):'파일 지문 인식으로 책 매칭 정확도를 높입니다.',
 ('AllowFingerprinting','pt-BR'):'Permitir identificação por impressão digital',
 ('AllowFingerprintingHelpText','pt-BR'):'Usar a identificação por impressão digital para melhorar a precisão da correspondência de livros.',
 ('AllowFingerprinting','vi'):'Cho phép nhận dạng bằng dấu vân tay',
 ('AllowFingerprinting','zh-Hant'):'允許指紋識別',
}
REASONS={
 'AddFormatSetupRequired':'The setup warning names a root folder and a quality profile for every selected format; the revised Arabic uses the established full term for quality profile.',
 'AddImportListExclusionHelpText':'This help text is used in book and author delete dialogs. The revisions state that import lists or author refresh can add the record back and preserve the Chaptarr product name.',
 'AddIndexer':'The caller is the add-indexer modal; the revisions name an indexer service rather than an index.',
 'AddList':'The caller is the add-import-list modal. The revisions use the natural modal title or keep the action from meaning add-to-an-existing-list.',
 'AddListAudiobooksAndEbooks':'The current Indonesian and Japanese values leave eBooks in English; the revisions localize the category name.',
 'AddListEbooks':'The current Indonesian and Japanese values leave eBooks in English, and the Vietnamese value leaves ebooks in English; the revisions localize it as electronic books.',
 'AddListExclusion':'The caller is a delete-dialog checkbox that creates an import-list exclusion. The revised labels explicitly identify that exclusion.',
 'AddNew':'These buttons and navigation titles need an idiomatic generic “add new” action.',
 'AddNewItem':'The source and callers describe a generic item; the revisions replace English “Item” where it reads as an untranslated label.',
 'AddNewSeries':'The modal creates a book series; the revisions avoid a “sequence” meaning and use the book-series sense.',
 'AddProxy':'The caller is a proxy settings modal; the revisions use the localized proxy term and a consistent infinitive title.',
 'AddSelected':'The series modal adds selected entries; the revisions name the selected items or selection idiomatically.',
 'AddToDownloadedQueue':'The search-row tooltip adds a result to the downloader queue; the revisions use “download queue” instead of a queue already downloaded.',
 'AddedToDownloadedQueue':'The success tooltip confirms that the result was added to the downloader queue; the revised label matches the action label.',
 'AddToLibrary':'The Korean and Chinese values used an overly literal or vague word for the app library; the revisions use the software/book-library term.',
 'AddedAuthorSettings':'These are fieldset headings for settings applied to authors added by an import list or root-folder configuration, not a completed “settings added” action.',
 'AddingTag':'These are tooltips shown while a tag operation is in progress; the revisions use progressive wording.',
 'AdjustEbookConversionSettings':'The current Hindi keeps the category in Latin-script English; the revision uses the established Hindi e-book term.',
 'AgeWhenGrabbed':'The caller shows release age in history at the time a download was grabbed; the revisions avoid literal “caught/seized” or a duration/lifetime reading.',
 'Agenda':'The caller is a calendar view switch. The revisions name a calendar schedule/list view rather than a meeting agenda.',
 'AllExpandedCollapseAll':'The revisions use the UI action “collapse all,” avoiding “close” or “shrink” meanings.',
 'AllExpandedExpandAll':'The revisions use the UI action “expand all,” avoiding an ungrammatical phrase or “show all.”',
 'AllowFingerprinting':'This setting uses file fingerprinting to improve book matching; the revised labels name fingerprint matching rather than biometric fingerprinting or audio tracking.',
 'AllowFingerprintingHelpText':'This setting uses file fingerprinting to improve book matching; the revised text describes that matching method without changing the source meaning.',
}
SEMANTICS={
 'AddFormatSetupRequired':'Before adding, each selected format needs a root folder and quality profile.',
 'AddImportListExclusionHelpText':'Prevent an author or book from being re-added through import lists or author refresh.',
 'AddIndexer':'Add an indexer integration.',
 'AddList':'Add an import list.',
 'AddListAudiobooks':'Add an import list for audiobooks.',
 'AddListAudiobooksAndEbooks':'Add an import list for audiobooks and eBooks.',
 'AddListEbooks':'Add an import list for eBooks.',
 'AddListExclusion':'Create an import-list exclusion while deleting a book or author.',
 'AddMetadataProfile':'Open the add metadata profile modal.',
 'AddMissing':'Server Match; exact caller and grammatical use are not available.',
 'AddMoreOptions':'Show more options.',
 'AddName':'Add the provided name.',
 'AddNew':'Add a new item.',
 'AddNewAuthor':'Open the add author modal.',
 'AddNewAuthorRootFolderHelpText':'The named subfolder is created automatically.',
 'AddNewBook':'Add a book.',
 'AddNewItem':'Open the generic add-item page.',
 'AddNewSeries':'Open the add book-series modal.',
 'AddNotification':'Open the add notification modal.',
 'AddProxy':'Open the add proxy modal.',
 'AddQualityProfile':'Open the add quality profile modal.',
 'AddRootFolder':'Add a root folder.',
 'AddRootFolderInlineIntroAllMediaType':'Fragment about all values for a dynamic media type.',
 'AddRootFolderInlineIntroPrefix':'Opening fragment for a dynamic root-folder explanation.',
 'AddRootFolderInlineIntroSuffix':'Closing fragment for a dynamic root-folder explanation.',
 'AddRootFolderInlineRootFolderLabel':'Dynamic media-type root-folder label.',
 'AddSelected':'Add selected series/items.',
 'AddToDownloadedQueue':'Add the result to the download-client queue.',
 'AddToLibrary':'Add the selected content to the app library.',
 'Added':'Added status and sort label.',
 'AddedAuthorSettings':'Section heading for settings applied to newly added authors.',
 'AddedToDownloadedQueue':'The result has been added to the download-client queue.',
 'AddingTag':'A tag is being added.',
 'AdditionalSelectedBooksNotLoaded':'Some selected books are not loaded in the current view.',
 'AdjustAudiobookConversionSettings':'Adjust audiobook conversion settings.',
 'AdjustEbookConversionSettings':'Adjust e-book conversion settings.',
 'Active':'Active.',
 'ActiveOnly':'Only active entries.',
 'AgeWhenGrabbed':'Age of the release at the time it was grabbed.',
 'Agenda':'Calendar agenda/list view.',
 'All':'All entries.',
 'AllAuthorBooks':'All books by the author.',
 'AllBooks':'All books.',
 'AllNewBooks':'All new books.',
 'AllExpandedCollapseAll':'Collapse all expanded entries.',
 'AllExpandedExpandAll':'Expand all entries.',
 'AllResultsAreHiddenByTheAppliedFilter':'The active filter hides every result.',
 'AllowAuthorChangeClickToChangeAuthor':'Click to change the author.',
 'AllowFingerprinting':'Allow file fingerprint matching.',
 'AllowFingerprintingHelpText':'Use file fingerprinting to improve book-match accuracy.',
}
HOLD_RATIONALES={
 'AddMissing':'No direct frontend translate caller is present. The source label could describe either an action or a state, and its grammatical role cannot be established from the pinned packet.',
 'AddRootFolderInlineIntroAllMediaType':'No direct caller is present. This fragment contains a dynamic media-type placeholder with language-specific number and gender requirements; its exact composed value cannot be verified.',
 'AddRootFolderInlineIntroPrefix':'No direct caller is present. This is a sentence fragment whose order and joining punctuation depend on its dynamic UI composition.',
 'AddRootFolderInlineIntroSuffix':'No direct caller is present. This is a sentence fragment whose subject and preposition depend on its dynamic UI composition.',
 'AddRootFolderInlineRootFolderLabel':'No direct caller is present. The dynamic media-type value can affect word order and grammatical agreement, so the correct full label cannot be verified.',
}

def sha(data):return hashlib.sha256(data).hexdigest()
def sha_text(s):return sha(s.encode('utf-8'))
def signature(s):return dict(sorted(collections.Counter(PLACEHOLDER_RE.findall(s)).items()))
def literals(s):return sorted(set(PROTECTED_RE.findall(s)) | (PROTECTED_BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def read_jsonl_lines(p):
    return [(json.loads(line),line.rstrip(b'\n')) for line in p.read_bytes().splitlines(keepends=True) if line.strip()]

def main():
    subprocess.run(['python',str(HERE/'verify_candidate_free.py')],check=True)
    subprocess.run(['sha256sum','-c','candidate-free-SHA256SUMS.txt'],cwd=HERE,check=True,stdout=subprocess.DEVNULL)
    sel=json.loads((HERE/'source-selection.json').read_text(encoding='utf-8'))
    rows_in=read_jsonl_lines(HERE/'candidate-free-cells.jsonl')
    source_selection_sha=sha((HERE/'source-selection.json').read_bytes())
    assert len(rows_in)==600
    for k,l in REVISIONS:assert k in SEMANTICS and l in TARGET_LOCALES,(k,l)
    for key in HOLD_KEYS:assert key in SEMANTICS and key in HOLD_RATIONALES
    assert set(SEMANTICS)==set(sel['keys'])
    rows=[];revisions=[];holds=[]
    for inp,line_bytes in rows_in:
        key,loc=inp['sourceKey'],inp['locale'];ident=f'{key}::{loc}'
        row_hash=sha(line_bytes);callers=inp['callerRefs'];caller_paths=sorted({r['path'] for r in callers})
        base={
            'batch':'W50-99','sourceOrdinal':inp['sourceOrdinal'],'sourceKey':key,'sourceId':key,'locale':loc,'cellId':ident,
            'sourceTextSha256':inp['sourceTextSha256'],'currentTargetSha256':inp['currentTargetSha256'],
            'sourceFile':inp['sourceFile'],'sourceFileSha256':inp['sourceFileSha256'],'sourceFileGitBlob':inp['sourceFileGitBlob'],
            'targetFile':inp['targetFile'],'targetFileSha256':inp['targetFileSha256'],'targetFileGitBlob':inp['targetFileGitBlob'],
            'sourcePlaceholders':inp['sourcePlaceholders'],'currentPlaceholders':inp['currentPlaceholders'],
            'protectedLiterals':inp['protectedLiterals'],'callerContextSha256':inp['callerContextSha256'],
            'callerReferenceCount':inp['callerReferenceCount'],'callerPaths':caller_paths,
            'candidateFreeRowSha256':row_hash,'sourceSelectionSha256':source_selection_sha,
            'exactHead':HEAD,'exactTree':TREE,'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,
            'reviewerMethod':'Independent primary semantic review from the sealed candidate-free source/current targets and pinned caller context. No wording from prior proposals was used.',
            'reviewerPartition':'primary-W50-99-all-locales','semanticInterpretation':SEMANTICS[key],
        }
        if key in HOLD_KEYS:
            out={**base,'primaryDisposition':'hold','holdRationale':HOLD_RATIONALES[key],
                 'reviewConfidence':'low','finalReviewedTarget':None,'finalReviewedTargetSha256':None,
                 'recommendedTarget':None,'recommendedTargetSha256':None,'finalPlaceholders':None,
                 'placeholderParity':None,'protectedLiteralChecks':[],'protectedLiteralDisposition':'not-assessed'}
            out.pop('semanticInterpretation')
            holds.append({k:out[k] for k in ('batch','sourceOrdinal','sourceKey','locale','cellId','sourceTextSha256','currentTargetSha256','callerContextSha256','callerReferenceCount','candidateFreeRowSha256','sourceSelectionSha256','primaryDisposition','holdRationale','reviewConfidence')})
        else:
            final=REVISIONS.get((key,loc),inp['currentTarget'])
            disposition='revise-current' if final!=inp['currentTarget'] else 'accept-current'
            assert signature(final)==inp['sourcePlaceholders']==inp['currentPlaceholders'],(ident,signature(final),inp['sourcePlaceholders'],inp['currentPlaceholders'])
            checks=[{'literal':lit,'currentPresent':lit in inp['currentTarget'],'currentExactCase':lit in inp['currentTarget'],'finalPresent':lit in final,'finalExactCase':lit in final} for lit in inp['protectedLiterals']]
            assert all(x['finalPresent'] and x['finalExactCase'] for x in checks),ident
            reason=REASONS.get(key,'The current wording preserves the source meaning in the pinned caller context; placeholders and protected literals are preserved.')
            if disposition=='revise-current':
                revisions.append({'batch':'W50-99','sourceOrdinal':inp['sourceOrdinal'],'sourceKey':key,'locale':loc,'cellId':ident,
                                  'currentTargetSha256':inp['currentTargetSha256'],'recommendedTarget':final,
                                  'recommendedTargetSha256':sha_text(final),'callerContextSha256':inp['callerContextSha256'],
                                  'candidateFreeRowSha256':row_hash,'sourceSelectionSha256':source_selection_sha,'rationale':reason})
            out={**base,'sourceText':inp['sourceText'],'sourceTextSha256':inp['sourceTextSha256'],
                 'currentTarget':inp['currentTarget'],'currentTargetSha256':inp['currentTargetSha256'],
                 'primaryDisposition':disposition,'decisionRationale':reason,
                 'recommendedTarget':final if disposition=='revise-current' else None,
                 'recommendedTargetSha256':sha_text(final) if disposition=='revise-current' else None,
                 'finalReviewedTarget':final,'finalReviewedTargetSha256':sha_text(final),
                 'finalPlaceholders':signature(final),'placeholderParity':True,
                 'protectedLiteralChecks':checks,'protectedLiteralDisposition':'pass','reviewConfidence':'moderate'}
        rows.append(out)
    review_dir=HERE/'primary-review';review_dir.mkdir(mode=0o700,exist_ok=True)
    def dump_jsonl(p,items):p.write_bytes(b''.join((json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8') for x in items))
    dump_jsonl(review_dir/'primary-review-cells.jsonl',rows)
    dump_jsonl(review_dir/'primary-review-proposals.jsonl',revisions)
    dump_jsonl(review_dir/'primary-review-holds.jsonl',holds)
    counts=collections.Counter(r['primaryDisposition'] for r in rows)
    rev_counts=collections.Counter(r['locale'] for r in rows if r['primaryDisposition']=='revise-current')
    summary={
        'packet':'ChaptarrNG PR #190 W50-99 primary semantic review',
        'exactHead':HEAD,'exactTree':TREE,'sourceSelectionSha256':source_selection_sha,
        'candidateFreeCellsSha256':sha((HERE/'candidate-free-cells.jsonl').read_bytes()),
        'primaryReviewCellsSha256':sha((review_dir/'primary-review-cells.jsonl').read_bytes()),
        'counts':{'cells':len(rows),'sourceKeys':50,'locales':12,'acceptCurrent':counts['accept-current'],
                  'reviseCurrent':counts['revise-current'],'hold':counts['hold'],
                  'callerlessCells':sum(r['callerReferenceCount']==0 for r in rows),
                  'callerlessKeys':sum(all(r['callerReferenceCount']==0 for r in rows if r['sourceKey']==k) for k in {r['sourceKey'] for r in rows}),
                  'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600},
        'revisionCountsByLocale':{k:rev_counts.get(k,0) for k in TARGET_LOCALES},
        'revisionCellIds':[r['cellId'] for r in rows if r['primaryDisposition']=='revise-current'],
        'holdCellIds':[r['cellId'] for r in rows if r['primaryDisposition']=='hold'],
        'holdKeys':sorted(HOLD_KEYS),
        'reviewScope':'Primary semantic recommendations only. Target catalogs remain unedited; blind cross-review and native-speaker review remain outstanding.'
    }
    (review_dir/'primary-review-summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    readme=f'''# ChaptarrNG PR #190 W50–W99 primary review

Pinned to head {HEAD} / tree {TREE}. The primary reviewer used only the sealed candidate-free packet at this head.

The ledger has 600 cells (50 English Core keys × 12 target locales). It records accepted current text, focused recommendations, and text-free holds. Holds contain no source or target wording and no proposed text. They cover one uncalled ambiguous label and four uncalled dynamic root-folder fragments whose placeholder context and composition cannot be verified from the pinned frontend.

No catalog or repository file was changed. Recommendations need blind cross-adjudication and native-speaker review; this packet does not claim native approval.
'''
    (review_dir/'README-primary-review.md').write_text(readme,encoding='utf-8')
    print(json.dumps({'result':'BUILT','exactHead':HEAD,'exactTree':TREE,'cells':len(rows),
                      'acceptCurrent':counts['accept-current'],'reviseCurrent':counts['revise-current'],
                      'holds':counts['hold'],'revisionCountsByLocale':dict(rev_counts),'revisionFiles':len(revisions)},
                     ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
