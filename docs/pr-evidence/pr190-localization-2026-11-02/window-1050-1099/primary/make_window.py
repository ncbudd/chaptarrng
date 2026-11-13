from __future__ import annotations
import collections, datetime, hashlib, json, pathlib, re, subprocess

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='c0a098e4e2b23117860c6e6827c1e84485273a7a'
TREE='669c5d82ab651dc38abb2db9d35fc2f893a19fef'
BRANCH='codex/chaptarrng-localization-complete-20261031'
REPO='snapetech-org/ChaptarrNG'; PR=190
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
LOCALE_ORDER=list(LOCALES)
SOURCE='src/NzbDrone.Core/Localization/Core/en.json'
FOLLOW='docs/localization/source-followup-20261101.json'
REGISTRIES={'server':'docs/localization/server-message-sources.json','loading':'docs/localization/loading-message-sources.json'}
CALLER_INDEX='docs/localization/server-message-callers.json'
TERMS='docs/localization/terminology.json'
PREV=WORK/'docs/pr-evidence/pr190-localization-2026-11-02/window-1000-1049'

OUT.mkdir(parents=True,exist_ok=True)
(OUT/'snapshots').mkdir(exist_ok=True)
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def git(*args,binary=False):
 r=subprocess.run(['git','-C',str(WORK),*args],check=True,capture_output=True)
 return r.stdout if binary else r.stdout.decode().strip()
_show_cache={}
def show(path):
 if path not in _show_cache: _show_cache[path]=git('show',f'{HEAD}:{path}',binary=True)
 return _show_cache[path]
def tracked(path):
 b=show(path); return {'path':path,'gitBlob':git('rev-parse',f'{HEAD}:{path}'),'sha256':sha(b),'bytes':len(b)}
def writej(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
def ph(s): return collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def icu(s): return sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
def state(): return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'branch':git('branch','--show-current'),'status':git('status','--porcelain')}
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},state()

prs=[('seerr','SeerrNG',418),('chaptarr','ChaptarrNG',190),('questarr','QuestarrNG',155),('romarr','ROMarrNG',70),('slskr','slskR',204),('slskdn','slskdN',409),('torrent','TorrentNG',243)]
fields='number state isDraft headRefName headRefOid baseRefName baseRefOid updatedAt url headRepository { name owner { login } } headRef { target { oid ... on Commit { tree { oid } } } }'
query='query { '+' '.join(f'{alias}: repository(owner: "snapetech-org", name: "{repo}") {{ pullRequest(number: {num}) {{ {fields} }} }}' for alias,repo,num in prs)+' }'
def query_heads(kind):
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 r=subprocess.run(['gh','api','graphql','-f',f'query={query}'],capture_output=True,text=True,check=True)
 finished=datetime.datetime.now(datetime.timezone.utc).isoformat(); d=json.loads(r.stdout)
 if d.get('errors'): raise RuntimeError(d['errors'])
 snap={'snapshot_kind':kind,'query_started_utc':started,'query_completed_utc':finished,'query':query,'pull_requests':d['data']}
 return snap
start=query_heads('start-before-source-selection')
ch=start['pull_requests']['chaptarr']['pullRequest']
assert ch['state']=='OPEN' and ch['isDraft'] and ch['headRefOid']==HEAD and ch['headRef']['target']['tree']['oid']==TREE and ch['headRefName']==BRANCH,ch
writej('snapshots/start-all-pr-heads.json',start)

source=json.loads(show(SOURCE)); follow=json.loads(show(FOLLOW)); queue=follow['currentMissingIds']
positions=list(range(1050,1100)); selected=queue[1050:1100]
assert len(queue)==1210 and len(selected)==50
selection={'window':'W1050-W1099','positions':positions,'selectedSourceIds':selected,'currentMissingIdsSha256':sha(canon(queue))}
assert selection['currentMissingIdsSha256']==follow['currentMissingIdsSha256']
post=query_heads('after-source-selection')
postch=post['pull_requests']['chaptarr']['pullRequest']
assert postch['headRefOid']==HEAD and postch['headRef']['target']['tree']['oid']==TREE and postch['headRefName']==BRANCH and postch['state']=='OPEN' and postch['isDraft']
writej('snapshots/after-source-selection-all-pr-heads.json',post)

# Exact source registry, catalog, and direct-caller pins.
reg_data={k:json.loads(show(p)) for k,p in REGISTRIES.items()}
reg_info={k:tracked(p) for k,p in REGISTRIES.items()}
reg_records={k:{x['id']:x for x in d['records']} for k,d in reg_data.items()}
source_info=tracked(SOURCE); follow_info=tracked(FOLLOW); caller_index_info=tracked(CALLER_INDEX); terms_info=tracked(TERMS)
locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{fn}' for loc,fn in LOCALES.items()}
catalogs={}; catalog_info={}
for loc,path in locale_paths.items():
 catalog=json.loads(show(path)); assert set(catalog)==set(source),(loc,'catalog key-set mismatch')
 catalogs[loc]=catalog; catalog_info[loc]=tracked(path)
