from __future__ import annotations
import json,hashlib,pathlib,subprocess,re,collections
from datetime import datetime,timezone
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-crossreview-20261102')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
SOURCE='src/NzbDrone.Core/Localization/Core/en.json'
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def git(*a): return subprocess.check_output(['git','-C',str(WORK),*a])
def flatten(obj,p=''):
 for k,v in obj.items():
  q=f'{p}.{k}' if p else k
  if isinstance(v,dict): yield from flatten(v,q)
  else: yield q,v
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def check_sums(path,base):
 result=subprocess.run(['sha256sum','-c',str(path)],cwd=base,text=True,capture_output=True)
 assert result.returncode==0,result.stdout+result.stderr
 return result.stdout.splitlines()
def readjl(name): return [json.loads(x) for x in (PRIMARY/name).read_text().splitlines()]
# Confirm the pinned tree and clean checkout before attesting any rows.
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert git('rev-parse','HEAD^{tree}').decode().strip()==TREE
assert git('branch','--show-current').decode().strip()=='codex/chaptarrng-localization-complete-20261031'
assert git('status','--porcelain').decode().strip()==''
input_checks=check_sums(PRIMARY/'INPUT-SHA256SUMS',WORK)
packet_checks=check_sums(PRIMARY/'SHA256SUMS',PRIMARY)
# Freeze the exact missing-ID queue and English source/registry at the pinned head.
ids=json.loads((PRIMARY/'current-missing-ids.json').read_text())
assert len(ids)==1210 and len(set(ids))==1210
follow=json.loads(git('show',f'{HEAD}:docs/localization/source-followup-20261101.json'))
assert ids==follow['currentMissingIds'] and sha(jbytes(ids))==follow['currentMissingIdsSha256']
source_raw=git('show',f'{HEAD}:{SOURCE}'); source=json.loads(source_raw)
source_blob=git('rev-parse',f'{HEAD}:{SOURCE}').decode().strip(); source_file_sha=sha(source_raw)
source_rows=readjl('source-slice.jsonl'); assert len(source_rows)==50
for offset,row in enumerate(source_rows,850):
 sid=ids[offset]
 assert row['sourceOrdinal']==offset and row['sourceId']==sid and source[sid]==row['source']
 assert row['sourceKeySha256']==sha(sid) and row['sourceTextSha256']==sha(row['source'])
 assert row['sourceCatalogBlob']==source_blob and row['sourceCatalogSha256']==source_file_sha
registry=json.loads(git('show',f'{HEAD}:docs/localization/server-message-sources.json'))
registry_by={x['id']:x for x in registry['records']}
assert len([x for x in registry['records'] if x['id'] in ids[850:900]])==50
for row in source_rows:
 rec=registry_by[row['sourceId']]
 assert rec['source']==row['source']
 assert rec['sourceFingerprint']==row['sourceRegistryFingerprint']
# Load all catalogs and exact file hash/blob pins.
locales={}; locale_pins={}
for loc,filename in LOCALES.items():
 path=f'src/NzbDrone.Core/Localization/Core/{filename}'
 raw=git('show',f'{HEAD}:{path}'); obj=json.loads(raw)
 assert set(obj)==set(source),(loc,'key-set parity')
 locales[loc]=obj; locale_pins[loc]={'path':path,'blob':git('rev-parse',f'{HEAD}:{path}').decode().strip(),'sha256':sha(raw)}
# Primary rows plus frozen input/current rows must agree exactly.
reviews=readjl('review-cells.jsonl'); current=readjl('input-cells.jsonl'); caller=readjl('caller-context.jsonl'); pipeline=readjl('pipeline-caller-context.jsonl')
assert len(reviews)==len(current)==600 and len(caller)==50 and len(pipeline)==76
cmap={(x['sourceOrdinal'],x['locale']):x for x in current}
ccmap={x['sourceId']:x for x in caller}
for c in caller:
 assert c['callerContextSha256']==sha(jbytes(c['callerRefs']))
 assert c['sourceId'] in registry_by and c['source']==registry_by[c['sourceId']]['source']
