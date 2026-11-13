import collections, hashlib, json, re
from pathlib import Path
OUT=Path('.')
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e'
TREE='d073e1373021bf715db37461a12654f7e993cdbf'
HEADNAME='codex/chaptarrng-localization-complete-20261031'
LOCALES=['ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
sha=lambda x: hashlib.sha256(x.encode('utf-8')).hexdigest()
inputs=[json.loads(x) for x in open(OUT/'input-cells.jsonl',encoding='utf8')]
sources={json.loads(x)['sourceOrdinal']:json.loads(x) for x in open(OUT/'source-slice.jsonl',encoding='utf8')}
callers={json.loads(x)['sourceOrdinal']:json.loads(x) for x in open(OUT/'caller-context.jsonl',encoding='utf8')}
manifest=json.load(open(OUT/'input-manifest.json',encoding='utf8'))
pins=json.load(open(OUT/'catalog-pins.json',encoding='utf8'))
assert manifest['head']==HEAD and manifest['tree']==TREE
# Mapping: (source ordinal, locale): (disposition, proposed target, rationale, confidence)
C={}
def cand(n,loc,disp,target,why,confidence='moderate'):
 assert disp in {'correction','refinement'}
 C[(n,loc)]=(disp,target,why,confidence)
# Active recovery state, grammatical target and format names.
for loc,target,why in [
 ('pt-BR','Recuperando a conversão interrompida de M4B.','The current noun stack does not read naturally as an active queue status; state the ongoing recovery of the interrupted M4B conversion.'),
 ('vi','Đang khôi phục quá trình chuyển đổi M4B bị gián đoạn.','The current noun stack does not clearly express the active recovery state; use a complete Vietnamese progress phrase.'),
 ('zh-Hans','正在恢复中断的 M4B 转换。','Add the modifier 的 and progressive aspect so the status clearly means recovery of an interrupted conversion.'),
 ('zh-Hant','正在恢復中斷的 M4B 轉換。','Add the modifier 的 and progressive aspect so the status clearly means recovery of an interrupted conversion.')]: cand(1153,loc,'correction',target,why)
# Correct FFmpeg dependency wording and availability terms; preserve exact tool names.
for loc,target,why,disp in [
 ('ja','FFmpeg を利用できません（m4b-tool に必要です）。','The current wording is an awkward literal passive; state that FFmpeg is unavailable and required by m4b-tool.','correction'),
 ('ko','FFmpeg를 사용할 수 없습니다(m4b-tool에 필요합니다).','The current parenthetical is an incomplete passive phrase; express the dependency as required by m4b-tool.','correction'),
 ('pt-BR','FFmpeg não está disponível (necessário para o m4b-tool).','Add sentence punctuation and use the natural dependency preposition while retaining both exact tool names.','refinement'),
 ('vi','FFmpeg không khả dụng (m4b-tool cần công cụ này).','Use the more idiomatic availability wording and state the dependency directly.','refinement'),
 ('zh-Hans','FFmpeg 不可用（m4b-tool 需要此工具）。','不提供 means “not provided”; the source reports that FFmpeg is unavailable.','correction'),
 ('zh-Hant','FFmpeg 無法使用（m4b-tool 需要此工具）。','不提供 means “not provided”; the source reports that FFmpeg is unavailable.','correction')]: cand(1156,loc,disp,target,why)
# The caller concatenates alternateClients with a separate protocol label and has no trailing space.
for loc,target,why in [
 ('ja','有効な {value0} ダウンロードクライアントが設定されていません。{value1} {value2} に対応するダウンロードクライアントを追加して有効にし、再試行してください。','The exact caller builds {value1} with string.Join and adds no trailing space; the current template joins it directly to {value2}, so the displayed values run together.'),
 ('ko','활성화된 {value0} 다운로드 클라이언트가 설정되어 있지 않습니다. {value1} {value2}를 지원하는 다운로드 클라이언트를 추가하고 활성화한 다음 다시 시도하세요.','The exact caller builds {value1} with string.Join and adds no trailing space; the current template joins it directly to {value2}, so the displayed values run together.')]: cand(1170,loc,'correction',target,why,'high')
# User-supplied file path and at-least-one identifier clarity.
for loc,target,why,disp in [
 ('ja','入力ファイルが存在しません: {value0}','The current Japanese predicate is unnatural; use the grammatical “input file does not exist” form.','correction'),
 ('pt-BR','O arquivo de entrada não existe: {value0}','Add the article required for a natural Portuguese error sentence.','correction'),
 ('vi','Tệp đầu vào không tồn tại: {value0}','Use the standard “input file” expression rather than wording that can mean an imported file.','correction'),
 ('ja','インタラクティブ検索には bookId、authorId、seriesId のいずれかが必要です。','The current spacing around raw identifiers is inconsistent; state the at-least-one requirement cleanly.','refinement'),
 ('ko','대화형 검색에는 bookId, authorId 또는 seriesId가 필요합니다.','The current expression for “interactive search” is an awkward calque; use the standard concise form and keep identifiers intact.','correction'),
 ('vi','Tìm kiếm tương tác cần có bookId, authorId hoặc seriesId.','The current word order is unnatural; use a direct requirement while preserving all three identifiers.','correction'),
 ('zh-Hans','互动搜索需要 bookId、authorId 或 seriesId。','Remove stray spaces around the unchanged code identifiers for a consistent Chinese sentence.','refinement'),
 ('zh-Hant','互動搜尋需要 bookId、authorId 或 seriesId。','Remove stray spaces around the unchanged code identifiers for a consistent Chinese sentence.','refinement')]:
 n=1171 if loc in {'ja','pt-BR','vi'} and target.startswith('入力') or target.startswith('O arquivo') or target.startswith('Tệp đầu vào') else 1159
 cand(n,loc,disp,target,why)
# Caller returns an empty result from GetBooks over ParsedBookInfo; preserve the source's parse operation.
for loc,target in [
 ('ja','リリース内の書籍を解析できませんでした。'),
 ('ko','릴리스에 포함된 도서를 파싱할 수 없습니다.'),
 ('pt-BR','Não foi possível analisar os livros do lançamento.'),
 ('vi','Không thể phân tích sách trong bản phát hành.'),
 ('zh-Hans','无法解析该发布中的书籍。'),
 ('zh-Hant','無法解析該發布中的書籍。')]:
 cand(1163,loc,'correction',target,'The exact caller passes ParsedBookInfo to GetBooks and returns this message when no book records result. The current translation shifts “parse” to identify or recognize; retain the source’s parse meaning.','moderate')
# FFprobe unavailable/required meaning.
for loc,target,disp,why in [
 ('zh-Hans','FFprobe 不可用（需要用它验证转换后的有声书）。','correction','不提供 means “not provided”; the source says FFprobe is unavailable and required for validation.'),
 ('zh-Hant','FFprobe 無法使用（驗證轉換後的有聲書需要此工具）。','refinement','Reorder the parenthetical so it clearly says FFprobe is required to validate converted audiobooks.')]: cand(1164,loc,disp,target,why)
# Completed conversion failures: correct word order and provide complete status phrases.
for loc,target in [
 ('ja','M4B の変換に失敗しました。'),('ko','M4B 변환에 실패했습니다.'),
 ('pt-BR','A conversão de M4B falhou.'),('vi','Quá trình chuyển đổi M4B đã thất bại.')]:
 cand(1165,loc,'correction',target,'The current translation has ungrammatical noun/verb order; state that the M4B conversion failed.','high')
# Ongoing percentage status.
for loc,target,why in [
 ('ja','M4B に変換中 - {value0}%','The source is an ongoing progress state; the current wording can read as an instruction.'),
 ('ko','M4B로 변환 중 - {value0}%','The source is an ongoing progress state; add the progressive marker to the current nominal label.'),
 ('vi','Đang chuyển đổi sang M4B - {value0}%','The current wording is a noun phrase; make the conversion clearly ongoing.'),
 ('zh-Hans','正在转换为 M4B - {value0}%','Make the progress aspect explicit for this ongoing status.'),
 ('zh-Hant','正在轉換為 M4B - {value0}%','Make the progress aspect explicit for this ongoing status.')]: cand(1166,loc,'refinement',target,why)
for loc,target,why in [
 ('pt-BR','O M4B convertido está pronto para ser importado.','The current word order treats “converted” as a standalone subject; identify the converted M4B and state that it is ready for import.'),
 ('vi','M4B đã chuyển đổi đã sẵn sàng để nhập.','The current phrase has an incomplete word order; make the converted M4B the item ready for import.')]: cand(1167,loc,'correction',target,why)
# Retained artifact and progress meaning.
cand(1168,'ja','correction','保存済みの M4B を使用しています。','The current phrase means “use saved M4B” like an instruction; express the active status of using the retained file.')
cand(1168,'ko','refinement','보관된 M4B를 사용 중입니다.','Add the status particle and spacing for a natural message that the retained M4B is currently being used.')
cand(1168,'zh-Hans','refinement','正在使用保留的 M4B。','Add 的 and progressive aspect to make the retained file the natural object of the status.')
cand(1168,'zh-Hant','refinement','正在使用保留的 M4B。','Add 的 and progressive aspect to make the retained file the natural object of the status.')
cand(1169,'vi','correction','Ứng dụng tải xuống Direct nội bộ không khả dụng.','The current translation leaves “download client” in English; translate the category while preserving the protected product/protocol name Direct.')
# Input path message, standard domain “import” verb.
cand(1171,'ja','correction','入力ファイルが存在しません: {value0}','The current Japanese predicate is unnatural; state that the input file does not exist.')
cand(1171,'pt-BR','correction','O arquivo de entrada não existe: {value0}','Add the article required for a natural Portuguese error sentence.')
cand(1171,'vi','correction','Tệp đầu vào không tồn tại: {value0}','Use the standard “input file” expression rather than wording that can mean an imported file.')
# Too-small validation concerns the converted file itself.
for loc,target,disp,why in [
 ('ja','変換後の M4B ファイルは、有効なオーディオブックとしては小さすぎます。','correction','The current Japanese is ungrammatical and does not make the converted file a natural subject.'),
 ('ko','변환된 M4B 파일은 유효한 오디오북으로 보기에는 너무 작습니다.','correction','The current comparison is malformed; state that the converted M4B file is too small to qualify as a valid audiobook.'),
 ('pt-BR','O arquivo M4B convertido é pequeno demais para ser um audiolivro válido.','refinement','Use the standard Brazilian Portuguese term audiolivro for the valid audiobook item.'),
 ('vi','Tệp M4B đã chuyển đổi quá nhỏ để được coi là sách nói hợp lệ.','correction','The current Vietnamese makes “convert” the subject rather than the resulting file.'),
 ('zh-Hans','转换后的 M4B 文件太小，无法成为有效的有声书。','correction','The current Chinese syntax reverses the “too small to be valid” relationship.'),
 ('zh-Hant','轉換後的 M4B 檔案太小，無法成為有效的有聲書。','correction','The current Chinese syntax reverses the “too small to be valid” relationship.')]: cand(1172,loc,disp,target,why)
for loc,target,disp,why in [
 ('ja','M4B の変換に失敗しました: {value0}','refinement','Use a complete Japanese failure sentence before the dynamic error detail.'),
 ('ko','M4B 변환에 실패했습니다: {value0}','refinement','Use natural Korean spacing and a complete failure phrase before the dynamic detail.'),
 ('pt-BR','A conversão de M4B falhou: {value0}','correction','The current target has ungrammatical word order.'),
 ('vi','Chuyển đổi M4B thất bại: {value0}','correction','The current target has ungrammatical word order.')]: cand(1173,loc,disp,target,why)
for loc,target in [
 ('zh-Hans','m4b-tool 以退出代码 {value0} 失败。'),('zh-Hant','m4b-tool 以結束代碼 {value0} 失敗。')]:
 cand(1174,loc,'correction',target,'The current Chinese puts the exit code in the wrong grammatical position; state that m4b-tool failed with the given code.')
# Chapter/tag error: preserve tools and use product import terminology.
cand(1177,'ja','refinement','m4b-tool は章やタグを書き込む際に失敗しました。変換後の音声は自動的にインポートされません。','Use standard Japanese punctuation and a natural verb for writing chapter/tag metadata.')
cand(1177,'ko','correction','m4b-tool은 챕터나 태그를 쓰는 중 실패했습니다. 변환된 오디오는 자동으로 가져오지 않습니다.','The current subject particle is wrong for the Latin product name, and 수입 means income/importing goods rather than importing a file.')
cand(1177,'vi','correction','m4b-tool thất bại khi ghi chương hoặc thẻ. Âm thanh đã chuyển đổi sẽ không được nhập tự động.','Fix sentence capitalization and replace nhập khẩu, which refers to importing goods, with the product’s file-import term.')
cand(1177,'zh-Hans','correction','m4b-tool 在写入章节或标签时失败。转换后的音频不会自动导入。','Use natural Chinese word spacing and 导入 for the application’s file-import action instead of 进口.')
cand(1177,'zh-Hant','correction','m4b-tool 在寫入章節或標籤時失敗。轉換後的音訊不會自動匯入。','Use natural Chinese word spacing and 匯入 for the application’s file-import action instead of 進口.')
# Finished without output file.
cand(1179,'ko','refinement','m4b-tool이 완료되었지만 변환된 M4B 파일을 만들지 못했습니다.','Correct the spacing in 변환된 and use the natural completed-tool result construction.')
cand(1179,'pt-BR','refinement','O m4b-tool terminou, mas não criou o arquivo M4B convertido.','Use the more neutral professional verb terminou rather than the colloquial acabou.')
cand(1179,'vi','correction','m4b-tool đã hoàn tất nhưng không tạo ra tệp M4B đã chuyển đổi.','The current phrase has awkward file/conversion word order; make the missing converted file the result of the completed tool run.')
cand(1179,'zh-Hans','correction','m4b-tool 已完成，但未创建转换后的 M4B 文件。','The current phrase omits the “after conversion” relation; use the natural converted-file construction.')
cand(1179,'zh-Hant','correction','m4b-tool 已完成，但未建立轉換後的 M4B 檔案。','The current phrase omits the “after conversion” relation; use the natural converted-file construction.')
cand(1180,'vi','correction','Tìm kiếm gói truyện yêu cầu có authorId.','The current translation leaves “series pack” untranslated; use a concise Vietnamese description while keeping authorId exact.')
# Failed conversion job.
for loc,target,disp,why in [
 ('ja','M4B 変換ジョブが失敗しました: {value0}','refinement','Make the failed conversion job a grammatical Japanese subject while preserving the error detail.'),
 ('ko','M4B 변환 작업이 실패했습니다: {value0}','refinement','Add the required subject particle and past-tense predicate for the failed job.'),
 ('pt-BR','A tarefa de conversão para M4B falhou: {value0}','correction','The current Portuguese noun order is ungrammatical.'),
 ('vi','Tác vụ chuyển đổi M4B đã thất bại: {value0}','correction','The current Vietnamese noun order is ungrammatical.')]: cand(1181,loc,disp,target,why)
# Requested book not found.
cand(1184,'ja','correction','要求された書籍が見つかりませんでした。','The current Japanese wording is an unnatural literal “requested book” phrase; use a direct not-found result.')
cand(1184,'ko','refinement','요청된 책을 찾을 수 없습니다.','Turn the current unfinished noun fragment into a complete, natural not-found message.')
cand(1184,'pt-BR','correction','Não foi possível encontrar o livro solicitado.','The current phrase assigns the inability to an unstated subject; use the standard impersonal error wording.')
cand(1184,'vi','refinement','Không tìm thấy cuốn sách được yêu cầu.','Use a concise result phrase rather than the current slightly awkward “cannot find” construction.')
cand(1186,'vi','correction','Tệp M4B đã chuyển đổi không được tạo.','The current chưa được tạo can imply “not yet”; the source reports that the file was not created.')
# Hold the source-registry literal conflict: the value is dynamic at both callers.
HOLD={1187}
# Process-result grammar.
cand(1188,'ja','correction','m4b-tool はプロセスの実行結果を返しませんでした。','The current Japanese lacks a grammatical relation between the tool and process result; report that the tool returned no process result.')
cand(1188,'ko','correction','m4b-tool이 프로세스 실행 결과를 반환하지 않았습니다.','The current Korean uses the wrong subject particle and an awkward calque for process result.')
cand(1188,'vi','correction','m4b-tool không trả về kết quả tiến trình.','Use trả về for returning a result and a natural term for the process result.')
cand(1188,'zh-Hans','correction','m4b-tool 未返回进程执行结果。','Use the standard Chinese term 进程执行结果 rather than the awkward literal 过程结果.')
cand(1188,'zh-Hant','correction','m4b-tool 未回傳程序執行結果。','Use the standard Traditional Chinese term 程序執行結果 rather than the awkward literal 過程結果.')
# Finalizing is an ongoing last processing stage.
for loc,target in [
 ('ja','M4B の最終処理中'),('ko','M4B 마무리 작업 중'),('pt-BR','Finalizando o M4B'),('vi','Đang hoàn tất M4B'),('zh-Hans','正在完成 M4B 的最终处理'),('zh-Hant','正在完成 M4B 的最後處理')]:
 cand(1189,loc,'correction',target,'The current target reads as a completed end/conclusion or an unnatural noun stack; the caller returns an ongoing finalization status.','moderate')
# No client available for this protocol.
cand(1190,'ko','correction','{value0}용 다운로드 클라이언트를 모두 사용할 수 없습니다.','The current particle makes clients the subject able to use something; state that all clients for this protocol are unavailable.')
cand(1190,'vi','correction','Tất cả ứng dụng tải xuống cho {value0} đều không khả dụng.','The current target translates clients as customers; use the established application category and state unavailability.')
cand(1190,'zh-Hans','correction','适用于 {value0} 的所有下载客户端均不可用。','The current phrase says clients cannot be provided; state that all clients supporting the protocol are unavailable.')
cand(1190,'zh-Hant','correction','適用於 {value0} 的所有下載用戶端均無法使用。','The current phrase says clients cannot be provided; state that all clients supporting the protocol are unavailable.')
cand(1192,'ko','correction','m4b-tool을 사용할 수 없습니다.','The current Korean is missing the object particle after m4b-tool.')
cand(1192,'vi','refinement','m4b-tool không khả dụng.','Use the more idiomatic availability term in a concise tool status.')
cand(1193,'ko','refinement','m4b-tool이 {value0} 후 시간 초과되어 변환이 중지되었습니다.','Use natural time-limit grammar and make clear that the timeout stopped the conversion.')
# Converted output does not contain a readable audio stream.
for loc,target,disp,why in [
 ('ja','変換後の M4B に、読み取り可能なオーディオストリームが含まれていません。','correction','The current Japanese uses an ungrammatical subject/containment construction.'),
 ('pt-BR','O M4B convertido não contém um fluxo de áudio legível.','correction','The current Portuguese starts with an incomplete translated adjective instead of a converted M4B file.'),
 ('vi','M4B đã chuyển đổi không chứa luồng âm thanh có thể đọc được.','correction','The current Vietnamese makes the conversion itself the subject instead of the resulting M4B.'),
 ('zh-Hans','转换后的 M4B 不包含可读取的音频流。','correction','The current Chinese lacks the “converted” result relation and uses an awkward “readable” construction.'),
 ('zh-Hant','轉換後的 M4B 不包含可讀取的音訊串流。','correction','The current Chinese lacks the “converted” result relation and uses an awkward “readable” construction.')]: cand(1195,loc,disp,target,why)
cand(1198,'ko','correction','M4B로 변환 중: {value0}/{value1}','The current phrase puts the count/protocol relations in the wrong order; use the standard current-step/total progress form.')
cand(1198,'vi','refinement','Đang chuyển đổi sang M4B - {value0}/{value1}','Make the progress status explicitly ongoing while retaining both step counters.')
cand(1199,'pt-BR','correction','Este indexador oferece suporte apenas a buscas de e-books. As URLs configuradas permanecem na ordem em que você as insere.','URLs is plural in Portuguese; the current target uses singular URL with a plural adjective.')

review=[]
for cell in inputs:
 n=cell['sourceOrdinal']; loc=cell['locale']
 if loc not in LOCALES: continue
 src=sources[n]; caller=callers[n]
 cur=cell['currentTarget']; held=n in HOLD
 if held:
  disp='hold'; target=None
  rationale=('Hold: source placeholder {value0} is supplied at the exact callers by TargetQualityName ?? "M4B". The value may be a different target quality, while the registry also requires the protected literal M4B. Neither adding M4B (which may misstate the dynamic value) nor removing the placeholder preserves both caller meaning and the registered literal requirement. Caller pins and the source-registry conflict are recorded; no target correction is inferred.')
  confidence='low'
 elif (n,loc) in C:
  disp,target,rationale,confidence=C[(n,loc)]
 else:
  disp='accept-current'; target=None
  rationale='Reviewed against the exact English source, exact pinned production caller(s), neighboring catalog usage, locale register, placeholders, markup, ICU signature, and registered protected literals; no material defect identified.'
  confidence='moderate'
 final=cur if target is None else target
 ph=lambda s: collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
 markup=lambda s: [] if re.fullmatch(r'<[^<>/]+>',s) else re.findall(r'</?[A-Za-z][^>]*>',s)
 icu=lambda s: sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
 literals=cell['protectedLiterals']
 checks={'sourcePlaceholders':dict(sorted(ph(cell['sourceText']).items())),'currentPlaceholders':dict(sorted(ph(cur).items())),'finalPlaceholders':dict(sorted(ph(final).items())),
  'placeholderParity':ph(cell['sourceText'])==ph(cur)==ph(final),'sourceMarkup':markup(cell['sourceText']),'currentMarkup':markup(cur),'finalMarkup':markup(final),
  'markupParity':markup(cell['sourceText'])==markup(cur)==markup(final),'sourceIcuSignature':icu(cell['sourceText']),'currentIcuSignature':icu(cur),'finalIcuSignature':icu(final),
  'icuParity':icu(cell['sourceText'])==icu(cur)==icu(final),
  'protectedLiteralChecks':[{'literal':lit,'inSource':lit in cell['sourceText'],'inCurrentTarget':lit in cur,'inFinalTarget':lit in final,
    'status':'hold-conflict' if held and (lit not in final) else ('pass' if lit in final else 'fail')} for lit in literals],
  'currentProtectedLiteralFailures':[lit for lit in literals if lit not in cur],
  'finalProtectedLiteralFailures':[lit for lit in literals if lit not in final],
  'protectedLiteralDisposition':'hold-conflict' if held else 'pass'}
 assert checks['placeholderParity'] and checks['markupParity'] and checks['icuParity'],(n,loc,checks)
 if not held: assert not checks['finalProtectedLiteralFailures'],(n,loc,checks)
 assert sha(cur)==cell['currentTargetSha256'],(n,loc,'current hash mismatch')
 cat=pins['localeCatalogs'][loc]
 sourcefile=pins['englishCatalog']
 callerrefs=cell['callerReferences']
 assert caller['callerReferenceStatus']=='exact' and caller['callerContextSha256']==cell['callerContextSha256']
 review.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':n,'sourceId':cell['sourceId'],'locale':loc,
  'source':cell['sourceText'],'sourceIdSha256':cell['sourceIdSha256'],'sourceTextSha256':cell['sourceTextSha256'],
  'sourceFile':sourcefile['path'],'sourceFileGitBlob':sourcefile['gitBlob'],'sourceFileSha256':sourcefile['sha256'],
  'currentTarget':cur,'currentTargetSha256':cell['currentTargetSha256'],'targetFile':cell['targetFile'],
  'targetFileGitBlob':cell['catalogGitBlob'],'targetFileSha256':cell['catalogFileSha256'],
  'primaryDisposition':disp,'recommendedTarget':target,'recommendedTargetSha256':sha(target) if target is not None else None,
  'finalReviewedTarget':final,'finalReviewedTargetSha256':sha(final),'decisionRationale':rationale,'reviewConfidence':confidence,
  'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,
  'callerContextSha256':cell['callerContextSha256'],'callerReferenceCount':len(callerrefs),'callerRefs':callerrefs,
  'protectedLiterals':literals,'sourceRegistryFingerprint':src['sourceRegistryFingerprint'],
  'sourceRegistryParameters':cell['registryParameters'],'sourceTemplates':src['sourceTemplates'],
  'structuralChecks':checks,
  'semanticInterpretation':'Exact registered server/API message and pinned production display/error surface: '+('; '.join(sorted({x.get('surface','') for x in callerrefs if x.get('surface')})) or 'surface is recorded by the caller references.')})
assert len(review)==300
assert len({(r['sourceOrdinal'],r['locale']) for r in review})==300
with open(OUT/'locale-review-ja-ko-pt-vi-zh.jsonl','w',encoding='utf8') as f:
 for row in review: f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
(OUT/'locale-review-ja-ko-pt-vi-zh.jsonl.sha256').write_text(sha((OUT/'locale-review-ja-ko-pt-vi-zh.jsonl').read_text(encoding='utf8'))+'  locale-review-ja-ko-pt-vi-zh.jsonl\n',encoding='utf8')
print(json.dumps({'rows':len(review),'counts':dict(collections.Counter(r['primaryDisposition'] for r in review)),'proposals':dict(collections.Counter(r['primaryDisposition'] for r in review if r['recommendedTarget'] is not None)),'holds':sum(r['primaryDisposition']=='hold' for r in review),'sha256':sha((OUT/'locale-review-ja-ko-pt-vi-zh.jsonl').read_text(encoding='utf8'))},ensure_ascii=False,indent=2))