source_rows=[]; caller_rows=[]; caller_file_info={}; source_records={}; gaps=[]; stale=[]
for ordinal,sid in enumerate(selected,1050):
 kind='loading' if sid.startswith('ui.loading.') else 'server' if sid.startswith('server.message.') else None
 assert kind and sid in source and sid in reg_records[kind],(ordinal,sid,kind)
 rec=reg_records[kind][sid]; assert rec['source']==source[sid],(sid,rec.get('source'),source.get(sid))
 source_records[sid]=(kind,rec)
 row={'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'sourceIdSha256':sha(sid),'sourceTextSha256':sha(source[sid]),
  'sourceCatalogPath':SOURCE,'sourceCatalogGitBlob':source_info['gitBlob'],'sourceCatalogSha256':source_info['sha256'],
  'sourceRegistryPath':REGISTRIES[kind],'sourceRegistryGitBlob':reg_info[kind]['gitBlob'],'sourceRegistrySha256':reg_info[kind]['sha256'],
  'sourceRegistryFingerprint':rec.get('sourceFingerprint'),'sourceRegistryProtectedLiterals':rec.get('protectedLiterals',[]),
  'effectiveProtectedLiterals':list(rec.get('protectedLiterals',[])),'registryCategory':rec.get('category'),'registrySurface':rec.get('surface'),
  'registryParameters':rec.get('parameters',[]),'registryPatterns':rec.get('patterns',[]),'sourceTemplates':rec.get('sourceTemplates',[])}
 source_rows.append(row); refs=[]; seen=set()
 for pin in rec.get('callsites',[]):
  path=pin['file']; ls=show(path).decode('utf-8').splitlines(); n=pin['line']; cur=ls[n-1] if 1<=n<=len(ls) else None
  exact=cur is not None and cur.strip()==pin.get('sourceLine','').strip() and sha(cur.strip())==pin.get('sourceLineSha256')
  hits=[(n,cur)] if exact else [(i+1,v) for i,v in enumerate(ls) if sid in v]
  if not exact: stale.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':path,'registryLine':n,'expectedLineSha256':pin.get('sourceLineSha256'),'reason':'registry source line differs at exact head'})
  for line,text in hits:
   if (path,line) in seen: continue
   seen.add((path,line)); caller_file_info[path]=tracked(path)
   refs.append({'file':path,'line':line,'lineText':text.strip(),'lineSha256':sha(text.strip()),'fileGitBlob':git('rev-parse',f'{HEAD}:{path}'),
    'fileSha256':sha(show(path)),'contextBefore':[x.strip() for x in ls[max(0,line-4):line-1]],'contextAfter':[x.strip() for x in ls[line:min(len(ls),line+3)]],
    'registryLine':n,'registrySourceLine':pin.get('sourceLine'),'registrySourceLineSha256':pin.get('sourceLineSha256'),'registryPinExact':exact,
    'category':pin.get('category'),'surface':pin.get('surface'),'kind':pin.get('kind'),'enum':pin.get('enum'),'member':pin.get('member')})
 refs.sort(key=lambda x:(x['file'],x['line']))
 if not refs: gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no direct source/caller line pinned'})
 caller_rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'registryPath':REGISTRIES[kind],
  'directCallerReferences':refs,'callerReferenceCount':len(refs),'callerContextSha256':sha(canon(refs)),
  'callerReferenceStatus':'pinned' if refs else 'gap','registryCategory':rec.get('category'),'registrySurface':rec.get('surface'),
  'enumOrParameterContext':[{'enum':x.get('enum'),'member':x.get('member'),'kind':x.get('kind')} for x in rec.get('callsites',[])],
  'protectedLiterals':list(rec.get('protectedLiterals',[]))})
assert len(source_rows)==len(caller_rows)==50 and not gaps and not stale,(gaps,stale)

# Pin loading rendering and matching-message display pipeline context.
loading_runtime=[]
for path in ['frontend/src/Components/Loading/loading-messages.json','frontend/src/Components/Loading/LoadingMessage.js']:
 ls=show(path).decode('utf-8').splitlines(); matches=[]
 if path.endswith('loading-messages.json'):
  for i,line in enumerate(ls,1):
   if any(sid in line for sid in selected[:10]): matches.append(i)
 else:
  for i,line in enumerate(ls,1):
   if 'messages' in line or 'translate(' in line or 'translateMessage' in line: matches.append(i)
 for n in matches:
  loading_runtime.append({'file':path,'line':n,'lineText':ls[n-1].strip(),'lineSha256':sha(ls[n-1].strip()),
   'fileGitBlob':git('rev-parse',f'{HEAD}:{path}'),'fileSha256':sha(show(path)),
   'contextBefore':[x.strip() for x in ls[max(0,n-4):n-1]],'contextAfter':[x.strip() for x in ls[n:min(len(ls),n+3)]],
   'interpretation':'Loading message source ID and UI rendering path.'})
  caller_file_info[path]=tracked(path)
assert len([x for x in loading_runtime if x['file'].endswith('loading-messages.json')])>=10

# Reattest all exact prior outcomes through W1049, retaining both original dispositions and cross-review outcomes.
prior_prev_path=PREV/'primary/prior-dispositions-through-W999.jsonl'
prior_root_path=PREV/'adjudication/root-adjudication.jsonl'
prior_prev_raw=prior_prev_path.read_bytes(); prior_root_raw=prior_root_path.read_bytes()
prior_prev=[json.loads(x) for x in prior_prev_raw.decode().splitlines()]
prior_root=[json.loads(x) for x in prior_root_raw.decode().splitlines()]
assert len(prior_prev)==12000 and len(prior_root)==600
prior=[]
for x in prior_prev:
 prior.append({**x,'sourcePacket':x.get('sourcePacket'),'originEvidenceFile':'window-1000-1049/primary/prior-dispositions-through-W999.jsonl',
  'originEvidenceFileSha256':sha(prior_prev_raw)})
