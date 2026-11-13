from __future__ import annotations
import collections, datetime, hashlib, json, pathlib, re, subprocess

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1100-1149-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='cc00a297fd221d52169f3c4683ffc1b0ee20871f'
TREE='5987da199f6d5567803ba3ed6c4dd143d1263cdf'
BRANCH='codex/chaptarrng-localization-complete-20261031'
REPO='snapetech-org/chaptarrng'; PR=190
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
SOURCE='src/NzbDrone.Core/Localization/Core/en.json'
FOLLOW='docs/localization/source-followup-20261101.json'
REGISTRIES={'server':'docs/localization/server-message-sources.json','loading':'docs/localization/loading-message-sources.json'}
CALLER_INDEX='docs/localization/server-message-callers.json'
TERMS='docs/localization/terminology.json'
PRIOR=WORK/'docs/pr-evidence/pr190-localization-2026-11-02/window-1050-1099'
PREVIOUS_PRIOR=PRIOR/'primary/prior-dispositions-through-W1049.jsonl'
PREVIOUS_PRIMARY=PRIOR/'primary/review-cells.jsonl'
PREVIOUS_CROSS=PRIOR/'crossreview/cross-review-cells.jsonl'
PREVIOUS_READBACK=PRIOR/'application/full-window-readback.jsonl'

(OUT/'snapshots').mkdir(exist_ok=True)
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def git(*args,binary=False):
 r=subprocess.run(['git','-C',str(WORK),*args],check=True,capture_output=True)
 return r.stdout if binary else r.stdout.decode().strip()
_cache={}
def show(path):
 if path not in _cache: _cache[path]=git('show',f'{HEAD}:{path}',binary=True)
 return _cache[path]
def tracked(path):
 b=show(path); return {'path':path,'gitBlob':git('rev-parse',f'{HEAD}:{path}'),'sha256':sha(b),'bytes':len(b)}
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
def ph(s): return collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def icu(s): return sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
def state(): return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'branch':git('branch','--show-current'),'status':git('status','--porcelain')}
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},state()

# Pin the live queue order across all seven localization PRs at selection.
prs=[('seerr','SeerrNG',418),('chaptarr','chaptarrng',190),('questarr','QuestarrNG',155),('romarr','ROMarrNG',70),('slskr','slskR',204),('slskdn','slskdN',409),('torrent','TorrentNG',243)]
fields='number state isDraft headRefName headRefOid baseRefName baseRefOid updatedAt url headRepository { name owner { login } } headRef { target { oid ... on Commit { tree { oid } } } }'
query='query { '+' '.join(f'{alias}: repository(owner:"snapetech-org",name:"{repo}") {{ pullRequest(number:{num}) {{ {fields} }} }}' for alias,repo,num in prs)+' }'
def snapshot(kind):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 r=subprocess.run(['gh','api','graphql','-f',f'query={query}'],check=True,capture_output=True,text=True)
 end=datetime.datetime.now(datetime.timezone.utc).isoformat(); data=json.loads(r.stdout)
 if data.get('errors'): raise RuntimeError(data['errors'])
 return {'snapshotKind':kind,'queryStartedUtc':start,'queryCompletedUtc':end,'query':query,'pullRequests':data['data']}
start=snapshot('start-before-source-selection')
head=start['pullRequests']['chaptarr']['pullRequest']
assert head['state']=='OPEN' and head['isDraft'] and head['headRefOid']==HEAD and head['headRefName']==BRANCH and head['headRef']['target']['tree']['oid']==TREE,head
writej('snapshots/start-all-pr-heads.json',start)

source=json.loads(show(SOURCE)); follow=json.loads(show(FOLLOW)); queue=follow['currentMissingIds']
assert len(queue)==1210 and sha(canon(queue))==follow['currentMissingIdsSha256']
source_info=tracked(SOURCE); follow_info=tracked(FOLLOW); caller_index_info=tracked(CALLER_INDEX); terms_info=tracked(TERMS)
locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{name}' for loc,name in LOCALES.items()}
catalogs={}; catalog_info={}; ordered_key_hashes={}
for loc,path in locale_paths.items():
 raw=show(path); catalog=json.loads(raw)
 assert set(catalog)==set(source),(loc,'catalog key-set mismatch')
 catalogs[loc]=catalog; catalog_info[loc]=tracked(path); ordered_key_hashes[loc]=sha(canon(list(catalog.keys())))
