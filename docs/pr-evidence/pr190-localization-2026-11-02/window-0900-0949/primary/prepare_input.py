from __future__ import annotations
import datetime, hashlib, json, pathlib, re, subprocess, time
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0900-0949-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
REPO='snapetech-org/ChaptarrNG'; PR=190; BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='a9a74f6ba733e8c1f06a2d260bd802d4fde2da0e'; TREE='d9d25f309f3a7256056b4ed8deb1dabee58b64fe'
ALL=[('snapetech-org/ChaptarrNG',190),('snapetech-org/SeerrNG',418),('snapetech-org/slskR',204),('snapetech-org/QuestarrNG',155),('snapetech-org/TorrentNG',243),('snapetech-org/slskdN',409),('snapetech-org/ROMarrNG',70)]
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
SRC='src/NzbDrone.Core/Localization/Core/en.json'; FOLLOW='docs/localization/source-followup-20261101.json'
REG_SERVER='docs/localization/server-message-sources.json'; REG_PROVIDER='docs/localization/provider-option-sources.json'; PIPE_SERVER='docs/localization/server-message-callers.json'
MANUAL_PROTECTED={'server.message.mf726e9f7b242':['MetadataProfileId'],'server.message.mf81018a04cff':['main'],'server.message.mfcc0e5918290':['Book Title','PartNumber','Original Title'],'server.message.mfde3b9fa63a8':['IPv6'],'server.message.mfa82f5859e19':['ValidationFailure'],'provider.option.o477e5af2fd7e':['Scene']}
PRIOR_ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch')
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def run(a,text=True):
 err=None
 for attempt in range(3):
  try: return subprocess.check_output(a,text=text,stderr=subprocess.PIPE)
  except subprocess.CalledProcessError as e:
   err=e
   if attempt<2: time.sleep(2)
 raise err