for x in prior_root:
 prior.append({'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'sourceTextSha256':x['sourceSha256'],
  'priorDisposition':x['finalDisposition'],'priorCrossReviewDisposition':x.get('crossReviewDisposition'),
  'priorInputTargetSha256':x['currentTargetSha256'],'priorFinalTargetSha256':x['finalTargetSha256'],
  'sourcePacket':'ChaptarrNG PR #190 W1000-W1049 adjudication and application',
  'sourceRecordFile':'window-1000-1049/adjudication/root-adjudication.jsonl','sourceRecordSha256':sha(canon(x)),
  'originEvidenceFile':'window-1000-1049/adjudication/root-adjudication.jsonl','originEvidenceFileSha256':sha(prior_root_raw),
  'liveCurrentTargetSha256':None,'liveTargetMatchesPriorFinalHash':None})
assert len(prior)==12600 and {x['sourceOrdinal'] for x in prior}==set(range(1050))
prior_live=[]
for x in prior:
 live=catalogs[x['locale']].get(x['sourceId']); live_hash=sha(live) if live is not None else None
 prior_packet_live=x.get('liveCurrentTargetSha256')
 prior_live.append({**x,'previousPacketLiveCurrentTargetSha256':prior_packet_live,
  'previousPacketLiveTargetMatchesFinal':x.get('liveTargetMatchesPriorFinalHash'),
  'liveCurrentTargetSha256':live_hash,'liveTargetMatchesPriorFinalHash':live_hash==x['priorFinalTargetSha256'],
  'noDriftSincePreviousPacket':prior_packet_live in (None,live_hash)})
prior_mismatches=[x for x in prior_live if not x['liveTargetMatchesPriorFinalHash']]
new_prior_drift=[x for x in prior_live if not x['noDriftSincePreviousPacket']]
assert not new_prior_drift,new_prior_drift[:5]
# Backward W1049 boundary and forward W1100 boundary are context only.
queue_hash=sha(canon(queue)); w1049_id=queue[1049]; w1100_id=queue[1100]
back=[]; forward=[]
for loc,path in locale_paths.items():
 curr=catalogs[loc][w1049_id]; past=next(x for x in prior_live if x['sourceOrdinal']==1049 and x['locale']==loc)
 back.append({'sourceOrdinal':1049,'sourceId':w1049_id,'source':source[w1049_id],'sourceTextSha256':sha(source[w1049_id]),'locale':loc,
  'previousDisposition':past['priorDisposition'],'previousFinalTargetSha256':past['priorFinalTargetSha256'],'liveTargetSha256':sha(curr),
  'liveTargetMatchesPreviousFinal':sha(curr)==past['priorFinalTargetSha256'],'targetFile':path,'targetFileGitBlob':catalog_info[loc]['gitBlob']})
 curr=catalogs[loc][w1100_id]
 forward.append({'sourceOrdinal':1100,'sourceId':w1100_id,'source':source[w1100_id],'sourceTextSha256':sha(source[w1100_id]),'locale':loc,
  'currentTarget':curr,'currentTargetSha256':sha(curr),'targetFile':path,'targetFileGitBlob':catalog_info[loc]['gitBlob'],
  'scope':'boundary context only; no W1100 disposition assigned'})
assert all(x['liveTargetMatchesPreviousFinal'] for x in back)

# Review proposals based on exact target, source, caller and relevant matching/display context.
C={}; H={}
def cand(pos,loc,target,kind,why,confidence='high'):
 C[(pos,loc)]={'target':target,'kind':kind,'why':why,'confidence':confidence}