assert len({len(x) for x in catalogs.values()}|{len(source)})==1
preselection={'exactHead':HEAD,'exactTree':TREE,'sourceFile':source_info,'sourceQueueFile':follow_info,
 'sourceQueueIdCount':len(queue),'sourceQueueHashMatchesRecorded':sha(canon(queue))==follow['currentMissingIdsSha256'],
 'catalogsAttestedBeforeSelection':True,'catalogKeyCount':len(source),'catalogCount':len(catalog_info),
 'catalogs':catalog_info,'allCatalogKeySetsMatchEnglish':all(set(v)==set(source) for v in catalogs.values()),
 'attestedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert preselection['sourceQueueHashMatchesRecorded'] and preselection['allCatalogKeySetsMatchEnglish']
writej('preselection-source-catalog-attestation.json',preselection)
positions=list(range(1100,1150)); selected=queue[1100:1150]
assert len(selected)==50 and len(set(selected))==50
selection={'window':'W1100-W1149','positions':positions,'selectedSourceIds':selected,'currentMissingIdsSha256':sha(canon(queue))}
selectionSnapshot=snapshot('after-source-selection')
post=selectionSnapshot['pullRequests']['chaptarr']['pullRequest']
assert post['state']=='OPEN' and post['isDraft'] and post['headRefOid']==HEAD and post['headRefName']==BRANCH and post['headRef']['target']['tree']['oid']==TREE,post
writej('snapshots/after-source-selection-all-pr-heads.json',selectionSnapshot)
reg_data={k:json.loads(show(path)) for k,path in REGISTRIES.items()}
reg_info={k:tracked(path) for k,path in REGISTRIES.items()}
reg_records={k:{row['id']:row for row in v.get('records',[])} for k,v in reg_data.items()}

# Direct UI references for the 18 non-registry labels in this queue.
UI_CALLER_FILES={
 'ui.author.syncMonitoringHelp':['frontend/src/Author/Edit/EditAuthorModalContent.js'],
 'ui.author.syncMonitoringRequiresRoots':['frontend/src/Author/Edit/EditAuthorModalContent.js'],
 'ui.oauth.windowClosed':['frontend/src/Store/Actions/oAuthActions.js'],
 'ui.oauth.authorizationTimedOut':['frontend/src/Store/Actions/oAuthActions.js'],
 'ui.error.unknown':['frontend/src/Settings/ImportLists/ImportLists/EditImportListModalContent.js'],
 'ui.release.queueFailed':['frontend/src/Store/Actions/releaseActions.js'],
 'ui.dialog.label':['frontend/src/Components/Modal/ModalContent.js'],
}
TASK_MAP='frontend/src/Utilities/Localization/scheduled-task-labels.json'
TASK_RENDER='frontend/src/Utilities/Localization/scheduled-task-labels.cjs'
ui_display_files=[TASK_MAP,TASK_RENDER]
caller_file_info={}; source_rows=[]; caller_rows=[]; gaps=[]; stale=[]; source_records={}
def line_pin(path,line,kind,registry=None):
 lines=show(path).decode('utf-8').splitlines()
 if line<1 or line>len(lines): return None
 text=lines[line-1]
 row={'file':path,'line':line,'lineText':text.strip(),'lineSha256':sha(text.strip()),'fileGitBlob':git('rev-parse',f'{HEAD}:{path}'),'fileSha256':sha(show(path)),
      'contextBefore':[x.strip() for x in lines[max(0,line-4):line-1]],'contextAfter':[x.strip() for x in lines[line:min(len(lines),line+3)]],
      'referenceKind':kind}
 if registry: row.update(registry)
 caller_file_info[path]=tracked(path)
 return row

task_records=json.loads(show(TASK_MAP))
for ordinal,sid in enumerate(selected,1100):
 if sid.startswith('server.message.'): kind='server'
 elif sid.startswith('ui.loading.'): kind='loading'
 elif sid.startswith('ui.'): kind='ui'
 else: raise AssertionError(('unclassified source id',ordinal,sid))
 reg=None if kind=='ui' else reg_records[kind].get(sid)
 if kind!='ui': assert reg and reg.get('source')==source[sid],(ordinal,sid)
 protected=list(reg.get('protectedLiterals',[])) if reg else []
 source_rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'sourceIdSha256':sha(sid),'sourceTextSha256':sha(source[sid]),
  'sourceCatalogPath':SOURCE,'sourceCatalogGitBlob':source_info['gitBlob'],'sourceCatalogSha256':source_info['sha256'],
  'sourceRegistryPath':REGISTRIES[kind] if reg else None,'sourceRegistryGitBlob':reg_info[kind]['gitBlob'] if reg else None,
  'sourceRegistrySha256':reg_info[kind]['sha256'] if reg else None,'sourceRegistryFingerprint':reg.get('sourceFingerprint') if reg else None,
  'effectiveProtectedLiterals':protected,'registryCategory':reg.get('category') if reg else None,'registrySurface':reg.get('surface') if reg else None,
  'registryParameters':reg.get('parameters',[]) if reg else [],'registryPatterns':reg.get('patterns',[]) if reg else [],
  'sourceTemplates':reg.get('sourceTemplates',[]) if reg else [],'uiCallerClassification':'direct frontend localization key' if kind=='ui' else None})
 refs=[]
 if reg:
  for pin in reg.get('callsites',[]):
   path=pin['file']; lines=show(path).decode('utf-8').splitlines(); n=pin['line']; cur=lines[n-1] if 1<=n<=len(lines) else None
   exact=cur is not None and cur.strip()==pin.get('sourceLine','').strip() and sha(cur.strip())==pin.get('sourceLineSha256')
   if exact: hits=[n]
   else:
    hits=[i+1 for i,line in enumerate(lines) if sid in line]
    stale.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':path,'registryLine':n,'reason':'registry source line differs at exact head'})
   for ln in hits:
    p=line_pin(path,ln,'registry callsite',{'registryLine':n,'registryPinExact':exact,'registrySourceLine':pin.get('sourceLine'),'registrySourceLineSha256':pin.get('sourceLineSha256'),
      'category':pin.get('category'),'surface':pin.get('surface'),'kind':pin.get('kind'),'enum':pin.get('enum'),'member':pin.get('member')})
    if p: refs.append(p)
 elif sid in UI_CALLER_FILES:
  for path in UI_CALLER_FILES[sid]:
   lines=show(path).decode('utf-8').splitlines()
   for ln,line in enumerate(lines,1):
    if sid in line:
     p=line_pin(path,ln,'direct UI localization-key caller')
     if p: refs.append(p)
 elif sid.startswith('ui.task.'):
  record=next((x for x in task_records if x['id']==sid),None); assert record and record['source']==source[sid],(sid,record)
  lines=show(TASK_MAP).decode('utf-8').splitlines()
  for ln,line in enumerate(lines,1):
   if sid in line:
    p=line_pin(TASK_MAP,ln,'scheduled-task label registry entry',{'taskName':record['name'],'labelId':sid,'sourceLabel':record['source']})
    if p: refs.append(p)
  render_lines=show(TASK_RENDER).decode('utf-8').splitlines()
  for ln,line in enumerate(render_lines,1):
   if 'translateWithFallback(record.id, record.source)' in line:
    p=line_pin(TASK_RENDER,ln,'scheduled-task localization display path',{'taskName':record['name'],'labelId':sid,'sourceLabel':record['source']})
    if p: refs.append(p)
 else: gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no caller pin strategy'})
 refs.sort(key=lambda x:(x['file'],x['line'],x['referenceKind']))
 if not refs: gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no exact direct/display caller found'})
 caller_rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'directCallerReferences':refs,'callerReferenceCount':len(refs),
  'callerContextSha256':sha(canon(refs)),'callerReferenceStatus':'pinned' if refs else 'gap','protectedLiterals':protected,
  'registryCategory':reg.get('category') if reg else None,'registrySurface':reg.get('surface') if reg else None,
  'enumOrParameterContext':[{'enum':x.get('enum'),'member':x.get('member'),'kind':x.get('kind')} for x in reg.get('callsites',[])] if reg else []})