def git(*a,text=True): return run(['git','-C',str(WORK),*a],text=text)
def show(path): return git('show',f'{HEAD}:{path}',text=False)
def tracked(path):
 raw=show(path); return {'path':path,'blob':git('rev-parse',f'{HEAD}:{path}').strip(),'sha256':sha(raw),'bytes':len(raw)}
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def jsoncmd(a): return json.loads(run(a))
def query_all():
 out=[]
 for repo,num in ALL:
  p=jsoncmd(['gh','pr','view',str(num),'--repo',repo,'--json','number,state,isDraft,headRefOid,headRefName,baseRefName,url'])
  branch=p['headRefName']
  tree=run(['gh','api',f'repos/{repo}/commits/{p["headRefOid"]}','--jq','.commit.tree.sha']).strip() if num==PR else None
  ref=jsoncmd(['gh','api',f'repos/{repo}/git/ref/heads/{branch}'])['object']['sha']
  remote_text=run(['git','ls-remote',f'https://github.com/{repo}.git',f'refs/heads/{branch}']).strip()
  remote=remote_text.split()[0] if remote_text else None
  out.append({'repository':repo,'pullRequest':num,'state':p['state'],'isDraft':p['isDraft'],'branch':branch,'head':p['headRefOid'],'tree':tree,'apiBranchRefHead':ref,'remoteBranchRef':remote_text,'remoteBranchHead':remote,'apiAndRemoteAgree':ref==remote==p['headRefOid'],'url':p['url']})
 assert all(x['apiAndRemoteAgree'] for x in out),out
 x=next(x for x in out if x['pullRequest']==PR)
 assert x['state']=='OPEN' and x['isDraft'] and x['head']==HEAD and x['tree']==TREE and x['branch']==BRANCH,x
 return {'queriedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'GitHub PR API, commit-tree API, branch-ref API, HTTPS git ls-remote','pullRequests':out}
def local_state():
 return {'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
def verify_packet_sums(folder):
 sums=folder/'SHA256SUMS'; assert sums.is_file(),folder
 for line in sums.read_text().splitlines():
  h,n=line.split('  ',1); assert sha((folder/n).read_bytes())==h,(folder,n)
 return sha(sums.read_bytes())
# Exact prefreeze refs, worktree, branch, and path state.
assert local_state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
# Output directory is task-owned and may contain artifacts from a previous failed preparation run.
start_heads=query_all(); writej('all-seven-pr-heads-start.json',start_heads)
initial=next(x for x in start_heads['pullRequests'] if x['pullRequest']==PR)
remote_url=git('remote','get-url','github').strip()
assert remote_url.rstrip('/').lower().endswith('snapetech-org/chaptarrng.git'),remote_url
# Freeze queue/source order. Queue positions, not catalog key order, define W900–949.
source_raw=show(SRC); source=json.loads(source_raw); source_info=tracked(SRC)
follow_raw=show(FOLLOW); follow=json.loads(follow_raw); follow_info=tracked(FOLLOW)
ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
queue_sha=sha(jbytes(ids)); assert queue_sha==follow['currentMissingIdsSha256']=='a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c'
selected=ids[900:950]; assert len(selected)==50 and len(set(selected))==50 and not(set(selected)&set(ids[:900]))
(OUT/'current-missing-ids.json').write_text(json.dumps(ids,ensure_ascii=False,indent=2)+'\n')
server_raw=show(REG_SERVER); server_reg=json.loads(server_raw); server_records={x['id']:x for x in server_reg['records']}
provider_raw=show(REG_PROVIDER); provider_reg=json.loads(provider_raw); provider_records={x['id']:x for x in provider_reg['records']}
registry_files={REG_SERVER:tracked(REG_SERVER),REG_PROVIDER:tracked(REG_PROVIDER)}
source_rows=[]; records={}
for ordinal,sid in enumerate(selected,900):
 regname=REG_SERVER if sid.startswith('server.message.') else REG_PROVIDER if sid.startswith('provider.option.') else None
 assert regname,(ordinal,sid)
 rec=(server_records if regname==REG_SERVER else provider_records).get(sid)
 assert rec and sid in source and rec.get('source')==source[sid],(ordinal,sid,'source/registry mismatch')
 records[sid]=(regname,rec)
 protected=list(rec.get('protectedLiterals',[]))
 for term in MANUAL_PROTECTED.get(sid,[]):
  if term not in protected: protected.append(term)
 source_rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'sourceKeySha256':sha(sid),'sourceTextSha256':sha(source[sid]),'sourceCatalogPath':SRC,'sourceCatalogBlob':source_info['blob'],'sourceCatalogSha256':source_info['sha256'],'sourceRegistryPath':regname,'sourceRegistryBlob':registry_files[regname]['blob'],'sourceRegistrySha256':registry_files[regname]['sha256'],'sourceRegistryFingerprint':rec.get('sourceFingerprint'),'sourceRegistryProtectedLiterals':rec.get('protectedLiterals',[]),'manualProtectedLiterals':MANUAL_PROTECTED.get(sid,[]),'effectiveProtectedLiterals':protected,'registryCategory':rec.get('category'),'registrySurface':rec.get('surface'),'registryParameters':rec.get('parameters',[]),'registryPatterns':rec.get('patterns',[]),'registrySourceTemplates':rec.get('sourceTemplates',[])})
assert [x['sourceId'] for x in source_rows]==selected
# Freeze all 12 complete catalogs and values.
locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{fn}' for loc,fn in LOCALES.items()}
catalogs={}; catalog_infos={}
for loc,path in locale_paths.items():
 raw=show(path); catalog=json.loads(raw); assert set(catalog)==set(source),(loc,'catalog key-set mismatch')
 catalogs[loc]=catalog; catalog_infos[loc]=tracked(path)
