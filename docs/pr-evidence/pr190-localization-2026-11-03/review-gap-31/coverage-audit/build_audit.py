#!/usr/bin/env python3
import collections, hashlib, json, pathlib, re, subprocess

REPO = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261103/chaptarrng-pr190-ar-rtl-fix-20261103')
OUT = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-full-coverage-audit-20261103')
EVID = REPO/'docs/pr-evidence/pr190-localization-2026-11-02'
QUEUE_PATH = REPO/'docs/localization/source-followup-20261101.json'
HEAD='580538d38f92e0ec005366ff6bea3f2634400c2e'
TREE='b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1'
BASE='03274100af783fdffaca4dd8436e163dc6b18795'
LOCALES=[('ar','ar'),('de','de'),('es','es'),('fr','fr'),('hi','hi'),('id','id'),('ja','ja'),('ko','ko'),('pt-BR','pt_BR'),('vi','vi'),('zh-Hans','zh_CN'),('zh-Hant','zh_TW')]
REGISTRIES=[
 'docs/localization/server-message-sources.json',
 'docs/localization/provider-field-sources.json',
 'docs/localization/provider-option-sources.json',
 'docs/localization/followup-ui-sources.json',
 'docs/localization/loading-message-sources.json',
 'docs/localization/outbound-message-sources.json',
]