assert len(source_rows)==len(caller_rows)==50 and not gaps and not stale,(gaps,stale)

# Previous evidence integrity and readback continuity, including the W1050 Dodge pun hold.
def verify_sums(base, checksum_path):
 rows=[]
 for line in checksum_path.read_text().splitlines():
  h,name=line.split('  ',1); file=base/name
  assert file.is_file() and sha(file.read_bytes())==h,(str(file),h)
  rows.append({'path':str(file),'sha256':h})
 return rows
prior_primary_sum=verify_sums(PRIOR/'primary',PRIOR/'primary/SHA256SUMS')
prior_cross_sum=verify_sums(PRIOR/'crossreview',PRIOR/'crossreview/SHA256SUMS')
prior_window_sum=verify_sums(WORK,PRIOR/'SHA256SUMS')
prior1049=[json.loads(line) for line in PREVIOUS_PRIOR.read_text().splitlines()]
primary1050=[json.loads(line) for line in PREVIOUS_PRIMARY.read_text().splitlines()]
cross1050=[json.loads(line) for line in PREVIOUS_CROSS.read_text().splitlines()]
readback1050=[json.loads(line) for line in PREVIOUS_READBACK.read_text().splitlines()]
assert len(prior1049)==12600 and len(primary1050)==len(cross1050)==len(readback1050)==600
maps=[{(r['sourceOrdinal'],r['locale']):r for r in rows} for rows in (primary1050,cross1050,readback1050)]
assert all(len(m)==600 for m in maps)
prior_rows=[]
for old in prior1049:
 live=catalogs[old['locale']].get(old['sourceId']); live_hash=sha(live) if live is not None else None
 prior_rows.append({**old,'liveCurrentTargetSha256':live_hash,'liveTargetMatchesHistoricFinal':live_hash==old['priorFinalTargetSha256'],
  'noDriftSinceW1050PreviousPrimary':live_hash==old.get('liveCurrentTargetSha256')})
for p,c,r in zip(primary1050,cross1050,readback1050):
 key=(p['sourceOrdinal'],p['locale']); assert key==(c['sourceOrdinal'],c['locale'])==(r['sourceOrdinal'],r['locale'])
 live=catalogs[p['locale']][p['sourceId']]; live_hash=sha(live)
 assert p['sourceId']==c['sourceId']==r['sourceId'] and p['sourceTextSha256']==c['sourceSha256']
 assert c['crossReviewedTargetSha256']==r['actualTargetSha256'] and r['matchesExpected']
 assert live_hash==r['actualTargetSha256'],(key,live_hash,r['actualTargetSha256'])
 prior_rows.append({'sourceOrdinal':p['sourceOrdinal'],'sourceId':p['sourceId'],'locale':p['locale'],'sourceTextSha256':p['sourceTextSha256'],
  'priorDisposition':p['primaryDisposition'],'priorCrossReviewDisposition':c['independentDisposition'],
  'priorInputTargetSha256':p['currentTargetSha256'],'priorFinalTargetSha256':r['actualTargetSha256'],
  'liveCurrentTargetSha256':live_hash,'liveTargetMatchesHistoricFinal':live_hash==r['actualTargetSha256'],
  'noDriftSinceW1050PreviousPrimary':live_hash==r['actualTargetSha256'],
  'sourcePacket':'ChaptarrNG PR #190 W1050-W1099 primary, cross-review, and exact-hash application readback',
  'primaryDisposition':p['primaryDisposition'],'crossReviewDisposition':c['independentDisposition'],
  'independentAssessment':c['independentAssessment'],'readbackMatchesExpected':r['matchesExpected'],
  'priorHoldPreserved':p['primaryDisposition']=='hold' and c['independentDisposition']=='confirm-hold' if p['primaryDisposition']=='hold' else None})
assert len(prior_rows)==13200 and {(x['sourceOrdinal'],x['locale']) for x in prior_rows}=={(i,l) for i in range(1100) for l in LOCALES}
old_mismatches=[x for x in prior_rows if not x['liveTargetMatchesHistoricFinal']]
new_drift=[x for x in prior_rows if not x['noDriftSinceW1050PreviousPrimary']]
assert len(old_mismatches)==195 and not new_drift, (len(old_mismatches),len(new_drift))
w1050_holds=[x for x in prior_rows if x.get('sourceOrdinal')==1054 and x.get('locale') in LOCALES]
# Check the exact W1050 source identity from prior review instead of assuming the window boundary.
source1050='ui.loading.dodgeBooks'
dodge_rows=[x for x in prior_rows if x['sourceOrdinal']==1054 and x['sourceId']==source1050]
assert len(dodge_rows)==12 and all(x['priorDisposition']=='hold' and x['priorCrossReviewDisposition']=='confirm-hold' and x['liveTargetMatchesHistoricFinal'] for x in dodge_rows),dodge_rows
writejl('prior-dispositions-through-W1099.jsonl',sorted(prior_rows,key=lambda x:(x['sourceOrdinal'],list(LOCALES).index(x['locale']))))
writej('prior-evidence-reattestation.json',{'priorEvidenceChecksumCounts':{'window':len(prior_window_sum),'primary':len(prior_primary_sum),'crossreview':len(prior_cross_sum)},
 'previousPrimaryRowsThroughW1049':len(prior1049),'previousAppliedW1050Rows':600,'combinedPriorRowsThroughW1099':len(prior_rows),
 'historicFinalHashMismatches':len(old_mismatches),'newDriftSincePriorPrimaryPacket':len(new_drift),
 'w1050ReadbacksAll600MatchCurrent':all(x['liveTargetMatchesHistoricFinal'] for x in prior_rows if x['sourceOrdinal']>=1050),
 'w1050DodgePunCells':len(dodge_rows),'w1050DodgePunHoldsPreserved':all(x['priorHoldPreserved'] for x in dodge_rows),
 'previousPacketSource':str(PRIOR),'verifiedChecksumFiles':prior_window_sum+prior_primary_sum+prior_cross_sum})