# Capture exact direct caller/source references and adjacent context from both source registries.
caller_rows=[]; caller_files={}; callers_by={}; caller_gaps=[]; stale=[]
for srcrow in source_rows:
 sid=srcrow['sourceId']; regname,rec=records[sid]; refs=[]; local_seen=set()
 for pin in rec.get('callsites',[]):
  path=pin['file']; raw=show(path); lines=raw.decode('utf-8').splitlines(); n=pin['line']; line=lines[n-1] if 1<=n<=len(lines) else None
  expected=pin.get('sourceLine','').strip(); expected_sha=pin.get('sourceLineSha256')
  exact=line is not None and line.strip()==expected and sha(line.strip())==expected_sha
  hits=[(n,line)] if exact else [(i+1,v) for i,v in enumerate(lines) if sid in v]
  if not exact: stale.append({'sourceOrdinal':srcrow['sourceOrdinal'],'sourceId':sid,'file':path,'registryLine':n,'registryLineSha256':expected_sha,'currentMatches':[{'line':i,'text':v.strip(),'sha256':sha(v.strip())} for i,v in hits],'reason':'registry caller pin differs at exact head'})
  for lineno,text in hits:
   if (path,lineno) in local_seen: continue
   local_seen.add((path,lineno))
   refs.append({'file':path,'line':lineno,'lineText':text.strip(),'lineSha256':sha(text.strip()),'fileBlob':git('rev-parse',f'{HEAD}:{path}').strip(),'fileSha256':sha(raw),'contextBefore':[v.strip() for v in lines[max(0,lineno-4):lineno-1]],'contextAfter':[v.strip() for v in lines[lineno:min(len(lines),lineno+3)]],'registryLine':n,'registrySourceLine':expected,'registrySourceLineSha256':expected_sha,'registryPinExact':exact,'category':pin.get('category'),'surface':pin.get('surface'),'kind':pin.get('kind'),'enum':pin.get('enum'),'member':pin.get('member')})
   caller_files[path]=tracked(path)
 refs.sort(key=lambda x:(x['file'],x['line']))
 if not refs: caller_gaps.append({'sourceOrdinal':srcrow['sourceOrdinal'],'sourceId':sid,'reason':'no direct caller location could be pinned'})
 callers_by[sid]=refs
 caller_rows.append({'sourceOrdinal':srcrow['sourceOrdinal'],'sourceId':sid,'source':srcrow['source'],'registryPath':regname,'directCallerReferences':refs,'callerReferenceCount':len(refs),'callerContextSha256':sha(jbytes(refs)),'callerReferenceStatus':'pinned' if refs else 'gap','registryCategory':rec.get('category'),'registrySurface':rec.get('surface'),'enumOrParameterContext':[{'enum':x.get('enum'),'member':x.get('member'),'kind':x.get('kind')} for x in rec.get('callsites',[])],'protectedLiterals':srcrow['effectiveProtectedLiterals']})
# Generic server-message translation pipeline refs from its exact registry.
pipeline_server_raw=show(PIPE_SERVER); pipeline_server=json.loads(pipeline_server_raw); pipeline_rows=[]; pipeline_gaps=[]
for pin in pipeline_server['callsites']:
 path=pin['file']; raw=show(path); lines=raw.decode('utf-8').splitlines(); n=pin['line']; line=lines[n-1] if 1<=n<=len(lines) else None
 exact=line is not None and line.strip()==pin['sourceLine'].strip() and sha(line.strip())==pin['sourceLineSha256']
 if not exact:
  pipeline_gaps.append({'file':path,'line':n,'reason':'generic server-message pipeline registry pin mismatch'}); continue
 pipeline_rows.append({'pipeline':'server-message id/template frontend display','file':path,'line':n,'lineText':line.strip(),'lineSha256':sha(line.strip()),'fileBlob':git('rev-parse',f'{HEAD}:{path}').strip(),'fileSha256':sha(raw),'contextBefore':[v.strip() for v in lines[max(0,n-4):n-1]],'contextAfter':[v.strip() for v in lines[n:min(len(lines),n+3)]],'registryLine':n,'surface':'generic server-message localized display'})
 caller_files[path]=tracked(path)