# Revalidate every production call line and generic pipeline line against the exact tree.
caller_line_checks=[]; caller_mismatches=[]
for c in caller:
 for ref in c['callerRefs']:
  raw=git('show',f"{HEAD}:{ref['file']}"); lines=raw.decode().splitlines(); n=ref['line']
  actual=lines[n-1] if 1<=n<=len(lines) else None
  result={'sourceId':c['sourceId'],'file':ref['file'],'line':n,'lineTextMatches':actual is not None and actual.strip()==ref['lineText'],
   'lineShaMatches':actual is not None and sha(actual.strip())==ref['lineSha256'],'fileShaMatches':sha(raw)==ref['fileSha256'],
   'fileBlobMatches':git('rev-parse',f"{HEAD}:{ref['file']}").decode().strip()==ref['fileBlob'],
   'contextBeforeMatches':actual is not None and [v.strip() for v in lines[max(0,n-4):n-1]]==ref['contextBefore'],
   'contextAfterMatches':actual is not None and [v.strip() for v in lines[n:min(len(lines),n+3)]]==ref['contextAfter'],
   'registryPinExact':ref['registryPinExact']}
  caller_line_checks.append(result)
  if not all(result[k] for k in ('lineTextMatches','lineShaMatches','fileShaMatches','fileBlobMatches','contextBeforeMatches','contextAfterMatches')): caller_mismatches.append(result)
pipeline_checks=[]; pipeline_gaps=[]
for ref in pipeline:
 raw=git('show',f"{HEAD}:{ref['file']}"); lines=raw.decode().splitlines(); n=ref['line']; actual=lines[n-1] if 1<=n<=len(lines) else None
 result={'file':ref['file'],'line':n,'lineTextMatches':actual is not None and actual.strip()==ref['lineText'],'lineShaMatches':actual is not None and sha(actual.strip())==ref['lineSha256'],
  'fileShaMatches':sha(raw)==ref['fileSha256'],'fileBlobMatches':git('rev-parse',f"{HEAD}:{ref['file']}").decode().strip()==ref['fileBlob'],
  'contextBeforeMatches':actual is not None and [v.strip() for v in lines[max(0,n-4):n-1]]==ref['contextBefore'],'contextAfterMatches':actual is not None and [v.strip() for v in lines[n:min(len(lines),n+3)]]==ref['contextAfter']}
 pipeline_checks.append(result)
 if not all(result[k] for k in ('lineTextMatches','lineShaMatches','fileShaMatches','fileBlobMatches','contextBeforeMatches','contextAfterMatches')): pipeline_gaps.append(result)