# W1099 backward boundary and W1150 forward boundary, pinned across all locales.
queue_hash=sha(canon(queue)); w1099_id=queue[1099]; w1150_id=queue[1150]
w1099=[]; w1150=[]
prior_map={(r['sourceOrdinal'],r['locale']):r for r in prior_rows}
for loc,path in LOCALES.items():
 old=prior_map[(1099,loc)]; curr=catalogs[loc][w1099_id]
 w1099.append({'sourceOrdinal':1099,'sourceId':w1099_id,'source':source[w1099_id],'sourceTextSha256':sha(source[w1099_id]),'locale':loc,
  'previousDisposition':old['priorDisposition'],'previousCrossReviewDisposition':old.get('priorCrossReviewDisposition'),
  'previousFinalTargetSha256':old['priorFinalTargetSha256'],'currentTarget':curr,'currentTargetSha256':sha(curr),
  'matchesPreviousFinal':sha(curr)==old['priorFinalTargetSha256'],'targetFile':locale_paths[loc],'targetFileGitBlob':catalog_info[loc]['gitBlob']})
 curr=catalogs[loc][w1150_id]
 w1150.append({'sourceOrdinal':1150,'sourceId':w1150_id,'source':source[w1150_id],'sourceTextSha256':sha(source[w1150_id]),'locale':loc,
  'currentTarget':curr,'currentTargetSha256':sha(curr),'targetFile':locale_paths[loc],'targetFileGitBlob':catalog_info[loc]['gitBlob'],
  'scope':'forward boundary context only; no W1150 disposition assigned'})
assert all(x['matchesPreviousFinal'] for x in w1099)

# Proposals from source/caller/context review. Each changed value is exact-hash pinned below.
C={}; H={}
def cand(pos,loc,target,kind,why,confidence='moderate'):
 C[(pos,loc)]={'target':target,'kind':kind,'why':why,'confidence':confidence}
def hold(pos,loc,why,confidence='low'): H[(pos,loc)]={'why':why,'confidence':confidence}
# W1111: use natural cross-format wording and target-language sentence punctuation.
cand(1111,'hi','सक्षम होने पर, निगरानी में रखी गई किताबें तुरंत अलग-अलग प्रारूपों में सिंक हो जाती हैं। इससे खोज शुरू नहीं होती।','correction','The current wording says “through formats,” uses English-style punctuation, and is less direct; the proposal says books sync across formats and this does not start a search.','high')
cand(1111,'id','Saat diaktifkan, buku yang dipantau langsung disinkronkan antarformat. Ini tidak memicu pencarian.','correction','The current “melalui format” means through formats and the second sentence starts lowercase. Antarformat states across formats in natural Indonesian UI copy.','high')
cand(1111,'ja','有効にすると、監視対象の書籍がすぐに形式間で同期されます。検索は実行されません。','correction','The current wording says format-mediated syncing and “起動” (launch) a search; the proposal describes sync across formats and does not run a search.','high')
cand(1111,'ko','활성화하면 모니터링 중인 책이 형식 간에 즉시 동기화됩니다. 검색을 실행하지는 않습니다.','correction','The current spacing and sentence join are malformed, and “through formats” does not express across formats.','high')
cand(1111,'vi','Khi bật, sách được theo dõi sẽ đồng bộ ngay giữa các định dạng. Việc này không kích hoạt tìm kiếm.','correction','The current “qua các định dạng” is a literal “through formats,” and the second sentence begins lowercase.','high')
cand(1111,'zh-Hans','启用后，受监控的书籍会立即在不同格式之间同步。此操作不会触发搜索。','correction','The current Chinese punctuation is ASCII and the phrase “在格式上” is awkward; the proposal expresses across formats with standard punctuation.','high')
cand(1111,'zh-Hant','啟用後，受監控的書籍會立即在不同格式間同步。此操作不會觸發搜尋。','correction','The current Chinese punctuation is ASCII and “在格式上” is awkward; the proposal expresses across formats with standard Traditional Chinese punctuation.','high')
# W1113: complete OAuth authorization, not generic permission/window completion.
cand(1113,'de','Das OAuth-Fenster wurde geschlossen, bevor die Autorisierung abgeschlossen war.','correction','The source concerns OAuth authorization; Genehmigung is generic approval, and the current sentence also omits an article before Fenster.','moderate')
cand(1113,'hi','प्राधिकरण पूरा होने से पहले OAuth विंडो बंद हो गई।','correction','The current Hindi reverses the event and says the window closed before it ended; this proposal preserves that authorization was not completed.','high')
cand(1113,'id','Jendela OAuth ditutup sebelum otorisasi selesai.','correction','Izin means permission; otorisasi is the more precise OAuth authorization term.','moderate')
cand(1113,'ja','OAuth ウィンドウは認可が完了する前に閉じられました。','correction','認可 is the OAuth authorization term; 許可 means permission and is less exact in this callback flow.','moderate')
cand(1113,'ko','OAuth 승인이 완료되기 전에 창이 닫혔습니다.','correction','허가 is closer to permission; 승인이 완료되다 states the OAuth authorization step did not finish.','moderate')
cand(1113,'pt-BR','A janela do OAuth foi fechada antes da conclusão da autorização.','correction','The current wording “antes da autorização concluída” is not grammatical Portuguese; the proposal uses a natural completion clause.','high')
cand(1113,'vi','Cửa sổ OAuth đã đóng trước khi quá trình ủy quyền hoàn tất.','correction','The current word order is ungrammatical and giấy phép means a permit; ủy quyền expresses OAuth authorization.','high')
# W1115-W1117: error wording and accessible dialog label.
cand(1115,'es','Se produjo un error desconocido.','correction','The current Spanish word order is unnatural for a user-facing error.','moderate')
cand(1115,'fr','Une erreur inconnue s’est produite.','refinement','This is the standard concise French error-state construction.','moderate')
cand(1115,'hi','एक अज्ञात त्रुटि हुई।','correction','गलती means a mistake; त्रुटि is the appropriate term for a software error.','high')
cand(1115,'id','Terjadi kesalahan yang tidak diketahui.','correction','The current word order is unnatural; this is the natural Indonesian construction for an unknown error.','high')
cand(1116,'hi','डाउनलोड कतार में नहीं जोड़ा जा सका।','correction','The current “विफल रहा” leaves an unclear masculine subject; the proposal gives a natural impersonal failure message.','moderate')
for loc,target in {
 'ar':'مربع حوار','es':'Cuadro de diálogo','fr':'Boîte de dialogue','hi':'संवाद बॉक्स','id':'Kotak dialog','ja':'ダイアログ','ko':'대화 상자','pt-BR':'Caixa de diálogo','vi':'Hộp thoại','zh-Hans':'对话框','zh-Hant':'對話方塊'}.items():
 cand(1117,loc,target,'correction','This string labels an accessible element with role="dialog". The current bare term can read as conversation; use the locale’s UI dialog-box term.','moderate')