# Runtime pipeline for provider.option labels/hints: enum FieldOption -> server-side ILocalizationService -> schema -> frontend select display.
provider_pipe_specs=[
 ('src/Chaptarr.Http/ClientSchema/SchemaBuilder.cs',[43,47,49,50,246,248],'SchemaBuilder localizes option.Name and provider.option.* hints using ILocalizationService before returning provider schema.'),
 ('src/NzbDrone.Core/Localization/LocalizationService.cs',[69,79,84],'server localization looks up the locale dictionary by key and returns the key when untranslated.'),
 ('frontend/src/Components/Form/ProviderFieldFormGroup.js',[52,55,56,122],'provider field schema options are mapped to display values and passed to FormInputGroup.'),
 ('frontend/src/Components/Form/FormInputGroup.js',[99,100],'select fields use EnhancedSelectInput.'),
 ('frontend/src/Components/Form/EnhancedSelectInput.js',[546,563,620,637],'enhanced select displays option values and hints verbatim.'),
 ('frontend/src/Components/Form/HintedSelectInputOption.js',[36],'option component displays the localized value and hint verbatim.')
]
provider_pipeline=[]
for path,nums,why in provider_pipe_specs:
 raw=show(path); lines=raw.decode('utf-8').splitlines()
 for n in nums:
  assert 1<=n<=len(lines),(path,n)
  line=lines[n-1]
  provider_pipeline.append({'pipeline':'provider-option server localization and UI display','file':path,'line':n,'lineText':line.strip(),'lineSha256':sha(line.strip()),'fileBlob':git('rev-parse',f'{HEAD}:{path}').strip(),'fileSha256':sha(raw),'contextBefore':[v.strip() for v in lines[max(0,n-4):n-1]],'contextAfter':[v.strip() for v in lines[n:min(len(lines),n+3)]],'interpretation':why})
 caller_files[path]=tracked(path)
# Freeze the 600 exact cells and technical comparisons.
cell_rows=[]
for row in source_rows:
 sid=row['sourceId']; rec=records[sid][1]; protected=row['effectiveProtectedLiterals']
 for loc,path in locale_paths.items():
  target=catalogs[loc][sid]
  checks=[{'literal':term,'inSource':term in row['source'],'inCurrentTarget':term in target} for term in protected]
  cell_rows.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'locale':loc,'source':row['source'],'sourceKeySha256':row['sourceKeySha256'],'sourceTextSha256':row['sourceTextSha256'],'sourceFile':SRC,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'currentTarget':target,'currentTargetSha256':sha(target),'targetFile':locale_paths[loc],'targetFileBlob':catalog_infos[loc]['blob'],'targetFileSha256':catalog_infos[loc]['sha256'],'sourcePlaceholders':placeholders(row['source']),'currentTargetPlaceholders':placeholders(target),'placeholderParity':placeholders(row['source'])==placeholders(target),'sourceMarkup':markup(row['source']),'currentTargetMarkup':markup(target),'markupParity':markup(row['source'])==markup(target),'protectedLiterals':protected,'protectedLiteralChecks':checks,'protectedLiteralCurrentFailures':[x['literal'] for x in checks if not x['inCurrentTarget']],'callerContextSha256':sha(jbytes(callers_by[sid]))})
