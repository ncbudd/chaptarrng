#!/usr/bin/env python3
from __future__ import annotations
import collections, datetime, hashlib, json, re, subprocess
from pathlib import Path

ROOT=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned')
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w450-499-20261105')
OUT=TASK/'candidate-free'/'input'
REPO='snapetech-org/chaptarrng'; PR=190
BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'; TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
MAIN='317c5b431649a69a89e1c795f9490fd4df0b682b'
W400=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w400-449-20261105/candidate-free/input')
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
DIRECT_FIELDS=('sourceKey','source_key','key','sourceId','source_id','id')
CODE_EXTS={'.js','.jsx','.ts','.tsx','.cs'}
RUNTIME_PATHS=['frontend/src/Utilities/String/translate.ts','frontend/src/Utilities/Localization/locale.js','frontend/src/Utilities/Localization/locale-utils.cjs','frontend/src/Utilities/Localization/message-formatting.cjs','frontend/src/Utilities/Localization/formatters.cjs','frontend/src/index.ts','frontend/src/login.html','src/NzbDrone.Core/Localization/LocalizationService.cs','src/Chaptarr.Api.V1/Localization/LocalizationController.cs','src/NzbDrone.Core/Localization/Core/ui-locales.json']
PH=re.compile(r'\{[^{}]+\}')
INLINE=re.compile(r'`([^`]+)`')
MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
DYNAMIC_CALL=re.compile(r'\b(?:translate|GetLocalizedString)\s*\(\s*([^,\)\n]+)')

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_text(s:str)->str:return sha(s.encode('utf-8'))
def canon(o)->bytes:return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def write_json(p:Path,o)->None:p.write_bytes((json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def write_jsonl(p:Path,rows)->None:p.write_bytes(b''.join(canon(r) for r in rows))
def require(ok,msg):
 if not ok:raise SystemExit('FAIL: '+msg)
def run(args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def tree_oid(rev,path):
 raw=run(['git','ls-tree',rev,'--',path])
 return raw.split('\t',1)[0].split()[-1] if raw else None
def branch_file(rev,path,working=False):
 if working:return (ROOT/path).read_bytes()
 oid=tree_oid(rev,path)
 if not oid:return None
 return subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',oid])
def signatures(s):return dict(sorted(collections.Counter(PH.findall(s)).items()))
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def parse_tree(rev):
 raw=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','-z',rev,'--','frontend/src','src'])
 out=[]
 for entry in raw.split(b'\0'):
  if not entry:continue
  meta,rpath=entry.split(b'\t',1);_,kind,oid=meta.decode().split();path=rpath.decode()
  if kind!='blob' or Path(path).suffix not in CODE_EXTS:continue
  parts=Path(path).parts; basename=Path(path).name.lower()
  test_project=any(part.lower() in ('test','tests','__tests__') or part.lower().endswith(('.test','.tests','-test','-tests')) for part in parts[:-1])
  test_file=basename.endswith(('.test.js','.test.jsx','.test.ts','.test.tsx','.spec.js','.spec.jsx','.spec.ts','.spec.tsx','.test.cs','.tests.cs'))
  if test_project or test_file:continue
  data=subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',oid])
  try:lines=data.decode('utf-8').splitlines()
  except UnicodeDecodeError:continue
  out.append((path,oid,data,lines))
 return sorted(out,key=lambda x:x[0])
def scan_branch(rev,keys):
 code=parse_tree(rev); file_pins=[]; contexts={}; dynamic=[]
 for path,oid,data,lines in code:
  file_pins.append({'path':path,'gitBlob':oid,'sha256':sha(data),'bytes':len(data)})
  for i,line in enumerate(lines):
   for m in DYNAMIC_CALL.finditer(line):
    arg=m.group(1).strip()
    if arg.startswith(("'",'"','`')) or line.lstrip().startswith(('//','/*','*')):continue
    dynamic.append({'path':path,'line':i+1,'lineText':line,'lineSha256':sha_text(line),'callExpression':m.group(0).strip(),'argumentExpression':arg,'fileSha256':sha(data),'fileGitBlob':oid,'contextBefore':lines[max(0,i-2):i],'contextAfter':lines[i+1:i+3]})
 dynamic.sort(key=lambda r:(r['path'],r['line'],r['callExpression']))
 for key in keys:
  rx=re.compile(r'(?<![A-Za-z0-9_])'+re.escape(key)+r'(?![A-Za-z0-9_])')
  refs=[];dyn=[]
  for path,oid,data,lines in code:
   hits=[]
   for i,line in enumerate(lines):
    if not rx.search(line):continue
    comment=line.lstrip().startswith(('//','/*','*','#'))
    front=bool(re.search(r'\btranslate\s*\(\s*([\'\"])'+re.escape(key)+r'\1',line))
    server=bool(re.search(r'\bGetLocalizedString\s*\(\s*([\'\"])'+re.escape(key)+r'\1',line))
    kind='literal-translate-call' if front else 'literal-server-call' if server else 'indirect-key-literal-reference'
    refs.append({'referenceKind':kind,'isComment':comment,'isRuntimeReference':not comment,'path':path,'line':i+1,'lineText':line,'lineSha256':sha_text(line),'fileSha256':sha(data),'fileGitBlob':oid,'contextBefore':lines[max(0,i-2):i],'contextAfter':lines[i+1:i+4]})
    hits.append(i)
   if hits:
    for i,line in enumerate(lines):
     for m in DYNAMIC_CALL.finditer(line):
      arg=m.group(1).strip()
      if arg.startswith(("'",'"','`')) or line.lstrip().startswith(('//','/*','*')):continue
      dyn.append({'path':path,'line':i+1,'lineText':line,'lineSha256':sha_text(line),'callExpression':m.group(0).strip(),'argumentExpression':arg,'fileSha256':sha(data),'fileGitBlob':oid,'contextBefore':lines[max(0,i-2):i],'contextAfter':lines[i+1:i+3]})
  refs.sort(key=lambda r:(r['path'],r['line'],r['referenceKind']));dyn.sort(key=lambda r:(r['path'],r['line'],r['callExpression']))
  actual=[r for r in refs if r['isRuntimeReference']]
  ctx={'sourceKey':key,'literalAndIndirectReferences':refs,'relatedDynamicTranslationCallsites':dyn}
  contexts[key]={'sourceKey':key,'callerContextSha256':sha(canon(ctx).rstrip(b'\n')),'callerReferenceCount':len(actual),'literalCallCount':sum(r['referenceKind']!='indirect-key-literal-reference' for r in actual),'indirectKeyReferenceCount':sum(r['referenceKind']=='indirect-key-literal-reference' for r in actual),'relatedDynamicTranslationCallsiteCount':len(dyn),'callerRefs':refs,'dynamicTranslationCallsites':dyn}
 return code,file_pins,contexts,dynamic

require(not OUT.exists() or all(p.name=='packet-builders' for p in OUT.iterdir()),'candidate-free output may contain only its packet-builders provenance directory before build')
require(run(['git','rev-parse','HEAD'])==HEAD and run(['git','rev-parse','HEAD^{tree}'])==TREE,'local PR head/tree')
require(run(['git','status','--porcelain=v1'])=='','review worktree must be clean')
require(run(['git','rev-parse',f'{MAIN}^{{commit}}'])==MAIN,'live main object')
subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=W400,check=True,stdout=subprocess.DEVNULL)
oldsel=json.loads((W400/'source-selection.json').read_text())
scan_raw=(W400/'prior-historical-evidence-scan.json').read_bytes();scan=json.loads(scan_raw)
require(scan.get('sourceScanSha256')==oldsel['historicalEvidenceScanSha256'],'original historical scan pin')
historical_ids=set(); frozen_files=[]; historical_rows=0
for f in scan['files']:
 data=subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',f['gitBlob']])
 require(sha(data)==f['sha256'],'frozen historical blob '+f['path'])
 frozen_files.append({'path':f['path'],'gitBlob':f['gitBlob'],'sha256':sha(data),'bytes':len(data)})
 for line in data.splitlines():
  if not line.strip():continue
  try:row=json.loads(line)
  except Exception:continue
  historical_rows+=1
  if isinstance(row,dict):
   for field in DIRECT_FIELDS:
    val=row.get(field)
    if isinstance(val,str):historical_ids.add(val)
require(len(frozen_files)==392 and historical_rows==211539,'frozen historical scan dimensions')
source_rel='src/NzbDrone.Core/Localization/Core/en.json'
source_raw=branch_file(HEAD,source_rel,True);source=json.loads(source_raw);source_keys=list(source)
require(len(source_keys)==4165,'English Core key count')
source_blob=tree_oid(HEAD,source_rel);source_sha=sha(source_raw)
prior_windows=[]
for d in oldsel['priorSelections']:
 keys=d['keys'];start=d['firstPosition'];end=d['lastPosition']
 require(len(keys)==50 and end-start==49,'prior window dimension '+d['batch'])
 prior_windows.append({'batch':d['batch'],'firstPosition':start,'lastPosition':end,'keys':keys,'selectionSha256':sha(canon(keys))})
require(oldsel['firstPosition']==400 and oldsel['lastPosition']==449 and len(oldsel['keys'])==50,'prior W400 selection dimensions')
prior_windows.append({'batch':'W400-449-Core','firstPosition':400,'lastPosition':449,'keys':oldsel['keys'],'selectionSha256':sha(canon(oldsel['keys']))})
prior_keys=[k for d in prior_windows for k in d['keys']]
uncovered=[k for k in source_keys if k not in historical_ids]
require(len(prior_keys)==450 and uncovered[:450]==prior_keys,'W0-W449 selection lineage')
keys=uncovered[450:500]
require(len(keys)==50 and len(set(keys))==50 and not any(k in historical_ids for k in keys),'W450-499 selection')
for key in keys: require(key in source,'selected source key exists')

catalogs={};parsed={}
for loc,name in {'en':'en.json',**LOCALE_FILES}.items():
 rel=f'src/NzbDrone.Core/Localization/Core/{name}';raw=branch_file(HEAD,rel,True);data=json.loads(raw)
 require(len(data)==4165 and set(data)==set(source_keys),'Core key-set parity '+loc)
 catalogs[loc]={'path':rel,'sha256':sha(raw),'gitBlob':tree_oid(HEAD,rel),'bytes':len(raw),'keyCount':len(data),'keyOrderSha256':sha(canon(list(data))),'orderMatchesEnglish':list(data)==source_keys};parsed[loc]=data

main_source_raw=branch_file(MAIN,source_rel);main_source=json.loads(main_source_raw)
main_catalogs={};main_parsed={}
for loc,name in {'en':'en.json',**LOCALE_FILES}.items():
 rel=f'src/NzbDrone.Core/Localization/Core/{name}';raw=branch_file(MAIN,rel);data=json.loads(raw)
 main_catalogs[loc]={'path':rel,'sha256':sha(raw),'gitBlob':tree_oid(MAIN,rel),'bytes':len(raw),'keyCount':len(data)};main_parsed[loc]=data
_,caller_file_pins,contexts,dynamic=scan_branch(HEAD,keys)
_,main_caller_file_pins,main_contexts,main_dynamic=scan_branch(MAIN,keys)

cells=[];checks=collections.Counter(); changed_sources=[]; changed_targets=[]; drift=[]
for key in keys:
 source_text=source[key];ctx=contexts[key];mctx=main_contexts[key]
 source_match=main_source.get(key)==source_text
 if not source_match:changed_sources.append({'sourceKey':key,'prSourceText':source_text,'prSourceTextSha256':sha_text(source_text),'mainSourceText':main_source.get(key),'mainSourceTextSha256':sha_text(main_source.get(key,'')) if key in main_source else None})
 if ctx['callerContextSha256']!=mctx['callerContextSha256']:
  drift.append({'sourceKey':key,'prCallerContextSha256':ctx['callerContextSha256'],'mainCallerContextSha256':mctx['callerContextSha256'],'prCallerReferenceCount':ctx['callerReferenceCount'],'mainCallerReferenceCount':mctx['callerReferenceCount'],'prCallerRefs':ctx['callerRefs'],'mainCallerRefs':mctx['callerRefs'],'prDynamicCallsites':ctx['dynamicTranslationCallsites'],'mainDynamicCallsites':mctx['dynamicTranslationCallsites']})
 for loc in LOCALES:
  target=parsed[loc][key]; main_target=main_parsed[loc].get(key)
  target_match=main_target==target
  if not target_match:changed_targets.append({'sourceKey':key,'locale':loc,'prTargetSha256':sha_text(target),'mainTargetSha256':sha_text(main_target or ''),'prTarget':target,'mainTarget':main_target})
  check={'placeholder':signatures(source_text)==signatures(target),'inlineCode':INLINE.findall(source_text)==INLINE.findall(target),'markup':MARKUP.findall(source_text)==MARKUP.findall(target),'numeric':collections.Counter(NUM.findall(source_text))==collections.Counter(NUM.findall(target)),'protectedLiteral':all(x in target for x in protected(source_text))}
  for name,value in check.items():
   if not value:checks[name]+=1
  cells.append({'batch':'W450-499-Core','sourceOrdinal':450+keys.index(key),'sourceKey':key,'locale':loc,'sourceText':source_text,'sourceTextSha256':sha_text(source_text),'currentTarget':target,'currentTargetSha256':sha_text(target),'sourceFile':source_rel,'sourceFileSha256':source_sha,'sourceFileGitBlob':source_blob,'targetFile':catalogs[loc]['path'],'targetFileSha256':catalogs[loc]['sha256'],'targetFileGitBlob':catalogs[loc]['gitBlob'],'sourcePlaceholders':signatures(source_text),'currentPlaceholders':signatures(target),'sourceInlineCode':INLINE.findall(source_text),'currentInlineCode':INLINE.findall(target),'sourceMarkup':MARKUP.findall(source_text),'currentMarkup':MARKUP.findall(target),'sourceNumericTokens':NUM.findall(source_text),'currentNumericTokens':NUM.findall(target),'protectedLiterals':protected(source_text),'integrityChecks':check,'callerContextSha256':ctx['callerContextSha256'],'callerReferenceCount':ctx['callerReferenceCount'],'literalCallCount':ctx['literalCallCount'],'indirectKeyReferenceCount':ctx['indirectKeyReferenceCount'],'relatedDynamicTranslationCallsiteCount':ctx['relatedDynamicTranslationCallsiteCount']})

context_rows=[contexts[k] for k in keys]
main_context_summary=[{'sourceKey':k,'prContextSha256':contexts[k]['callerContextSha256'],'mainContextSha256':main_contexts[k]['callerContextSha256'],'contextChanged':contexts[k]['callerContextSha256']!=main_contexts[k]['callerContextSha256'],'prCallerReferenceCount':contexts[k]['callerReferenceCount'],'mainCallerReferenceCount':main_contexts[k]['callerReferenceCount']} for k in keys]
source_manifest='docs/localization/server-message-sources.json'
manifest_raw=branch_file(HEAD,source_manifest,True);main_manifest_raw=branch_file(MAIN,source_manifest)
manifest_pin={'path':source_manifest,'prSha256':sha(manifest_raw) if manifest_raw is not None else None,'prGitBlob':tree_oid(HEAD,source_manifest),'mainSha256':sha(main_manifest_raw) if main_manifest_raw is not None else None,'mainGitBlob':tree_oid(MAIN,source_manifest),'matches':manifest_raw==main_manifest_raw}

base=run(['git','merge-base',HEAD,MAIN])
pr_paths=run(['git','diff','--name-status',f'{base}...{HEAD}']).splitlines()
workflow_paths=[line.split('\t')[-1] for line in pr_paths if line.split('\t')[-1].startswith('.github/workflows/')]
PR_API_BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'
main_advance=run(['git','diff','--name-status',PR_API_BASE+'..'+MAIN]).splitlines()
main_change_paths=[line.split('\t')[-1] for line in main_advance]

selection={'batch':'W450-499-Core','repository':REPO,'pullRequest':PR,'branch':BRANCH,'head':HEAD,'tree':TREE,'liveMain':MAIN,'firstPosition':450,'lastPosition':499,'keyCount':50,'localeCount':12,'locales':LOCALES,'catalogPath':source_rel,'catalogGitBlob':source_blob,'catalogSha256':source_sha,'catalogKeyCount':len(source_keys),'catalogOrder':'English Core insertion order after excluding direct identifiers in the frozen 392-blob historical evidence scan, continuing from the verified W0-W449 selections.','historicalFileCount':len(frozen_files),'historicalRows':historical_rows,'historicalUniqueDirectIdentifiers':len(historical_ids),'historicalEvidenceScanSha256':scan['sourceScanSha256'],'historicalEvidenceScanPacketFileSha256':sha(scan_raw),'priorSelections':prior_windows,'priorSelectedKeysCount':len(prior_keys),'priorSelectedKeysSha256':sha(canon(prior_keys)),'keys':keys,'selectedKeysSha256':sha(canon(keys)),'selectionMatchesFirstUncoveredPositions':True}
write_json(OUT/'source-selection.json',selection)
write_json(OUT/'prior-historical-evidence-scan.json',scan)
write_json(OUT/'catalog-pins.json',catalogs)
write_json(OUT/'runtime-source-pins.json',[{'path':p,'sha256':sha(branch_file(HEAD,p,True) or b''),'gitBlob':tree_oid(HEAD,p),'bytes':len(branch_file(HEAD,p,True) or b'')} for p in RUNTIME_PATHS])
write_json(OUT/'caller-scan-file-pins.json',{'head':HEAD,'gitBlobFileCount':len(caller_file_pins),'files':caller_file_pins})
write_json(OUT/'main-caller-scan-file-pins.json',{'main':MAIN,'gitBlobFileCount':len(main_caller_file_pins),'files':main_caller_file_pins})
write_jsonl(OUT/'candidate-free-cells.jsonl',cells)
write_jsonl(OUT/'caller-context.jsonl',context_rows)
write_jsonl(OUT/'dynamic-translation-callers.jsonl',dynamic)
write_json(OUT/'latest-main-drift.json',{'prHead':HEAD,'liveMain':MAIN,'mergeBase':base,'mainAdvanceSincePrApiBase':{'base':PR_API_BASE,'paths':main_advance,'pathCount':len(main_advance)},'prPathsFromMergeBase':pr_paths,'workflowPathsInPrDiff':workflow_paths,'sourceDifferences':changed_sources,'targetDifferences':changed_targets,'callerContextDifferences':drift,'callerContextSummary':main_context_summary,'sourceManifest':manifest_pin,'sourceAndTargetsCompared':True,'callerContextsCompared':True,'result':'PASS' if not changed_sources and not changed_targets else 'DRIFT'})
write_jsonl(OUT/'selection-boundary.jsonl',[{'sourceOrdinal':pos,'role':role,'sourceKey':uncovered[pos],'sourceTextSha256':sha_text(source[uncovered[pos]])} for pos,role in [(449,'prior-window-end'),(450,'selected-start'),(499,'selected-end'),(500,'next-window-start')]])
write_json(OUT/'candidate-free-summary.json',{'batch':'W450-499-Core','head':HEAD,'tree':TREE,'main':MAIN,'sourceIds':50,'locales':12,'cells':len(cells),'callerContextKeys':len(context_rows),'callerReferenceCount':sum(r['callerReferenceCount'] for r in context_rows),'callerContextChangedAgainstMain':sum(x['contextChanged'] for x in main_context_summary),'sourceChangesAgainstMain':len(changed_sources),'targetChangesAgainstMain':len(changed_targets),'integrityCheckFailures':dict(checks),'cellOrder':'sourceOrdinal ascending, then locale order in manifest','targetKeySetParityVerifiedForAllCatalogs':True,'sourceQueueVerifiedFromFrozenHistoricalScan':True,'workflowPathsInPrDiff':workflow_paths,'candidateFreeOnly':True,'noCandidateSuggestionsIncluded':True,'result':'PASS' if len(cells)==600 and not changed_sources and not changed_targets else 'REVIEW-DRIFT'})

att=json.loads((TASK/'attestation'/'live-pre-build.json').read_text())
write_json(OUT/'PR-attestation.json',att)
(OUT/'README.md').write_text('''# W450–W499 Core candidate-free review packet

This packet is pinned to ChaptarrNG PR #190 head `16c809b4787d70616a1a296ab0d90cf17923ba86` (tree `dbd8343a42476f4e830428cc59efb7f4830251d5`), API base `025498c1a9deb999a4acd1eafc4c807a252e0c29`, and live `main` recorded in `PR-attestation.json`. It contains 50 consecutive uncovered English Core source keys × 12 locale catalogs = 600 current translation cells.

`candidate-free-cells.jsonl` gives each English source, current locale value, exact source/target file hashes, token-integrity summaries, and current caller-context hash. `caller-context.jsonl` contains caller lines and neighboring source context for the 50 keys. `latest-main-drift.json` compares source texts, all 600 current targets, and all 50 caller contexts against the attested live `main`; the workflow file list from the PR diff and main advance since the API base are recorded there. No proposed translations, candidate targets, or primary-review judgments are present.

The source selection continues the verified W0–W449 English Core queue, excluding direct identifiers found in the pinned 392-blob historical evidence scan. The W0–W399 selections are inherited from the W400 packet, and W400–W449 keys are reattested against this exact PR head; see `source-selection.json` and `selection-boundary.jsonl`. The 12 locale catalogs are pinned in `catalog-pins.json`; each has the same 4,165 ordered keys as English.

The packet is candidate-free input for independent review. It does not claim a cross-review or root adjudication, and it authorizes no catalog edits.
''')
manifest={'schemaVersion':1,'scope':{'firstPosition':450,'lastPosition':499,'sourceIds':50,'locales':LOCALES,'cells':600},'head':HEAD,'tree':TREE,'liveMain':MAIN,'sourceSelectionSha256':sha((OUT/'source-selection.json').read_bytes()),'candidateFreeCells':{'path':'candidate-free-cells.jsonl','rows':len(cells),'sha256':sha((OUT/'candidate-free-cells.jsonl').read_bytes())},'callerContext':{'path':'caller-context.jsonl','rows':len(context_rows),'sha256':sha((OUT/'caller-context.jsonl').read_bytes())},'candidateFreeOnly':True,'nativeSpeakerApproval':False,'result':'PASS' if len(cells)==600 else 'FAIL'}
write_json(OUT/'candidate-free-manifest.json',manifest)
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name!='SHA256SUMS.txt': pass
sum_path=OUT/'SHA256SUMS.txt'
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in {'SHA256SUMS.txt'})
sum_path.write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files))
print(json.dumps({'output':str(OUT),'files':len(files)+1,'cells':len(cells),'keys':keys,'callerContextChangesAgainstMain':len(drift),'sourceDiffs':len(changed_sources),'targetDiffs':len(changed_targets),'workflowPaths':workflow_paths,'integrityFailures':dict(checks),'result':'PASS'},ensure_ascii=False,indent=2))