# W1120/W1126 scheduled-task labels.
cand(1120,'hi','एप्लिकेशन अपडेट की जाँच','refinement','“अपडेट” is the natural product-UI term here; चेक is an avoidable English loan in the current label.','moderate')
cand(1126,'de','Hardcover-Bibliothekssynchronisierung','refinement','Join the proper name to Bibliothek with the standard German compound hyphen and use a compact task label.','moderate')
cand(1126,'ja','Hardcover ライブラリ同期','refinement','同期 is the natural Japanese label for a sync task; シンク is an English transliteration that reads as a device/object.','moderate')
# OAuth provider errors and formal user guidance.
cand(1134,'ar','لم تُرجِع AudioBookShelf مفتاح API.','correction','The current verb form is ungrammatical for the feminine service name AudioBookShelf.','high')
cand(1134,'ja','AudioBookShelf は API キーを返しませんでした。','refinement','The current plain negative is less consistent with Japanese user-facing error notices; use polite past-negative form.','moderate')
cand(1135,'ar','لم تُرجِع AudioBookShelf رمز وصول صالحًا.','correction','The current verb form is ungrammatical and “الصحيح” means correct rather than valid; preserve AudioBookShelf.','high')
cand(1135,'hi','AudioBookShelf ने मान्य एक्सेस टोकन नहीं लौटाया।','correction','The current Hindi uses present tense for a completed response; the source describes a missing value in a completed API response.','moderate')
cand(1136,'ar','لم تُرجِع AudioBookShelf أي ملفات تعريف ارتباط لجلسة OIDC.','correction','The current Arabic verb form is ungrammatical and omits the OIDC session relationship; the proposal preserves both protected literals.','high')
cand(1136,'ja','AudioBookShelf は OIDC セッション用の Cookie を一つも返しませんでした。','refinement','Use a polite past-negative form and state explicitly that no cookie was returned for the OIDC session.','moderate')
# Use formal German and Spanish customer guidance in provider authorization errors.
cand(1140,'de','Die Autorisierung des Anbieters ist abgelaufen. Bitte melden Sie sich erneut an.','refinement','This is user-facing error guidance; use the catalog’s formal Sie register rather than the informal “melde dich”.','moderate')
cand(1140,'es','La autorización del proveedor ha caducado. Inicie sesión de nuevo.','refinement','Match the formal user-directed register used by neighboring provider-error guidance.','moderate')
cand(1140,'hi','प्रदाता का प्राधिकरण समाप्त हो गया है। कृपया फिर से साइन इन करें।','refinement','Use standard Hindi punctuation and the more precise authorization term प्राधिकरण.','moderate')
cand(1141,'de','AudioBookShelf OIDC hat nicht weitergeleitet (Status {value0}). Stellen Sie sicher, dass OpenID Connect auf Ihrem AudioBookShelf-Server aktiviert und konfiguriert ist.','refinement','The source gives user-facing configuration guidance; use formal Sie address consistently with neighboring German error messages.','moderate')
cand(1141,'vi','AudioBookShelf OIDC không chuyển hướng (trạng thái {value0}). Hãy đảm bảo OpenID Connect được bật và cấu hình trên máy chủ AudioBookShelf của bạn.','correction','The current passive says OIDC was not redirected, instead of saying the OIDC flow did not redirect; retain the placeholder and exact product literals.','moderate')
# W1143 contains a parameter-name literal; make the missing-value message grammatical without changing it.
for loc,target in {
 'ar':'المتغير requestTokenSecret غير موجود.','de':'requestTokenSecret fehlt.','ja':'requestTokenSecret がありません。','ko':'requestTokenSecret이 없습니다.','zh-Hans':'缺少 requestTokenSecret。','zh-Hant':'缺少 requestTokenSecret。'}.items():
 cand(1143,loc,target,'correction','The current translation is ungrammatical or means “lost”; state that the exact protected requestTokenSecret parameter is missing.','high')