assert len(cell_rows)==600
# Reattest predecessor packets and exact prior disposition records through queue position 899.
p850=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
x850=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-crossreview-20261102')
p850_sums=verify_packet_sums(p850); x850_sums=verify_packet_sums(x850)
p850_manifest=json.loads((p850/'manifest.json').read_text()); x850_manifest=json.loads((x850/'cross-review-summary.json').read_text())
prior_0_849=[json.loads(x) for x in (p850/'prior-disposition-hashes.jsonl').read_text().splitlines()]
prior_850_899=[json.loads(x) for x in (x850/'cross-review-ledger.jsonl').read_text().splitlines()]
assert len(prior_0_849)==10200 and len(prior_850_899)==600
assert all(x.get('sourceOrdinal') is not None and 0<=x['sourceOrdinal']<=849 for x in prior_0_849)
assert all(x.get('sourceOrdinal') is not None and 850<=x['sourceOrdinal']<=899 for x in prior_850_899)
assert len({(x['sourceOrdinal'],x['locale']) for x in prior_0_849})==10200
assert len({(x['sourceOrdinal'],x['locale']) for x in prior_850_899})==600
prior_records=[]
for x in prior_0_849:
 ordinal=x['sourceOrdinal']; sid=x['sourceId']; loc=x['locale']; live=catalogs[loc].get(sid)
 prior_records.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'sourceTextSha256':x.get('priorSourceTextSha256'),'priorDisposition':x.get('priorDisposition'),'priorFinalTargetSha256':x.get('priorFinalTargetSha256'),'priorCurrentTargetSha256':x.get('priorCurrentTargetSha256'),'liveCurrentTargetSha256':sha(live) if live is not None else None,'liveTargetMatchesPriorFinalHash':live is not None and sha(live)==x.get('priorFinalTargetSha256'),'priorPacket':x.get('priorPacket'),'priorRecordFile':x.get('priorRecordFile'),'priorRecordSha256':x.get('priorRecordSha256')})
for x in prior_850_899:
 ordinal=x['sourceOrdinal']; sid=x['sourceId']; loc=x['locale']; live=catalogs[loc].get(sid)
 prior_records.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'sourceTextSha256':x.get('sourceTextSha256'),'priorDisposition':x.get('primaryDisposition'),'priorCrossReviewDisposition':x.get('crossReviewDisposition'),'priorFinalTargetSha256':x.get('crossReviewFinalTargetSha256',x.get('finalTargetSha256')),'priorCurrentTargetSha256':x.get('currentTargetSha256'),'liveCurrentTargetSha256':sha(live) if live is not None else None,'liveTargetMatchesPriorFinalHash':live is not None and sha(live)==x.get('crossReviewFinalTargetSha256',x.get('finalTargetSha256')),'priorPacket':'chaptarrng-pr190-window-0850-0899-crossreview-20261102','priorRecordFile':'cross-review-ledger.jsonl','priorRecordSha256':sha(json.dumps(x,ensure_ascii=False,sort_keys=True).encode())})
assert len(prior_records)==10800
selected_keyset={(x['sourceOrdinal'],loc) for x in source_rows for loc in LOCALES}
prior_keyset={(x['sourceOrdinal'],x['locale']) for x in prior_records}
assert len(prior_keyset)==10800 and not any(900<=o<=949 for o,l in prior_keyset)
# Immediately previous queue position 899 is cross-reviewed and the live value must still match each final.
prev=prior/'unused' if False else ids[899]
prev_rows=[x for x in prior_850_899 if x['sourceOrdinal']==899]
assert len(prev_rows)==12 and all(x['sourceId']==prev for x in prev_rows)
boundary=[]
for x in prev_rows:
 loc=x['locale']; live=catalogs[loc][prev]; final=x.get('crossReviewFinalTarget',x.get('finalTarget'))
 boundary.append({'sourceOrdinal':899,'sourceId':prev,'locale':loc,'source':source[prev],'sourceTextSha256':sha(source[prev]),'primaryDisposition':x.get('primaryDisposition'),'crossReviewDisposition':x.get('crossReviewDisposition'),'previousFinalTarget':final,'previousFinalTargetSha256':x.get('crossReviewFinalTargetSha256',x.get('finalTargetSha256')),'liveTarget':live,'liveTargetSha256':sha(live),'liveMatchesPriorCrossReviewFinal':live==final,'callerContextSha256':x.get('callerContextSha256')})