def hold(pos,loc,why,confidence='low'): H[(pos,loc)]={'why':why,'confidence':confidence}
# Loading state: preserve the display meaning, use target-language syntax and punctuation.
cand(1050,'ar','جارٍ تحميل مغامرتك القادمة…','refinement','The current double full stop is nonstandard in this loading-status phrase; use a single Arabic ellipsis marker and an explicit in-progress construction.','moderate')
cand(1050,'hi','आपका अगला एडवेंचर लोड हो रहा है...','correction','The current ending means “in order to load,” not that the next adventure is loading; use a natural progressive status phrase.','high')
cand(1050,'zh-Hans','正在加载你的下一场冒险……','refinement','A natural Simplified Chinese progress clause and measure word improve the current noun phrase while preserving the playful metaphor.','moderate')
cand(1050,'zh-Hant','正在載入你的下一場冒險……','refinement','A natural Traditional Chinese progress clause and measure word improve the current noun phrase while preserving the playful metaphor.','moderate')
# API-reference joke: correct syntax and keep the proper name/API token.
cand(1052,'ar','عذرًا يا Gomeyy... هذه ليست واجهة API التي تبحث عنها.','correction','The current Arabic word order is ungrammatical. The corrected sentence uses the feminine noun واجهة and its matching relative clause while preserving Gomeyy and API.','high')
cand(1052,'hi','माफ़ कीजिए, Gomeyy... यह वह API नहीं है जिसे आप ढूँढ रहे हैं।','correction','The current Hindi word order is an English-shaped fragment. The revised clause expresses “this is not the API you are looking for” naturally.','high')
cand(1052,'ko','죄송해요, Gomeyy… 찾으시는 API가 아닙니다.','refinement','The current direct 당신이 phrase is unnatural in Korean UI copy; the honorific modifier is concise and keeps the apologetic tone.','moderate')
cand(1052,'pt-BR','Desculpe, Gomeyy... esta não é a API que você está procurando.','correction','API is feminine in this interface context; use esta/a API instead of este/o API.','moderate')
cand(1052,'es','Lo siento, Gomeyy... esta no es la API que buscas.','refinement','API refers to interfaz de programación and is feminine in Spanish; use esta/la API while retaining the catalog’s informal tú address.','moderate')
cand(1052,'zh-Hans','抱歉，Gomeyy……这不是你要找的 API。','correction','The current zh-Hans value is written in Traditional Chinese characters. Use Simplified Chinese script and a natural API-search clause.','high')
cand(1052,'zh-Hant','抱歉，Gomeyy……這不是你要找的 API。','refinement','Use the natural Traditional Chinese expression for the API the reader is seeking and consistent Chinese punctuation.','moderate')
# Preserve named joke characters while making the standard “walk into a library” setup natural.
cand(1057,'de','Ein Black Swan und ein Goldan Dragon betreten eine Bibliothek…','refinement','Betreten is the natural verb for the joke setup of characters entering a place; preserve both protected names exactly.','moderate')
cand(1057,'es','Un Black Swan y un Goldan Dragon entran en una biblioteca…','correction','Caminan en means they walk around inside; entran en expresses the joke setup “walk into” and preserves both protected names.','high')
cand(1057,'hi','एक Black Swan और एक Goldan Dragon पुस्तकालय में दाख़िल होते हैं...','refinement','The current चलते हैं says they walk, while दाख़िल होते हैं naturally expresses entering for the joke setup; preserve both protected names.','moderate')
cand(1057,'id','Black Swan dan Goldan Dragon berjalan masuk ke perpustakaan…','refinement','The current phrase only says they walk to a library; masuk makes the joke setup explicitly mean entering it.','moderate')
cand(1057,'ko','Black Swan과 Goldan Dragon이 도서관에 들어갑니다…','correction','Swan ends in a consonant sound, so the connective is 과; Dragon takes the subject particle 이, not 는. Preserve both protected names.','high')
cand(1057,'pt-BR','Um Black Swan e um Goldan Dragon entram em uma biblioteca…','refinement','Entram em renders the “walk into a place” joke setup naturally; preserve both protected names.','moderate')
cand(1057,'vi','Một Black Swan và một Goldan Dragon bước vào thư viện…','refinement','Bước vào is the natural “enter” phrasing for this joke setup; preserve both protected names.','moderate')
cand(1057,'zh-Hans','一个 Black Swan 和一个 Goldan Dragon 走进一间图书馆……','refinement','Add standard spacing around the protected Latin proper names and use a natural measure phrase; preserve both names exactly.','moderate')
cand(1057,'zh-Hant','一個 Black Swan 和一個 Goldan Dragon 走進一間圖書館……','refinement','Add standard spacing around the protected Latin proper names and use a natural measure phrase; preserve both names exactly.','moderate')
cand(1058,'vi','Những cuốn sách cũ này luôn bị bỏ qua.','refinement','Add sentence-ending punctuation to this descriptive loading line.','moderate')
# This source makes a protected proper-name pun that does not transfer directly; retain it for native creative localization.
for loc in LOCALES:
 hold(1054,loc,'The source uses the protected proper name Dodge in an English verb-form pun (Dodge-ing). The current target keeps the English construction, and translating it without changing the name risks losing or changing the joke; request native creative localization.', 'low')