# W1144: simplify duplicated/lowercase “id” forms while retaining the Hardcover product name.
cand(1144,'ar','معرّف Hardcover {value0} غير صالح: {value1}','correction','The current Arabic repeats id twice; this keeps the object and placeholder order clear while preserving Hardcover.','moderate')
cand(1144,'de','Die Hardcover-ID {value0} ist ungültig: {value1}','correction','Use the standard German compound ID rather than the lowercase English id suffix.','moderate')
cand(1144,'id','ID Hardcover {value0} tidak valid: {value1}','correction','The current Indonesian duplicates id; use one clear ID label while preserving both values and Hardcover.','moderate')
# W1145: distinguish session expiry from completion and make retry guidance idiomatic.
for loc,target,kind,why in [
 ('de','Die OIDC-Sitzung ist abgelaufen. Bitte versuchen Sie es erneut.','correction','Abgeschlossen means completed, not expired; this also uses formal Sie.'),
 ('es','La sesión de OIDC ha caducado. Inténtelo de nuevo.','correction','The current wording says the session ended; caducado precisely denotes an expired session and the imperative is formal.'),
 ('fr','La session OIDC a expiré. Veuillez réessayer.','correction','The current French lacks a natural article and has non-native retry wording.'),
 ('hi','OIDC सत्र की अवधि समाप्त हो गई है। कृपया फिर से कोशिश करें।','refinement','Use Hindi sentence punctuation and a natural expiry construction.'),
 ('id','Sesi OIDC telah kedaluwarsa. Silakan coba lagi.','correction','The current phrasing says the session ended; kedaluwarsa states that it expired.'),
 ('ja','OIDC セッションの有効期限が切れました。もう一度お試しください。','correction','The current wording says the session ended and uses nonstandard full stops; state expiry and retry politely.'),
 ('pt-BR','A sessão do OIDC expirou. Tente novamente.','correction','The current word order is ungrammatical Portuguese; use a natural retry notice.'),
 ('vi','Phiên OIDC đã hết hạn. Vui lòng thử lại.','correction','The current wording is ungrammatical; the proposal states that the session expired and gives concise polite retry guidance.'),
 ('zh-Hant','OIDC 工作階段已過期。請再試一次。','correction','逾時 means timed out, while the source says the session expired; use 已過期.')]:
 cand(1145,loc,target,kind,why,'moderate')
# W1147: express a completed decode failure with target-language aspect and natural source-file order.
for loc,target,why in [
 ('es','m4b-tool/ffmpeg no pudo decodificar uno de los archivos de audio de origen.','The imperfect podía is less direct for this completed decode failure; the proposal uses a simple past and preserves both tool names.'),
 ('fr','m4b-tool/ffmpeg n’a pas pu décoder l’un des fichiers audio source.','The current imperfect ne pouvait pas is less direct for this completed failure; use passé composé and preserve tool names.'),
 ('hi','m4b-tool/ffmpeg स्रोत ऑडियो फ़ाइलों में से एक को डिकोड नहीं कर सका।','The current phrasing uses an awkward ability construction; this gives the completed failure with the exact tool name.'),
 ('pt-BR','m4b-tool/ffmpeg não conseguiu decodificar um dos arquivos de áudio de origem.','The current podia is less direct for a completed decode failure; use a natural resultative verb and preserve tool names.'),
 ('zh-Hans','m4b-tool/ffmpeg 无法解码其中一个源音频文件。','Reorder “one of the source audio files” into the natural Chinese construction and preserve exact tool literals.'),
 ('zh-Hant','m4b-tool/ffmpeg 無法解碼其中一個來源音訊檔案。','Use the natural Traditional Chinese “one of the source audio files” construction and preserve exact tool literals.')]:
 cand(1147,loc,target,'correction',why,'moderate')
assert not(set(C)&set(H))

# Build detailed per-cell review and structural checks.
source_by={x['sourceId']:x for x in source_rows}; caller_by={x['sourceId']:x for x in caller_rows}
review=[]
for pos,sid in enumerate(selected,1100):
 src=source[sid]; srcrow=source_by[sid]; caller=caller_by[sid]
 for loc,path in LOCALES.items():
  cur=catalogs[loc][sid]; candidate=C.get((pos,loc)); held=H.get((pos,loc))
  if candidate:
   disp=candidate['kind']; proposed=candidate['target']; final=proposed; rationale=candidate['why']; confidence=candidate['confidence']
  elif held:
   disp='hold'; proposed=None; final=cur; rationale=held['why']; confidence=held['confidence']
  else:
   disp='accept-current'; proposed=None; final=cur
   rationale='Reviewed against the exact English source, pinned caller/display path, neighboring catalog usage, locale register, placeholders, markup, ICU signature, and protected literals; no material defect identified.'
   confidence='moderate'
  checks={'sourcePlaceholders':dict(sorted(ph(src).items())),'currentPlaceholders':dict(sorted(ph(cur).items())),'finalPlaceholders':dict(sorted(ph(final).items())),
   'placeholderParity':ph(src)==ph(cur)==ph(final),'sourceMarkup':markup(src),'currentMarkup':markup(cur),'finalMarkup':markup(final),
   'markupParity':markup(src)==markup(cur)==markup(final),'sourceIcuSignature':icu(src),'currentIcuSignature':icu(cur),'finalIcuSignature':icu(final),
   'icuParity':icu(src)==icu(cur)==icu(final),'protectedLiteralChecks':[{'literal':lit,'inSource':lit in src,'inCurrentTarget':lit in cur,'inFinalTarget':lit in final} for lit in srcrow['effectiveProtectedLiterals']],
   'currentProtectedLiteralFailures':[lit for lit in srcrow['effectiveProtectedLiterals'] if lit not in cur],
   'finalProtectedLiteralFailures':[lit for lit in srcrow['effectiveProtectedLiterals'] if lit not in final]}
  assert checks['placeholderParity'] and checks['markupParity'] and checks['icuParity'],((pos,loc),checks)
  assert not checks['finalProtectedLiteralFailures'],((pos,loc),checks)
  review.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':pos,'sourceId':sid,'locale':loc,'source':src,'sourceIdSha256':sha(sid),'sourceTextSha256':sha(src),
   'sourceFile':SOURCE,'sourceFileGitBlob':source_info['gitBlob'],'sourceFileSha256':source_info['sha256'],'currentTarget':cur,'currentTargetSha256':sha(cur),
   'targetFile':path,'targetFileGitBlob':catalog_info[loc]['gitBlob'],'targetFileSha256':catalog_info[loc]['sha256'],
   'primaryDisposition':disp,'recommendedTarget':proposed,'recommendedTargetSha256':sha(proposed) if proposed is not None else None,
   'finalReviewedTarget':final,'finalReviewedTargetSha256':sha(final),'decisionRationale':rationale,'reviewConfidence':confidence,
   'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'callerContextSha256':caller['callerContextSha256'],'callerReferenceCount':caller['callerReferenceCount'],
   'callerRefs':caller['directCallerReferences'],'protectedLiterals':srcrow['effectiveProtectedLiterals'],'structuralChecks':checks,
   'semanticInterpretation':'UI status/help, OAuth, task label, or accessible dialog text.' if sid.startswith('ui.') else 'Exact registered server-message caller and error/diagnostic context.'})
