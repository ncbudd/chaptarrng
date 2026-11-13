#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

TASK=Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104')
INPUT=TASK/'candidate-free/input'; OUT=TASK/'primary-review'
HEAD='f0082d1b655c05b8d4019ede523dd695cd6d745a'; TREE='4cf2322354e9cf9b12d59cf10d0d8661c68ab4af'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}

def sha(b):return hashlib.sha256(b).hexdigest()
def stsha(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def writej(p,o):p.write_bytes((json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def writejl(p,rows):p.write_bytes(b''.join(canon(r) for r in rows))
def rj(n):return json.loads((INPUT/n).read_text(encoding='utf-8'))
def rjl(n):return [json.loads(x) for x in (INPUT/n).read_text(encoding='utf-8').splitlines() if x.strip()]
def need(v,m):
 if not v:raise SystemExit('FAIL: '+m)
def counter(rx,s):return collections.Counter(rx.findall(s))
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def keyhash(k):return stsha(k)
def cellhash(k,loc):return stsha(f'{k}::{loc}')

# Primary semantic recommendations are derived from this exact candidate-free source/caller packet only.
PROPOSALS={}
def add(key,loc,target,rationale,confidence='moderate'):
 PROPOSALS[(key,loc)]={'target':target,'rationale':rationale,'confidence':confidence}

# Indonesian download status: the book is the object being downloaded.
add('BookIsDownloading','id','Buku sedang diunduh','The activity and book-status callers show the book as the item being downloaded. The passive form avoids making the book sound like the downloader.','high')
add('BookIsDownloadingInterp','id','Buku sedang diunduh - {0}% {1}','The queue and calendar show download progress and the book title; the passive form preserves that meaning and both placeholders.','high')

# Match-mode vocabulary and help copy in the pinned Settings and Quickstart callers.
add('BookMatchingStrictness','id','Mode pencocokan','The settings label names the selectable book-matching mode; “Mode cocok” reads like a mode that is suitable rather than a matching mode.','high')
for loc,target in {
 'de':'Locker','es':'Flexible','fr':'Souple','hi':'लचीला','id':'Longgar','pt-BR':'Flexível','vi':'Linh hoạt'
}.items():
 why={'de':'The standalone “Lose” is awkward as a strictness option; “Locker” names the less strict mode more naturally.',
      'es':'“Suave” means soft or mild; “Flexible” describes a permissive matching mode more clearly.',
      'fr':'“Lâche” has an undesirable slack or cowardly sense in French; “Souple” is a natural label for a permissive matching mode.',
      'hi':'The current label transliterates “loose”; “लचीला” gives a readable Hindi label for flexible matching.',
      'id':'“Lepas” suggests free or detached; “Longgar” expresses loose matching.',
      'pt-BR':'“Frouxo” can sound weak or slack; “Flexível” is clearer for a permissive matching mode.',
      'vi':'“Thả lỏng” reads as relax/loosen; “Linh hoạt” is a clearer mode label for flexible matching.'}[loc]
 add('BookMatchingStrictnessAggressive',loc,target,why,'moderate')
for loc,target in {
 'de':'Locker: Ein Treffer ist möglich, wenn der Buchtitel vorhanden ist, es sei denn, ein weiterer Buchtitel erklärt das sauberste Titelfeld besser. Ein Abgleich mit einem allgemeinen Serientitel wird ebenfalls blockiert, wenn jedes Titelfeld auf eine andere Position in der Reihe verweist.',
 'es':'Flexible: coincide cuando está presente el título del libro, salvo que otro título de libro explique mejor el campo de título más claro. También se bloquea la coincidencia con un título genérico de serie cuando todos los campos de título apuntan a posiciones distintas de la serie.',
 'fr':'Souple : le titre du livre suffit, sauf si un autre titre de livre explique mieux le champ de titre le plus clair. Une correspondance avec un titre de série générique est également bloquée lorsque tous les champs de titre pointent vers des positions différentes dans la série.',
 'hi':'लचीला: पुस्तक का शीर्षक मौजूद होने पर मिलान करें, जब तक कि कोई अन्य पुस्तक शीर्षक सबसे स्पष्ट शीर्षक फ़ील्ड की बेहतर व्याख्या न करे। यदि सभी शीर्षक फ़ील्ड अलग-अलग श्रृंखला स्थानों की ओर संकेत करते हैं, तो सामान्य श्रृंखला-शीर्षक का मिलान भी अवरुद्ध होता है।',
 'id':'Longgar: cocokkan jika judul buku tersedia, kecuali ada judul buku lain yang lebih tepat menjelaskan bidang judul paling jelas. Pencocokan berdasarkan judul seri umum juga diblokir jika setiap bidang judul menunjuk ke posisi yang berbeda dalam seri.',
 'pt-BR':'Flexível: corresponde quando o título do livro está presente, a menos que outro título de livro explique melhor o campo de título mais claro. A correspondência com um título de série genérico também é bloqueada quando todos os campos de título apontam para posições diferentes da série.',
 'vi':'Linh hoạt: khớp khi có tựa sách, trừ khi một tựa sách khác giải thích rõ hơn trường tựa sách rõ nhất. Việc khớp với tiêu đề series chung cũng bị chặn khi mọi trường tiêu đề đều trỏ đến các vị trí khác nhau trong series.'
}.items():
 why={'de':'The pinned help-text caller explains that this mode accepts a book-title match unless a better sibling-title explanation exists. The revised wording removes the English “Match” fragment and keeps the series-position rejection condition.',
      'es':'The help text is shown beside the matching-mode control and in Quickstart examples; the revision makes the permissive rule and series-position block grammatical and explicit.',
      'fr':'The help text defines the permissive mode; the current “Lâche” wording is both awkward and negative, and the revision preserves the title and series-position conditions.',
      'hi':'The settings help text defines when loose matching is allowed; the revision replaces the transliterated mode label and preserves both exception rules.',
      'id':'The settings help text contains untranslated English terms and awkward literal phrases. The revision preserves the book-title, better-title, and generic-series-position rules.',
      'pt-BR':'The settings help text defines a flexible match and its two blocking conditions. The revision uses a natural mode label and keeps those conditions intact.',
      'vi':'The settings help text defines flexible matching; the revision uses a clearer label and keeps the sibling-title and series-position conditions.'}[loc]
 add('BookMatchingStrictnessAggressiveHelpText',loc,target,why,'moderate')
add('BookMatchingStrictnessBalanced','id','Seimbang','The Quickstart and Settings callers use this as the middle match-strictness option; “Dibalanced” is an untranslated, malformed label.','high')
for loc,target in {
 'de':'Ausgewogen: die beste Voreinstellung. Der passende Titel muss vorhanden sein. Rauschen und Abweichungen bei der Seriennummer werden toleriert, es sei denn, ein anderer Buchtitel erklärt dasselbe Tag besser oder jedes allgemeine Serientitelfeld verweist auf eine andere Position in der Reihe.',
 'es':'Equilibrado: la mejor opción predeterminada. El título coincidente debe estar presente. Se toleran el ruido y las discrepancias en el número de serie, salvo que otro título de libro explique mejor la misma etiqueta o todos los campos de título de serie genéricos apunten a posiciones distintas de la serie.',
 'fr':'Équilibré : le meilleur choix par défaut. Le titre correspondant doit être présent. Le bruit et les désaccords sur le numéro de série sont tolérés, sauf si un autre titre de livre explique mieux le même tag ou si chaque champ générique de titre de série pointe vers une position différente dans la série.',
 'id':'Seimbang: pilihan bawaan terbaik. Judul yang cocok harus tersedia. Kata-kata tambahan dan perbedaan nomor seri masih ditoleransi, kecuali judul buku lain lebih tepat menjelaskan tag yang sama atau setiap bidang judul seri umum menunjuk ke posisi yang berbeda dalam seri.',
 'pt-BR':'Equilibrado: melhor opção padrão. O título correspondente precisa estar presente. Ruído e divergências no número da série são tolerados, a menos que outro título de livro explique melhor a mesma tag ou todos os campos genéricos de título de série apontem para posições diferentes da série.'
}.items():
 why={'de':'The help text is shown beside the default mode. The revision makes “best default” and series-number disagreements read naturally while preserving both exceptions.',
      'es':'The direct Settings and Quickstart callers use this as the recommended default; the revision fixes the awkward “best by default” construction and preserves the matching conditions.',
      'fr':'The Settings help text calls this the default mode; the revision fixes the clipped “meilleur défaut” and retains the tolerance and blocking rules.',
      'id':'The current target begins with the malformed “Dibalanced” and leaves “series” untranslated in a broken sentence. The revision expresses the default, noise tolerance, and two blocking cases.',
      'pt-BR':'The Settings help text describes the recommended default; the revision makes the noise and series-number conditions grammatical and preserves the exceptions.'}[loc]
 add('BookMatchingStrictnessBalancedHelpText',loc,target,why,'moderate')
add('BookMatchingStrictnessStrict','ar','صارم','The strict help text uses “صارم”, while the option label uses “حازم”. Use the same strictness term in the matching-mode selector and its explanation.','moderate')
add('BookMatchingStrictnessStrictHelpText','hi','सख्त: साफ़ टैग फ़ील्ड की आवश्यकता होती है, जिसमें शीर्षक और आस-पास का अर्थपूर्ण पाठ पुस्तक के मेटाडेटा से स्पष्ट हो। श्रृंखला की विरोधाभासी स्थिति उस फ़ील्ड को अमान्य कर देती है। पाथ फ़ॉलबैक बंद रहता है।','The Settings help text describes a tag-field check and disables path fallback. The current “पथ वापसी” means path return, not fallback; the revision preserves the rule.','moderate')
add('BookMatchingStrictnessStrictHelpText','id','Ketat: diperlukan bidang tag yang bersih, tempat judul dan teks bermakna di sekitarnya dapat dijelaskan oleh metadata buku. Posisi seri yang bertentangan membuat bidang tersebut tidak valid. Pencocokan cadangan berdasarkan jalur dinonaktifkan.','The Settings help text uses “Strict” untranslated and calls fallback “path return” in other locales; this revision keeps the title, nearby-text, conflicting-position, and path-fallback rules in Indonesian.','moderate')

# Quickstart token labels: retain the distinction between good metadata, conflicts, and title/series examples.
add('AccurateMetadataPlaceholder','pt-BR','Informações precisas de autor/narrador/série','This is an allowed metadata token in the Quickstart match example. The current phrase says “precise author” and does not label the information as accurately as the source does.','moderate')
add('ConflictingBookDataPlaceholder','id','Data buku yang bertentangan','This is a blocked-token label in the Quickstart example; the current “Data buku konflik” is an awkward noun stack.','moderate')
add('KnownAccurateMetadataPlaceholder','id','Metadata akurat yang diketahui','This is the allowed metadata label in the strict Quickstart example; the current “Metadata akurat dikenal” is not natural Indonesian.','moderate')
add('GenericSeriesTitleWithDifferentPositionPlaceholder','es','Solo campos de título de serie con una posición diferente','The Quickstart example labels a conflicting generic series-title field. The current hyphenated “serie-títulos” construction is ungrammatical.','moderate')
add('GenericSeriesTitleWithDifferentPositionPlaceholder','hi','केवल वे श्रृंखला-शीर्षक फ़ील्ड जिनकी स्थिति अलग है','The Quickstart example uses this as a blocked token for a series title at a different position; the current word order is unclear.','moderate')
add('GenericSeriesTitleWithDifferentPositionPlaceholder','id','Hanya bidang judul seri dengan posisi berbeda','The Quickstart example uses this as a blocked token; the current “series- judul” mix is awkward and leaves the term partly untranslated.','moderate')
add('SiblingTitleBetterMatchPlaceholder','hi','पुस्तक का कोई अन्य शीर्षक बेहतर मेल खाता है','This blocked Quickstart token says another book title is a better match; the current borrowed “फिट” is awkward in this label.','moderate')
add('SiblingTitleBetterMatchPlaceholder','id','Judul buku lain lebih cocok','This blocked Quickstart token says a different book title fits better; the current word order is awkward.','moderate')
add('SiblingTitleBetterMatchPlaceholder','ja','別の書籍タイトルのほうが適しています','This blocked Quickstart token explains why a title is rejected; the revision uses the same book-title terminology as the nearby example labels.','moderate')
add('SameSeriesDifferentPositionPlaceholder','ar','السلسلة نفسها، بموضع مختلف','This Quickstart token means another item is in the same series but at a different sequence position; “موقف” can mean a stance, so “موضع” is clearer.','moderate')

# Import-list status, count, and history labels in the pinned sync modal.
add('FailureStage','es','Etapa del error','The sync summary prints this label before the failure-stage code; “etapa de fracaso” is an unnatural label for an error stage.','moderate')
add('FailureStage','vi','Giai đoạn xảy ra lỗi','The sync summary prints this label before the failure-stage code; the current word order “Lỗi giai đoạn” is unnatural.','moderate')
add('NoImportListSyncHistory','de','Noch kein Synchronisierungsverlauf vorhanden.','The Import List history modal uses this as its empty-state message; “Sync-Geschichte” reads as sync story rather than history.','high')
add('DryRunNoProviderCommit','zh-Hans','模拟运行——提供者状态保持不变','The history row uses this when a preview ran without committing provider state. “干运行” is a literal and unnatural translation of dry run.','moderate')
add('PreviewComplete','ar','اكتملت المعاينة','The sync modal uses this as the result title for a completed preview. The current “الاستعراض” means review/inspection, while the neighboring preview strings use “المعاينة”.','high')
for key,target,why in [
 ('PreviewComplete','Pratinjau selesai','The sync modal uses this as a completed-preview result title; “Pratilik” is a typo/nonstandard form, while “pratinjau” is the standard Indonesian term.'),
 ('PreviewFailed','Pratinjau gagal','The sync modal uses this as the failed-preview result title; “Pratilik” is a typo/nonstandard form.'),
 ('PreviewNextSync','Pratinjau sinkronisasi berikutnya','This is the action button that requests a preview of the next sync; the current “Pratilik” is nonstandard.'),
 ('PreviewingSync','Sedang membuat pratinjau…','This is the modal button state while a sync preview is in progress; the current “Pratilik…” does not express progress and uses a nonstandard term.')]:
 add(key,'id',target,why,'high')
add('PreviewNextSync','fr','Aperçu de la prochaine synchronisation','This is the Import List button that starts a preview of the next synchronization; the current “Aperçu Synchronisation suivante” lacks the needed link between the nouns.','moderate')
add('PreviewNextSync','ja','次回の同期をプレビュー','This is the action button for a preview of the next sync; the current “プレビュー 次の同期” has unnatural word order.','moderate')
add('PreviewingSync','ja','プレビュー中…','This is the sync-preview button state while the request is running; the current “プレビュー...” names the preview but does not express that it is in progress.','moderate')

# The history row reaches this label only after ImportListSyncService.CommitState succeeds.
for loc,target in {
 'ar':'تم حفظ حالة المزوّد','de':'Anbieterstatus gespeichert','es':'Estado del proveedor guardado','fr':'État du fournisseur enregistré','hi':'प्रदाता की स्थिति सहेजी गई','id':'Status penyedia telah disimpan','pt-BR':'Estado do provedor salvo','vi':'Đã lưu trạng thái nhà cung cấp','zh-Hans':'提供者状态已保存','zh-Hant':'供應商狀態已儲存'
}.items():
 why={'ar':'The history row shows this after the provider state is persisted; “confirmed” describes confirmation rather than saving that state.',
      'de':'The sync history marks a completed provider-state commit; “festgelegt” means set, while “gespeichert” conveys the persisted result.',
      'es':'The sync history shows this after CommitState succeeds; “comprometido” is ambiguous and can mean compromised, while “guardado” conveys persisted state.',
      'fr':'The sync history shows this after CommitState succeeds; “engagé” is ambiguous, while “enregistré” conveys the persisted state.',
      'hi':'The sync history shows this after provider state is saved; the current “प्रतिबद्ध” reads as pledged/committed rather than saved.',
      'id':'The sync history shows this after CommitState persists provider state; the current “dikomit” is untranslated technical jargon.',
      'pt-BR':'The sync history shows this after CommitState succeeds; “comprometido” can mean compromised, while “salvo” conveys persisted state.',
      'vi':'The sync history shows this after provider state is persisted; “cam kết” means a pledge/commitment rather than saved state.',
      'zh-Hans':'The sync history shows this after provider state is persisted; “已提交” reads as submitted, while “已保存” conveys saved state.',
      'zh-Hant':'The sync history shows this after provider state is persisted; “已提交” reads as submitted, while “已儲存” conveys saved state.'}[loc]
 add('ProviderStateCommitted',loc,target,why,'moderate')

add('RequestFailed','es','La solicitud falló.','This is the generic network/request error shown in the import-list modal and search fallback; “Solicitud fallada” is an unnatural passive construction.','high')
add('RequestFailed','pt-BR','A solicitação falhou.','This generic error appears in the import-list modal and search fallback; “pedido” usually means an order, not a request.','high')
for loc,target in {
 'es':'Aptos para la búsqueda','fr':'Éligibles à la recherche','hi':'खोज के लिए पात्र','id':'Memenuhi syarat untuk pencarian','pt-BR':'Elegíveis para busca','vi':'Đủ điều kiện để tìm kiếm','zh-Hans':'符合搜索条件的条目','zh-Hant':'可供搜尋'
}.items():
 why={'es':'The modal displays this as a count of items eligible to be searched; “Búsqueda elegible” describes an eligible search, not eligible items.',
      'fr':'The modal displays a count of items that can be searched; the current phrase makes the search itself sound admissible.',
      'hi':'The modal displays a count of items eligible to be searched; the revision makes eligibility apply to the items for search.',
      'id':'The modal displays a count of items eligible for search; the revision makes eligibility apply to the items rather than the search action.',
      'pt-BR':'The modal displays a count of items eligible to be searched; “Procura elegível” makes the search itself sound eligible.',
      'vi':'The modal displays a count of items eligible to be searched; the revision makes the eligibility relation explicit.',
      'zh-Hans':'The modal displays a count of list items that qualify for search; the revision gives this count label a clear object.',
      'zh-Hant':'The modal displays a count of list items available for search; the current “搜尋符合” is an incomplete phrase.'}[loc]
 add('SearchEligibleItems',loc,target,why,'moderate')

# Running/succeeded state labels are shown as sync-history statuses.
for loc,target,why in [
 ('de','Läuft','The history row uses this as a status; “Laufen” is an infinitive/noun rather than a running state.'),
 ('es','En curso','The history row uses this as a sync status; “Corriendo” suggests a person or process running rather than a sync in progress.'),
 ('ja','同期中','The history row uses this while synchronization is underway; “ランニング” is an unnatural English loan in this status.'),
 ('zh-Hans','同步中','The history row uses this while a sync is in progress; this names the sync state directly.'),
 ('zh-Hant','同步中','The history row uses this while a sync is in progress; this names the sync state directly.')]:
 add('SyncRunning',loc,target,why,'moderate')
for loc in ['zh-Hans','zh-Hant']:
 add('SyncSucceeded',loc,'同步成功','The history row uses this as a completed-sync status; the revised label states what succeeded instead of the awkward “already successful” wording.','moderate')

# These strings are count headers in ImportListSyncModal, so plural/noun-like forms read better with the counts.
for loc,target in {'es':'Nuevos','fr':'Nouveaux','hi':'नए','pt-BR':'Novos','zh-Hans':'新增','zh-Hant':'新增'}.items():
 add('NewItems',loc,target,'The sync summary displays this label before a count of new items; the current singular Spanish/French/Hindi/Portuguese forms and literal Chinese forms do not read naturally as count labels.','moderate')
add('ChangedItems','pt-BR','Alterações','The sync summary displays this before the number of changed items; the current singular adjective “Alterado” does not fit the count label.','moderate')
for loc,target in {'es':'Procesados','pt-BR':'Processados'}.items():
 add('ProcessedItems',loc,target,'The sync summary displays this before the processed-item count; the current singular form is mismatched with the count label.','moderate')

# The Quickstart renders these as mock filename tokens, where a terminal sentence period becomes part of the example text.
for key,loc,target in [
 ('ExtraUnrelatedTextPlaceholder','pt-BR','Palavras extras não relacionadas'),
 ('NoisyExtraTextPlaceholder','pt-BR','Palavras extras confusas'),
 ('SiblingTitleBetterMatchPlaceholder','pt-BR','Outro título de livro se encaixa melhor'),
]:
 add(key,loc,target,'The Quickstart renders this as text inside a mock filename-token pill; the source is a fragment, so a sentence-final period becomes part of the displayed token. The last label also needs “outro título de livro”, not “outro título do livro”.','moderate')

need(not OUT.exists(),'primary review output already exists')
subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=INPUT,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['python3',str(INPUT/'verify_candidate_free.py')],check=True,stdout=subprocess.DEVNULL)
manifest=rj('candidate-free-manifest.json'); selection=rj('source-selection.json')
need((manifest['head'],manifest['tree'])==(HEAD,TREE),'candidate-free pin')
raw=(INPUT/'candidate-free-cells.jsonl').read_bytes().splitlines(); incoming=[json.loads(x) for x in raw]
need(len(incoming)==600 and len(selection['keys'])==50,'candidate-free dimensions')
ctxs={r['sourceKey']:r for r in rjl('caller-context.jsonl')}
source_notes=[]; bykey=collections.defaultdict(list)
for c,line in zip(incoming,raw):bykey[c['sourceKey']].append((c,line))
callerless={k for k,c in ctxs.items() if not c['callerReferenceCount'] and not c['indirectKeyReferenceCount'] and not c['relatedDynamicTranslationCallsiteCount']}
need(callerless=={'BookOnePlaceholder','BookTwoPlaceholder','ConflictsConsidered','SiblingTitlePlaceholder'},'callerless source-key inventory')
need(all(k in ctxs for k in selection['keys']),'caller context identity')
need(all(key in {(r['sourceKey'],r['locale']) for r in incoming} for key in PROPOSALS),'proposal coverage')

rows=[];prows=[];holds=[];counts=collections.Counter();proposal_counts=collections.Counter();notes=[]
for key in selection['keys']:
 ctx=ctxs[key]; refs=[r for r in ctx['callerRefs'] if r['isRuntimeReference']]
 if key in callerless:
  note='No pinned production literal or indirect caller, and no same-file dynamic translation callsite was found. All 12 locale cells are held hash-only; no target change is recommended without verified caller context.'
 else:
  note='Reviewed all locale values against the English source and the exact pinned direct/indirect production caller context. Placeholder, inline-code, markup, protected-literal, numeric, and locale-convention checks were considered for each cell.'
 if key in {'BookMatchingStrictness','BookMatchingStrictnessAggressive','BookMatchingStrictnessAggressiveHelpText','BookMatchingStrictnessBalanced','BookMatchingStrictnessBalancedHelpText','BookMatchingStrictnessStrict','BookMatchingStrictnessStrictHelpText'}:
  note='Reviewed as a Settings selector/help block and a Quickstart matching example; meaning is tied to strictness level, title evidence, and series-position behavior.'
 elif key in {'BookTitlePlaceholder','AccurateMetadataPlaceholder','KnownAccurateMetadataPlaceholder','ConflictingBookDataPlaceholder','ExtraUnrelatedTextPlaceholder','NoisyExtraTextPlaceholder','GenericSeriesTitleWithDifferentPositionPlaceholder','SameSeriesDifferentPositionPlaceholder','SiblingTitleBetterMatchPlaceholder'}:
  note='Reviewed as a translated mock filename/tag token in Quickstart’s allow/block examples; term choices must distinguish title, metadata, unrelated text, and conflicting series position.'
 elif key in {'ProcessedItems','NewItems','ChangedItems','ExcludedItems','FailureStage','PreviewComplete','PreviewFailed','PreviewNextSync','PreviewingSync','DryRunNoProviderCommit','ProviderStateCommitted','RequestFailed','NoImportListSyncHistory','SearchEligibleItems','SyncFailed','SyncRunning','SyncSucceeded'}:
  note='Reviewed in the Import List preview/history modal; status labels, count labels, preview actions, failure-stage values, and provider-state persistence use their exact UI contexts.'
 note_row={'sourceKey':key,'sourceKeySha256':keyhash(key),'sourceOrdinal':next(c['sourceOrdinal'] for c,_ in bykey[key]),'callerContextSha256':ctx['callerContextSha256'],'callerReferenceCount':ctx['callerReferenceCount'],'literalCallCount':ctx['literalCallCount'],'indirectKeyReferenceCount':ctx['indirectKeyReferenceCount'],'relatedDynamicTranslationCallsiteCount':ctx['relatedDynamicTranslationCallsiteCount'],'callerPaths':sorted({r['path'] for r in refs}),'callerLines':sorted({f"{r['path']}:{r['line']}" for r in refs}),'sourceReviewNote':note}
 notes.append(note_row)
 for c,line in bykey[key]:
  loc=c['locale']; ident=(key,loc); proposal=PROPOSALS.get(ident)
  if key in callerless:
   hold={'batch':'W300-349-Core','exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':c['sourceOrdinal'],'locale':loc,'sourceKeySha256':keyhash(key),'cellIdSha256':cellhash(key,loc),'sourceTextSha256':c['sourceTextSha256'],'currentTargetSha256':c['currentTargetSha256'],'candidateFreeRowSha256':sha(line),'callerContextSha256':ctx['callerContextSha256'],'callerReferenceCount':0,'relatedDynamicTranslationCallsiteCount':0,'primaryDisposition':'hold-callerless-context','holdReason':'No verified production caller/context at the exact pinned tree; do not propose wording for this cell.','sourceTextIncluded':False,'targetTextIncluded':False,'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True}
   rows.append(hold);holds.append(hold);counts['hold-callerless-context']+=1
   continue
  need(refs and ctx['callerReferenceCount']>0,'verified caller context '+key)
  source=c['sourceText']; current=c['currentTarget']; final=proposal['target'] if proposal else current
  need(counter(PH,source)==counter(PH,final),'placeholder mismatch '+key+'/'+loc)
  need(INLINE.findall(source)==INLINE.findall(final),'inline code mismatch '+key+'/'+loc)
  need(MARKUP.findall(source)==MARKUP.findall(final),'markup mismatch '+key+'/'+loc)
  need(all(x in final for x in protected(source)),'protected literal lost '+key+'/'+loc)
  source_nums=counter(NUM,source); final_nums=counter(NUM,final)
  # Existing localized numerals/number words are reviewed in context; no recommendations alter them.
  numeric_disposition='exact' if source_nums==final_nums else 'reviewed-localized-or-written-out'
  primary='revise-current' if proposal else 'accept-current'
  mainref=refs[0]
  rationale=proposal['rationale']+f" Exact production context: {mainref['path']}:{mainref['line']}." if proposal else f"The current {loc} wording conveys the source in its pinned production context ({mainref['path']}:{mainref['line']}); no material meaning, token, or locale-convention issue was identified."
  row={'batch':'W300-349-Core','exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':c['sourceOrdinal'],'sourceKey':key,'cellId':f'{key}::{loc}','locale':loc,'sourceText':source,'sourceTextSha256':c['sourceTextSha256'],'currentTarget':current,'currentTargetSha256':c['currentTargetSha256'],'finalReviewedTarget':final,'finalReviewedTargetSha256':stsha(final),'recommendedTarget':final if proposal else None,'recommendedTargetSha256':stsha(final) if proposal else None,'primaryDisposition':primary,'reviewConfidence':proposal['confidence'] if proposal else 'moderate','decisionRationale':rationale,'candidateFreeRowSha256':sha(line),'callerContextSha256':c['callerContextSha256'],'callerReferenceCount':ctx['callerReferenceCount'],'literalCallCount':ctx['literalCallCount'],'indirectKeyReferenceCount':ctx['indirectKeyReferenceCount'],'relatedDynamicTranslationCallsiteCount':ctx['relatedDynamicTranslationCallsiteCount'],'callerRefs':refs,'callerPaths':sorted({r['path'] for r in refs}),'sourcePlaceholders':dict(counter(PH,source)),'currentPlaceholders':dict(counter(PH,current)),'finalPlaceholders':dict(counter(PH,final)),'placeholderParity':True,'sourceInlineCode':INLINE.findall(source),'currentInlineCode':INLINE.findall(current),'finalInlineCode':INLINE.findall(final),'inlineCodeParity':True,'sourceMarkup':MARKUP.findall(source),'currentMarkup':MARKUP.findall(current),'finalMarkup':MARKUP.findall(final),'markupParity':True,'sourceNumericTokens':NUM.findall(source),'currentNumericTokens':NUM.findall(current),'finalNumericTokens':NUM.findall(final),'numericTokenDisposition':numeric_disposition,'protectedLiterals':protected(source),'protectedLiteralDisposition':'exact-preserved','nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'reviewerPartition':'primary-W300-349-Core-all-locales','reviewerMethod':'Independent primary semantic review of candidate-free inputs and exact pinned caller context only; no W300-349 blind or cross-review materials accessed.'}
  rows.append(row);counts[primary]+=1
  if proposal:
   proposal_row={'batch':row['batch'],'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':row['sourceOrdinal'],'sourceKey':key,'cellId':row['cellId'],'locale':loc,'sourceText':source,'sourceTextSha256':c['sourceTextSha256'],'currentTarget':current,'currentTargetSha256':c['currentTargetSha256'],'recommendedTarget':final,'recommendedTargetSha256':stsha(final),'decisionRationale':rationale,'reviewConfidence':proposal['confidence'],'candidateFreeRowSha256':sha(line),'callerContextSha256':c['callerContextSha256'],'callerPaths':row['callerPaths'],'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'placeholderParity':True,'inlineCodeParity':True,'markupParity':True,'numericTokenDisposition':numeric_disposition,'protectedLiteralDisposition':'exact-preserved'}
   prows.append(proposal_row);proposal_counts[loc]+=1

need(sum(counts.values())==600,'primary row count')
need(counts['hold-callerless-context']==48 and counts['accept-current']+counts['revise-current']==552,'dispositions')
need(len(prows)==sum(proposal_counts.values()) and len(prows)==len(PROPOSALS),'proposal count')
OUT.mkdir(parents=True,mode=0o700)
writejl(OUT/'primary-review-cells.jsonl',rows);writejl(OUT/'primary-review-proposals.jsonl',prows);writejl(OUT/'primary-review-holds.jsonl',holds)
writej(OUT/'primary-review-source-notes.json',{'batch':'W300-349-Core','exactHead':HEAD,'exactTree':TREE,'candidateFreeCellsSha256':sha((INPUT/'candidate-free-cells.jsonl').read_bytes()),'candidateFreeManifestSha256':sha((INPUT/'candidate-free-manifest.json').read_bytes()),'sourceSelectionSha256':sha((INPUT/'source-selection.json').read_bytes()),'callerlessKeys':sorted(callerless),'callerlessHoldCells':len(holds),'currentWindowBlindOrCrossOutputsAccessed':False,'priorWindowCrossReviewSemanticallyUsed':False,'sourceNotes':notes,'integrityMismatchDisposition':{'candidateFreeNumericMismatchCount':5,'review':'All five mismatches were checked in source and caller context: Book One/Two are written as localized numbers in Korean/German; Japanese “at least one” uses 1; Arabic “one item” uses the singular word. These are faithful localization choices, not dropped quantities. Callerless Book One/Two cells remain hash-only holds.'},'mainCallerDriftAttestationSha256':sha((INPUT/'live-main-caller-drift.json').read_bytes()),'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600})
summary={'result':'PASS','batch':'W300-349-Core','exactHead':HEAD,'exactTree':TREE,'cells':600,'sourceKeys':50,'locales':12,'counts':{'cells':600,'accept-current':counts['accept-current'],'revise-current':counts['revise-current'],'proposals':len(prows),'hold':counts['hold-callerless-context'],'callerBackedKeys':50-len(callerless),'callerBackedCells':552,'callerlessKeys':len(callerless),'callerlessHoldCells':len(holds),'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600},'proposalsByLocale':dict(sorted(proposal_counts.items())),'proposalCellIds':[p['cellId'] for p in prows],'candidateFreeCellsSha256':sha((INPUT/'candidate-free-cells.jsonl').read_bytes()),'candidateFreeManifestSha256':sha((INPUT/'candidate-free-manifest.json').read_bytes()),'sourceSelectionSha256':sha((INPUT/'source-selection.json').read_bytes()),'currentWindowBlindOrCrossOutputsAccessed':False,'priorWindowCrossReviewSemanticallyUsed':False,'repositoryModified':False,'testsBuildsSecurityScansCiWorkflowsRun':False,'primaryReviewSourceAndCallerInventoryUsed':True}
writej(OUT/'primary-review-summary.json',summary)
(OUT/'README-primary-review.md').write_text(f'''# ChaptarrNG PR #190 Core W300–W349 primary review\n\nPinned source: `{HEAD}` / tree `{TREE}`. The review covers 50 source keys × 12 locales = 600 cells. It used only the sealed candidate-free packet and direct caller context at this exact head.\n\nThe primary ledger contains {len(prows)} proposed corrections, {counts['accept-current']} accepted-current cells, and {len(holds)} hash-only callerless holds across four keys. No target changes are recommended for callerless keys without verified production context. Recommendations remain pending native-speaker review and have not been applied.\n\nPrior lineage through W250–W299 is hash-only: W0–W199 has 1,519 reattested rows including 312 preserved holds; W200–W249 has 600 rows including 12 preserved holds; W250–W299 has 600 final readbacks, 42 applied changes and 558 preserved-current cells. The separate Indonesian root adjudication is attested by its exact SHA-256 in the candidate-free packet.\n\nNo W300–W349 blind or cross-review outputs were accessed or used. The candidate-free packet records live main/base drift and caller-path overlap. No product catalog or PR state was modified; no tests, builds, security scans, CI jobs, or workflow changes were run.\n''',encoding='utf-8')
verify='''#!/usr/bin/env python3\nimport collections,hashlib,json,subprocess\nfrom pathlib import Path\nP=Path(__file__).resolve().parent; I=P.parent/"candidate-free/input"; HEAD="f0082d1b655c05b8d4019ede523dd695cd6d745a"; TREE="4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"\ndef sha(b):return hashlib.sha256(b).hexdigest()\ndef rj(p):return json.loads(p.read_text(encoding="utf-8"))\ndef rjl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]\ndef need(v,m):\n if not v:raise SystemExit("FAIL: "+m)\ndef sums(p):\n rec={}\n for line in p.read_text().splitlines():\n  h,n=line.split("  ",1);f=p.parent/n;need(f.is_file() and sha(f.read_bytes())==h,"checksum "+n);rec[n]=h\n need(set(rec)=={x.name for x in p.parent.iterdir() if x.is_file() and x.name!=p.name},"checksum coverage")\nneed((rj(I/"candidate-free-manifest.json")["head"],rj(I/"candidate-free-manifest.json")["tree"])==(HEAD,TREE),"candidate-free pin")\nsums(I/"SHA256SUMS.txt");sums(P/"primary-review-SHA256SUMS.txt")\nsubprocess.run(["python3",str(I/"verify_candidate_free.py")],check=True,stdout=subprocess.DEVNULL)\ninc=rjl(I/"candidate-free-cells.jsonl"); rows=rjl(P/"primary-review-cells.jsonl"); props=rjl(P/"primary-review-proposals.jsonl"); holds=rjl(P/"primary-review-holds.jsonl"); summary=rj(P/"primary-review-summary.json"); note=rj(P/"primary-review-source-notes.json")\nneed(len(inc)==len(rows)==600 and len(holds)==48,"cell/hold counts")\nim={(x["sourceOrdinal"],x["locale"]):x for x in inc}; rm={(x["sourceOrdinal"],x["locale"]):x for x in rows}; pm={(x["sourceOrdinal"],x["locale"]):x for x in props}\nneed(len(im)==len(rm)==600 and set(im)==set(rm),"cell identity coverage")\nneed(len(pm)==len(props) and len(pm)==summary["counts"]["proposals"] and set(pm).issubset(rm),"proposal identity/count")\ncounts=collections.Counter(x["primaryDisposition"] for x in rows)\nneed(counts["hold-callerless-context"]==48 and counts["accept-current"]+counts["revise-current"]==552,"disposition counts")\nneed(counts["revise-current"]==len(props),"proposal disposition count")\nfor ident,c in im.items():\n r=rm[ident]; h=ident in {(x["sourceOrdinal"],x["locale"]) for x in holds}\n need((r["exactHead"],r["exactTree"])==(HEAD,TREE) and r["batch"]=="W300-349-Core","row pin")\n need(r["sourceOrdinal"]==c["sourceOrdinal"] and r["locale"]==c["locale"],"cell identity")\n need(r["candidateFreeRowSha256"]==sha((I/"candidate-free-cells.jsonl").read_bytes().splitlines()[list(im).index(ident)]),"candidate-free row linkage")\n if h:\n  need(r["primaryDisposition"]=="hold-callerless-context" and r.get("targetTextIncluded") is False and r.get("sourceTextIncluded") is False,"hash-only hold")\n  need(not any(k in r for k in ("sourceText","currentTarget","finalReviewedTarget","recommendedTarget")),"hold text leakage")\n  need(r["currentTargetSha256"]==c["currentTargetSha256"] and r["sourceTextSha256"]==c["sourceTextSha256"],"hold hash linkage")\n else:\n  need(r["sourceKey"]==c["sourceKey"] and r["sourceText"]==c["sourceText"] and r["currentTarget"]==c["currentTarget"],"source/current linkage")\n  need(r["sourceTextSha256"]==c["sourceTextSha256"] and r["currentTargetSha256"]==c["currentTargetSha256"],"source/current hash linkage")\n  need(sha(r["finalReviewedTarget"].encode())==r["finalReviewedTargetSha256"],"final target hash")\n  if r["primaryDisposition"]=="accept-current":need(r["finalReviewedTarget"]==c["currentTarget"] and ident not in pm,"accepted-current")\n  else:\n   p=pm[ident];need(p["recommendedTarget"]==r["finalReviewedTarget"] and p["recommendedTargetSha256"]==r["finalReviewedTargetSha256"],"proposal linkage")\n   need(p["sourceTextSha256"]==c["sourceTextSha256"] and p["currentTargetSha256"]==c["currentTargetSha256"],"proposal source hashes")\n   need(r["callerReferenceCount"]>0 and bool(r["callerRefs"]),"proposed cell caller context")\n  need(r["nativeSpeakerApproval"] is False and r["nativeSpeakerReviewOutstanding"] is True,"speaker status")\nneed(summary["counts"]["accept-current"]==counts["accept-current"] and summary["counts"]["revise-current"]==counts["revise-current"],"summary counts")\nneed(summary["currentWindowBlindOrCrossOutputsAccessed"] is False and note["currentWindowBlindOrCrossOutputsAccessed"] is False,"current-window review independence")\nneed(note["priorWindowCrossReviewSemanticallyUsed"] is False,"prior-window cross use")\nneed(note["callerlessKeys"]==["BookOnePlaceholder","BookTwoPlaceholder","ConflictsConsidered","SiblingTitlePlaceholder"],"callerless key set")\nprint(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":600,"proposals":len(props),"acceptCurrent":counts["accept-current"],"callerlessHolds":counts["hold-callerless-context"],"callerBackedKeys":46,"nativeSpeakerApproval":0,"nativeSpeakerReviewOutstanding":600},sort_keys=True))\n'''
(OUT/'verify_primary_review.py').write_text(verify,encoding='utf-8')
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='primary-review-SHA256SUMS.txt')
(OUT/'primary-review-SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files),encoding='utf-8')
subprocess.run(['sha256sum','-c','primary-review-SHA256SUMS.txt'],cwd=OUT,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['python3',str(OUT/'verify_primary_review.py')],check=True)
print(json.dumps({'primaryReviewOutput':str(OUT),'files':len(files)+1,'summarySha256':sha((OUT/'primary-review-summary.json').read_bytes()),'checksumManifestSha256':sha((OUT/'primary-review-SHA256SUMS.txt').read_bytes()),'counts':summary['counts'],'proposalsByLocale':summary['proposalsByLocale'],'holds':len(holds),'proposalCellIds':[x['cellId'] for x in prows]},ensure_ascii=False,sort_keys=True,indent=2))
