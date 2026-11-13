from __future__ import annotations
import collections, hashlib, json, pathlib, subprocess

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-primary-20261102')
WORK=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0700-0749-02f0d84')
REPO='snapetech-org/chaptarrng'; PR=190
HEAD='02f0d841b54c7806005fc67973973799c6960bcf'; TREE='eab2516e48adf4586f14cb131dc1ca6876f87e5f'
LOCALES={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
PRIOR=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-primary-20261102')
CROSS=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-crossreview-independent-20261102')
SRC='src/NzbDrone.Core/Localization/Core/en.json'
FOLLOW='docs/localization/source-followup-20261101.json'
REGISTRY='docs/localization/server-message-sources.json'
PIPELINE='docs/localization/server-message-callers.json'

def sha(data): return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()
def jbytes(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def run(args,text=True): return subprocess.check_output(args,text=text)
def git(*args,text=True): return run(['git','-C',str(WORK),*args],text=text)
def readgit(path): return git('show',f'{HEAD}:{path}',text=False)
def tracked(path):
 b=readgit(path); return {'path':path,'blob':git('rev-parse',f'{HEAD}:{path}').strip(),'sha256':sha(b),'bytes':len(b)}
def writej(path,obj): (OUT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def writejl(path,rows): (OUT/path).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def placeholders(s): return sorted(set(__import__('re').findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if __import__('re').fullmatch(r'<[^<>/]+>',s): return []
 return __import__('re').findall(r'</?[A-Za-z][^>]*>',s)
def live_pr():
 p=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
 t=run(['gh','api',f'repos/{REPO}/commits/{p["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 r=run(['git','ls-remote',f'https://github.com/{REPO}.git',f'refs/heads/{p["headRefName"]}']).split()[0]
 return p,t,r
def checksum_packet(path):
 sums=path/'SHA256SUMS'
 if not sums.is_file(): raise SystemExit(f'missing checksum file {sums}')
 for line in sums.read_text().splitlines():
  digest,name=line.split('  ',1); f=path/name
  if not f.is_file() or sha(f.read_bytes())!=digest: raise SystemExit(f'checksum mismatch: {f}')

# Exact live pin, clean snapshot, and clean destination.
pr,api_tree,remote=live_pr()
assert pr['state']=='OPEN' and pr['isDraft'] is True and pr['headRefOid']==HEAD and api_tree==TREE and remote==HEAD,(pr,api_tree,remote)
assert git('rev-parse','HEAD').strip()==HEAD and git('rev-parse','HEAD^{tree}').strip()==TREE
assert git('status','--porcelain').strip()==''
assert {p.name for p in OUT.iterdir()} <= {'prepare_input.py'},f'output directory already contains packet artifacts: {list(OUT.iterdir())[:5]}'

# Check the prior W650 primary/cross-review packets and reconcile their applied targets.
checksum_packet(PRIOR); checksum_packet(CROSS)
ps=json.loads((PRIOR/'summary.json').read_text()); xs=json.loads((CROSS/'summary.json').read_text())
assert (ps['exactHead'],ps['exactTree'])==('4701933a50d367406fd6749c4baaf4befee22129','2b22ea480c934d2dc41c6813b1296f1a3c41b027')
assert (xs['head'],xs['tree'])==(ps['exactHead'],ps['exactTree'])

src_bytes=readgit(SRC); source=json.loads(src_bytes)
follow_bytes=readgit(FOLLOW); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
ids_hash=sha(jbytes(ids)); assert ids_hash==follow['currentMissingIdsSha256']
selected=ids[700:750]; assert len(selected)==50 and not set(selected)&set(ids[:700])
source_rows=[{'sourceOrdinal':o,'sourceId':sid,'source':source[sid],'sourceKeySha256':sha(sid),'sourceTextSha256':sha(source[sid]),'sourceCatalogBlob':git('rev-parse',f'HEAD:{SRC}').strip(),'sourceCatalogSha256':sha(src_bytes)} for o,sid in enumerate(selected,700)]
catalog_paths={loc:f'src/NzbDrone.Core/Localization/Core/{file}' for loc,file in LOCALES.items()}
catalogs={}; catalog_infos={}
for loc,path in catalog_paths.items():
 raw=readgit(path); data=json.loads(raw)
 assert set(data)==set(source),f'catalog key set drift: {loc}'
 catalogs[loc]=data; catalog_infos[loc]=tracked(path)
source_info=tracked(SRC); follow_info=tracked(FOLLOW); registry_info=tracked(REGISTRY); pipeline_info=tracked(PIPELINE)
registry=json.loads(readgit(REGISTRY)); registry_by={x['id']:x for x in registry['records']}
assert all(sid in registry_by for sid in selected)

# Reattest production callers from the exact-head server-message registry.
caller_rows=[]; callers_by={}; gaps=[]; stale_registry_refs=[]; caller_file_infos={}
for ordinal,sid in enumerate(selected,700):
 rec=registry_by[sid]
 assert rec.get('source')==source[sid],f'registry source differs at {ordinal} {sid}'
 refs=[]; seen=set()
 for call in rec.get('callsites',[]):
  path=call['file']; lines=readgit(path).decode('utf-8').splitlines()
  n=call['line']; line=lines[n-1] if 1<=n<=len(lines) else None
  valid=line is not None and line.strip()==call['sourceLine'] and sha(line.strip())==call['sourceLineSha256']
  if not valid:
   hits=[(i+1,v) for i,v in enumerate(lines) if sid in v]
   if not hits:
    # A source-text-only callsite can legitimately omit the generated ID.
    needle=call['sourceLine'].strip()
    hits=[(i+1,v) for i,v in enumerate(lines) if needle and needle in v.strip()]
   if not hits:
    stale_registry_refs.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':path,'registryLine':n,'registryLineText':call.get('sourceLine'),'reason':'registry line stale and no current source-ID/literal line found'})
    continue
   stale_registry_refs.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':path,'registryLine':n,'registryLineText':call.get('sourceLine'),'reason':'registry line changed; current production source-ID/literal line was refreshed'})
   cand=hits
  else: cand=[(n,line)]
  for lineno,text in cand:
   if (path,lineno) in seen: continue
   seen.add((path,lineno)); raw=readgit(path); current=raw.decode('utf-8').splitlines()
   refs.append({'file':path,'line':lineno,'kind':call.get('category','source-registry-callsite'),'surface':call.get('surface'),'registryLine':n,'registryLineSha256':call.get('sourceLineSha256'),'currentLineText':text.strip(),'currentLineSha256':sha(text.strip()),'currentFileBlob':git('rev-parse',f'HEAD:{path}').strip(),'currentFileSha256':sha(raw),'contextBefore':[x.strip() for x in current[max(0,lineno-4):lineno-1]],'contextAfter':[x.strip() for x in current[lineno:min(len(current),lineno+3)]],'registryPinReattested':valid})
   caller_file_infos[path]=tracked(path)
 if not refs: gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'reason':'no current source registry caller reference reattested'})
 refs.sort(key=lambda x:(x['file'],x['line']))
 caller_hash=sha(jbytes(refs)); callers_by[sid]=refs
 caller_rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'callerReferenceStatus':'pinned' if refs else 'gap','callerRefs':refs,'callerContextSha256':caller_hash,'sourceRegistryCategory':rec.get('category'),'sourceRegistrySurface':rec.get('surface'),'sourcePatterns':rec.get('patterns',[]),'protectedLiterals':rec.get('protectedLiterals',[]),'sourceRegistryFingerprint':rec.get('sourceFingerprint')})

# Reattest the generic frontend translation surfaces for server messages.
pipeline=json.loads(readgit(PIPELINE)); pipeline_refs=[]; pipeline_gaps=[]
for entry in pipeline['callsites']:
 path=entry['file']; raw=readgit(path); lines=raw.decode('utf-8').splitlines(); n=entry['line']; line=lines[n-1] if 1<=n<=len(lines) else None
 if line is None or line.strip()!=entry['sourceLine'] or sha(line.strip())!=entry['sourceLineSha256']:
  pipeline_gaps.append({'file':path,'line':n,'reason':'frontend pipeline caller pin differs from exact head'}); continue
 pipeline_refs.append({'file':path,'line':n,'lineText':line.strip(),'lineSha256':sha(line.strip()),'fileBlob':git('rev-parse',f'HEAD:{path}').strip(),'fileSha256':sha(raw),'contextBefore':[x.strip() for x in lines[max(0,n-4):n-1]],'contextAfter':[x.strip() for x in lines[n:min(len(lines),n+3)]],'surface':'generic server-message translation pipeline'})
 caller_file_infos.update({x['file']:tracked(x['file']) for x in pipeline_refs})

# Freeze exact current locale targets and structural/token parity for all 600 cells.
input_cells=[]
for row in source_rows:
 sid=row['sourceId']; src=row['source']
 for loc,path in catalog_paths.items():
  target=catalogs[loc][sid]; rec=registry_by[sid]; protected=rec.get('protectedLiterals',[])
  input_cells.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'locale':loc,'source':src,'sourceKeySha256':row['sourceKeySha256'],'sourceTextSha256':row['sourceTextSha256'],'sourceFile':SRC,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'currentTarget':target,'currentTargetSha256':sha(target),'targetFile':path,'targetFileBlob':catalog_infos[loc]['blob'],'targetFileSha256':catalog_infos[loc]['sha256'],'sourcePlaceholders':placeholders(src),'currentTargetPlaceholders':placeholders(target),'sourceMarkup':markup(src),'currentTargetMarkup':markup(target),'placeholderParity':placeholders(src)==placeholders(target),'markupParity':markup(src)==markup(target),'protectedLiterals':protected,'protectedLiteralChecks':[{'literal':x,'presentInSource':x in src,'presentInCurrentTarget':x in target} for x in protected],'callerContextSha256':callers_by[sid] and sha(jbytes(callers_by[sid]))})

# Verify all 600 W650 applied values against independent cross-review finals.
prior_cells=[json.loads(x) for x in (CROSS/'cell-crossreview.jsonl').read_text().splitlines()]
assert len(prior_cells)==600
prior_diffs=[]; source_changes={}; w699=[]
prior_sid=ids[699]; prior_refs=[]
for call in registry_by[prior_sid].get('callsites',[]):
 path=call['file']; lines=readgit(path).decode('utf-8').splitlines(); n=call['line']; line=lines[n-1] if 1<=n<=len(lines) else None
 if line is None or line.strip()!=call['sourceLine'] or sha(line.strip())!=call['sourceLineSha256']:
  hits=[(i+1,v) for i,v in enumerate(lines) if prior_sid in v]
  if not hits: continue
  candidates=hits
 else: candidates=[(n,line)]
 for lineno,text in candidates:
  raw=readgit(path); content=raw.decode('utf-8').splitlines()
  prior_refs.append({'file':path,'line':lineno,'kind':call.get('category','source-registry-callsite'),'surface':call.get('surface'),'registryLine':n,'registryLineSha256':call.get('sourceLineSha256'),'currentLineText':text.strip(),'currentLineSha256':sha(text.strip()),'currentFileBlob':git('rev-parse',f'HEAD:{path}').strip(),'currentFileSha256':sha(raw),'contextBefore':[v.strip() for v in content[max(0,lineno-4):lineno-1]],'contextAfter':[v.strip() for v in content[lineno:min(len(content),lineno+3)]],'registryPinReattested':True})
assert prior_refs,f'W699 caller context is missing for {prior_sid}'
prior_context_hash=sha(jbytes(prior_refs))
for x in prior_cells:
 sid=ids[x['sourceOrdinal']]; loc=x['locale']; live_source=source[sid]; live_target=catalogs[loc][sid]
 if sid!=x['sourceId']: prior_diffs.append({'sourceOrdinal':x['sourceOrdinal'],'locale':loc,'kind':'source-id','prior':x['sourceId'],'live':sid})
 if live_source!=x['sourceText']:
  source_changes[(x['sourceOrdinal'],sid)]=(x['sourceText'],live_source)
 if live_target!=x['independentlyPreferredTarget']:
  prior_diffs.append({'sourceOrdinal':x['sourceOrdinal'],'locale':loc,'kind':'live-target','live':live_target,'crossReviewFinal':x['independentlyPreferredTarget']})
 if x['sourceOrdinal']==699:
  w699.append({'sourceOrdinal':699,'sourceId':sid,'locale':loc,'source':live_source,'sourceTextSha256':sha(live_source),'liveTarget':live_target,'liveTargetSha256':sha(live_target),'priorCrossReviewFinalTarget':x['independentlyPreferredTarget'],'priorCrossReviewFinalTargetSha256':x['independentlyPreferredTargetSha256'],'callerContext':prior_refs,'callerContextSha256':prior_context_hash})
assert len(w699)==12 and not prior_diffs
writej('prior-w650-reconciliation.json',{'primaryHead':ps['exactHead'],'primaryTree':ps['exactTree'],'crossReviewHead':xs['head'],'crossReviewTree':xs['tree'],'currentHead':HEAD,'currentTree':TREE,'primaryAndCrossReviewChecksumsVerified':True,'priorSourceIdCount':50,'priorCellCount':600,'liveTargetsMatchCrossReviewFinal':600,'liveTargetDiffs':prior_diffs,'sourceTextChangesSinceReview':[{'sourceOrdinal':o,'sourceId':sid,'priorSource':before,'liveSource':after,'sourceTextSha256':sha(after)} for (o,sid),(before,after) in source_changes.items()],'sourceChangesCount':len(source_changes),'w654SourceTypoCorrected':'SABnzbd' in source[ids[654]],'w695ThroughMailgunSourceCorrected':'through Mailgun' in source[ids[695]],'recommendation':'W650 is applied: all 600 live locale values match independent cross-review final targets; source typos at W654 and W695 are corrected at the current head.'})
writejl('w699-boundary-reattestation.jsonl',w699)

# Pin previous boundary IDs and detect any prior source ID/disposition overlap.
prior_ids=set(ids[:700]); selected_set=set(selected)
overlap=[]
for packet in sorted(OUT.parent.glob('chaptarrng-pr190-*')):
 if packet.resolve()==OUT.resolve(): continue
 for fp in packet.rglob('*.jsonl'):
  try: lines=fp.read_text().splitlines()
  except Exception: continue
  for line in lines:
   try: x=json.loads(line)
   except Exception: continue
   sid=x.get('sourceId',x.get('id',x.get('catalogKey')))
   ordinal=x.get('sourceOrdinal',x.get('sourcePosition',x.get('windowOrdinal')))
   disposition=next((x.get(k) for k in ('disposition','primaryDisposition','crossDisposition','crossReviewDisposition','finalDisposition','independentDisposition') if x.get(k) is not None),None)
   if sid in selected_set and disposition is not None: overlap.append({'path':str(fp),'sourceOrdinal':ordinal,'sourceId':sid,'locale':x.get('locale'),'disposition':disposition})
assert not overlap

writejl('source-slice.jsonl',source_rows)
writejl('caller-context.jsonl',caller_rows)
writejl('input-cells.jsonl',input_cells)
writejl('pipeline-caller-context.jsonl',pipeline_refs)
writej('caller-context-summary.json',{'sourceCallerRows':len(caller_rows),'sourceCallerRefs':sum(len(x['callerRefs']) for x in caller_rows),'uniqueSourceCallerFiles':len({r['file'] for c in caller_rows for r in c['callerRefs']}),'sourceCallerGaps':gaps,'staleRegistryPinsRefreshed':stale_registry_refs,'genericPipelineRefs':len(pipeline_refs),'genericPipelineFiles':len({r['file'] for r in pipeline_refs}),'genericPipelineGaps':pipeline_gaps})
writej('prior-disposition-boundary.json',{'scopePositions':[700,749],'sourceIds':50,'selectedSourceIdListSha256':sha(jbytes(selected)),'uniqueSourceIds':len(set(selected))==50,'priorSourceIdCount':700,'priorSourceIdsDisjoint':not bool(selected_set & prior_ids),'exactPriorDispositionOverlapRows':overlap,'exactPriorDispositionOverlapCount':len(overlap),'w650Applied':len(prior_cells)==600 and not prior_diffs,'w699BoundaryRows':len(w699),'w699BoundarySourceTargetMatchesPriorCrossReview':sum(x['liveTarget']==x['priorCrossReviewFinalTarget'] for x in w699),'priorW650Reconciliation':'prior-w650-reconciliation.json','priorPacketChecksumsVerified':True})

# Frozen exact-head input manifest and input checksums for all catalogs and callers.
caller_files=sorted(caller_file_infos.values(),key=lambda x:x['path'])
source_caller_files={r['file'] for c in caller_rows for r in c['callerRefs']}
pipeline_caller_files={r['file'] for r in pipeline_refs}
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'livePullRequest':pr,'remoteBranchHead':remote,'scope':{'positions':[700,749],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceListCount':len(ids),'sourceListSha256':ids_hash,'selectedSourceIds':selected,'selectedSourceIdListSha256':sha(jbytes(selected)),'sourceCatalog':source_info,'sourceFollowup':follow_info,'serverMessageRegistry':registry_info,'genericCallerRegistry':pipeline_info,'localeCatalogs':catalog_infos,'callerFiles':caller_files,'callerReferences':sum(len(x['callerRefs']) for x in caller_rows),'sourceCallerFiles':len(source_caller_files),'genericPipelineReferences':len(pipeline_refs),'genericPipelineCallerFiles':len(pipeline_caller_files),'callerGaps':gaps,'staleRegistryPinsRefreshed':stale_registry_refs,'priorW650':{'head':ps['exactHead'],'tree':ps['exactTree'],'crossReviewHead':xs['head'],'crossReviewTree':xs['tree'],'targetsMatch':600,'sourceChangesSinceReview':len(source_changes)},'priorBoundaryOrdinal':699,'priorExactDispositionOverlap':len(overlap),'worktree':str(WORK),'worktreeClean':True}
writej('input-manifest.json',manifest)
all_input_infos=[source_info,follow_info,registry_info,pipeline_info,*catalog_infos.values(),*caller_files]
inputs={x['path']:x['sha256'] for x in all_input_infos}
(OUT/'INPUT-SHA256SUMS').write_text(''.join(f'{digest}  {path}\n' for path,digest in sorted(inputs.items())))

# Final exact-head/ref reattestation before packet authoring proceeds.
pr2,tree2,remote2=live_pr()
repo_state={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'status':git('status','--porcelain').strip()}
assert pr2['state']=='OPEN' and pr2['isDraft'] is True and pr2['headRefOid']==HEAD and tree2==TREE and remote2==HEAD and repo_state=={'head':HEAD,'tree':TREE,'status':''}
writej('prepare-reattestation.json',{'passed':True,'head':HEAD,'tree':TREE,'livePullRequest':pr2,'remoteBranchHead':remote2,'repoState':repo_state,'sourceIds':50,'cells':600,'callerGaps':gaps,'registryPinsRefreshed':len(stale_registry_refs),'priorW650TargetsMatching':600,'w699BoundaryRows':len(w699)})
print(json.dumps({'head':HEAD,'tree':TREE,'sources':len(source_rows),'cells':len(input_cells),'callerRefs':sum(len(x['callerRefs']) for x in caller_rows),'callerFiles':len(caller_files),'callerGaps':gaps,'staleRegistryPinsRefreshed':len(stale_registry_refs),'W650TargetsMatchingCrossReview':600,'W650SourceChanges':len(source_changes),'W699BoundaryRows':len(w699),'priorOverlap':len(overlap),'reattestPassed':True},ensure_ascii=False,indent=2))
