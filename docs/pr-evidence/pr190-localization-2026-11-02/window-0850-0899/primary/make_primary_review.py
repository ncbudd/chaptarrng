from __future__ import annotations
import collections, hashlib, json, pathlib, re, subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
REPO='snapetech-org/ChaptarrNG'; PR=190
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def readjl(name): return [json.loads(x) for x in (OUT/name).read_text().splitlines()]
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
# Ordinal rationale describes the exact code behavior at the caller pins.
WHY={
850:'Hadouken host validation reports a failed connection.',851:'The quality profile validator accepts only the Audiobook or Ebook profile type.',852:'The Series API rejects an empty title.',853:'Manual import rejects an edition whose BookId differs from the selected book.',854:'QualityNameValidator rejects names assigned to individual quality entries.',855:'Seed ratio and seed-time fields are warnings when their values are not greater than zero.',856:'Manual import could not resolve the selected foreign edition identifier.',857:'Several download-client and Calibre host validations report a generic connection failure.',858:'Two API routes require the unmappedFiles.scope request value.',859:'Hardcover host validation includes the URL, API key, and logs as troubleshooting directions.',860:'Specific-book monitoring needs provider IDs and directs callers to the book-add endpoint.',861:'Author validation requires the selected root folder to support the expected audiobook or ebook type.',862:'The Book API validates the mediaType query parameter against audiobook and ebook.',863:'Plex validation could not resolve the selected library section.',864:'Join validation recommends using device names instead of device IDs.',865:'The metadata-profile validator reports a missing profile.',866:'Plex settings reject an invalid library selection.',867:'Deluge host validation reports an invalid hostname.',868:'NZBVortex host validation reports a failed connection.',869:'Goodreads bookshelf settings require an access token when an OAuth secret is set.',870:'External media processes can be cancelled, and the canceled state is surfaced as the process result.',871:'Plex validation reports an invalid authentication token.',872:'QualityItemsValidator requires at least one allowed quality.',873:'The Book API rejects negative offsets.',874:'qBittorrent reports that it is still downloading metadata while the item is queued.',875:'Telegram settings allow an absent TopicId or a numeric value greater than one.',876:'Deluge host validation reports a secure-channel connection failure.',877:'rTorrent host validation reports a failed connection.',878:'BookLore credential validation reports that the username or password was rejected.',879:'Manual import rejects an edition that does not belong to the selected book.',880:'Hadouken validation requires client version 5.1 or newer because its older API is unsupported.',881:'The configuration or proxy test result includes the underlying exception text.',882:'SABnzbd validation requires version 0.7.0 or later and reports the detected version.',883:'Twitter settings advise Direct Messaging or a private account as a warning.',884:'qBittorrent category validation forbids empty segments, repeated slashes, and leading or trailing slashes; the pinned caller also forbids backslashes.',885:'The API rejects RanobeDB metadata for non-eBook media types.',886:'ProviderControllerBase requires provider names to be unique.',887:'The development configuration check received no response from the metadata server.',888:'The indexer request failed because the indexer cannot handle the current query; the message points to categories and season or episode search support.',889:'Goodreads and Hardcover import-list callers require the selected root folder to have defaults for the interpolated media type.',890:'The Author API accepts only the documented monitor enum values.',891:'IPTorrents must receive a direct-download RSS URL that includes the ;download suffix.',892:'The Calibre endpoint returned a URL that is not a Calibre content server.',893:'The command API found no book matching the supplied book ID and requested media type.',894:'qBittorrent requires torrent queueing to be enabled for the configured priority.',895:'The Author API could not find the requested author.',896:'The naming-pattern API requires the ast request field.',897:'AudioBookShelf library discovery failed; value0 carries the opaque service response.',898:'ntfy rejects a topic that violates its configured validation rules.',899:'The direct-download client is retrying after a transfer error; placeholders carry attempt counts and the opaque error.'}
# Primary target recommendations. Candidate keys are (ordinal, locale).
C={
(850,'ar'):'تعذّر الاتصال بـ Hadouken.',
(850,'de'):'Verbindung zu Hadouken nicht möglich.',
(850,'es'):'No se pudo conectar con Hadouken.',
(850,'hi'):'Hadouken से कनेक्ट नहीं हो सका।',
(850,'pt-BR'):'Não foi possível conectar-se ao Hadouken.',
(852,'id'):'Judul wajib diisi.',
(852,'ja'):'タイトルは必須です。',
(852,'vi'):'Tiêu đề là bắt buộc.',
(852,'zh-Hans'):'标题为必填项。',
(852,'zh-Hant'):'標題為必填項。',
(853,'hi'):'चयनित संस्करण {value0} चयनित पुस्तक {value1} से संबंधित नहीं है।',
(853,'ja'):'選択したエディション {value0} は、選択した書籍 {value1} に属していません。',
(855,'id'):'Harus lebih besar dari nol.',
(857,'pt-BR'):'Não foi possível conectar.',
(861,'es'):'La carpeta raíz seleccionada no está configurada para {value0}.',
(861,'id'):'Folder root yang dipilih belum dikonfigurasi untuk {value0}.',
(862,'fr'):"Le paramètre mediaType '{value0}' est invalide. Valeurs valides : audiobook, ebook.",
(863,'vi'):'Không tìm thấy thư viện Plex đã chọn.',
(867,'fr'):'Nom d’hôte invalide.',
(867,'ja'):'無効なホスト名。',
(868,'es'):'No se pudo conectar con NZBVortex.',
(868,'pt-BR'):'Não foi possível conectar ao NZBVortex.',
(869,'ar'):'يلزم توفير رمز الوصول إلى Goodreads عند إعداد سر OAuth.',
(869,'de'):'Goodreads-Zugriffstoken ist erforderlich, wenn ein OAuth-Geheimnis konfiguriert ist.',
(869,'hi'):'OAuth सीक्रेट कॉन्फ़िगर होने पर Goodreads एक्सेस टोकन आवश्यक है।',
(869,'ja'):'OAuth シークレットを設定する場合は、Goodreads のアクセストークンが必要です。',
(869,'ko'):'OAuth 시크릿을 설정한 경우 Goodreads 액세스 토큰이 필요합니다.',
(871,'fr'):'Jeton d’authentification invalide.',
(871,'ja'):'無効な認証トークン。',
(871,'ko'):'잘못된 인증 토큰입니다.',
(872,'hi'):'कम से कम एक अनुमत गुणवत्ता शामिल होनी चाहिए।',
(872,'id'):'Harus memiliki setidaknya satu kualitas yang diizinkan.',
(872,'ko'):'허용된 품질을 하나 이상 포함해야 합니다.',
(872,'zh-Hans'):'必须至少包含一个允许的质量。',
(872,'zh-Hant'):'必須至少包含一個允許的品質。',
(873,'ja'):'オフセットは0以上である必要があります。',
(873,'ko'):'오프셋은 0 이상이어야 합니다.',
(875,'es'):'El ID del tema debe ser mayor que 1 o estar vacío.',
(875,'id'):'ID topik harus lebih besar dari 1 atau kosong.',
(875,'ja'):'トピックIDは1より大きいか、未設定である必要があります。',
(878,'ja'):'BookLore がユーザー名またはパスワードを拒否しました。',
(878,'ko'):'BookLore가 사용자 이름 또는 비밀번호를 거부했습니다.',
(879,'hi'):'चयनित संस्करण चयनित पुस्तक से संबंधित नहीं है।',
(879,'zh-Hans'):'所选版本不属于所选书籍。',
(879,'zh-Hant'):'所選版本不屬於所選書籍。',
(880,'hi'):'पुराना Hadouken क्लाइंट असमर्थित API का उपयोग कर रहा है; संस्करण 5.1 या उससे नया आवश्यक है।',
(880,'ja'):'古いHadoukenクライアントはサポートされていないAPIを使用しています。バージョン5.1以降が必要です。',
(880,'ko'):'오래된 Hadouken 클라이언트가 지원되지 않는 API를 사용합니다. 버전 5.1 이상이 필요합니다.',
(880,'zh-Hans'):'旧版 Hadouken 客户端使用了不受支持的 API；需要 5.1 或更高版本。',
(880,'zh-Hant'):'舊版 Hadouken 用戶端使用了不支援的 API；需要 5.1 或更新版本。',
(882,'zh-Hans'):'需要版本 0.7.0+，但当前检测到：{value0}',
(882,'zh-Hant'):'需要版本 0.7.0+，但目前偵測到：{value0}',
(883,'ko'):'다이렉트 메시지를 사용하는 것이 좋습니다. 또는 비공개 계정을 사용하세요.',
(886,'vi'):'Tên phải là duy nhất.',
(889,'ko'):"선택한 루트 폴더 '{value0}'에 {value1} 기본값이 설정되어 있지 않습니다.",
(889,'id'):"Folder root yang dipilih '{value0}' belum memiliki pengaturan default untuk {value1}.",
(889,'vi'):"Thư mục gốc đã chọn '{value0}' chưa được cấu hình giá trị mặc định cho {value1}.",
(889,'zh-Hans'):'所选根文件夹“{value0}”尚未配置 {value1} 的默认值。',
(892,'fr'):'Ce n’est pas un serveur de contenu Calibre ; vérifiez l’URL.',
(892,'hi'):'यह Calibre कंटेंट सर्वर नहीं है; URL जाँचें।',
(892,'id'):'Ini bukan server konten Calibre; periksa URL.',
(892,'ko'):'Calibre 콘텐츠 서버가 아닙니다. URL을 확인하세요.',
(892,'pt-BR'):'Não é um servidor de conteúdo do Calibre; verifique a URL.',
(892,'zh-Hans'):'这不是 Calibre 内容服务器，请检查 URL。',
(892,'zh-Hant'):'這不是 Calibre 內容伺服器，請檢查 URL。',
(893,'de'):'Die Buch-ID stimmt mit keinem Buch des angeforderten Medientyps überein.',
(893,'es'):'El ID del libro no corresponde a ningún libro del tipo de medio solicitado.',
(893,'fr'):'L’ID du livre ne correspond à aucun livre du type de média demandé.',
(893,'hi'):'पुस्तक की ID अनुरोधित मीडिया प्रकार की किसी पुस्तक से मेल नहीं खाती।',
(893,'id'):'ID buku tidak cocok dengan buku dalam jenis media yang diminta.',
(893,'pt-BR'):'O ID do livro não corresponde a nenhum livro do tipo de mídia solicitado.',
(895,'ko'):'작가를 찾을 수 없습니다.',
(895,'zh-Hans'):'未找到作者。',
(895,'zh-Hant'):'未找到作者。',
(897,'hi'):'AudioBookShelf से मीडिया लाइब्रेरी प्राप्त नहीं की जा सकीं: {value0}',
(897,'id'):'Tidak dapat memperoleh pustaka dari AudioBookShelf: {value0}',
(897,'ja'):'AudioBookShelfからライブラリを取得できませんでした: {value0}',
(897,'zh-Hans'):'无法从 AudioBookShelf 获取媒体库：{value0}',
(897,'zh-Hant'):'無法從 AudioBookShelf 取得媒體庫：{value0}'
}
# Preserve key/product/API literals and code-shaped tokens. The source registry list is merged with these explicit checks.
EXTRA={
850:['Hadouken'],
858:['unmappedFiles.scope'],
880:['Hadouken','5.1'],
882:['0.7.0+'],
885:['RanobeDB'],
890:['all','future','missing','existing','first','latest','none','specificBook'],
891:[';download'],
896:['ast'],
}
# The English source is missing the backslash present in the exact validator caller; the string cannot be safely finalized until source is aligned.
HOLD_ORDINALS={884}
inputs=readjl('input-cells.jsonl'); callers={x['sourceId']:x for x in readjl('caller-context.jsonl')}
assert len(inputs)==600 and len(callers)==50
by_key={(c['sourceOrdinal'],c['locale']):c for c in inputs}
assert len(by_key)==600 and set(WHY)==set(range(850,900))
assert all(k in by_key for k in C)
assert all(c['sourceOrdinal'] in range(850,900) for c in inputs)
# Use caller evidence to verify the known source/caller discrepancy exactly.
w884=callers[next(c['sourceId'] for c in inputs if c['sourceOrdinal']==884)]
assert "Can not contain '\\', '//', or start/end with '/'" in '\n'.join(r['lineText'] for r in w884['callerRefs'])
assert "Can not contain '', '//', or start/end with '/'"==w884['source']
rows=[]; protected_rows=[]; counts=collections.Counter(); per=collections.defaultdict(collections.Counter); token_mismatch=[]
for c in inputs:
 o=c['sourceOrdinal']; loc=c['locale']; current=c['currentTarget']; sid=c['sourceId']
 source_tokens=list(dict.fromkeys(c['protectedLiterals']+EXTRA.get(o,[])))
 # Hold W884 on the caller/source mismatch, not on the meaning of the localized current values.
 if o in HOLD_ORDINALS:
  disposition='hold'; target=None; rationale="Hold: the pinned caller forbids a backslash (\\), but the English source-catalog string omits it; final localized targets should wait for the source and caller message to be aligned."
 elif (o,loc) in C:
  target=C[(o,loc)]; disposition='propose-correction'
  if o==855: disposition='propose-refinement'
  if o in (872,889,897):
   # Align the exact application term or repair an otherwise comprehensible but materially weak phrase.
   disposition='propose-refinement' if o in (872,889) else 'propose-correction'
  reason={
   850:'The current wording is an awkward noun/infinitive fragment; this uses a natural localized connection-failure message.',
   852:'The current phrase is incomplete or non-idiomatic for a required form field; this uses the locale’s standard required-field wording.',
   853:'The current sentence has awkward word order or agreement; this clearly states that the selected edition does not belong to the selected book.',
   855:'The message is correct, but capitalizing and punctuating the Indonesian validation sentence improves consistency.',
   857:'The current PT-BR fragment is less natural as a connection error; this uses the standard “could not connect” form.',
   861:'The Spanish word “pasta” means pasta; “carpeta raíz” is the correct term for the selected filesystem folder.',
   862:'The current French word order is awkward; this preserves the exact mediaType parameter and accepted values.',
   863:'The current Vietnamese passive construction is unnatural; this uses a concise “not found” error.',
   867:'The current French phrase omits the noun link and the Japanese phrase omits the adjective marker.',
   868:'The current phrases state that an unspecified subject cannot connect; these use the usual error-message form for a failed connection.',
   869:'The current phrasing is awkward or literal; these versions make the conditional requirement clear while preserving Goodreads and OAuth.',
   871:'The current French wording is a malformed fragment and the Japanese/Korean versions are awkward noun strings; these are natural invalid-token errors.',
   872:'These versions state the requirement naturally and align the quality term with the media-quality profile terminology.',
   873:'The current Japanese/Korean wording is an unnatural loanword or literal negative; “0 or higher” is the natural numeric constraint.',
   875:'The current Spanish/Indonesian noun order and Japanese “empty” phrasing are awkward; these state the nullable Topic ID constraint clearly.',
   878:'The current Japanese/Korean strings are ungrammatical fragments; these clearly report that BookLore rejected the supplied credentials.',
   879:'The current Hindi agreement is wrong and the Chinese term is too abbreviated; these use the standard “edition/version” wording.',
   880:'The current Hindi/Japanese/Korean/Chinese text is fragmentary; these state the unsupported API and required minimum version clearly.',
   882:'The current Chinese word order is ungrammatical; these clearly say version 0.7.0+ is required and show the detected version.',
   883:'The current Korean wording makes the alternative recommendation ungrammatical; this separates the two choices clearly.',
   886:'“Độc đáo” means distinctive; this validation requires a name to be unique, so “duy nhất” is the accurate constraint.',
   889:'The current Korean word for root means a plant root and the Vietnamese/Chinese phrases are awkward; these use the UI’s root-folder term and a clear defaults statement.',
   892:'These current phrases are fragments or say no server exists; the candidates state that the URL does not point to a Calibre content server.',
   893:'These current strings use awkward “Book ID” word order or grammar; the candidates use the natural “book ID” term and preserve the media-type condition.',
   895:'The current Korean and Chinese strings are malformed fragments; these use the standard author-not-found message.',
   897:'These current terms refer to a physical library or use an awkward retrieval phrase; the candidates align with AudioBookShelf’s localized media-library terminology.'
  }[o]
  rationale=reason
 else:
  disposition='accept-current'; target=current
  rationale=f"{WHY[o]} The current {loc} wording preserves that meaning in the pinned caller context; no material grammar, terminology, placeholder, markup, or protected-literal issue was found."
 final_target=target
 target_ph=placeholders(target) if target is not None else None
 target_markup=markup(target) if target is not None else None
 source_ph=placeholders(c['source']); current_ph=placeholders(current); source_markup=markup(c['source']); current_markup=markup(current)
 source_checks=[{'literal':lit,'presentInSource':lit in c['source'],'presentInCurrentTarget':lit in current,'presentInRecommendedTarget':None if target is None else lit in target} for lit in source_tokens]
 missing_current=[x['literal'] for x in source_checks if x['presentInSource'] and not x['presentInCurrentTarget']]
 missing_target=[x['literal'] for x in source_checks if x['presentInSource'] and target is not None and not x['presentInRecommendedTarget']]
 candidate_ph_ok=target is None or target_ph==source_ph
 candidate_markup_ok=target is None or target_markup==source_markup
 if not candidate_ph_ok or not candidate_markup_ok or missing_target:
  token_mismatch.append({'sourceOrdinal':o,'sourceId':sid,'locale':loc,'placeholderParity':candidate_ph_ok,'markupParity':candidate_markup_ok,'missingRecommendedLiterals':missing_target})
 assert candidate_ph_ok,(o,loc,'candidate placeholder mismatch',source_ph,target_ph)
 assert candidate_markup_ok,(o,loc,'candidate markup mismatch',source_markup,target_markup)
 assert not missing_target,(o,loc,'candidate missing protected token',missing_target,target)
 caller=callers[sid]
 record={**c,
  'callerRefs':caller['callerRefs'],'callerReferenceStatus':caller['callerReferenceStatus'],'callerContextSha256':caller['callerContextSha256'],
  'sourceRegistrySurface':caller.get('sourceRegistrySurface'),'sourceRegistryCategory':caller.get('sourceRegistryCategory'),
  'disposition':disposition,'rationale':rationale,'recommendedTarget':None if target is None or target==current else target,
  'recommendedTargetSha256':None if target is None or target==current else sha(target),
  'finalTarget':final_target,'finalTargetSha256':sha(final_target) if final_target is not None else None,
  'sourcePlaceholders':source_ph,'currentTargetPlaceholders':current_ph,'recommendedTargetPlaceholders':target_ph if target!=current else None,
  'sourceMarkup':source_markup,'currentTargetMarkup':current_markup,'recommendedTargetMarkup':target_markup if target!=current else None,
  'placeholderParity':source_ph==current_ph and (target is None or source_ph==target_ph),
  'markupParity':source_markup==current_markup and (target is None or source_markup==target_markup),
  'protectedLiterals':source_tokens,'protectedLiteralChecks':source_checks,
  'protectedLiteralsPreserved':not missing_target and (target is not None or not missing_current),
  'callerSourceMessageMismatch':o==884,
  'nativeSpeakerApproval':False,'confidence':'moderate'}
 rows.append(record)
 protected_rows.append({'sourceOrdinal':o,'sourceId':sid,'locale':loc,'source':c['source'],'sourceTextSha256':c['sourceTextSha256'],'currentTarget':current,'currentTargetSha256':c['currentTargetSha256'],'finalTarget':final_target,'finalTargetSha256':record['finalTargetSha256'],'protectedLiterals':source_tokens,'protectedLiteralChecks':source_checks,'placeholderParity':record['placeholderParity'],'markupParity':record['markupParity'],'sourcePlaceholders':source_ph,'currentPlaceholders':current_ph,'finalPlaceholders':target_ph,'sourceMarkup':source_markup,'currentMarkup':current_markup,'finalMarkup':target_markup,'callerSourceMessageMismatch':o==884,'head':HEAD,'tree':TREE})
 counts[disposition]+=1; per[loc][disposition]+=1
