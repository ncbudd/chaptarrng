from __future__ import annotations
import collections, hashlib, json, pathlib, re, subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
REPO='snapetech-org/ChaptarrNG'; PR=190
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
SRC='src/NzbDrone.Core/Localization/Core/en.json'
FOLLOW='docs/localization/source-followup-20261101.json'
FOLLOW2='docs/localization/source-followup-20261102.json'
REG='docs/localization/server-message-sources.json'
PIPE='docs/localization/server-message-callers.json'
PRIOR_ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch')

def sha(data): return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()
def jbytes(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def run(args,text=True): return subprocess.check_output(args,text=text)
def git(*args,text=True): return run(['git','-C',str(WORK),*args],text=text)
def show(path): return git('show',f'{HEAD}:{path}',text=False)
def tracked(path):
 b=show(path); return {'path':path,'blob':git('rev-parse',f'{HEAD}:{path}').strip(),'sha256':sha(b),'bytes':len(b)}
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def live():
 p=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
 t=run(['gh','api',f'repos/{REPO}/commits/{p["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 ref=json.loads(run(['gh','api',f'repos/{REPO}/git/ref/heads/{BRANCH}']))['object']['sha']
 remote=run(['git','-C',str(WORK),'ls-remote','github',f'refs/heads/{BRANCH}']).split()[0]
 return p,t,ref,remote
def verify_sums(folder):
 sums=folder/'SHA256SUMS'; assert sums.is_file(),f'missing sums {folder}'
 for line in sums.read_text().splitlines():
  digest,name=line.split('  ',1); assert sha((folder/name).read_bytes())==digest,(folder/name)
 return sha(sums.read_bytes())

# Exact live pin and clean worktree before reading the review inputs.
pr,api_tree,api_ref,remote=live()
assert pr['state']=='OPEN' and pr['isDraft'] and pr['headRefOid']==HEAD and pr['headRefName']==BRANCH
assert api_tree==TREE and api_ref==remote==HEAD
assert git('rev-parse','HEAD').strip()==HEAD and git('rev-parse','HEAD^{tree}').strip()==TREE
assert git('branch','--show-current').strip()==BRANCH and not git('status','--porcelain').strip()
assert {p.name for p in OUT.iterdir()} <= {'prepare_input.py'},list(OUT.iterdir())

# Freeze source order from currentMissingIds at this exact head.
src_raw=show(SRC); source=json.loads(src_raw)
follow_raw=show(FOLLOW); follow=json.loads(follow_raw); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
ids_sha=sha(jbytes(ids)); assert ids_sha==follow['currentMissingIdsSha256']
selected=ids[850:900]; assert len(selected)==50 and not(set(selected)&set(ids[:850]))
assert len(set(selected))==50
registry_raw=show(REG); registry=json.loads(registry_raw); records={r['id']:r for r in registry['records']}
assert all(sid in records for sid in selected)
source_info=tracked(SRC); follow_info=tracked(FOLLOW); follow2_info=tracked(FOLLOW2); reg_info=tracked(REG); pipe_info=tracked(PIPE)
rows=[]
for ordinal,sid in enumerate(selected,850):
 rec=records[sid]
 assert sid in source and rec.get('source')==source[sid],(ordinal,sid,'source/registry drift')
 rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'sourceKeySha256':sha(sid),'sourceTextSha256':sha(source[sid]),'sourceCatalogBlob':source_info['blob'],'sourceCatalogSha256':source_info['sha256'],'sourceRegistryFingerprint':rec.get('sourceFingerprint'),'sourceRegistryProtectedLiterals':rec.get('protectedLiterals',[])})

# Reattest all direct locale catalogs and freeze exact current values/hashes.
locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{fn}' for loc,fn in LOCALES.items()}
catalogs={}; catalog_infos={}
for loc,path in locale_paths.items():
 raw=show(path); obj=json.loads(raw)
 assert set(obj)==set(source),(loc,'catalog key set differs from English source')
 catalogs[loc]=obj; catalog_infos[loc]=tracked(path)

# Reattest production caller references from the current source registry.
caller_rows=[]; caller_files={}; caller_gaps=[]; refreshed=[]; callers_by={}
for row in rows:
 sid=row['sourceId']; rec=records[sid]; refs=[]; seen=set()
 for pin in rec.get('callsites',[]):
  path=pin['file']; raw=show(path); lines=raw.decode('utf-8').splitlines(); n=pin['line']
  line=lines[n-1] if 1<=n<=len(lines) else None
  expected=pin.get('sourceLine','').strip(); valid=line is not None and line.strip()==expected and sha(line.strip())==pin.get('sourceLineSha256')
  hits=[]
  if valid: hits=[(n,line)]
  else:
   needles=[sid,expected]
   hits=[(i+1,v) for i,v in enumerate(lines) if any(q and q in v for q in needles)]
   if hits: refreshed.append({'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'path':path,'registryLine':n,'registryLineSha256':pin.get('sourceLineSha256'),'currentHits':[{'line':i,'text':v.strip(),'sha256':sha(v.strip())} for i,v in hits],'reason':'registry callsite pin stale; current source line reattested'})
  for lineno,text in hits:
   if (path,lineno) in seen: continue
   seen.add((path,lineno)); current=raw.decode('utf-8').splitlines()
   refs.append({'file':path,'line':lineno,'lineText':text.strip(),'lineSha256':sha(text.strip()),'fileBlob':git('rev-parse',f'HEAD:{path}').strip(),'fileSha256':sha(raw),'contextBefore':[v.strip() for v in current[max(0,lineno-4):lineno-1]],'contextAfter':[v.strip() for v in current[lineno:min(len(current),lineno+3)]],'registryLine':n,'registryLineSha256':pin.get('sourceLineSha256'),'registryPinExact':valid,'category':pin.get('category'),'surface':pin.get('surface')})
   caller_files[path]=tracked(path)
 refs.sort(key=lambda x:(x['file'],x['line']))
 if not refs: caller_gaps.append({'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'source':row['source'],'reason':'no production callsite could be reattested'})
 callers_by[sid]=refs
 caller_rows.append({'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'source':row['source'],'callerReferenceStatus':'pinned' if refs else 'gap','callerRefs':refs,'callerContextSha256':sha(jbytes(refs)),'sourceRegistryCategory':rec.get('category'),'sourceRegistrySurface':rec.get('surface'),'sourcePatterns':rec.get('patterns',[]),'protectedLiterals':rec.get('protectedLiterals',[]),'sourceRegistryFingerprint':rec.get('sourceFingerprint')})

# Reattest the generic frontend server-message display pipeline at this head.
pipeline=json.loads(show(PIPE)); pipeline_rows=[]; pipeline_gaps=[]
for pin in pipeline['callsites']:
 path=pin['file']; raw=show(path); lines=raw.decode('utf-8').splitlines(); n=pin['line']; line=lines[n-1] if 1<=n<=len(lines) else None
 valid=line is not None and line.strip()==pin['sourceLine'].strip() and sha(line.strip())==pin['sourceLineSha256']
 if not valid:
  pipeline_gaps.append({'file':path,'line':n,'reason':'generic display pipeline line pin differs from exact head'}); continue
 pipeline_rows.append({'file':path,'line':n,'lineText':line.strip(),'lineSha256':sha(line.strip()),'fileBlob':git('rev-parse',f'HEAD:{path}').strip(),'fileSha256':sha(raw),'contextBefore':[v.strip() for v in lines[max(0,n-4):n-1]],'contextAfter':[v.strip() for v in lines[n:min(len(lines),n+3)]],'surface':'generic server-message display pipeline'})
 caller_files[path]=tracked(path)

# Freeze cell values and source/caller technical parity.
cells=[]
for row in rows:
 sid=row['sourceId']; rec=records[sid]; protected=rec.get('protectedLiterals',[]); caller_hash=sha(jbytes(callers_by[sid]))
 for loc,path in locale_paths.items():
  target=catalogs[loc][sid]
  cells.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'locale':loc,'source':row['source'],'sourceKeySha256':row['sourceKeySha256'],'sourceTextSha256':row['sourceTextSha256'],'sourceFile':SRC,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'currentTarget':target,'currentTargetSha256':sha(target),'targetFile':path,'targetFileBlob':catalog_infos[loc]['blob'],'targetFileSha256':catalog_infos[loc]['sha256'],'sourcePlaceholders':placeholders(row['source']),'currentTargetPlaceholders':placeholders(target),'sourceMarkup':markup(row['source']),'currentTargetMarkup':markup(target),'placeholderParity':placeholders(row['source'])==placeholders(target),'markupParity':markup(row['source'])==markup(target),'protectedLiterals':protected,'protectedLiteralChecks':[{'literal':lit,'presentInSource':lit in row['source'],'presentInCurrentTarget':lit in target} for lit in protected],'callerContextSha256':caller_hash})
assert len(cells)==600

# Reattest the immediately previous W849 boundary and compare with prior independent final values.
prior=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0800-0849-crossreview-20261102')
prior_sums=verify_sums(prior)
prior_manifest=json.loads((prior/'manifest.json').read_text())
prior_ledger=[json.loads(x) for x in (prior/'crossreview-ledger.jsonl').read_text().splitlines()]
assert len(prior_ledger)==600
w849_id=ids[849]; w849row=next(x for x in rows if x['sourceOrdinal']==800) if False else None
prior_w849=[x for x in prior_ledger if x.get('sourceOrdinal')==849]
assert len(prior_w849)==12
boundary=[]
for old in prior_w849:
 loc=old['locale']; sid=old['sourceId']; assert sid==w849_id and old['source']==source[sid]
 live_target=catalogs[loc][sid]
 boundary.append({'sourceOrdinal':849,'sourceId':sid,'locale':loc,'source':source[sid],'sourceTextSha256':sha(source[sid]),'previousCrossReviewDisposition':old.get('crossReviewDisposition'),'previousPrimaryDisposition':old.get('primaryDisposition'),'previousCrossReviewFinalTarget':old.get('finalTarget'),'previousCrossReviewFinalTargetSha256':old.get('finalTargetSha256'),'liveTarget':live_target,'liveTargetSha256':sha(live_target),'matchesPreviousCrossReviewFinal':live_target==old.get('finalTarget'),'callerRefs':old.get('callerRefs',[]),'callerContextSha256':old.get('callerContextSha256')})

# Preliminary compatibility scan only; reconcile_prior.py replaces this scan with checksummed prior evidence covering positions 0–849 before the packet is finalized.
prior_packets=[]; prior_ids=set(); prior_decisions=[]; overlap=[]; coverage=[]
for folder in sorted(PRIOR_ROOT.glob('chaptarrng-pr190-window-*-primary-20261102')):
 if folder.resolve()==OUT.resolve(): continue
 mp=folder/'manifest.json'
 if not mp.is_file(): continue
 try: m=json.loads(mp.read_text())
 except Exception: continue
 scope=m.get('scope')
 if isinstance(scope,dict): bounds=scope.get('positions',[])
 elif isinstance(scope,list): bounds=scope
 else: bounds=[]
 if len(bounds)!=2 or bounds[1]>849: continue
 sums_sha=verify_sums(folder)
 source_file=folder/'source-slice.jsonl'
 srows=[json.loads(x) for x in source_file.read_text().splitlines()] if source_file.exists() else []
 for x in srows:
  prior_ids.add(x['sourceId']); coverage.append(x.get('sourceOrdinal'))
 ledger=folder/'primary-review-ledger.jsonl'
 if not ledger.exists(): ledger=folder/'review-cells.jsonl'
 if ledger.exists():
  for x in (json.loads(line) for line in ledger.read_text().splitlines()):
   sid=x.get('sourceId'); loc=x.get('locale'); disp=x.get('disposition')
   ordinal=x.get('sourceOrdinal')
   if ordinal is not None and ordinal>=850: overlap.append({'packet':folder.name,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'disposition':disp})
   if sid in set(selected) and disp is not None: overlap.append({'packet':folder.name,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'disposition':disp})
   if ordinal is not None and ordinal<850: prior_decisions.append({'packet':folder.name,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'disposition':disp,'sourceTextSha256':x.get('sourceTextSha256',x.get('sourceSha256')),'currentTargetSha256':x.get('currentTargetSha256',x.get('targetSha256')),'finalTargetSha256':x.get('independentTargetSha256',x.get('finalTargetSha256'))})
 prior_packets.append({'path':str(folder),'manifestSha256':sha(mp.read_bytes()),'sha256sumsSha256':sums_sha,'bounds':bounds,'sourceCount':m.get('sourceCount'),'cellCount':m.get('cellCount')})
assert not overlap,overlap
assert len(set(selected)&prior_ids)==0
# Reattest all 12 W849 boundary targets and source in current catalogs; collect previous values including mismatches.
writejl('source-slice.jsonl',rows); writejl('caller-context.jsonl',caller_rows); writejl('input-cells.jsonl',cells)
writejl('pipeline-caller-context.jsonl',pipeline_rows); writejl('w849-boundary-reattestation.jsonl',boundary)
writejl('prior-disposition-hashes.jsonl',prior_decisions)
writej('prior-disposition-boundary.json',{'priorPrimaryPackets':prior_packets,'priorPrimaryPacketCount':len(prior_packets),'priorSourceIdsUnique':len(prior_ids),'sourcePositionCoverageObserved':sorted(set(x for x in coverage if x is not None)),'priorDispositionsRecorded':len(prior_decisions),'selectedPositions':[850,899],'selectedSourceIds':50,'selectedSourceIdListSha256':sha(jbytes(selected)),'selectedIdsUnique':len(set(selected))==50,'noOverlapWithPositions0Through849':not bool(set(selected)&prior_ids),'exactPriorDispositionOverlapCount':len(overlap),'exactPriorDispositionOverlapRows':overlap,'w849BoundaryRows':len(boundary),'w849MatchesPriorCrossReviewFinalCount':sum(x['matchesPreviousCrossReviewFinal'] for x in boundary),'w849MatchesPriorCrossReviewFinal':all(x['matchesPreviousCrossReviewFinal'] for x in boundary),'previousWindowChecksumsVerified':True,'previousWindowManifestSha256':sha((prior/'manifest.json').read_bytes()),'previousWindowSha256SUMS':prior_sums})
writej('caller-context-summary.json',{'sourceCallerRows':len(caller_rows),'sourceCallerReferences':sum(len(x['callerRefs']) for x in caller_rows),'uniqueSourceCallerFiles':len({r['file'] for c in caller_rows for r in c['callerRefs']}),'sourceCallerGaps':caller_gaps,'staleRegistryPinsRefreshed':refreshed,'genericPipelineReferences':len(pipeline_rows),'genericPipelineFiles':len({r['file'] for r in pipeline_rows}),'genericPipelineGaps':pipeline_gaps})

# Build exact-head input manifest and source/catalog/caller hash inventory.
all_files={x['path']:x for x in [source_info,follow_info,follow2_info,reg_info,pipe_info,*catalog_infos.values(),*caller_files.values()]}
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'branch':BRANCH,'livePullRequest':pr,'githubBranchRefHead':api_ref,'githubRemoteBranchHead':remote,'scope':{'window':'W850-W899','positions':[850,899],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceQueue':{'path':FOLLOW,'blob':follow_info['blob'],'sha256':follow_info['sha256'],'currentMissingIdsCount':len(ids),'currentMissingIdsSha256':ids_sha,'queueBaseHead':follow['baseHead'],'selectedSourceIds':selected,'selectedSourceIdListSha256':sha(jbytes(selected))},'sourceCatalog':source_info,'sourceRegistry':reg_info,'genericPipelineRegistry':pipe_info,'sourceFollowupCorrectionEvidence':follow2_info,'localeCatalogs':catalog_infos,'callerFiles':sorted((all_files[x] for x in caller_files),key=lambda v:v['path']),'callerReferences':sum(len(x['callerRefs']) for x in caller_rows),'sourceCallerGaps':caller_gaps,'genericPipelineReferences':len(pipeline_rows),'genericPipelineGaps':pipeline_gaps,'priorWindowBoundaryOrdinal':849,'priorDispositionPacketCount':len(prior_packets),'priorDispositionsRecorded':len(prior_decisions),'noPriorDispositionOverlap':not overlap,'w849BoundaryMatchesPriorCrossReview':sum(x['matchesPreviousCrossReviewFinal'] for x in boundary),'worktree':str(WORK),'worktreeClean':True}
writej('input-manifest.json',manifest)
(OUT/'INPUT-SHA256SUMS').write_text(''.join(f'{entry["sha256"]}  {path}\n' for path,entry in sorted(all_files.items())))
# Final exact-head check after freeze.
pr2,t2,r2,remote2=live(); st={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
assert pr2['state']=='OPEN' and pr2['isDraft'] and pr2['headRefOid']==HEAD and t2==TREE and r2==remote2==HEAD
assert st=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
writej('prepare-reattestation.json',{'passed':True,'head':HEAD,'tree':TREE,'livePullRequest':pr2,'githubBranchRefHead':r2,'githubRemoteBranchHead':remote2,'worktree':st,'sourceIds':50,'cells':600,'currentMissingIdsCount':len(ids),'currentMissingIdsSha256':ids_sha,'sourceCallerReferences':sum(len(x['callerRefs']) for x in caller_rows),'sourceCallerGaps':caller_gaps,'genericPipelineReferences':len(pipeline_rows),'genericPipelineGaps':pipeline_gaps,'catalogCount':len(catalog_infos),'w849BoundaryRows':len(boundary),'w849BoundaryMatches':sum(x['matchesPreviousCrossReviewFinal'] for x in boundary),'priorPrimaryPacketCount':len(prior_packets),'priorDispositionsRecorded':len(prior_decisions),'priorOverlapCount':len(overlap)})
print(json.dumps({'head':HEAD,'tree':TREE,'sources':len(rows),'cells':len(cells),'callerRefs':sum(len(x['callerRefs']) for x in caller_rows),'callerFiles':len(caller_files),'callerGaps':caller_gaps,'pipelineRefs':len(pipeline_rows),'pipelineGaps':pipeline_gaps,'catalogs':len(catalog_infos),'queueCount':len(ids),'queueSha':ids_sha,'w849Matches':sum(x['matchesPreviousCrossReviewFinal'] for x in boundary),'priorPackets':len(prior_packets),'priorDispositions':len(prior_decisions),'priorOverlap':len(overlap),'checksPassed':True},ensure_ascii=False,indent=2))