# Matching terminology: duration means audio playback length, and native format is the expected ReadingFormatId (2 for audiobooks).
cand(1073,'fr','L’édition du catalogue ne dispose d’aucune durée exploitable.','correction','Durée d’utilisation means usage time; this match-provenance message refers to a usable audiobook playback duration.','high')
cand(1073,'ko','카탈로그 판본에는 유효한 재생 시간이 없습니다.','correction','The current 기간 means a time period/term, not audio length. Use the established playback-time term 재생 시간.','high')
cand(1074,'fr','Le fichier ne dispose d’aucune durée exploitable.','correction','Durée d’utilisation means usage time; this match-provenance message refers to a usable audio playback duration.','high')
cand(1074,'vi','Tệp này không có thời lượng khả dụng.','correction','Thời gian sử dụng means usage time. Thời lượng is the appropriate measure for playback duration.','high')
cand(1076,'de','Die Namensbestandteile des Erzählers stützten diese Ausgabe.','refinement','Use Erzähler consistently for narrator with the preceding narrator-evidence message; Sprecher can mean any speaker.','moderate')
for loc,target in {
'ar':'كانت هناك عدة إصدارات من الكتب الصوتية، لكن الملف لم يقدّم معلومات قابلة للاستخدام عن الراوي أو مدة الكتاب كاملة للتمييز بينها. اختار Chaptarr كتابًا صوتيًا بالتنسيق المطابق وفق الترتيب المعتاد والحتمي للإصدارات.',
'de':'Es gab mehrere Hörbuchausgaben, doch die Datei lieferte keine verwertbaren Hinweise zum Sprecher oder zur Gesamtdauer des Buchs, um sie zu unterscheiden. Chaptarr wählte nach der üblichen deterministischen Reihenfolge der Ausgaben ein Hörbuch im passenden Format aus.',
'es':'Había varias ediciones de audiolibros, pero el archivo no aportó datos utilizables del narrador ni de la duración del libro completo para distinguirlas. Chaptarr seleccionó un audiolibro en el formato correspondiente siguiendo el orden determinista habitual de las ediciones.',
'fr':'Plusieurs éditions de livres audio étaient disponibles, mais le fichier ne fournissait aucune information exploitable sur le narrateur ni sur la durée du livre complet pour les distinguer. Chaptarr a sélectionné un livre audio au format correspondant selon l’ordre déterministe habituel des éditions.',
'hi':'कई ऑडियोबुक संस्करण उपलब्ध थे, लेकिन फ़ाइल ने उनमें अंतर करने के लिए कथावाचक या पूरी पुस्तक की अवधि की कोई उपयोगी जानकारी नहीं दी। Chaptarr ने संस्करणों के सामान्य नियतात्मक क्रम के अनुसार उपयुक्त फ़ॉर्मैट वाला ऑडियोबुक चुना।',
'id':'Beberapa edisi buku audio tersedia, tetapi file tidak memberikan informasi yang dapat digunakan tentang narator atau durasi buku penuh untuk membedakannya. Chaptarr memilih buku audio dengan format yang sesuai menurut urutan edisi deterministik seperti biasanya.',
'ja':'複数のオーディオブック版がありましたが、ファイルには区別に使えるナレーター情報も書籍全体の再生時間もありませんでした。Chaptarr は通常の決定的な版の順序に従って、形式が一致するオーディオブックを選択しました。',
'ko':'여러 오디오북 판본이 있었지만, 파일에는 서로 구분할 수 있는 내레이터 정보나 책 전체의 재생 시간에 관한 유효한 정보가 없었습니다. Chaptarr는 일반적인 결정적 판본 순서에 따라 형식이 일치하는 오디오북을 선택했습니다.',
'pt-BR':'Havia várias edições de audiolivro, mas o arquivo não forneceu informações utilizáveis sobre o narrador nem sobre a duração do livro completo para diferenciá-las. O Chaptarr selecionou um audiolivro no formato correspondente, seguindo a ordem determinística habitual das edições.',
'vi':'Có nhiều ấn bản sách nói, nhưng tệp không cung cấp thông tin hữu dụng về người dẫn chuyện hoặc thời lượng toàn bộ cuốn sách để phân biệt chúng. Chaptarr đã chọn sách nói đúng định dạng theo thứ tự ấn bản xác định thông thường.',
'zh-Hans':'有多个有声书版本可选，但文件未提供可用于区分它们的旁白者信息或全书时长。Chaptarr 按照通常的确定性版本顺序选择了格式匹配的有声书版本。',
'zh-Hant':'有多個有聲書版本可選，但檔案未提供可用於區分它們的旁白者資訊或全書時長。Chaptarr 依照通常的確定性版本順序選擇了格式相符的有聲書版本。'} .items():
 cand(1078,loc,target,'correction','The source code defines native format as ReadingFormatId matching the audiobook media type (expected ID 2). “Native audiobook” can be mistaken for a language/native-speaker attribute; describe the format match explicitly and retain Chaptarr.', 'high')
cand(1084,'de','Das Format der Ausgabe entspricht dem erkannten Dateityp.','refinement','Edition-Format is an unnatural hybrid; Ausgabe is the existing German term for edition in this matching context.','moderate')
cand(1084,'fr','Le format de l’édition correspond au type de fichier détecté.','refinement','Use the standard French phrase for the edition’s format and the catalog’s established détecté wording.','moderate')
cand(1084,'ko','판본 형식이 발견된 파일 형식과 일치합니다.','correction','Fix the spacing in 발견된 and use 판본, the established Korean term for book edition, instead of the generic 버전.','high')
cand(1099,'pt-BR','Este texto foi considerado, mas não corroborou nem contradisse a correspondência selecionada.','refinement','The source says this text neither supports nor contradicts the result; corroborou preserves “support” more precisely than confirmou.','moderate')
assert not(set(C)&set(H))

# Construct each exact cell review and enforce structural and protected-literal integrity.
source_by={x['sourceId']:x for x in source_rows}; caller_by={x['sourceId']:x for x in caller_rows}; input_cells=[]
for row in source_rows:
 for loc,path in locale_paths.items():
  cur=catalogs[loc][row['sourceId']]
  input_cells.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':row['sourceOrdinal'],'sourceId':row['sourceId'],'locale':loc,
   'source':row['source'],'sourceIdSha256':row['sourceIdSha256'],'sourceTextSha256':row['sourceTextSha256'],'sourceFile':SOURCE,
   'sourceFileGitBlob':source_info['gitBlob'],'sourceFileSha256':source_info['sha256'],'currentTarget':cur,'currentTargetSha256':sha(cur),
   'targetFile':path,'targetFileGitBlob':catalog_info[loc]['gitBlob'],'targetFileSha256':catalog_info[loc]['sha256'],
   'sourcePlaceholders':dict(sorted(ph(row['source']).items())),'currentTargetPlaceholders':dict(sorted(ph(cur).items())),
   'placeholderParity':ph(row['source'])==ph(cur),'sourceMarkup':markup(row['source']),'currentTargetMarkup':markup(cur),
   'markupParity':markup(row['source'])==markup(cur),'sourceIcuSignature':icu(row['source']),'currentIcuSignature':icu(cur),
   'icuParity':icu(row['source'])==icu(cur),'protectedLiterals':row['effectiveProtectedLiterals'],
   'protectedLiteralCurrentFailures':[lit for lit in row['effectiveProtectedLiterals'] if lit not in cur],
   'callerContextSha256':caller_by[row['sourceId']]['callerContextSha256']})