assert len(rows)==600 and len(token_mismatch)==0,token_mismatch
assert len({(x['sourceOrdinal'],x['locale']) for x in rows})==600
assert counts['hold']==12
for k in ['accept-current','propose-correction','propose-refinement','hold']: counts.setdefault(k,0)
writejl('review-cells.jsonl',rows); writejl('protected-literal-integrity.jsonl',protected_rows)
findings=[{'sourceOrdinal':884,'sourceId':next(c['sourceId'] for c in inputs if c['sourceOrdinal']==884),'severity':'source-caller mismatch','affectedCells':12,'source':'Can not contain \'\', \'//\', or start/end with \'/\'','pinnedCaller':'Can not contain \'\\\', \'//\', or start/end with \'/\'','recommendation':'Align the English source catalog entry with the caller’s backslash restriction, then re-review this row in all locales. This packet holds all twelve target cells.'}]
(OUT/'primary-findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':HEAD,'exactTree':TREE,'window':'W850-W899','sourcePositions':[850,899],'sourceIds':50,'localeCells':600,'locales':LOCALES,'dispositionCounts':dict(counts),'perLocaleDispositionCounts':{l:dict(per[l]) for l in LOCALES},'candidateCount':sum(counts[x] for x in ('propose-correction','propose-refinement')),'correctionCandidates':counts['propose-correction'],'refinementCandidates':counts['propose-refinement'],'holdCount':counts['hold'],'placeholderMismatchCells':sum(not x['placeholderParity'] for x in rows),'markupMismatchCells':sum(not x['markupParity'] for x in rows),'protectedLiteralFailureCells':sum(not x['protectedLiteralsPreserved'] for x in rows),'sourceCallerRows':len(callers),'sourceCallerReferences':sum(len(x['callerRefs']) for x in callers.values()),'sourceCallerGaps':[x['sourceId'] for x in callers.values() if not x['callerRefs']],'genericPipelineReferences':len(readjl('pipeline-caller-context.jsonl')),'genericPipelineGaps':[],'w849BoundaryMatches':12,'priorDispositionRows':10200,'priorCoverageThrough849':True,'priorOverlapCount':0,'callerSourceMismatchRows':[884],'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'machineAssistedConfidence':'moderate','repositoryModified':False,'testsBuildsCiBrowserRun':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'counts':dict(counts),'candidateCount':summary['candidateCount'],'callerRefs':summary['sourceCallerReferences'],'pipelineRefs':summary['genericPipelineReferences'],'placeholders':summary['placeholderMismatchCells'],'markup':summary['markupMismatchCells'],'protectedFailures':summary['protectedLiteralFailureCells'],'holds':summary['holdCount']},ensure_ascii=False,indent=2))