def bsha(b): return hashlib.sha256(b).hexdigest()
def sha(s): return bsha(s.encode('utf-8'))
def file_sha(p): return bsha(pathlib.Path(p).read_bytes())
def git_blob(p): return subprocess.check_output(['git','hash-object',str(p)],cwd=REPO,text=True).strip()
def dump_json(p,obj): pathlib.Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def dump_jsonl(p,rows):
 with open(p,'w',encoding='utf-8') as f:
  for r in rows: f.write(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
def load_json(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def normloc(s):
 if s is None:return None
 x=str(s).replace('_','-').lower()
 return {'pt-br':'pt-br','zh-cn':'zh-hans','zh-tw':'zh-hant','zh-hans':'zh-hans','zh-hant':'zh-hant'}.get(x,x)
def flat_hashes(obj):
 out=set()
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if isinstance(v,str) and re.fullmatch(r'[0-9a-fA-F]{64}',v): out.add(v.lower())
    walk(v)
  elif isinstance(x,list):
   for v in x: walk(v)
 walk(obj); return out
def row_ident(r):
 if not isinstance(r,dict): return None,None
 sid=next((r.get(k) for k in ('sourceId','source_id','id','sourceKey') if isinstance(r.get(k),str)),None)
 loc=next((r.get(k) for k in ('locale','localeTag','language') if isinstance(r.get(k),str)),None)
 return sid,normloc(loc)
def row_source_hashes(r):
 out=set()
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    kl=k.lower()
    if isinstance(v,str) and 'source' in kl and 'sha' in kl and re.fullmatch(r'[0-9a-fA-F]{64}',v): out.add(v.lower())
    walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(r); return out
def targetish_fields(r):
 out=[]
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    kl=k.lower()
    if 'target' in kl and isinstance(v,str):
     if re.fullmatch(r'[0-9a-fA-F]{64}',v):out.append(v.lower())
     elif k in ('currentTarget','finalTarget','crossReviewTarget','afterTarget','target','value'):out.append(sha(v))
    walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(r);return set(out)
def source_row_refs(sid,loc,source_hash):
 return [x for x in evidence_cell_index.get((sid,loc),[]) if source_hash in x['sourceHashes']]
def all_evidence_refs_for_hash(h):
 return evidence_hash_paths.get(h,[])
def nested_dicts(x):
 if isinstance(x,dict):
  yield x
  for v in x.values(): yield from nested_dicts(v)
 elif isinstance(x,list):
  for v in x: yield from nested_dicts(v)

# Exact immutable starting pin checks.
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=REPO,text=True).strip()
status=subprocess.check_output(['git','status','--porcelain=v1'],cwd=REPO,text=True)
if head!=HEAD or tree!=TREE or status.strip(): raise SystemExit(f'worktree gate failed head={head} tree={tree} status={status!r}')
queue=load_json(QUEUE_PATH)
ids=queue['currentMissingIds']
source=json.loads((REPO/'src/NzbDrone.Core/Localization/Core/en.json').read_text(encoding='utf-8'))
if len(ids)!=1210 or len(set(ids))!=len(ids): raise SystemExit('unexpected queue shape')
queue_list_sha=sha(json.dumps(ids,ensure_ascii=False,separators=(',',':')))
source_by_id={sid:source.get(sid) for sid in ids}
if any(v is None for v in source_by_id.values()): raise SystemExit('queue ID missing from English catalog')
source_hash={sid:sha(source_by_id[sid]) for sid in ids}

# Load all direct catalogs and verify completeness, key parity, blanks, protected placeholder tokens.
catalogs={}; cat_meta=[]; en_keys=list(source.keys()); en_set=set(en_keys)
placeholder_re=re.compile(r'\{[^{}]+\}|%[0-9$.*+\-#]*[a-zA-Z]')
def tokens(s): return collections.Counter(placeholder_re.findall(s))
en_token_map={k:tokens(v) for k,v in source.items()}
locale_errors={}
for tag,filetag in LOCALES:
 p=REPO/f'src/NzbDrone.Core/Localization/Core/{filetag}.json'
 data=json.loads(p.read_text(encoding='utf-8'))
 catalogs[tag]=data
 keys=list(data.keys()); keyset=set(keys)
 missing=sorted(en_set-keyset); extra=sorted(keyset-en_set)
 blanks=[k for k,v in data.items() if not isinstance(v,str) or not v.strip()]
 ph_mismatches=[k for k,v in data.items() if isinstance(v,str) and tokens(v)!=en_token_map.get(k,collections.Counter())]
 order_sha=sha(json.dumps(keys,ensure_ascii=False,separators=(',',':')))
 meta={'locale':tag,'catalogPath':str(p.relative_to(REPO)),'keyCount':len(keys),'fileSha256':file_sha(p),'gitBlob':git_blob(p),'keyParity':not missing and not extra,'missingKeyCount':len(missing),'extraKeyCount':len(extra),'nonStringOrBlankCount':len(blanks),'placeholderMismatchCount':len(ph_mismatches),'orderedKeySha256':order_sha}
 cat_meta.append(meta)
 locale_errors[tag]={'missing':missing,'extra':extra,'blanks':blanks,'placeholderMismatches':ph_mismatches,'keys':keys}

# Load retained JSONL evidence and index immutable row hashes without writing any candidate text.
evidence_rows=[]; evidence_hash_paths=collections.defaultdict(list); evidence_cell_index=collections.defaultdict(list)
evidence_roots=[REPO/'docs/pr-evidence/pr190-localization-2026-11-02',REPO/'docs/pr-evidence/pr190-localization-2026-11-03',REPO/'docs/localization']
all_evidence_files=sorted({p for root in evidence_roots if root.exists() for p in root.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl')})
for p in all_evidence_files:
 try:
  if p.suffix=='.jsonl': rows=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
  else: rows=list(nested_dicts(json.loads(p.read_text(encoding='utf-8'))))
 except Exception: continue
 rel=str(p.relative_to(REPO)); ph=file_sha(p); file_hashes=set()
 for row in rows:
  file_hashes.update(flat_hashes(row))
  rid,rloc=row_ident(row)
  if rid and rloc:
   item={'path':rel,'sha256':ph,'row':row,'sourceHashes':row_source_hashes(row),'targetHashes':targetish_fields(row),'allHashes':flat_hashes(row),'primaryLike':('primary' in rel.lower() or 'primaryDisposition' in row or 'primary_disposition' in row)}
   evidence_cell_index[(rid,rloc)].append(item)
 for h in file_hashes:
  if rel not in evidence_hash_paths[h]:evidence_hash_paths[h].append(rel)

# Build per-cell coverage map: exact current catalog hash plus a pinned review row with matching source hash.
coverage=[]; primary_dispositions=collections.Counter(); primary_paths=collections.Counter(); hash_missing=[]; primary_missing=[]
for ordinal,sid in enumerate(ids):
 sh=source_hash[sid]
 for tag,filetag in LOCALES:
  value=catalogs[tag].get(sid)
  th=sha(value) if isinstance(value,str) else None
  refs=source_row_refs(sid,normloc(tag),sh)
  primary_refs=[x for x in refs if x['primaryLike']]
  hash_refs=all_evidence_refs_for_hash(th) if th else []
  if not primary_refs:primary_missing.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':tag,'sourceSha256':sh})
  if not hash_refs:hash_missing.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':tag,'targetSha256':th})
  disp=collections.Counter()
  for rec in refs:
   r=rec['row']
   for k in ('primaryDisposition','primary_disposition','finalDisposition','final_disposition','adjudicationDisposition','crossReviewDisposition','crossReviewAction','disposition'):
    v=r.get(k)
    if isinstance(v,str) and v:disp[v]+=1
  primary_dispositions.update(disp)
  primary_paths.update(x['path'] for x in primary_refs)
  coverage.append({'sourceOrdinal':ordinal,'sourceId':sid,'sourceTextSha256':sh,'locale':tag,'catalogPath':f'src/NzbDrone.Core/Localization/Core/{filetag}.json','catalogTargetSha256':th,'primaryReviewRowCount':len(primary_refs),'primaryReviewPaths':[x['path'] for x in primary_refs[:4]],'currentTargetHashEvidenceCount':len(hash_refs),'currentTargetHashEvidencePaths':hash_refs[:4]})

dump_jsonl(OUT/'candidate-free-coverage-map.jsonl',coverage)
dump_jsonl(OUT/'candidate-free-source-queue.jsonl',[{'sourceOrdinal':i,'sourceId':sid,'sourceTextSha256':source_hash[sid]} for i,sid in enumerate(ids)])

# Ordered key sequence comparison across the 12 locales; source order included for exact parity diagnosis.
orders={m['orderedKeySha256'] for m in cat_meta}
base_order=cat_meta[0]['orderedKeySha256']
order_diffs=[]
for tag,filetag in LOCALES:
 keys=list(catalogs[tag].keys())
 if keys!=en_keys:
  differences=[]
  for i,(a,b) in enumerate(zip(keys,en_keys)):
   if a!=b:
    differences.append({'firstDifferenceIndex':i,'localeKey':a,'englishKey':b});break
  order_diffs.append({'locale':tag,'catalogPath':f'src/NzbDrone.Core/Localization/Core/{filetag}.json','orderedKeySha256':sha(json.dumps(keys,ensure_ascii=False,separators=(',',':'))),'firstDifference':differences[0] if differences else None,'sameLength':len(keys)==len(en_keys)})
order_groups=collections.defaultdict(list)
for tag,filetag in LOCALES:order_groups[sha(json.dumps(list(catalogs[tag].keys()),ensure_ascii=False,separators=(',',':')))].append(tag)
order_groups=[{'orderedKeySha256':h,'locales':tags} for h,tags in sorted(order_groups.items(),key=lambda x:(-len(x[1]),x[1]))]
order_key='EmbyJellyfinHostHelpText'
order_key_positions={tag:list(catalogs[tag].keys()).index(order_key) for tag,_ in LOCALES}
base_order_preserved={}
for tag,filetag in LOCALES:
 bp=f'src/NzbDrone.Core/Localization/Core/{filetag}.json'
 try:
  base_keys=list(json.loads(subprocess.check_output(['git','show',f'{BASE}:{bp}'],cwd=REPO).decode('utf-8')).keys())
  base_set=set(base_keys)
  current_old=[k for k in catalogs[tag] if k in base_set]
  current_set=set(catalogs[tag])
  base_old=[k for k in base_keys if k in current_set]
  base_order_preserved[tag]=(current_old==base_old)
 except Exception: base_order_preserved[tag]=None

# Compare current direct catalog cells that existed at live PR base; only hash-only output.
base_data={}
for tag,filetag in LOCALES:
 p=f'src/NzbDrone.Core/Localization/Core/{filetag}.json'
 try:
  raw=subprocess.check_output(['git','show',f'{BASE}:{p}'],cwd=REPO)
  base_data[tag]=json.loads(raw.decode('utf-8'))
 except subprocess.CalledProcessError:base_data[tag]={}
changed_existing=[]
for tag,filetag in LOCALES:
 cur=catalogs[tag]; old=base_data[tag]
 for sid,val in cur.items():
  if sid in old and old[sid]!=val:
   current_hash=sha(val); old_hash=sha(old[sid]) if isinstance(old[sid],str) else None
   eh=all_evidence_refs_for_hash(current_hash)
   status='retained-target-hash-evidence-found' if eh else 'uncovered-current-target-hash'
   changed_existing.append({'locale':tag,'sourceId':sid,'sourceTextSha256':sha(source[sid]) if sid in source else None,'baseTargetSha256':old_hash,'currentTargetSha256':current_hash,'evidenceStatus':status,'evidencePaths':eh[:5]})
dump_jsonl(OUT/'changed-existing-cell-audit.jsonl',changed_existing)

# Cross-check source queue ID coverage with direct-source and caller registry files.
registry_records=[]; registry_meta=[]
for rel in REGISTRIES:
 data=load_json(REPO/rel); rows=data.get('records',[])
 if rel.endswith('server-message-sources.json'):
  rows=data.get('records',[])
 registry_meta.append({'path':rel,'sha256':file_sha(REPO/rel),'gitBlob':git_blob(REPO/rel),'recordCount':len(rows),'sourceCallsiteCount':sum(len(r.get('callsites',[])) for r in rows)})
 registry_records.extend((rel,r) for r in rows)
queue_registry_ids=collections.defaultdict(list)
caller_rows=[]
for rel,r in registry_records:
 sid=r.get('id') or r.get('sourceId')
 if sid not in source_hash:continue
 queue_registry_ids[sid].append(rel)
 for call in r.get('callsites',[]):
  file=call.get('file') or call.get('path')
  if not isinstance(file,str):continue
  absfile=REPO/file
  regline=call.get('line')
  refhash=call.get('sourceLineSha256') or call.get('lineSha256') or call.get('sourceSha256')
  if absfile.exists():
   lines=absfile.read_text(encoding='utf-8',errors='replace').splitlines()
   trimmed_hashes=[sha(x.strip()) for x in lines]
   matches=[i+1 for i,h in enumerate(trimmed_hashes) if refhash and h==refhash.lower()]
   at_line=(trimmed_hashes[regline-1] if isinstance(regline,int) and 0<regline<=len(lines) else None)
   if refhash and at_line==refhash.lower(): state='registered-line-current'
   elif len(matches)==1:state='registered-line-relocated-unique'
   elif sid in absfile.read_text(encoding='utf-8',errors='replace'):state='line-changed-id-still-in-file'
   else:state='no-pinned-line-or-id-in-file'
   file_hash=file_sha(absfile); blob=git_blob(absfile)
  else:
   matches=[];state='caller-file-missing';file_hash=None;blob=None
  caller_rows.append({'sourceId':sid,'registryPath':rel,'callerFile':file,'registeredLine':regline,'registeredLineSha256':refhash,'currentLineMatches':matches,'status':state,'currentFileSha256':file_hash,'currentFileGitBlob':blob})
dump_jsonl(OUT/'caller-coverage.jsonl',caller_rows)
caller_counts=collections.Counter(r['status'] for r in caller_rows)
registry_id_missing=sorted(set(ids)-set(queue_registry_ids))

# Holds: latest retained resolutions; W1187 primary hold is superseded by the dedicated W1187 decision.
hold_groups=[
 {'sourceOrdinal':447,'sourceId':'server.message.m00dbcd234174','locales':[x[0] for x in LOCALES],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-0400-0449/cross-review/cross-review-cells.jsonl','reasonCode':'no exact production caller; nearest caller builds raw dynamic exception text; placeholder argument unverified'},
 {'sourceOrdinal':498,'sourceId':'server.message.m23e7ac60ea9c','locales':[x[0] for x in LOCALES],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-0450-0499/cross-review/cross-review-candidates-and-holds.jsonl','reasonCode':'no direct caller or exact UI role pinned; source surface/function unknown'},
 {'sourceOrdinal':561,'sourceId':'server.message.m453c42aa8de5','locales':[x[0] for x in LOCALES],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-0550-0599/crossreview/full-cell-final-dispositions.jsonl','reasonCode':'source says less than 25000 but caller accepts exactly 25000; source/caller semantic mismatch unresolved'},
 {'sourceOrdinal':884,'sourceId':'server.message.mf00d6bc38ae8','locales':['hi'],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-0884-corrected-source/cross-review/crossreview.jsonl','reasonCode':'caller forbids backslash but corrected English catalog source omits it; source/caller mismatch unresolved'},
 {'sourceOrdinal':963,'sourceId':'provider.option.oe4d40d318e99','locales':['id'],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-0950-0999/adjudication/adjudication-ledger.jsonl','reasonCode':'Indonesian label preference between Farsi and Bahasa Persia needs qualified native review'},
 {'sourceOrdinal':1000,'sourceId':'provider.option.o7285d46b982d','locales':['vi'],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-1000-1049/adjudication/root-adjudication.jsonl','reasonCode':'retain current value pending qualified Vietnamese review'},
 {'sourceOrdinal':1047,'sourceId':'ui.loading.newEbookSmell','locales':['ar','hi','id','ja','ko','vi','zh-Hans','zh-Hant'],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-1000-1049/adjudication/root-adjudication.jsonl','reasonCode':'retain current value pending qualified native-speaker review'},
 {'sourceOrdinal':1049,'sourceId':'ui.loading.rewindAudiobooks','locales':['ar','id'],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-1000-1049/adjudication/root-adjudication.jsonl','reasonCode':'retain current value pending qualified native-speaker review'},
 {'sourceOrdinal':1054,'sourceId':'ui.loading.dodgeBooks','locales':[x[0] for x in LOCALES],'evidence':'docs/pr-evidence/pr190-localization-2026-11-02/window-1050-1099/crossreview/cross-review-cells.jsonl','reasonCode':'Dodge is a protected proper-name verb-form pun; current wording held for native creative localization'},
]
holds=[]
for g in hold_groups:
 row={'sourceOrdinal':g['sourceOrdinal'],'sourceId':g['sourceId'],'sourceTextSha256':source_hash.get(g['sourceId']),'locale':None,'evidencePath':g['evidence'],'evidenceSha256':file_sha(REPO/g['evidence']),'reasonCode':g['reasonCode']}
 for tag,_ in LOCALES:
  if tag in g['locales']:
   holds.append({**row,'locale':tag,'currentTargetSha256':sha(catalogs[tag][g['sourceId']])})
dump_jsonl(OUT/'active-holds.jsonl',holds)

# Exact changed-target evidence classification. Only cell hashes and evidence path IDs are retained.
changed_summary={'count':len(changed_existing),'supportedCount':sum(x['evidenceStatus']=='retained-target-hash-evidence-found' for x in changed_existing),'uncoveredCount':sum(x['evidenceStatus']=='uncovered-current-target-hash' for x in changed_existing),'uncovered':[{k:x[k] for k in ('locale','sourceId','baseTargetSha256','currentTargetSha256','evidenceStatus')} for x in changed_existing if x['evidenceStatus']!='retained-target-hash-evidence-found']}

# Fixed positions/order evidence windows and source corrections.
windows=[]
for start in range(0,1200,50):
 end=min(start+49,1199)
 dirp=next((p for p in EVID.glob(f'window-{start:04d}-{end:04d}') if p.is_dir()),None)
 if dirp is None and start>=200: dirp=next((p for p in EVID.glob(f'window-{start}-{end}') if p.is_dir()),None)
 if dirp is None and start<200: dirp=next((p for p in EVID.glob(f'window-{start:04d}-{end:04d}') if p.is_dir()),None)
 windows.append({'startOrdinal':start,'endOrdinal':end,'evidenceDirectory':str(dirp.relative_to(REPO)) if dirp else None})
windows.append({'startOrdinal':1200,'endOrdinal':1209,'evidenceDirectory':'docs/pr-evidence/pr190-localization-2026-11-02/window-1200-tail-10'})

# Manifest of every source evidence row/file explicitly consumed by this audit.
used_paths=set([str(QUEUE_PATH.relative_to(REPO)),'src/NzbDrone.Core/Localization/Core/en.json'])
used_paths.update(m['catalogPath'] for m in cat_meta)
used_paths.update(REGISTRIES)
used_paths.update(rec['path'] for cells in evidence_cell_index.values() for rec in cells if rec['row'].get('sourceId') in set(ids) or rec['row'].get('source_id') in set(ids) or rec['row'].get('id') in set(ids))
used_paths.update(g['evidence'] for g in hold_groups)
used_paths.update([
 'frontend/src/login.html','frontend/src/Utilities/Localization/locale-utils.cjs','src/NzbDrone.Core/Localization/Core/ui-locales.json','src/NzbDrone.Core/Localization/LocalizationService.cs','docs/pr-evidence/pr190-localization-2026-11-03/arabic-login-rtl/README.md'
])
used_files=[]
for rel in sorted(used_paths):
 p=REPO/rel
 if p.is_file():used_files.append({'path':rel,'sha256':file_sha(p),'gitBlob':git_blob(p)})

summary={
 'schemaVersion':1,'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'liveState':'OPEN_DRAFT','baseRefOid':BASE,'head':head,'tree':tree,'branch':'codex/chaptarrng-localization-complete-20261031','worktree':'/mnt/disks/scratch/task-worktrees/localization-20261103/chaptarrng-pr190-ar-rtl-fix-20261103','worktreeClean':True,
 'sourceQueue':{'path':str(QUEUE_PATH.relative_to(REPO)),'fileSha256':file_sha(QUEUE_PATH),'gitBlob':git_blob(QUEUE_PATH),'count':len(ids),'currentMissingIdsSha256':queue.get('currentMissingIdsSha256'),'compactIdListSha256':queue_list_sha,'firstOrdinal':0,'lastOrdinal':len(ids)-1},
 'localeCount':len(LOCALES),'locales':[x[0] for x in LOCALES],'englishKeyCount':len(en_keys),'directCatalogCellCount':len(ids)*len(LOCALES),'catalogs':cat_meta,
 'catalogChecks':{'keySetMismatchLocales':[x['locale'] for x in cat_meta if not x['keyParity']],'nonStringOrBlankValues':sum(x['nonStringOrBlankCount'] for x in cat_meta),'placeholderTokenMismatches':sum(x['placeholderMismatchCount'] for x in cat_meta),'distinctLocaleOrderedKeySequences':len(orders),'orderedKeyGroups':order_groups,'englishOrderSha256':sha(json.dumps(en_keys,ensure_ascii=False,separators=(',',':'))),'orderedKeyDifferencesFromEnglish':order_diffs,'baseOrderPreservedForExistingKeys':base_order_preserved,'positionOfEmbyJellyfinHostHelpText':order_key_positions},
 'queueCoverage':{'expectedCells':len(ids)*len(LOCALES),'coverageRows':len(coverage),'missingPrimaryExactSourceRows':len(primary_missing),'missingCurrentTargetHashEvidence':len(hash_missing),'primaryDispositionCountsAcrossMatchingEvidenceRows':dict(sorted(primary_dispositions.items())),'missingPrimaryExamples':primary_missing[:10],'missingHashExamples':hash_missing[:10]},
 'changedExistingCellsVsBase':changed_summary,
 'activeHolds':{'cellCount':len(holds),'sourceCount':len(hold_groups),'cells':len(holds),'supersededHold':{'sourceOrdinal':1187,'sourceId':'server.message.md764ed5e74b4','reason':'dedicated W1187 dynamic-target-quality adjudication overrides W1150–1199 primary hold'}},
 'callerCoverage':{'registryFiles':registry_meta,'queueIdsWithRegistry':len(queue_registry_ids),'queueIdsWithoutRegistry':registry_id_missing,'queueCallsiteCount':len(caller_rows),'callsiteDispositionCounts':dict(caller_counts)},
 'sourceWindows':windows,'sourcePinExceptions':[{'sourceOrdinal':654,'sourceId':'server.message.m783307436ce0','reason':'English source corrected to modern SABnzbd spelling; earlier review rows carry the old source hash','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'},{'sourceOrdinal':695,'sourceId':'server.message.m843e64bf5198','reason':'English source corrected to explicit Mailgun test-message wording; earlier review rows carry the old source hash','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'}],'sourcePinExceptions':[{'sourceOrdinal':654,'sourceId':'server.message.m783307436ce0','reason':'English source corrected to modern SABnzbd spelling; earlier review rows carry the old source hash','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'},{'sourceOrdinal':695,'sourceId':'server.message.m843e64bf5198','reason':'English source corrected to explicit Mailgun test-message wording; earlier review rows carry the old source hash','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'}],'sourcePinExceptions':[{'sourceOrdinal':654,'sourceId':'server.message.m783307436ce0','reason':'source corrected to modern product spelling; primary source hash is stale and correction packet pins the current source/caller','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'},{'sourceOrdinal':695,'sourceId':'server.message.m843e64bf5198','reason':'English source rewritten for correct Mailgun test-message wording; primary source hash is stale and correction packet pins the current source/caller','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'}],
 'codePaths':{'loginHtml':{'path':'frontend/src/login.html','sha256':file_sha(REPO/'frontend/src/login.html'),'gitBlob':git_blob(REPO/'frontend/src/login.html'),'branchLines':'478-487','languageExtraction':'Locale normalizes underscores to hyphens, then lowercases the first subtag.','directionList':['ar','dv','fa','he','ku','ps','sd','ug','ur','yi'],'arabicResult':'ar is included, so document.dir is assigned rtl.','fixCommit':'46049fadfc1ad02775a4a096178bc08ca78407ad','preFixHead':'edbfa7cb12b7eb0e3591981d32b2643c9a7b0987','preFixFileSha256':'fc9f5bcbb220092b529836ef45a0af2676ff5b39aeb4688f0d21e26d0988681b','preFixGitBlob':'79cd2492712014e5879cc147938728ada850dba2','rtlFixEvidencePath':'docs/pr-evidence/pr190-localization-2026-11-03/arabic-login-rtl/README.md'},'sharedHelper':{'path':'frontend/src/Utilities/Localization/locale-utils.cjs','sha256':file_sha(REPO/'frontend/src/Utilities/Localization/locale-utils.cjs'),'gitBlob':git_blob(REPO/'frontend/src/Utilities/Localization/locale-utils.cjs'),'rtlLanguages':['ar','ckb','dv','fa','he','khw','ks','ku','ps','sd','ug','ur','yi'],'rtlScripts':['adlm','arab','hebr','nkoo','rohg','syrc','thaa'],'arabicResult':'getDirectionForLocale("ar") returns rtl.'},'localeRegistry':{'path':'src/NzbDrone.Core/Localization/Core/ui-locales.json','sha256':file_sha(REPO/'src/NzbDrone.Core/Localization/Core/ui-locales.json'),'gitBlob':git_blob(REPO/'src/NzbDrone.Core/Localization/Core/ui-locales.json'),'arabicTag':'ar','arabicFile':'ar','arabicDirection':'rtl','arabicSelectable':True},'sharedCatalogLoader':{'path':'src/NzbDrone.Core/Localization/LocalizationService.cs','sha256':file_sha(REPO/'src/NzbDrone.Core/Localization/LocalizationService.cs'),'gitBlob':git_blob(REPO/'src/NzbDrone.Core/Localization/LocalizationService.cs'),'mergeOrder':'English base -> optional fallback catalog -> selected direct locale catalog; later values overwrite earlier values.'}},
 'recommendation':'The focused fix is present at the current PR head: login.html now includes ar in its RTL list, matching getDirectionForLocale("ar") and the locale registry. A later cleanup could make the standalone login page consume a shared/generated direction source to prevent future drift. Catalog fallback logic is consistent with full direct-catalog key coverage.',
 'evidenceInventory':{'fileCount':len(all_evidence_files),'hashEntryCount':sum(len(v) for v in evidence_hash_paths.values()),'evidenceRoots':[str(p.relative_to(REPO)) for p in evidence_roots]},'evidenceInventory':{'fileCount':len(all_evidence_files),'hashEntryCount':sum(len(v) for v in evidence_hash_paths.values()),'evidenceRoots':[str(p.relative_to(REPO)) for p in evidence_roots]},'evidenceInventory':{'fileCount':len(all_evidence_files),'hashEntryCount':sum(len(v) for v in evidence_hash_paths.values()),'evidenceRoots':[str(p.relative_to(REPO)) for p in evidence_roots]},'usedEvidenceFiles':used_files
}
dump_json(OUT/'catalog-and-pin-attestation.json',summary)

# Candidate-free README. Do not print catalog values or candidate translations.
readme=f'''# ChaptarrNG PR #190 exact-head catalog coverage audit\n\nRead-only audit at `{head}` (tree `{tree}`), live open draft PR #190, base `{BASE}`. Exact worktree was clean.\n\n## Catalog and source coverage\n\n- {len(LOCALES)} direct catalogs, {len(en_keys)} English keys each, {len(ids)} current source IDs, {len(coverage)} source/locale cells.\n- Key sets match English in all catalogs. Nonblank string values: {sum(x['nonStringOrBlankCount'] for x in cat_meta)} failures. Placeholder token mismatches: {sum(x['placeholderMismatchCount'] for x in cat_meta)}.\n- Locale ordered-key arrays form {len(order_groups)} sequences; they are not identical to English. Exact groups and the index of `EmbyJellyfinHostHelpText` are in `catalog-and-pin-attestation.json`. Existing-key order matches each locale's PR-base order, so the sequence differences predate this PR.\n- Candidate-free coverage ledger has {len(coverage)} rows; rows retain source/current-target hashes and exact review evidence paths, never target text. Missing exact-current-source primary rows: {len(primary_missing)} (source positions 654 and 695; their correction packets separately pin the current source and callers). Missing current-target hash evidence: {len(hash_missing)}.\n- {changed_summary['count']} existing translated cells differ from the PR base: {changed_summary['supportedCount']} have retained exact-target-hash evidence, {changed_summary['uncoveredCount']} do not. The uncovered cells are listed by ID/locale and hashes only in `changed-existing-cell-audit.jsonl`.\n- Active unresolved holds: {len(holds)} cells across {len(hold_groups)} IDs. See `active-holds.jsonl`; W1187's earlier primary hold is superseded by its dedicated final adjudication.\n\n## Caller and runtime findings\n\nCaller references are mapped hash-only in `caller-coverage.jsonl`, with current file/line status. The locale catalog loader merges English, then optional fallback, then the selected locale catalog. Since all direct catalogs have complete English key coverage, fallback is not needed for these 12 locales.\n\nAt the earlier PR head `edbfa7c`, `frontend/src/login.html` omitted `ar` from its RTL list and assigned Arabic LTR. The shared helper returns RTL for `ar`, and the registry marks Arabic as selectable/RTL. The current PR head fixes this with the one-line `ar` addition in commit `46049fad`; the resulting branch matches the helper for Arabic. A shared/generated direction source is a future drift-prevention improvement.\n\n## Retained files\n\n- `candidate-free-source-queue.jsonl`\n- `candidate-free-coverage-map.jsonl`\n- `changed-existing-cell-audit.jsonl`\n- `active-holds.jsonl`\n- `caller-coverage.jsonl`\n- `catalog-and-pin-attestation.json`\n- `build_audit.py`\n\nThe audit did not modify repository or PR files and did not run tests, builds, scans, or CI. Machine review evidence is not native-speaker approval.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Top-level checksums cover every retained output except the checksum file itself.
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
with open(OUT/'SHA256SUMS','w',encoding='utf-8') as f:
 for p in files:f.write(f'{file_sha(p)}  {p.name}\n')
print(json.dumps({'output':str(OUT),'head':head,'tree':tree,'cells':len(coverage),'missingPrimary':len(primary_missing),'missingHash':len(hash_missing),'changedExisting':changed_summary,'activeHolds':len(holds),'callerCount':len(caller_rows),'callerCounts':dict(caller_counts),'orderDiffLocales':[x['locale'] for x in order_diffs],'outputFiles':len(files)+1},ensure_ascii=False))