assert len(input_cells)==600
review=[]
for cell in input_cells:
 pos=cell['sourceOrdinal']; loc=cell['locale']; key=(pos,loc); cur=cell['currentTarget']; src=cell['source']; candidate=C.get(key); held=H.get(key)
 if candidate:
  disposition=candidate['kind']; proposed=candidate['target']; final=proposed; rationale=candidate['why']; confidence=candidate['confidence']
 elif held:
  disposition='hold'; proposed=None; final=cur; rationale=held['why']; confidence=held['confidence']
 else:
  disposition='accept-current'; proposed=None; final=cur
  rationale='Reviewed source, current translation, exact caller/matching or loading context, placeholders, and locale script/register; no material semantic or language defect identified.'
  confidence='moderate'
 protected=cell['protectedLiterals']; checks={'sourcePlaceholders':dict(sorted(ph(src).items())),'currentPlaceholders':dict(sorted(ph(cur).items())),
  'finalPlaceholders':dict(sorted(ph(final).items())),'placeholderParity':ph(src)==ph(cur)==ph(final),
  'sourceMarkup':markup(src),'currentMarkup':markup(cur),'finalMarkup':markup(final),'markupParity':markup(src)==markup(cur)==markup(final),
  'sourceIcuSignature':icu(src),'currentIcuSignature':icu(cur),'finalIcuSignature':icu(final),'icuParity':icu(src)==icu(cur)==icu(final),
  'protectedLiteralChecks':[{'literal':lit,'inSource':lit in src,'inCurrentTarget':lit in cur,'inFinalTarget':lit in final} for lit in protected],
  'currentProtectedLiteralFailures':[lit for lit in protected if lit not in cur],
  'finalProtectedLiteralFailures':[lit for lit in protected if lit not in final]}
 assert checks['placeholderParity'] and checks['markupParity'] and checks['icuParity'],(key,checks)
 assert not checks['finalProtectedLiteralFailures'],(key,checks)
 caller=caller_by[cell['sourceId']]; srcrow=source_by[cell['sourceId']]
 review.append({**cell,'primaryDisposition':disposition,'recommendedTarget':proposed,'recommendedTargetSha256':sha(proposed) if proposed is not None else None,
  'finalReviewedTarget':final,'finalReviewedTargetSha256':sha(final),'decisionRationale':rationale,'reviewConfidence':confidence,
  'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'callerContextSha256':caller['callerContextSha256'],
  'callerReferenceCount':caller['callerReferenceCount'],'callerRefs':caller['directCallerReferences'],
  'sourceRegistryContext':{'path':srcrow['sourceRegistryPath'],'fingerprint':srcrow['sourceRegistryFingerprint'],'category':srcrow['registryCategory'],
   'surface':srcrow['registrySurface'],'parameters':srcrow['registryParameters'],'patterns':srcrow['registryPatterns'],'protectedLiterals':srcrow['effectiveProtectedLiterals']},
  'structuralChecks':checks,'semanticInterpretation':'Playful authored loading copy; product-name puns are preserved or held.' if srcrow['sourceId'].startswith('ui.loading.') else 'Book matching provenance detail; user-defined and dynamic values are not introduced.'})
assert len(review)==600 and {(x['sourceOrdinal'],x['locale']) for x in review if x['primaryDisposition'] in ('correction','refinement')}==set(C)
assert {(x['sourceOrdinal'],x['locale']) for x in review if x['primaryDisposition']=='hold'}==set(H)

# Capture the prior/new source boundaries and current input at exact HEAD.
writejl('source-slice.jsonl',source_rows); writejl('caller-context.jsonl',caller_rows); writejl('input-cells.jsonl',input_cells)
writejl('loading-message-pipeline-context.jsonl',loading_runtime); writejl('prior-dispositions-through-W1049.jsonl',prior_live)
writej('w1049-backward-boundary.json',{'sourceOrdinal':1049,'sourceId':w1049_id,'source':source[w1049_id],'rows':back,'all12MatchPreviousFinal':all(x['liveTargetMatchesPreviousFinal'] for x in back)})
writej('w1100-forward-boundary.json',{'sourceOrdinal':1100,'sourceId':w1100_id,'source':source[w1100_id],'rows':forward,'dispositionsAssigned':False})
writej('selected-queue-window.json',{**selection,'sourceFileGitBlob':source_info['gitBlob'],'sourceFileSha256':source_info['sha256'],
 'sourceQueueFileGitBlob':follow_info['gitBlob'],'sourceQueueFileSha256':follow_info['sha256']})
