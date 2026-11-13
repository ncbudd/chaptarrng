#!/usr/bin/env python3
import collections, hashlib, json
from pathlib import Path
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w350-399-20261104')
INPUT=TASK/'candidate-free'/'input'; OUT=TASK/'primary-review'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def wj(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def wjl(p,rows):p.write_bytes(b''.join(canon(r) for r in rows))

def p(key,loc,target,rationale,confidence='moderate'):
 proposals[(key,loc)]={'target':target,'rationale':rationale,'confidence':confidence}
proposals={}
# Clear wording/grammar defects in the exact pinned UI context.
p('BookMonitoring','de','Buchüberwachung','The setting controls book monitoring; Beobachtung means observation and is misleading here.')
p('BookMonitoring','ko','도서 모니터링','The label names the app’s monitoring setting; 감시 suggests surveillance.')
p('BookMonitoring','pt-BR','Monitoramento de livros','The source is a category label for monitoring books; plural wording fits the setting.')
p('BookNaming','es','Nomenclatura de libros','Nomenclatura is the natural section label for book file naming; Nombrado de libros is awkward.')
p('BookNaming','hi','पुस्तकों का नामकरण','The current mixes transliterated English with Hindi; this gives a direct Hindi section label.')
p('BookNaming','ja','書籍の命名','The current is a malformed transliteration; the fieldset is the book naming settings section.','high')
p('BookProgress','ja','書籍の進捗','The current transliterates the English phrase; this is a natural label for the book-progress filter.','high')
p('BookProgress','ko','도서 진행률','The current phrase 책 진행 is incomplete; 진행률 names the progress value used by the filter.','high')
p('BookTitle','hi','पुस्तक का शीर्षक','The current uses an awkward mixed phrase; the label is the sortable book title column.')
p('BooksProgress','de','Fortschritt der Bücher','The current compound order is unidiomatic for the sort label.')
p('BooksProgress','ko','도서 진행률','The current 책 진행 is incomplete for the book-progress sort label.','high')
p('BooksCount','ar','عدد الكتب: {count}','The plural count label uses singular كتاب; a count-first phrasing avoids incorrect Arabic number agreement.')
p('BooksCountMessage','ar','عدد الكتب: {count}','This key is used only when bookCount is greater than one; the current singular noun is incorrect for that branch.')
p('BookNotFound','hi','पुस्तक नहीं मिली','पुस्तक is feminine; the current masculine agreement is incorrect.','high')
p('BooksWithFiles','hi','फ़ाइलों वाली पुस्तकें','The postposition requires the oblique plural फ़ाइलों, not फ़ाइलें.')
p('Bookshelf','hi','किताबों की शेल्फ़','This label opens Goodreads-style shelves; पुस्तकालय means a library, which is a different destination.')
p('Bookshelf','fr','Étagère','The key labels a Goodreads shelf, and neighboring shelf inputs use étagère; Bibliothèque can be mistaken for the overall library.')
p('BookshelfInputManualAddPlaceholder','ar','يدويًا: أضف رفًا (مثل: read، currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','de','Manuell: Regal hinzufügen (z. B. read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','es','Manual: añadir estantería (p. ej., read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','fr','Manuel : ajouter une étagère (ex. : read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','hi','मैन्युअल: शेल्फ़ जोड़ें (जैसे: read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','ko','수동: 선반 추가 (예: read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','pt-BR','Manual: adicionar estante (ex.: read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','vi','Thủ công: thêm kệ (ví dụ: read, currently-reading)','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','zh-Hans','手动：添加书架（例如：read、currently-reading）','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputManualAddPlaceholder','zh-Hant','手動：新增書架（例如：read、currently-reading）','The examples are exact Goodreads shelf names; translating them would suggest shelf IDs the user cannot select.','high')
p('BookshelfInputEnterUserIdPrompt','zh-Hans','输入上方的 Goodreads 用户 ID 以获取书架。','The current has a space before Chinese punctuation and uses a less clear rendering of User ID.')
p('BookshelfInputEnterUserIdPrompt','zh-Hant','輸入上方的 Goodreads 使用者 ID 以取得書架。','The current has a space before Chinese punctuation and uses a less clear rendering of User ID.')
p('BookshelfInputFetchError','zh-Hans','无法从 Goodreads 获取书架。请检查用户 ID 和书架是否公开，也可以在下方手动添加书架。','The current has spaces before punctuation and commas; the revision restores normal Simplified Chinese punctuation.')
p('BookshelfInputFetchError','zh-Hant','無法從 Goodreads 取得書架。請檢查使用者 ID 及書架是否公開，或在下方手動新增書架。','The current has spaces before punctuation and commas; the revision restores normal Traditional Chinese punctuation.')
p('BookshelfInputNoShelvesForUser','zh-Hans','未返回 Goodreads 用户 {user} 的书架。您仍可在下方手动添加书架。','The current word order makes {user} appear after the bookshelf instead of identifying the Goodreads user.')
p('BooksInSeries','vi','Sách trong bộ sách','The caller is a heading for books belonging to a series; leaving Series in English is unnatural here.')
p('BooksInThisSeries','vi','Sách trong bộ sách này:','The search-result heading refers to this book series; bộ sách is a localized term.')
p('Born','vi','Ngày sinh','The caller data property is DateTime? Born; Nơi sinh means place of birth, not the date field.','high')
p('Branch','ko','브랜치','In update settings this means a Git branch; 브랜치 is the standard technical term, while 분기 can mean quarter.')
p('BranchUpdate','ko','{appName} 업데이트에 사용할 브랜치','This setting names the Git branch used for updates; 브랜치 is the standard technical term.')
p('BranchUpdateMechanism','ko','외부 업데이트 메커니즘에서 사용하는 브랜치','This setting names the Git branch used by an external updater; 브랜치 avoids the quarter/organizational meaning of 분기.')
p('BuiltInCustomFormatAppliesToHelpText','es','Los formatos personalizados integrados usan un tipo de medio fijo.','The current drops the article and reads as a fragment; this is a full, natural sentence.')
p('BuiltInCustomFormatAppliesToHelpText','id','Format kustom bawaan menggunakan jenis media tetap.','The current leaves Built-in Custom Formats in English despite the surrounding Indonesian sentence.')
p('BuiltInCustomFormatAppliesToHelpText','ko','내장 사용자 지정 형식은 고정된 미디어 유형을 사용합니다.','The current spacing 고정 된 is incorrect; 고정된 is the correct modifier.')
p('BuiltInCustomFormatAppliesToHelpText','pt-BR','Formatos personalizados integrados usam um tipo de mídia fixo.','The current adjective agrees with mídia instead of the masculine noun tipo; fix the agreement.')
p('BuiltInCustomFormatAppliesToHelpText','vi','Các định dạng tùy chỉnh tích hợp sẵn sử dụng một kiểu phương tiện cố định.','The current title-cases common nouns; this uses normal Vietnamese sentence capitalization and natural word order.')
p('BuiltInCustomFormatAppliesToHelpText','zh-Hans','内置自定义格式使用固定的媒体类型。','The current has an English period; use standard Chinese sentence punctuation and 内置.')
p('BuiltInCustomFormatAppliesToHelpText','zh-Hant','內建自訂格式使用固定的媒體類型。','The current has an extra space before punctuation; this gives standard Traditional Chinese punctuation.')
p('ByPrefix','vi','bởi','The About-page caller renders “version by package author”; qua means via/through, not by.')
# The proxy field is a comma-separated list of hosts/domains that should connect directly.
proxy_labels={
'ar':'قائمة استثناءات الوكيل','de':'Proxy-Ausnahmeliste','es':'Filtro de excepciones del proxy','fr':'Filtre d’exception du proxy','hi':'प्रॉक्सी अपवाद फ़िल्टर','id':'Filter pengecualian proxy','ja':'プロキシ除外フィルター','ko':'프록시 우회 필터','pt-BR':'Filtro de exceções do proxy','vi':'Bộ lọc ngoại lệ proxy','zh-Hans':'代理例外筛选器','zh-Hant':'代理例外篩選器'}
for loc,target in proxy_labels.items():
 p('BypassFilter',loc,target,'The adjacent help text says this field is a list of hosts/domains that connect directly; the current label can read as an instruction to bypass a generic filter.')
p('BypassIfAboveCustomFormatScore','de','Umgehen bei Überschreiten des benutzerdefinierten Formatwerts','The current clause is grammatically incomplete; this is a concise checkbox label for exceeding the configured custom-format score.')
p('BypassIfAboveCustomFormatScore','id','Lewati jika skor Format Kustom terlampaui','The current retains Bypass in English; this delay-profile checkbox can use the Indonesian verb and keeps the product term clear.')
p('BypassIfAboveCustomFormatScore','zh-Hant','高於自訂格式分數時略過','The current uses an awkward noun “旁路”; the checkbox describes skipping the delay when the score is higher.')
p('BypassIfHighestQuality','ar','تجاوز إذا كانت الجودة هي الأعلى','The current says high quality, while the source and help text require the highest enabled quality.')
p('BypassIfHighestQuality','de','Umgehen bei höchster Qualität','The current imperative fragment is rough; this names the condition clearly.')
p('BypassIfHighestQuality','pt-BR','Ignorar quando for a qualidade mais alta','The current comparative “mais alta” is ambiguous; this states the top enabled quality condition.')
p('BypassIfHighestQuality','zh-Hant','若為最高品質則略過','The current wording is awkward; this clearly expresses the highest-quality condition.')
p('BypassProxyForLocalAddresses','zh-Hant','對本機／LAN 位址略過代理','The current phrase 副路徑代理 is incorrect; this says to bypass the proxy for local/LAN addresses.','high')

holds={}
for loc in LOCALES:
 holds[('BookVisibilityToggleHelpText',loc)]='The English source says “Wanted”, but the pinned component renders the option as “Library”; do not select translated wording until the source label is reconciled.'

att=json.loads((INPUT/'PR-attestation.json').read_text())
cells=[json.loads(x) for x in (INPUT/'candidate-free-cells.jsonl').read_text().splitlines()]
ctxs={r['sourceKey']:r for r in map(json.loads,(INPUT/'caller-context.jsonl').read_text().splitlines())}
cfrows={ (r['sourceKey'],r['locale']):r for r in cells }
assert len(cells)==600 and len(proposals)==len(set(proposals))
review=[];prop_rows=[];hold_rows=[];counts=collections.Counter();bykey=collections.Counter();byloc=collections.Counter()
for cf in cells:
 key=cf['sourceKey'];loc=cf['locale'];ident=(key,loc);context=ctxs[key]
 base={'batch':'W350-399-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'liveMainSha':att['liveMainSha'],'liveMainTree':att['liveMainTree'],'sourceOrdinal':cf['sourceOrdinal'],'sourceKey':key,'cellId':f'{key}::{loc}','cellIdSha256':shat(f'{key}::{loc}'),'locale':loc,'sourceText':cf['sourceText'],'sourceTextSha256':cf['sourceTextSha256'],'currentTarget':cf['currentTarget'],'currentTargetSha256':cf['currentTargetSha256'],'candidateFreeRowSha256':sha(canon(cf)),'callerContextSha256':cf['callerContextSha256'],'callerReferenceCount':cf['callerReferenceCount'],'callerPaths':sorted({r['path'] for r in context['callerRefs'] if r['isRuntimeReference']}),'sourcePlaceholders':cf['sourcePlaceholders'],'currentPlaceholders':cf['currentPlaceholders'],'sourceInlineCode':cf['sourceInlineCode'],'currentInlineCode':cf['currentInlineCode'],'sourceMarkup':cf['sourceMarkup'],'currentMarkup':cf['currentMarkup'],'sourceNumericTokens':cf['sourceNumericTokens'],'currentNumericTokens':cf['currentNumericTokens'],'protectedLiterals':cf['protectedLiterals'],'integrityChecks':cf['integrityChecks'],'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'reviewerMethod':'Primary semantic review of candidate-free cells, exact caller context, and read-only adjacent UI/source labels needed for the stale-label and proxy-field context; no current-window blind/cross outputs accessed.'}
 if ident in holds:
  row={**base,'primaryDisposition':'hold-text-free','recommendedTarget':None,'recommendedTargetSha256':None,'finalReviewedTarget':None,'finalReviewedTargetSha256':None,'reviewConfidence':'high','decisionRationale':holds[ident]}
  hold_rows.append({'batch':row['batch'],'exactHead':row['exactHead'],'cellId':row['cellId'],'cellIdSha256':row['cellIdSha256'],'sourceOrdinal':row['sourceOrdinal'],'sourceKey':key,'locale':loc,'sourceTextSha256':row['sourceTextSha256'],'currentTargetSha256':row['currentTargetSha256'],'callerContextSha256':row['callerContextSha256'],'disposition':'hold-text-free','recommendedTarget':None,'recommendedTargetSha256':None,'reason':row['decisionRationale']})
  counts['hold-text-free']+=1
 elif ident in proposals:
  info=proposals[ident]; target=info['target']
  row={**base,'primaryDisposition':'revise-current','recommendedTarget':target,'recommendedTargetSha256':shat(target),'finalReviewedTarget':target,'finalReviewedTargetSha256':shat(target),'reviewConfidence':info['confidence'],'decisionRationale':info['rationale']}
  prop_rows.append({'batch':row['batch'],'exactHead':row['exactHead'],'cellId':row['cellId'],'cellIdSha256':row['cellIdSha256'],'sourceOrdinal':row['sourceOrdinal'],'sourceKey':key,'locale':loc,'sourceTextSha256':row['sourceTextSha256'],'currentTargetSha256':row['currentTargetSha256'],'callerContextSha256':row['callerContextSha256'],'recommendedTarget':target,'recommendedTargetSha256':shat(target),'reviewConfidence':info['confidence'],'decisionRationale':info['rationale']})
  counts['revise-current']+=1;bykey[key]+=1;byloc[loc]+=1
 else:
  row={**base,'primaryDisposition':'accept-current','recommendedTarget':None,'recommendedTargetSha256':None,'finalReviewedTarget':cf['currentTarget'],'finalReviewedTargetSha256':cf['currentTargetSha256'],'reviewConfidence':'moderate','decisionRationale':'The current wording conveys the pinned English source in its available caller context; no clear meaning, grammar, token, or locale-convention defect was identified.'}
  counts['accept-current']+=1
 review.append(row)
assert len(review)==600 and len(prop_rows)==len(proposals) and len(hold_rows)==12
assert not (set(proposals)&set(holds))
wjl(OUT/'primary-review-cells.jsonl',review)
wjl(OUT/'primary-review-proposals.jsonl',prop_rows)
wjl(OUT/'primary-review-holds.jsonl',hold_rows)
summary={'batch':'W350-399-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'liveMainSha':att['liveMainSha'],'liveMainTree':att['liveMainTree'],'candidateFreeCellsSha256':sha((INPUT/'candidate-free-cells.jsonl').read_bytes()),'candidateFreeManifestSha256':sha((INPUT/'candidate-free-manifest.json').read_bytes()),'candidateFreeSumsSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'cells':600,'sourceIds':50,'locales':12,'counts':{'accept-current':counts['accept-current'],'revise-current':counts['revise-current'],'hold-text-free':counts['hold-text-free'],'callerBackedKeys':sum(1 for r in ctxs.values() if r['callerReferenceCount']>0),'callerlessKeys':sum(1 for r in ctxs.values() if r['callerReferenceCount']==0),'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600},'proposalCountByLocale':dict(sorted(byloc.items())),'proposalCountBySourceKey':dict(sorted(bykey.items())),'heldCellIds':[r['cellId'] for r in hold_rows],'currentWindowBlindOrCrossOutputsAccessed':False,'nativeSpeakerApproval':False,'result':'PASS'}
wj(OUT/'primary-review-summary.json',summary)
source_notes=[]
for key in ctxs:
 source_notes.append({'sourceKey':key,'sourceOrdinal':next(r['sourceOrdinal'] for r in cells if r['sourceKey']==key),'sourceTextSha256':next(r['sourceTextSha256'] for r in cells if r['sourceKey']==key),'callerContextSha256':ctxs[key]['callerContextSha256'],'callerReferenceCount':ctxs[key]['callerReferenceCount'],'callerPaths':sorted({r['path'] for r in ctxs[key]['callerRefs'] if r['isRuntimeReference']}),'proposedCells':[f'{key}::{loc}' for k,loc in proposals if k==key],'heldCells':[f'{key}::{loc}' for k,loc in holds if k==key]})
wj(OUT/'primary-review-source-notes.json',{'batch':'W350-399-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'sourceNotes':source_notes,'heuristicIntegrityFlags':16,'integrityFlagReview':'The protected-literal regex flags ID/LAN in 16 cells; these are heuristics, not automatic holds. Each flagged source/current target was reviewed directly.','sourceContextHold':'BookVisibilityToggleHelpText is held in all locales because pinned UI option is Library while English source says Wanted.'})
exposure={'batch':'W350-399-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'candidateFreePacketSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'currentWindowBlindOrCrossOutputsAccessed':False,'priorWindowMaterialExposure':['Inspected W300 primary-review schema/summary solely to match evidence structure; did not use W300 translation recommendations for W350 judgments.'],'candidateFreeInputUsed':True,'adjacentContextReadOnly':['frontend/src/Author/Details/BookVisibilityToggle.js','frontend/src/Settings/General/ProxySettingsFields.js','src/NzbDrone.Core/Localization/Core/en.json keys Library, All, ProxyBypassFilterHelpText'],'currentWindowPrimaryReviewUses':{'candidateFreeCells':True,'callerContext':True,'exactSourceAndTargetHashes':True,'latestMainComparison':True},'nativeSpeakerReviewPerformed':False,'reviewerRole':'primary','result':'RECORDED'}
wj(OUT/'review-process-exposure.json',exposure)
(OUT/'README-primary-review.md').write_text('''# W350–W399 Core primary review\n\nThis review covers all 600 cells (50 English Core source keys × 12 locales) from the candidate-free packet pinned to PR head `dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0` / tree `be10d71209076f753ef295038a9f3c3646a918a3`, with latest main `0d711ce1a9828675e879b2ba97f36fc3b9544188`.\n\nThe primary review records **{accept} accept-current**, **{revise} proposed revisions**, and **12 text-free holds**. The holds are the `BookVisibilityToggleHelpText` cells: source says “Wanted” while the pinned UI button is “Library”, so no translation target was selected pending source/context reconciliation. The manual-shelf placeholder proposals preserve the exact Goodreads shelf names `read` and `currently-reading`.\n\nAll proposals are exact-hash and caller-context bound in `primary-review-cells.jsonl`; `primary-review-proposals.jsonl` contains only proposed text. The 16 protected-literal heuristic flags for `ID`/`LAN` were manually reviewed and are not automatic holds.\n\nThis is machine-assisted primary review, not native-speaker approval. The current-window blind and cross-review outputs were not accessed. Exposure and scope are recorded in `review-process-exposure.json`; see `primary-review-summary.json` for per-locale and per-key proposal counts.\n'''.format(accept=counts['accept-current'],revise=counts['revise-current']))
print(json.dumps(summary,ensure_ascii=False,indent=2))