# Verify each of the 600 exact source/current/candidate hashes, placeholders, markup, and protected literals.
structural=[]; counts=collections.Counter(); noops=[]; failures=[]; mismatch_source=[]
for r in reviews:
 key=(r['sourceOrdinal'],r['locale']); c=cmap.get(key); assert c is not None
 sid=r['sourceId']; loc=r['locale']; src=source[sid]; target=locales[loc][sid]
 checks={
  'head_tree':r['exactHead']==HEAD and r['exactTree']==TREE and c['exactHead']==HEAD and c['exactTree']==TREE,
  'source_ordinal_id_text':r['sourceOrdinal'] in range(850,900) and ids[r['sourceOrdinal']]==sid and r['source']==src and c['source']==src,
  'source_key_hash':r['sourceKeySha256']==sha(sid) and c['sourceKeySha256']==sha(sid),
  'source_text_hash':r['sourceTextSha256']==sha(src) and c['sourceTextSha256']==sha(src),
  'source_file_pin':r['sourceFile']=='src/NzbDrone.Core/Localization/Core/en.json' and r['sourceFileBlob']==source_blob and r['sourceFileSha256']==source_file_sha,
  'target_file_pin':r['targetFile']==locale_pins[loc]['path'] and r['targetFileBlob']==locale_pins[loc]['blob'] and r['targetFileSha256']==locale_pins[loc]['sha256'],
  'current_target_value_hash':r['currentTarget']==target and r['currentTargetSha256']==sha(target) and c['currentTarget']==target and c['currentTargetSha256']==sha(target),
  'caller_hash':r['callerContextSha256']==ccmap[sid]['callerContextSha256']==c['callerContextSha256'],
  'caller_refs':r['callerRefs']==ccmap[sid]['callerRefs'],
  'source_placeholder_pin':r['sourcePlaceholders']==placeholders(src) and c['sourcePlaceholders']==placeholders(src),
  'current_placeholder_pin':r['currentTargetPlaceholders']==placeholders(target) and c['currentTargetPlaceholders']==placeholders(target),
  'source_markup_pin':r['sourceMarkup']==markup(src) and c['sourceMarkup']==markup(src),
  'current_markup_pin':r['currentTargetMarkup']==markup(target) and c['currentTargetMarkup']==markup(target),
  'placeholder_parity':r['placeholderParity']==(placeholders(src)==placeholders(target)) and c['placeholderParity']==(placeholders(src)==placeholders(target)),
  'markup_parity':r['markupParity']==(markup(src)==markup(target)) and c['markupParity']==(markup(src)==markup(target)),
  'caller_status':r['callerReferenceStatus']=='pinned' and ccmap[sid]['callerReferenceStatus']=='pinned',
  'protected_preserved':r['protectedLiteralsPreserved']==all(lit in target for lit in r['protectedLiterals']) if r['disposition'] in ('accept-current','hold') else r['protectedLiteralsPreserved']==all(lit in r['finalTarget'] for lit in r['protectedLiterals']),
 }
 final=r['finalTarget']; final_hash=r['finalTargetSha256']
 if final is not None:
  checks['final_hash']=sha(final)==final_hash
  checks['final_placeholder_parity']=placeholders(src)==placeholders(final)
  checks['final_markup_parity']=markup(src)==markup(final)
  if r['recommendedTarget'] is not None:
   checks['recommended_target_metadata']=r['recommendedTarget']==final and r['recommendedTargetSha256']==sha(final) and r['recommendedTargetPlaceholders']==placeholders(final) and r['recommendedTargetMarkup']==markup(final)
  else: checks['accepted_current_target_metadata']=r['disposition']=='accept-current' and final==target
 else: checks['held_target_unset']=r['disposition']=='hold' and final_hash is None
 if r['disposition'] in ('propose-correction','propose-refinement'):
  checks['proposal_hashes']=r['recommendedTarget']==final and r['recommendedTargetSha256']==sha(final)
  if final==target: noops.append({'sourceOrdinal':r['sourceOrdinal'],'sourceId':sid,'locale':loc,'disposition':r['disposition'],'currentTargetSha256':sha(target),'finalTargetSha256':sha(final)})
 elif r['disposition']=='accept-current': checks['accept_current_exact']=final==target
 elif r['disposition']=='hold': checks['hold_exact']=final is None
 else: checks['known_disposition']=False
 if r['callerSourceMessageMismatch']: mismatch_source.append({'sourceOrdinal':r['sourceOrdinal'],'sourceId':sid,'locale':loc})
 bad=[k for k,v in checks.items() if not v]
 if bad: failures.append({'sourceOrdinal':r['sourceOrdinal'],'sourceId':sid,'locale':loc,'failedChecks':bad})
 counts[r['disposition']]+=1
 structural.append({'sourceOrdinal':r['sourceOrdinal'],'sourceId':sid,'locale':loc,'primaryDisposition':r['disposition'],
  'sourceTextSha256':sha(src),'currentTargetSha256':sha(target),'recommendedTargetSha256':sha(r['recommendedTarget']) if r['recommendedTarget'] is not None else None,
  'finalTargetSha256':final_hash,'sourceKeySha256':sha(sid),'callerContextSha256':ccmap[sid]['callerContextSha256'],'sourceCatalogBlob':source_blob,
  'targetCatalogBlob':locale_pins[loc]['blob'],'checks':checks})