writejl('review-cells.jsonl',review); writejl('correction-candidates.jsonl',[x for x in review if x['primaryDisposition']=='correction'])
writejl('refinement-candidates.jsonl',[x for x in review if x['primaryDisposition']=='refinement']); writejl('holds.jsonl',[x for x in review if x['primaryDisposition']=='hold'])
writejl('protected-literal-integrity.jsonl',[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],
 'sourceTextSha256':x['sourceTextSha256'],'currentTargetSha256':x['currentTargetSha256'],'primaryDisposition':x['primaryDisposition'],
 'recommendedTargetSha256':x['recommendedTargetSha256'],'finalReviewedTargetSha256':x['finalReviewedTargetSha256'],
 'protectedLiterals':x['protectedLiterals'],'checks':x['structuralChecks']} for x in review])
writej('caller-context-summary.json',{'sourceRows':len(caller_rows),'directCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),
 'uniqueDirectCallerFiles':len({r['file'] for x in caller_rows for r in x['directCallerReferences']}),'callerGaps':gaps,'staleRegistryPins':stale,
 'loadingPipelineReferences':len(loading_runtime),'loadingCallerRows':sum(1 for x in caller_rows if x['registryPath']==REGISTRIES['loading']),
 'serverMessageSourceRows':sum(1 for x in source_rows if x['sourceRegistryPath']==REGISTRIES['server']),'serverMessageCallerIndex':caller_index_info})
term_data=json.loads(show(TERMS)); term_map={x['id']:x for x in term_data.get('terms',[])}
writej('internal-terminology-context.json',{'source':terms_info,'records':{k:term_map[k] for k in ['domain.audiobook','domain.ebook'] if k in term_map},
 'readingFormatCodeContext':{'file':'src/NzbDrone.Core/MediaFiles/BookImport/FileMatchingService.cs','lines':[8849,9791,9854],
  'summary':'ReadingFormatMatch compares the candidate ReadingFormatId with expectedRf (3 for ebook, 2 for audiobook); the “native audiobook” phrase is a matching-format concept, not language/native-speaker status.'},
 'notes':['No external dictionary or CLDR source was used.','Native-speaker review remains outstanding.']})
pinned={x['path']:x for x in [source_info,follow_info,caller_index_info,terms_info,*reg_info.values(),*catalog_info.values(),*caller_file_info.values()]}
writej('pinned-files.json',{'exactHead':HEAD,'exactTree':TREE,'fileCount':len(pinned),'files':sorted(pinned.values(),key=lambda x:x['path'])})
writej('input-manifest.json',{'schemaVersion':1,'repository':REPO,'pullRequest':PR,'url':'https://github.com/snapetech-org/ChaptarrNG/pull/190',
 'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'worktreeState':state(),'scope':{'window':'W1050-W1099','positionsAreZeroBasedQueueIndexes':True,
 'positions':[1050,1099],'sourceCount':50,'localeCount':12,'locales':LOCALE_ORDER,'cells':600},'selection':selection,
 'sourceQueueFile':follow_info,'sourceCatalogFile':source_info,'sourceRegistries':reg_info,'localeCatalogs':catalog_info,
 'startSnapshot':'snapshots/start-all-pr-heads.json','afterSourceSelectionSnapshot':'snapshots/after-source-selection-all-pr-heads.json',
 'priorDispositionCountThroughW1049':len(prior_live),'historicalPriorFinalMismatches':len(prior_mismatches),'newPriorHashDriftSincePreviousPacket':len(new_prior_drift),'callerGaps':gaps,'stalePins':stale,
 'nativeSpeakerApproval':False,'browserReviewPerformed':False})

counts=collections.Counter(x['primaryDisposition'] for x in review)
per_locale={loc:dict(collections.Counter(x['primaryDisposition'] for x in review if x['locale']==loc)) for loc in LOCALES}
summary={'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'window':'W1050-W1099','sourceCount':50,'localeCellCount':600,'locales':LOCALE_ORDER,
 'dispositionCounts':dict(sorted(counts.items())),'perLocaleDispositionCounts':per_locale,
 'placeholderMismatchCells':sum(not x['structuralChecks']['placeholderParity'] for x in review),
 'markupMismatchCells':sum(not x['structuralChecks']['markupParity'] for x in review),
 'icuMismatchCells':sum(not x['structuralChecks']['icuParity'] for x in review),
 'currentProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['currentProtectedLiteralFailures']) for x in review),
 'finalProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['finalProtectedLiteralFailures']) for x in review),
 'directCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),'directCallerGaps':len(gaps),'staleRegistryPins':len(stale),
 'priorDispositionRowsThroughW1049':len(prior_live),'priorLiveTargetMismatches':len(prior_mismatches),
 'historicalPriorFinalMismatches':len(prior_mismatches),'newPriorHashDriftSincePreviousPacket':len(new_prior_drift),
 'w1049BoundaryAll12Match':all(x['liveTargetMatchesPreviousFinal'] for x in back),'w1100BoundaryDispositionsAssigned':False,
 'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'overallConfidence':'moderate',
 'limitations':'Static machine-assisted primary review; no qualified native-speaker approval, browser acceptance, or runtime validation is claimed.'}
writej('summary.json',summary)