assert len(review)==600 and len(C)==sum(1 for r in review if r['primaryDisposition'] in ('correction','refinement'))
assert len(H)==sum(1 for r in review if r['primaryDisposition']=='hold')

writejl('source-slice.jsonl',source_rows); writejl('caller-context.jsonl',caller_rows); writejl('review-cells.jsonl',review)
writejl('correction-candidates.jsonl',[r for r in review if r['primaryDisposition']=='correction'])
writejl('refinement-candidates.jsonl',[r for r in review if r['primaryDisposition']=='refinement'])
writejl('holds.jsonl',[r for r in review if r['primaryDisposition']=='hold'])
writejl('protected-literal-integrity.jsonl',[{'sourceOrdinal':r['sourceOrdinal'],'sourceId':r['sourceId'],'locale':r['locale'],'currentTargetSha256':r['currentTargetSha256'],
 'primaryDisposition':r['primaryDisposition'],'recommendedTargetSha256':r['recommendedTargetSha256'],'finalReviewedTargetSha256':r['finalReviewedTargetSha256'],
 'protectedLiterals':r['protectedLiterals'],'checks':r['structuralChecks']} for r in review])
writejl('prior-dispositions-through-W1099.jsonl',sorted(prior_rows,key=lambda x:(x['sourceOrdinal'],list(LOCALES).index(x['locale']))))
writej('w1099-backward-boundary.json',{'sourceOrdinal':1099,'sourceId':w1099_id,'source':source[w1099_id],'rows':w1099,'all12MatchPreviousFinal':all(x['matchesPreviousFinal'] for x in w1099)})
writej('w1150-forward-boundary.json',{'sourceOrdinal':1150,'sourceId':w1150_id,'source':source[w1150_id],'rows':w1150,'dispositionsAssigned':False})
writej('selected-queue-window.json',{'window':'W1100-W1149','positions':positions,'selectedSourceIds':selected,'currentMissingIdsSha256':queue_hash,
 'sourceFileGitBlob':source_info['gitBlob'],'sourceFileSha256':source_info['sha256'],'sourceQueueFileGitBlob':follow_info['gitBlob'],'sourceQueueFileSha256':follow_info['sha256']})
writej('caller-context-summary.json',{'sourceRows':len(caller_rows),'directCallerReferences':sum(r['callerReferenceCount'] for r in caller_rows),
 'uniqueDirectCallerFiles':len({p['file'] for r in caller_rows for p in r['directCallerReferences']}),'callerGaps':gaps,'staleRegistryPins':stale,
 'uiRows':sum(1 for r in source_rows if r['sourceId'].startswith('ui.')),'serverRows':sum(1 for r in source_rows if r['sourceId'].startswith('server.message.'))})
term_data=json.loads(show(TERMS));
writej('terminology-and-locale-notes.json',{'terminologySource':terms_info,'cataloguedTermCount':len(term_data.get('terms',[])),
 'notes':['Protected literals are enforced from the exact source registry record at this head.','German provider/OAuth error guidance was checked against formal Sie register; source UI/task labels were judged in their display context.',
 'The W1050 Dodge verb-form pun remains on hold in all 12 locales; no creative translation decision is inferred here.','No external dictionary or native-speaker source was used.']})
writej('catalog-pins.json',{'exactHead':HEAD,'exactTree':TREE,'catalogKeyCount':len(source),'orderedCatalogKeysSha256':ordered_key_hashes,
 'catalogs':catalog_info,'allKeySetsIdentical':True})
files={x['path']:x for x in [source_info,follow_info,caller_index_info,terms_info,*reg_info.values(),*catalog_info.values(),*caller_file_info.values()]}
writej('pinned-files.json',{'exactHead':HEAD,'exactTree':TREE,'fileCount':len(files),'files':sorted(files.values(),key=lambda x:x['path'])})

counts=collections.Counter(r['primaryDisposition'] for r in review)
per_locale={loc:dict(collections.Counter(r['primaryDisposition'] for r in review if r['locale']==loc)) for loc in LOCALES}
summary={'repository':REPO,'pullRequest':PR,'state':head['state'],'isDraft':head['isDraft'],'branch':BRANCH,'head':HEAD,'tree':TREE,
 'window':'W1100-W1149','zeroBasedQueuePositions':[1100,1149],'sourceCount':50,'localeCount':12,'cellCount':600,'catalogKeyCount':len(source),
 'dispositionCounts':dict(sorted(counts.items())),'proposalKindCounts':dict(sorted(collections.Counter(x['kind'] for x in C.values()).items())),
 'proposedValueChanges':len(C),'holdCellCount':len(H),'perLocaleDispositionCounts':per_locale,
 'directCallerReferences':sum(r['callerReferenceCount'] for r in caller_rows),'callerFiles':len({p['file'] for r in caller_rows for p in r['directCallerReferences']}),
 'callerGaps':len(gaps),'staleRegistryPins':len(stale),'placeholderMismatchCells':sum(not r['structuralChecks']['placeholderParity'] for r in review),
 'markupMismatchCells':sum(not r['structuralChecks']['markupParity'] for r in review),'icuMismatchCells':sum(not r['structuralChecks']['icuParity'] for r in review),
 'currentProtectedLiteralFailureCells':sum(bool(r['structuralChecks']['currentProtectedLiteralFailures']) for r in review),
 'finalProtectedLiteralFailureCells':sum(bool(r['structuralChecks']['finalProtectedLiteralFailures']) for r in review),
 'priorDispositionRowsThroughW1099':len(prior_rows),'priorLiveFinalHashMismatches':len(old_mismatches),'newPriorHashDrift':len(new_drift),
 'w1050DodgeHoldCountPreserved':len(dodge_rows),'w1050DodgeHoldsPreserved':all(x['priorHoldPreserved'] for x in dodge_rows),
 'w1099BoundaryAll12Match':all(x['matchesPreviousFinal'] for x in w1099),'w1150BoundaryPinned':len(w1150)==12,
 'allSevenPrsSnapshottedAtSelection':True,'nativeSpeakerApproval':False,'headedBrowserAcceptance':False,'overallConfidence':'moderate',
 'limitations':'Static machine-assisted primary review. No native-speaker approval, browser acceptance, or runtime validation is claimed; the prior W1050 Dodge pun remains on hold.'}