assert not failures,failures[:10]
assert not caller_mismatches and not pipeline_gaps
assert counts=={'accept-current':509,'propose-correction':69,'propose-refinement':10,'hold':12},counts
assert not noops,noops
assert mismatch_source and {x['sourceOrdinal'] for x in mismatch_source}=={884}
assert all(x['sourceOrdinal']==884 for x in reviews if x['disposition']=='hold')
# Exact qBittorrent source/caller mismatch for W884; the hold remains.
holds=[x for x in reviews if x['sourceOrdinal']==884]
assert len(holds)==12 and {x['disposition'] for x in holds}=={'hold'}
qsource='src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrentSettings.cs'
qraw=git('show',f'{HEAD}:{qsource}').decode()
qline=next((i+1,line.strip()) for i,line in enumerate(qraw.splitlines()) if "Can not contain" in line)
assert "'\\\\'" in qline[1] or "'\\'" in qline[1]
assert holds[0]['source']=="Can not contain '', '//', or start/end with '/'"
# Freeze compact data for source/caller/pipeline/target readback.
(OUT/'structural-caller-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in structural))
inputs=['README.md','all-seven-pr-heads.json','caller-context-summary.json','caller-context.jsonl','correction-candidates.jsonl','current-missing-ids.json','input-cells.jsonl','input-manifest.json','manifest.json','manual-protected-literals.json','pipeline-caller-context.jsonl','primary-findings.json','prior-disposition-boundary.json','prior-disposition-hashes.jsonl','protected-literal-integrity.jsonl','review-cells.jsonl','source-slice.jsonl','w800-w849-applied-reattestation.jsonl','w849-boundary-reattestation.jsonl']
provenance={name:{'path':str(PRIMARY/name),'sha256':sha((PRIMARY/name).read_bytes()),'bytes':(PRIMARY/name).stat().st_size} for name in inputs}
(OUT/'input-provenance.json').write_text(json.dumps({'primaryPacket':str(PRIMARY),'head':HEAD,'tree':TREE,'inputChecksumRowsVerified':len(input_checks),'primaryPacketChecksumRowsVerified':len(packet_checks),'inputs':provenance},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
summary={'schemaVersion':1,'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'head':HEAD,'tree':TREE,'sourceOrdinals':[850,899],'cellCount':600,
 'primaryDispositionCounts':dict(counts),'targetHashesVerified':600,'callerRows':len(caller),'callerRefsVerified':len(caller_line_checks),'callerRefFailures':len(caller_mismatches),
 'genericPipelineRows':len(pipeline),'genericPipelineRefsVerified':len(pipeline_checks),'genericPipelineFailures':len(pipeline_gaps),
 'sourceCatalogBlob':source_blob,'localeCatalogs':locale_pins,'placeholderOrMarkupFailures':len(failures),'recommendedTargetNoOps':len(noops),
 'callerSourceMessageMismatchRows':mismatch_source,'w884SourceText':holds[0]['source'],'w884CallerText':qline[1],'w884HoldCells':len(holds),
 'sourceQueueCanonicalSha256':sha(jbytes(ids)),'priorPacketInputManifestSha256':sha((PRIMARY/'input-manifest.json').read_bytes()),
 'languageAuditPending':True,'nativeSpeakerApproval':False,'browserReview':False,'testsBuildCiRun':False,'repoModified':False,
 'callerFiles':len({x['file'] for c in caller for x in c['callerRefs']}),'pipelineFiles':len({x['file'] for x in pipeline}),
 'reproducibleEvidence':'structural-caller-reattestation.jsonl, input-provenance.json, and live-seven-pr-heads.json'}
(OUT/'structural-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'counts':dict(counts),'cells':len(structural),'failures':len(failures),'callerRefChecks':len(caller_line_checks),'callerRefFailures':len(caller_mismatches),'pipelineChecks':len(pipeline_checks),'pipelineFailures':len(pipeline_gaps),'noOpProposals':len(noops),'w884CallerText':qline[1],'inputChecksumRowsVerified':len(input_checks),'primaryPacketChecksumRowsVerified':len(packet_checks)},ensure_ascii=False,indent=2))