# Final exact-head reattestation. Other app branches may progress independently; this PR must stay pinned.
final=query_heads('final-seal-reattestation')
finalch=final['pull_requests']['chaptarr']['pullRequest']
assert finalch['state']=='OPEN' and finalch['isDraft'] and finalch['headRefOid']==HEAD and finalch['headRefName']==BRANCH and finalch['headRef']['target']['tree']['oid']==TREE,finalch
writej('snapshots/final-seal-all-pr-heads.json',final)
heads_unchanged={}
for alias,_,_ in prs:
 a=start['pull_requests'][alias]['pullRequest']; b=final['pull_requests'][alias]['pullRequest']
 heads_unchanged[alias]=a['headRefOid']==b['headRefOid'] and a['headRef']['target'].get('tree',{}).get('oid')==b['headRef']['target'].get('tree',{}).get('oid')
writej('final-reattestation.json',{'passed':True,'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'worktreeState':state(),
 'chaptarrPrState':finalch['state'],'chaptarrPrDraft':finalch['isDraft'],'chaptarrPrHead':finalch['headRefOid'],'chaptarrPrTree':finalch['headRef']['target']['tree']['oid'],
 'allSevenHeadsAndTreesUnchangedFromStart':all(heads_unchanged.values()),'perRepositoryUnchangedFromStart':heads_unchanged,
 'startUtc':start['query_started_utc'],'finalUtc':final['query_completed_utc']})
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},state()

readme=f'''# ChaptarrNG PR #190 primary localization review — W1050–W1099

## Exact scope and snapshot

This packet reviews zero-based positions 1050–1099 from `{FOLLOW}`: 50 authored loading and book-matching messages × 12 direct locales = 600 reviewed cells. The selection hash and each source/current target hash are recorded with the caller and registry pins.

PR #190 was open and draft on `{BRANCH}` at head `{HEAD}`, tree `{TREE}` when sealed. The worktree remained clean. Start, post-selection, and final seven-PR snapshots are under `snapshots/`; the final attestation confirms this PR remained at the exact head and records any independent movement in other app PRs.

## Primary review result

{counts['accept-current']} cells were accepted unchanged, {counts['correction']} corrections and {counts['refinement']} refinements were proposed, and {counts['hold']} cells were held for native creative localization. No proposal is applied by this packet. The held cells concern the protected English `Dodge` verb-form joke, which needs locale-native creative adaptation.

The W1078 audiobook fallback text is reviewed against the caller and matcher implementation: `ReadingFormatMatch` compares the expected reading-format ID (3 for ebooks, 2 for audiobooks). The proposals clarify that “native” here means the matching audiobook format, not a native-language property. Protected product names remain exact.

## Structural and continuity checks

All 600 source/current/final rows passed placeholder, markup, ICU-signature, and protected-literal checks. All direct source caller pins resolved at the exact head. The prior ledger preserves 12,600 previous dispositions through W1049. It reattests current hashes against the preceding packet: 195 older rows were already recorded as differing from their historic final target at W1000–1049, and all 195 live hashes remain unchanged since that packet; W1000–1049 finals all match. No prior decision is reopened. The W1049 backward boundary matches all 12 prior finals. W1100 is pinned as forward boundary context only, with no disposition assigned.

This is a static machine-assisted primary review with moderate overall confidence. It is not native-speaker signoff. No browser, runtime, tests, builds, scans, or CI were run.

## Packet contents

- `input-manifest.json`, `selected-queue-window.json`, and `source-slice.jsonl`: exact selection and source pins.
- `input-cells.jsonl`, `pinned-files.json`, and `caller-context.jsonl`: current values/hashes, all 12 catalogs, and caller contexts.
- `review-cells.jsonl`, `correction-candidates.jsonl`, `refinement-candidates.jsonl`, and `holds.jsonl`: primary decisions and proposals.
- `prior-dispositions-through-W1049.jsonl`, `w1049-backward-boundary.json`, `w1100-forward-boundary.json`: decision continuity and boundaries.
- `summary.json`, `final-reattestation.json`, snapshots, `manifest.json`, and `SHA256SUMS`: seal and integrity records.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Final checksums cover every artifact except the manifest and SHA256SUMS; then include the manifest.
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS','make_window.py'})
artifacts=[{'path':str(p.relative_to(OUT)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in files]
manifest={'schemaVersion':1,'packet':'ChaptarrNG PR #190 primary localization review W1050-W1099',
 'sealedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,
 'artifactCountExcludingManifestAndSums':len(artifacts),'artifacts':artifacts,'summary':summary,
 'liveHeadSnapshots':['snapshots/start-all-pr-heads.json','snapshots/after-source-selection-all-pr-heads.json','snapshots/final-seal-all-pr-heads.json']}
writej('manifest.json',manifest)
all_files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in {'SHA256SUMS','make_window.py'})
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT)}\n' for p in all_files),encoding='utf-8')
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1); assert sha((OUT/n).read_bytes())==h,(n,h)
assert len(review)==600 and all(x['primaryDisposition'] in {'accept-current','correction','refinement','hold'} for x in review)
print(json.dumps({'path':str(OUT),'head':HEAD,'tree':TREE,'summary':summary,'priorHashesReattested':len(prior_live),
 'callerReferences':sum(x['callerReferenceCount'] for x in caller_rows),'callerGaps':gaps,'stalePins':stale,
 'boundary1049All12':all(x['liveTargetMatchesPreviousFinal'] for x in back),'allSevenUnchanged':all(heads_unchanged.values()),
 'outputBytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'sealedAtUtc':manifest['sealedAtUtc']},ensure_ascii=False,indent=2))