writej('summary.json',summary)

# Final exact-head and worktree seal check.
final=snapshot('final-seal-reattestation'); finalch=final['pullRequests']['chaptarr']['pullRequest']
assert finalch['state']=='OPEN' and finalch['isDraft'] and finalch['headRefOid']==HEAD and finalch['headRefName']==BRANCH and finalch['headRef']['target']['tree']['oid']==TREE,finalch
writej('snapshots/final-seal-all-pr-heads.json',final)
unchanged={}
for alias,_,_ in prs:
 a=start['pullRequests'][alias]['pullRequest']; b=final['pullRequests'][alias]['pullRequest']
 unchanged[alias]=a['headRefOid']==b['headRefOid'] and a['headRef']['target'].get('tree',{}).get('oid')==b['headRef']['target'].get('tree',{}).get('oid')
writej('final-reattestation.json',{'passed':True,'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'worktreeState':state(),
 'chaptarrPrState':finalch['state'],'chaptarrPrDraft':finalch['isDraft'],'chaptarrPrHead':finalch['headRefOid'],'chaptarrPrTree':finalch['headRef']['target']['tree']['oid'],
 'allSevenHeadsAndTreesUnchangedFromStart':all(unchanged.values()),'perRepositoryUnchangedFromStart':unchanged,
 'startUtc':start['queryStartedUtc'],'finalUtc':final['queryCompletedUtc']})
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},state()

readme=f'''# ChaptarrNG PR #190 primary localization review — W1100–W1149

## Exact scope and snapshot

This packet reviews zero-based positions 1100–1149 from `{FOLLOW}`: 50 source IDs × 12 direct locales = 600 cells. Sources include registered server errors and UI help, OAuth, accessibility, and scheduled-task labels. The English catalog, queue file, all locale catalogs, source registries, and caller files are pinned to exact Git blobs and SHA-256 values.

PR #190 remained open and draft on `{BRANCH}` at head `{HEAD}`, tree `{TREE}`. Seven localization PRs were snapshotted before and after source selection and again at final seal. The worktree remained clean.

## Primary decisions

{counts['accept-current']} cells accept the current value; {counts['correction']} corrections and {counts['refinement']} refinements are proposed; {counts['hold']} cells are held. Proposals are review recommendations and were not applied. Notable findings address cross-format sync wording, the accessible dialog label, malformed/misleading OAuth errors, the `requestTokenSecret` missing-value message, and the expired OIDC session text. Exact product and protocol literals are checked per cell.

The W1050–W1099 `Dodge-ing` protected proper-name pun remains held across all 12 locales. Its primary and independent dispositions remain upheld, and all 12 applied values still match their pinned readbacks. This packet assigns no new disposition to that prior window.

## Structural and historical checks

All 600 final targets pass placeholder, markup, ICU signature, and source-registered protected-literal checks. Every source has an exact caller/display-path pin. Prior evidence checksums pass; the combined ledger contains all 13,200 prior cells through W1099. The already-recorded 195 historic final-hash differences remain unchanged since the prior packet. W1099 matches all 12 prior readbacks; W1150 is pinned as forward-boundary context only.

This is static machine-assisted primary review with moderate overall confidence. No qualified native-speaker approval, browser acceptance, or runtime validation is claimed. No tests, builds, scans, CI, or browser actions were run.

## Packet files

- `source-slice.jsonl`, `caller-context.jsonl`, `catalog-pins.json`, and `pinned-files.json`: exact source, caller, catalog, and file evidence.
- `review-cells.jsonl`, `correction-candidates.jsonl`, `refinement-candidates.jsonl`, `holds.jsonl`: all 600 decisions and exact target hashes.
- `protected-literal-integrity.jsonl`: placeholder, markup, ICU, and protected-token checks for each final target.
- `prior-dispositions-through-W1099.jsonl`, `prior-evidence-reattestation.json`, `w1099-backward-boundary.json`, `w1150-forward-boundary.json`: prior continuity and sequential boundaries.
- `snapshots/`, `summary.json`, `final-reattestation.json`, `manifest.json`, and `SHA256SUMS`: live PR state and packet seal.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
# Include the builder itself in the inventory, but omit only manifest and checksum list.
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'})
artifacts=[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files]
manifest={'schemaVersion':1,'packet':'ChaptarrNG PR #190 primary localization review W1100-W1149','sealedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'branch':BRANCH,'artifactCountExcludingManifestAndSums':len(artifacts),'artifacts':artifacts,
 'summary':summary,'liveHeadSnapshots':['snapshots/start-all-pr-heads.json','snapshots/after-source-selection-all-pr-heads.json','snapshots/final-seal-all-pr-heads.json']}
writej('manifest.json',manifest)
all_files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT)}\n' for p in all_files),encoding='utf-8')
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1); assert sha((OUT/n).read_bytes())==h,n
print(json.dumps({'path':str(OUT),'head':HEAD,'tree':TREE,'summary':summary,'priorRows':len(prior_rows),'dodgeHolds':len(dodge_rows),
 'w1099Boundary':all(x['matchesPreviousFinal'] for x in w1099),'allSevenUnchanged':all(unchanged.values()),
 'packetBytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'manifestSha256':sha((OUT/'manifest.json').read_bytes()),
 'sumsSha256':sha((OUT/'SHA256SUMS').read_bytes())},ensure_ascii=False,indent=2))