# Reattest the dedicated W884 source correction as context only; it is outside this window.
w884=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng/docs/pr-evidence/pr190-localization-2026-11-02/window-0850-0899/source-correction/source-correction-record.json')
w884_record=json.loads(w884.read_text())
w884_source=source.get('server.message.mf00d6bc38ae8')
assert w884_record and w884_source and w884_record.get('newSource')==w884_source
w884_context={'path':str(w884),'sha256':sha(w884.read_bytes()),'record':w884_record,'currentSourceTextSha256':sha(w884_source),'currentSourceText':w884_source,'outsideSelectedPositions':True,'instruction':'Specific source-884 follow-up only; no decisions in this packet modify/reopen its 12 locale cells.'}
# Freeze exact source/pipeline/caller/cell and predecessor artifacts.
writejl('source-slice.jsonl',source_rows); writejl('caller-context.jsonl',caller_rows); writejl('input-cells.jsonl',cell_rows)
writejl('server-message-pipeline-context.jsonl',pipeline_rows); writejl('provider-option-pipeline-context.jsonl',provider_pipeline)
writejl('prior-disposition-hashes.jsonl',prior_records); writejl('w899-boundary-reattestation.jsonl',boundary)
writej('source-884-followup-context.json',w884_context)
# Record file pins for the source, registries, queue, locale catalogs, callers, and generic pipelines.
all_info={x['path']:x for x in [source_info,follow_info,tracked(REG_SERVER),tracked(REG_PROVIDER),tracked(PIPE_SERVER),*catalog_infos.values(),*caller_files.values()]}
writej('pinned-files.json',{'head':HEAD,'tree':TREE,'files':sorted(all_info.values(),key=lambda x:x['path']),'count':len(all_info)})
writej('caller-context-summary.json',{'sourceRows':len(caller_rows),'directCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),'uniqueDirectCallerFiles':len({r['file'] for x in caller_rows for r in x['directCallerReferences']}),'callerGaps':caller_gaps,'staleRegistryPins':stale,'serverMessagePipelineReferences':len(pipeline_rows),'serverMessagePipelineGaps':pipeline_gaps,'providerOptionPipelineReferences':len(provider_pipeline),'providerOptionPipelineGaps':[]})
writej('prior-disposition-boundary.json',{'verifiedPriorPrimaryPacket':str(p850),'priorPrimaryManifestSha256':sha((p850/'manifest.json').read_bytes()),'priorPrimarySumsSha256':p850_sums,'priorCrossReviewPacket':str(x850),'priorCrossReviewSummarySha256':sha((x850/'cross-review-summary.json').read_bytes()),'priorCrossReviewSumsSha256':x850_sums,'sourcePositionCoverage':[0,899],'priorCellDispositionRows':len(prior_records),'priorPrimaryRows0Through849':len(prior_0_849),'priorCrossReviewRows850Through899':len(prior_850_899),'priorQueuePositionOverlapWithSelected':0,'w899BoundaryRows':len(boundary),'w899BoundaryLiveMatchesCrossReviewFinal':sum(x['liveMatchesPriorCrossReviewFinal'] for x in boundary),'w899BoundaryAll12Match':all(x['liveMatchesPriorCrossReviewFinal'] for x in boundary),'priorLiveCatalogMatchesFinalCount':sum(x['liveTargetMatchesPriorFinalHash'] for x in prior_records),'priorLiveCatalogMismatchesCount':sum(not x['liveTargetMatchesPriorFinalHash'] for x in prior_records),'priorExactDispositionRows':len(prior_records),'w884SourceCorrectionContext':w884_context})
writej('input-manifest.json',{'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'branch':BRANCH,'livePullRequest':initial,'remoteUrl':remote_url,'scope':{'window':'W900-W949','queuePositionSemantics':'zero-based positions in currentMissingIds from source-followup-20261101.json; these are not catalog key ordinals','positions':[900,949],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceQueue':{'path':FOLLOW,'blob':follow_info['blob'],'sha256':follow_info['sha256'],'count':len(ids),'canonicalCurrentMissingIdsSha256':queue_sha,'queueBaseHead':follow.get('baseHead'),'selectedSourceIds':selected,'selectedSourceIdsSha256':sha(jbytes(selected))},'sourceCatalog':source_info,'sourceRegistries':registry_files,'serverMessagePipelineRegistry':tracked(PIPE_SERVER),'localeCatalogs':catalog_infos,'callerFiles':sorted((all_info[path] for path in caller_files),key=lambda x:x['path']),'sourceCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),'sourceCallerGaps':caller_gaps,'staleRegistryCallerPins':stale,'serverMessagePipelineReferences':len(pipeline_rows),'serverMessagePipelineGaps':pipeline_gaps,'providerOptionPipelineReferences':len(provider_pipeline),'providerOptionPipelineGaps':[],'priorBoundaryQueuePosition':899,'priorDispositionRows':len(prior_records),'priorPositionCoverage':[0,899],'priorOverlapCount':0,'w899BoundaryAll12Match':all(x['liveMatchesPriorCrossReviewFinal'] for x in boundary),'worktree':str(WORK),'worktreeClean':True})
# All seven APIs/branch refs/remote refs and worktree rechecked after freezing the inputs.
end_heads=query_all(); writej('all-seven-pr-heads-after-freeze.json',end_heads)
assert {x['pullRequest']:x['head'] for x in start_heads['pullRequests']}=={x['pullRequest']:x['head'] for x in end_heads['pullRequests']}
assert local_state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
assert all(x['apiAndRemoteAgree'] for x in end_heads['pullRequests'])
writej('prepare-reattestation.json',{'passed':True,'head':HEAD,'tree':TREE,'worktree':local_state(),'allSevenPRHeadsUnchangedDuringFreeze':True,'sourceIds':len(source_rows),'localeCells':len(cell_rows),'sourceQueueCount':len(ids),'sourceQueueCanonicalSha256':queue_sha,'selectedSourceIdsSha256':sha(jbytes(selected)),'directCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),'callerGaps':caller_gaps,'staleRegistryPins':stale,'serverPipelineReferences':len(pipeline_rows),'serverPipelineGaps':pipeline_gaps,'providerOptionPipelineReferences':len(provider_pipeline),'providerPipelineGaps':[],'catalogCount':len(catalog_infos),'priorDispositionRows':len(prior_records),'priorOverlapCount':0,'w899BoundaryRows':len(boundary),'w899BoundaryMatches':sum(x['liveMatchesPriorCrossReviewFinal'] for x in boundary),'w884FollowupSourceContextOnly':True,'allSevenStartHeadsSha256':sha((OUT/'all-seven-pr-heads-start.json').read_bytes()),'allSevenAfterFreezeHeadsSha256':sha((OUT/'all-seven-pr-heads-after-freeze.json').read_bytes())})
print(json.dumps({'head':HEAD,'tree':TREE,'sourceCount':len(source_rows),'cells':len(cell_rows),'positions':[900,949],'queueSha256':queue_sha,'directCallerRefs':sum(x['callerReferenceCount'] for x in caller_rows),'callerGaps':caller_gaps,'stalePins':len(stale),'serverPipelineRefs':len(pipeline_rows),'serverPipelineGaps':pipeline_gaps,'providerPipelineRefs':len(provider_pipeline),'priorRows':len(prior_records),'priorCurrentMatchesFinal':sum(x['liveTargetMatchesPriorFinalHash'] for x in prior_records),'priorCurrentMismatches':sum(not x['liveTargetMatchesPriorFinalHash'] for x in prior_records),'w899BoundaryMatches':sum(x['liveMatchesPriorCrossReviewFinal'] for x in boundary),'w884Context':str(w884),'checksPassed':True},ensure_ascii=False,indent=2))
