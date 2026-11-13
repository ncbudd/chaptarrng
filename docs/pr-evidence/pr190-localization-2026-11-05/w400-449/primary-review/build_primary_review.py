#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, re
from pathlib import Path
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w400-449-20261105')
INPUT=TASK/'candidate-free'/'input'; OUT=TASK/'primary-review'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def wj(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def wjl(p,rows):p.write_bytes(b''.join(canon(r) for r in rows))
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def p(key,loc,target,rationale,confidence='moderate'):
 proposals[(key,loc)]={'target':target,'rationale':rationale,'confidence':confidence}
proposals={}
# Corrections selected from the candidate-free source/target/context packet only.
p('CalendarWeekColumnHeaderHelpText','es','Se muestra encima de cada columna cuando la vista semanal está activa','The current wording is an awkward calque; this describes the helper text shown while the weekly calendar view is active.')
p('CalendarWeekColumnHeaderHelpText','fr','Affiché au-dessus de chaque colonne lorsque la vue Semaine est active','Adds the missing hyphen in au-dessus and expresses the active weekly view naturally.')
p('CalendarWeekColumnHeaderHelpText','hi','जब सप्ताह दृश्य सक्रिय हो, तब प्रत्येक स्तंभ के ऊपर दिखाया जाता है','Reorders the clause into natural Hindi while preserving the passive “shown above” meaning.')
p('CalendarWeekColumnHeaderHelpText','pt-BR','Exibido acima de cada coluna quando a visualização semanal está ativa','The current uses the imperative “Mostrar”; this is the passive helper-text wording in the source.')
p('CalibreContentServerText','es','Usar un servidor de contenido de Calibre (no Calibre Web) permite a Chaptarr añadir libros a tu biblioteca de Calibre e iniciar conversiones entre formatos.','Disparar is an awkward literal rendering of “trigger” in this sentence; iniciar expresses starting format conversions.')
p('CalibreContentServerText','hi','Calibre Content Server (Calibre Web नहीं) का उपयोग करने से Chaptarr आपके Calibre पुस्तकालय में पुस्तकें जोड़ सकता है और फ़ॉर्मैट के बीच रूपांतरण शुरू कर सकता है।','The current verb प्रेरित कर सकता है means “can inspire”; शुरू कर सकता है conveys initiating conversions.')
p('CalibreContentServerText','vi','Dùng máy chủ nội dung Calibre (không phải Calibre Web) cho phép Chaptarr thêm sách vào thư viện Calibre và kích hoạt chuyển đổi giữa các định dạng.','Máy phục vụ is not the normal Vietnamese term for a server; máy chủ keeps the established product meaning.')
p('CalibreHost','ar','مضيف Calibre','The current feminine form المضيفة is mismatched for the masculine host label.')
p('CalibrePush','ar','إرسال إلى Calibre','This is a button that sends metadata to Calibre; دفع Calibre is unclear in Arabic.')
p('CalibrePush','es','Enviar a Calibre','This button sends metadata to Calibre; Empujar Calibre is an unnatural literal translation.')
p('CalibrePush','hi','Calibre में भेजें','This action sends metadata to Calibre; transliterated पुश does not say where the metadata goes.')
p('CalibrePush','id','Kirim ke Calibre','This button sends metadata to Calibre; retaining Push in English is unnecessary here.')
p('CalibrePush','vi','Gửi tới Calibre','This is the destination of the metadata push; Đẩy Calibre omits the direction.')
p('CalibrePush','zh-Hans','推送到 Calibre','This action sends metadata to Calibre; the current noun phrase does not name the destination.')
p('CalibrePush','zh-Hant','推送至 Calibre','This action sends metadata to Calibre; the current noun phrase does not name the destination.')
p('CalibrePushDescriptionInterp','hi','{0} पुस्तकों के लिए Calibre में लिखे जाने वाले फ़ील्ड चुनें। जिन फ़ील्डों का चयन नहीं किया गया है, वे Calibre में अपरिवर्तित रहेंगी।','The current second sentence says untouched items remain untouched but loses the “not checked” condition; this restores it.')
p('CalibrePushDescriptionInterp','pt-BR','Escolha quais campos serão gravados no Calibre para {0} livro(s). Os campos não selecionados permanecerão inalterados no Calibre.','Reorders the count naturally and makes clear that unchecked fields remain unchanged.')
p('CalibrePushTipPreview','es','Consejo: Para previsualizar los campos de metadatos, selecciona «Cancelar», luego elige cualquier libro y usa el','The button label should match the localized Cancel action; the current leaves the English label in the Spanish sentence.')
p('CalibrePushTipPreview','hi','टिप: मेटाडेटा फ़ील्ड का पूर्वावलोकन करने के लिए “रद्द करें” चुनें, फिर कोई भी पुस्तक चुनें और इसका उपयोग करें:','Uses the catalog’s localized Cancel label and keeps the sentence open for the adjacent tag icon.')
p('CalibrePushTipPreview','zh-Hans','提示：要预览元数据字段，请选择“取消”，再选择任意一本书并使用','Uses standard Chinese punctuation and the same localized Cancel label shown by the control.')
p('CalibrePushTipPreview','zh-Hant','提示：若要預覽中繼資料欄位，請選擇「取消」，再選擇任一本書並使用','Removes the stray spaces inside Chinese punctuation and matches the localized Cancel label.')
p('CalibreSettings','de','Calibre-Einstellungen','German compounds this setting label with a hyphen; the current open compound is not idiomatic.')
p('CalibreSettings','hi','Calibre सेटिंग्स','The section groups several settings, so the plural form is appropriate.')
p('CancelAllQueuedAndRunningTasks','hi','क्या आप कतार में मौजूद और चल रहे सभी कार्यों को रद्द करना चाहते हैं?','Replaces the English queued with a natural Hindi description of tasks waiting in the queue.')
p('CancelAllQueuedAndRunningTasks','ja','キューに入っているすべてのタスクと実行中のタスクをキャンセルしますか？','Uses natural Japanese for queued tasks and fullwidth question punctuation.')
p('CancelAllQueuedAndRunningTasks','zh-Hans','确定要取消所有排队和正在运行的任务吗？','Uses a complete Chinese confirmation question and standard punctuation.')
p('CancelAllQueuedAndRunningTasks','zh-Hant','確定要取消所有排隊及執行中的工作嗎？','Uses standard Traditional Chinese confirmation wording and punctuation.')
p('CancelRunningTask','es','Cancelar la tarea en ejecución','The current “tarea de ejecución” is an awkward calque; this is the natural action label.')
p('CancelRunningTask','hi','चल रहे कार्य को रद्द करें','The current omits the source’s running state; this retains it in the action label.')
p('CancelPendingTask','es','¿Seguro que quieres cancelar esta tarea pendiente?','Adds the opening Spanish question mark, which is required for the complete question.')
p('CancelPendingTask','fr','Êtes-vous sûr de vouloir annuler cette tâche en attente ?','Corrects sûr and keeps the standard French spacing before the question mark.')
p('CancelPendingTask','ko','이 대기 중인 작업을 취소하시겠습니까?','Corrects spacing in 보류중인/취소 하시겠습니까 and uses the usual pending-task wording.')
p('CancelPendingTask','zh-Hant','您確定要取消此待處理工作嗎？','Replaces the to-do sense of 待辦 with the pending-state wording and removes the space before punctuation.')
p('CancelledCountCommands','ar','تم إلغاء {count} من الأوامر','The count-first construction avoids Arabic singular/plural agreement ambiguity.')
p('CancelledCountCommands','de','{count} Befehle abgebrochen','The current Storniert is suited to orders, while these are commands that were cancelled.')
p('CancelledCountCommands','hi','{count} आदेश रद्द किए गए','The current is an unfinished infinitive phrase; this is a complete status message.')
p('CancelledCountCommands','ja','{count} 個のコマンドをキャンセルしました','The current noun sequence is unnatural; this is a complete Japanese notification.')
p('CancelledCountCommands','ko','{count}개 명령이 취소되었습니다','Adds the Korean count marker and a complete passive status construction.')
p('CancelledCountCommands','zh-Hans','已取消 {count} 条命令','Adds the normal classifier for Chinese commands.')
p('CancelledCountCommands','zh-Hant','已取消 {count} 個命令','Adds the normal classifier for Traditional Chinese commands.')
p('Cancelling','ar','جارٍ الإلغاء','This is an in-progress queue state, not the noun “cancellation”.')
p('Cancelling','de','Wird abgebrochen','This queue state describes an operation currently being cancelled.')
p('Cancelling','es','Cancelando','The current noun Cancelación does not show the action is still in progress.')
p('Cancelling','fr','Annulation en cours','The current noun Annulation does not show the action is still in progress.')
p('Cancelling','hi','रद्द किया जा रहा है','This is an in-progress queue state, not an infinitive action.')
p('Cancelling','id','Sedang membatalkan','Adds the ongoing aspect required by this queue status.')
p('Cancelling','ja','キャンセル中','The current simply says “cancel”; this indicates cancellation is in progress.')
p('Cancelling','zh-Hans','正在取消','The current simply says “cancel”; this indicates cancellation is in progress.')
p('Cancelling','zh-Hant','正在取消','The current simply says “cancel”; this indicates cancellation is in progress.')
p('CanonicalAuthorFolderPartialEditionSelectionWarning','es','Solo se han seleccionado algunos archivos de una edición. Si continúas, esa edición quedará repartida entre las carpetas de los autores.','Fixes the awkward tense in the continuation warning while retaining the split-across-folders consequence.')
p('CanonicalAuthorFolderPartialEditionSelectionWarning','hi','किसी संस्करण की केवल कुछ फ़ाइलें चुनी गई हैं। जारी रखने पर वह संस्करण लेखकों के अलग-अलग फ़ोल्डरों में बँट जाएगा।','Restores the “only some files from an edition” meaning and uses a natural consequence clause.')
p('CanonicalAuthorFolderPartialEditionSelectionWarning','ja','あるエディションの一部のファイルのみが選択されています。続行すると、そのエディションが複数の作者フォルダーに分かれて保存されます。','The current says only the edition’s files are selected; this correctly says only some files are selected and explains the split.')
p('CanonicalAuthorFolderPartialEditionSelectionWarning','zh-Hans','仅选中了某个版本中的部分文件。继续后，该版本将分散到多个作者文件夹中。','Corrects the current “some files from a version” word order and removes spacing artifacts.')
p('CanonicalAuthorFolderPartialEditionSelectionWarning','zh-Hant','僅選取了某個版本的部分檔案。繼續後，該版本將分散到多個作者資料夾中。','Clarifies the partial selection and removes the spacing artifacts around Chinese punctuation.')
p('CannotAddFormatMissingProviderIds','fr',"Impossible d'ajouter {format} : IDs de fournisseur manquants",'Keeps the protected provider acronym and states clearly why the format cannot be added.')
p('CannotAddFormatMissingProviderIds','hi','प्रदाता IDs उपलब्ध न होने के कारण {format} नहीं जोड़ा जा सकता','The current says “not found” rather than “cannot add”; this states the missing provider IDs as the cause.')
p('CannotAddFormatMissingProviderIds','zh-Hans','缺少提供方 IDs，无法添加 {format}','The current 身份 means identity rather than provider IDs; this keeps the acronym and the source meaning.')
p('CannotAddFormatMissingProviderIds','zh-Hant','缺少提供者 IDs，無法新增 {format}','The current wording turns provider IDs into codes; this keeps the source acronym and meaning.')
p('FormatAddRequiresCatalogIdsHelpText','fr','Ce livre et son auteur ont besoin d’IDs de catalogue. Utilisez « Actualiser » sur ce livre et sur la page de l’auteur, puis revenez ici.','Uses the French Refresh label and lowercase auteur while retaining the source’s catalog ID acronym.')
p('Categories','vi','Danh mục','In the settings-backup picker this labels selectable categories; Loại reads as type rather than category.')
p('CertificateValidationHelpText','de','Ändern Sie, wie streng HTTPS-Zertifikate überprüft werden. Ändern Sie diese Einstellung nur, wenn Sie die Risiken verstehen.','Zertifikatsprüfung is the right term here; Zertifizierung refers to certification rather than validating HTTPS certificates.')
p('CertificateValidationHelpText','es','Cambia el nivel de exigencia de la validación del certificado HTTPS. No cambies esta opción si no comprendes los riesgos.','Corrects certificación, which means certification, to certificado validation as in the source.')
p('CertificateValidationHelpText','fr','Modifiez le niveau d’exigence de la validation des certificats HTTPS. Ne modifiez pas cette option sans comprendre les risques.','Corrects certification to certificate validation and keeps the warning direct.')
p('CertificateValidationHelpText','hi','HTTPS प्रमाणपत्र सत्यापन की सख्ती बदलें। जोखिमों को समझे बिना इसे न बदलें।','प्रमाणन means certification; प्रमाणपत्र is the certificate whose validation strictness the setting changes.')
p('CertificateValidationHelpText','pt-BR','Altere o rigor da validação do certificado HTTPS. Não altere esta opção sem compreender os riscos.','Corrects certificação to certificado and makes the setting warning read naturally.')
p('CertificateValidationHelpText','zh-Hant','變更 HTTPS 憑證驗證的嚴格程度。不了解風險時請勿變更。','Restores the missing certificate-validation concept and removes the punctuation artifacts.')
p('ChaptarrCalendarFeed','vi','Nguồn cấp lịch Chaptarr','Nguồn cấp lịch is the standard Vietnamese term for a calendar feed; Bộ nạp lịch means a loader.')
p('ChaptarrSupportsAnyIndexerThatUsesTheNewznabStandardAsWellAsOtherIndexersListedBelow','zh-Hans','Chaptarr 支持任何使用 Newznab 标准的索引器，以及下方列出的其他索引器。','Uses standard Chinese punctuation and spacing around the protected product/standard names.')
p('ChaptarrSupportsAnyIndexerThatUsesTheNewznabStandardAsWellAsOtherIndexersListedBelow','zh-Hant','Chaptarr 支援任何使用 Newznab 標準的索引器，以及下方列出的其他索引器。','Uses standard Traditional Chinese punctuation and spacing around the protected product/standard names.')
p('ChaptarrSupportsMultipleListsForImportingBooksAndAuthorsIntoTheDatabase','fr',"Chaptarr prend en charge plusieurs listes pour importer des livres et des auteurs dans la base de données.",'Book and author are generic nouns here and should not be capitalized.')
p('ChaptarrSupportsMultipleListsForImportingBooksAndAuthorsIntoTheDatabase','ko','Chaptarr는 책과 저자를 데이터베이스로 가져오기 위한 여러 목록을 지원합니다.','Corrects the spacing in 가져오기 위한.')
p('ChaptarrSupportsMultipleListsForImportingBooksAndAuthorsIntoTheDatabase','zh-Hant','Chaptarr 支援多份清單，可將書籍與作者匯入資料庫。','Removes the stray space before punctuation and gives the sentence a natural clause structure.')
p('ChaptarrTags','ar','وسوم Chaptarr','وسوم is the usual Arabic term for tags; العلامات is ambiguous and the current order is awkward.')
p('EditionCatalog','hi','संस्करण और कथावाचन','This section lists editions and narrated versions; कथावाचन is a Hindi noun for narration rather than a transliteration.')
p('EditionCatalog','vi','Các ấn bản và bản kể','The section contains editions and narrated versions; bản kể names narrations rather than the people who narrate them.')

att=json.loads((INPUT/'PR-attestation.json').read_text())
cand=[json.loads(x) for x in (INPUT/'candidate-free-cells.jsonl').read_text().splitlines()]
contexts={r['sourceKey']:r for r in (json.loads(x) for x in (INPUT/'caller-context.jsonl').read_text().splitlines())}
assert len(cand)==600 and len(proposals)==len(set(proposals))
# A source without any literal translate/GetLocalizedString caller remains text-free and hash-only.
hash_only_keys={k for k,c in contexts.items() if c['literalCallCount']==0}
assert hash_only_keys=={'CatalogNumber'}
review=[]; proposal_rows=[]; hold_rows=[]; counts=collections.Counter(); byloc=collections.Counter(); bykey=collections.Counter()
for cf in cand:
 key=cf['sourceKey'];loc=cf['locale']; ident=(key,loc); ctx=contexts[key]
 cellid=f'{key}::{loc}'
 common={'batch':'W400-449-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'liveMainSha':att['liveMainSha'],'liveMainTree':att['liveMainTree'],'sourceOrdinal':cf['sourceOrdinal'],'sourceKey':key,'locale':loc,'cellId':cellid,'cellIdSha256':shat(cellid),'candidateFreeRowSha256':sha(canon(cf)),'sourceTextSha256':cf['sourceTextSha256'],'currentTargetSha256':cf['currentTargetSha256'],'callerContextSha256':cf['callerContextSha256'],'callerReferenceCount':cf['callerReferenceCount'],'literalCallCount':cf['literalCallCount'],'indirectKeyReferenceCount':cf['indirectKeyReferenceCount'],'sourceFileSha256':cf['sourceFileSha256'],'targetFileSha256':cf['targetFileSha256'],'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True}
 if key in hash_only_keys:
  assert ident not in proposals
  rationale='No exact literal translation caller is pinned; the matching occurrences are model/property identifiers. Keep the current cell unquoted and hash-only until an exact UI caller is identified.'
  row={**common,'primaryDisposition':'hold-hash-only','recommendedTarget':None,'recommendedTargetSha256':None,'finalReviewedTarget':None,'finalReviewedTargetSha256':None,'reviewConfidence':'high','decisionRationale':rationale,'sourceTextIncluded':False,'currentTargetIncluded':False}
  hold_rows.append({**common,'disposition':'hold-hash-only','recommendedTarget':None,'recommendedTargetSha256':None,'reason':rationale,'sourceTextIncluded':False,'currentTargetIncluded':False})
  counts['hold-hash-only']+=1
 elif ident in proposals:
  item=proposals[ident]; target=item['target']
  row={**common,'sourceText':cf['sourceText'],'currentTarget':cf['currentTarget'],'primaryDisposition':'revise-current','recommendedTarget':target,'recommendedTargetSha256':shat(target),'finalReviewedTarget':target,'finalReviewedTargetSha256':shat(target),'reviewConfidence':item['confidence'],'decisionRationale':item['rationale'],'sourceTextIncluded':True,'currentTargetIncluded':True}
  proposal_rows.append({**common,'recommendedTarget':target,'recommendedTargetSha256':shat(target),'reviewConfidence':item['confidence'],'decisionRationale':item['rationale']})
  counts['revise-current']+=1;byloc[loc]+=1;bykey[key]+=1
 else:
  row={**common,'sourceText':cf['sourceText'],'currentTarget':cf['currentTarget'],'primaryDisposition':'accept-current','recommendedTarget':None,'recommendedTargetSha256':None,'finalReviewedTarget':cf['currentTarget'],'finalReviewedTargetSha256':cf['currentTargetSha256'],'reviewConfidence':'moderate','decisionRationale':'The current wording conveys the pinned English source in its caller context; no clear semantic, grammar, placeholder, markup, numeric, or locale-convention defect was identified.','sourceTextIncluded':True,'currentTargetIncluded':True}
  counts['accept-current']+=1
 review.append(row)
assert len(review)==600 and len(proposal_rows)==len(proposals) and len(hold_rows)==12
assert not (set(proposals)&{(k,l) for k in hash_only_keys for l in LOCALES})
# Validate every selected target before sealing.
for row in review:
 if row['primaryDisposition']=='revise-current': target=row['recommendedTarget']; source=row['sourceText']
 elif row['primaryDisposition']=='accept-current': target=row['currentTarget']; source=row['sourceText']
 else: continue
 assert collections.Counter(PH.findall(source))==collections.Counter(PH.findall(target)),row['cellId']+' placeholders'
 assert INLINE.findall(source)==INLINE.findall(target),row['cellId']+' inline code'
 assert MARKUP.findall(source)==MARKUP.findall(target),row['cellId']+' markup'
 assert collections.Counter(NUM.findall(source))==collections.Counter(NUM.findall(target)),row['cellId']+' numeric tokens'
 assert all(x in target for x in protected(source)),row['cellId']+' protected literals'
wjl(OUT/'primary-review-cells.jsonl',review)
wjl(OUT/'primary-review-proposals.jsonl',proposal_rows)
wjl(OUT/'primary-review-holds.jsonl',hold_rows)
summary={'batch':'W400-449-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'liveMainSha':att['liveMainSha'],'liveMainTree':att['liveMainTree'],'candidateFreeCellsSha256':sha((INPUT/'candidate-free-cells.jsonl').read_bytes()),'candidateFreeManifestSha256':sha((INPUT/'candidate-free-manifest.json').read_bytes()),'candidateFreeSumsSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'cells':600,'sourceIds':50,'locales':12,'counts':{'accept-current':counts['accept-current'],'revise-current':counts['revise-current'],'hold-hash-only':counts['hold-hash-only'],'keysWithExactLiteralCallers':sum(1 for r in contexts.values() if r['literalCallCount']>0),'keysWithoutExactLiteralCallers':len(hash_only_keys),'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600},'proposalCountByLocale':dict(sorted(byloc.items())),'proposalCountBySourceKey':dict(sorted(bykey.items())),'heldCellIds':[r['cellId'] for r in hold_rows],'currentWindowBlindOrCrossOutputsAccessed':False,'applicationPerformed':False,'nativeSpeakerApproval':False,'result':'PASS'}
wj(OUT/'primary-review-summary.json',summary)
source_notes=[]
for key in contexts:
 cells_for_key=[x for x in cand if x['sourceKey']==key]
 c=contexts[key]
 source_notes.append({'sourceKey':key,'sourceOrdinal':cells_for_key[0]['sourceOrdinal'],'sourceTextSha256':cells_for_key[0]['sourceTextSha256'],'callerContextSha256':c['callerContextSha256'],'callerReferenceCount':c['callerReferenceCount'],'literalCallCount':c['literalCallCount'],'indirectKeyReferenceCount':c['indirectKeyReferenceCount'],'callerPaths':sorted({x['path'] for x in c['callerRefs'] if x['isRuntimeReference']}),'proposedCells':[f'{key}::{loc}' for k,loc in proposals if k==key],'heldCells':[f'{key}::{loc}' for k,loc in proposals if k==key] if False else ([f'{key}::{loc}' for loc in LOCALES] if key in hash_only_keys else [])})
wj(OUT/'primary-review-source-notes.json',{'batch':'W400-449-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'sourceNotes':source_notes,'hashOnlyHoldReason':'No exact literal translate/GetLocalizedString caller is pinned for CatalogNumber; model/property identifier occurrences are insufficient to select a UI translation.','protectedLiteralPlaceholderMarkupNumericChecks':'Every selected target was checked against the candidate-free source; all checks pass.'})
exposure={'batch':'W400-449-Core','exactHead':att['headSha'],'exactTree':att['headTree'],'candidateFreePacketSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'candidateFreeInputUsed':True,'candidateFreeCellsUsed':True,'callerContextUsed':True,'exactSourceTargetCallerHashesBound':True,'currentWindowBlindOrCrossOutputsAccessed':False,'applicationPerformed':False,'otherWindowMaterialExposure':['Read W350 candidate-free source selection, application readback, its hold dispositions/hashes, and parts of its primary summary/ledger while checking the sequential pipeline. W350 suggestions were not used for any W400 target judgment; no W400 blind/cross packet was accessed.'],'currentWindowPrimaryReviewUses':{'candidateFreeCells':True,'callerContext':True,'sourceAndTargetHashes':True,'latestMainDrift':True,'hashOnlyCallerlessHold':True},'nativeSpeakerReviewPerformed':False,'reviewerRole':'primary','result':'RECORDED'}
wj(OUT/'review-process-exposure.json',exposure)
(OUT/'README-primary-review.md').write_text(f'''# W400–W449 Core primary review\n\nThis primary review covers all 600 cells (50 English Core keys × 12 locales) from the candidate-free packet pinned to PR head `{att['headSha']}` / tree `{att['headTree']}` and live `main` `{att['liveMainSha']}`.\n\nDispositions: **{counts['accept-current']} accept current**, **{counts['revise-current']} proposed revisions**, and **{counts['hold-hash-only']} hash-only holds**. The holds cover all locales for `CatalogNumber`: the exact source has no literal translation caller, and the pinned references are data/property identifiers. The review ledger records only source, target, caller, and candidate-free row hashes for those cells; it contains no source or target text for them.\n\nEach accept or revision is bound to the candidate-free source/target file hashes and per-key caller-context hash. Every selected target preserves source placeholders, inline code, markup, numeric tokens, and protected literals. The proposal ledger contains only the reviewed revisions; see `primary-review-summary.json` for per-locale and per-key counts.\n\nThis is a machine-assisted primary review, not native-speaker approval. No current-window blind/cross output was accessed, and no application was performed. The exposure record discloses the prior-window artifacts read for sequential lineage and hash reattestation.\n''')
print(json.dumps(summary,ensure_ascii=False,indent=2))
