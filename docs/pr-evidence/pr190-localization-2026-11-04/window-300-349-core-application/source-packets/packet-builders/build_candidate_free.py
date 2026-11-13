#!/usr/bin/env python3
from __future__ import annotations
import collections, datetime, hashlib, json, re, subprocess
from pathlib import Path

ROOT=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w300-349-source')
TASK=Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104')
OUT=TASK/'candidate-free'/'input'
HEAD='f0082d1b655c05b8d4019ede523dd695cd6d745a'
TREE='4cf2322354e9cf9b12d59cf10d0d8661c68ab4af'
PR=190; REPO='snapetech-org/ChaptarrNG'; BRANCH='codex/chaptarrng-localization-complete-20261031'
BASE_EXPECTED='17bde320915af42de73b8646ad56f8ba2ccebf4e'
W250=Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w250-299-core-20261104')
W250_INPUT=W250/'candidate-free/input'; W250_PRIMARY=W250/'primary-review'
W250_APPLY=ROOT/'docs/pr-evidence/pr190-localization-2026-11-04/window-250-299-followup'
W150_INPUT=Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w150-199-primary-20261104/candidate-free/input')
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
def readjl(p:Path):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def readj(p:Path):return json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def require(ok,msg):
 if not ok:raise SystemExit('FAIL: '+msg)
def tree_oid(path):
 raw=subprocess.check_output(['git','-C',str(ROOT),'ls-tree',HEAD,'--',path],text=True).strip()
 return raw.split('\t',1)[0].split()[-1] if raw else None
def signatures(s):return dict(sorted(collections.Counter(PH.findall(s)).items()))
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def graphql_pr():
 q='query { repository(owner:"snapetech-org",name:"ChaptarrNG") { pullRequest(number:190) { number state isDraft mergedAt headRefName headRefOid baseRefName baseRefOid } } }'
 raw=subprocess.check_output(['gh','api','graphql','-f','query='+q],text=True)
 return json.loads(raw)['data']['repository']['pullRequest']
def capture(label):
 now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
 pr=graphql_pr()
 require(pr['number']==PR and pr['state']=='OPEN' and pr['isDraft'] is True and pr['mergedAt'] is None,'live PR state')
 require(pr['headRefOid']==HEAD and pr['headRefName']==BRANCH and pr['baseRefName']=='main' and pr['baseRefOid']==BASE_EXPECTED,'live PR identity/base')
 refs_raw=subprocess.check_output(['git','-C',str(ROOT),'ls-remote','origin',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'],text=True)
 refs=sorted(refs_raw.splitlines()); refmap={x.split('\t')[1]:x.split('\t')[0] for x in refs}
 require(refmap.get(f'refs/heads/{BRANCH}')==HEAD and refmap.get(f'refs/pull/{PR}/head')==HEAD,'live branch/pull refs')
 apihead=json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/git/commits/{HEAD}','--jq','{sha:.sha,tree:.tree.sha}'],text=True))
 require(apihead=={'sha':HEAD,'tree':TREE},'API head/tree')
 require(git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE,'local exact head/tree')
 main=refmap['refs/heads/main']
 return {'snapshot':label,'capturedAtUtc':now,'repository':REPO,'pullRequest':PR,'state':pr['state'].lower(),'draft':pr['isDraft'],'merged':False,'headRef':pr['headRefName'],'headSha':pr['headRefOid'],'headTree':apihead['tree'],'branchRefSha':refmap[f'refs/heads/{BRANCH}'],'pullRefSha':refmap[f'refs/pull/{PR}/head'],'baseRef':pr['baseRefName'],'prApiBaseSha':pr['baseRefOid'],'liveMainSha':main,'baseBranchMoved':pr['baseRefOid']!=main,'remoteRefs':refs,'sourceWorktree':str(ROOT),'sourceWorktreeStatus':git('status','--porcelain=v1'),'prBodyRequested':False,'result':'PASS'}

require(git('status','--porcelain=v1')=='','source worktree must remain clean')
require(git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE,'source worktree pin')
require(not OUT.exists(),'candidate-free output already exists')
require(W250_INPUT.is_dir() and W250_PRIMARY.is_dir() and W250_APPLY.is_dir() and W150_INPUT.is_dir(),'prior evidence missing')
# Validate only W250 candidate-free, primary, and apply lineage artifacts. No blind/cross packets are used.
subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=W250_INPUT,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['python3',str(W250_INPUT/'verify_candidate_free.py')],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['sha256sum','-c','primary-review-SHA256SUMS.txt'],cwd=W250_PRIMARY,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['python3',str(W250_PRIMARY/'verify_primary_review.py')],check=True,stdout=subprocess.DEVNULL)
for name in ['apply-readback.jsonl','apply-result.json','root-adjudication.json','catalog-readback-evidence.json','product-commit.json']:
 require((W250_APPLY/name).is_file(),'W250 apply evidence missing '+name)
OUT.mkdir(parents=True,mode=0o700)
before=capture('before-candidate-free')

# Rebuild the frozen historical direct-identifier set from the exact 392 Git blobs used by W250.
scan_path=W250_INPUT/'prior-historical-evidence-scan.json'; scan_raw=scan_path.read_bytes(); scan=json.loads(scan_raw)
historical_ids=set(); historical_rows=0; frozen_files=[]
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
require(len(frozen_files)==392 and historical_rows==211539,'frozen source-selection inventory')
source_rel='src/NzbDrone.Core/Localization/Core/en.json'
source_raw=(ROOT/source_rel).read_bytes(); source=json.loads(source_raw); source_keys=list(source)
require(len(source_keys)==4165,'English Core key count')
source_blob=tree_oid(source_rel); source_sha=sha(source_raw)
oldsel=readj(W250_INPUT/'source-selection.json')
prior_windows=[]
for d in oldsel['priorSelections']:
 keys=d['keys']; start=d['firstPosition']; end=d['lastPosition']
 require(len(keys)==50 and end-start==49,'prior source selection window size')
 prior_windows.append({'batch':d['batch'],'firstPosition':start,'lastPosition':end,'keys':keys,'selectionSha256':sha(canon(keys))})
require(oldsel['firstPosition']==250 and oldsel['lastPosition']==299 and len(oldsel['keys'])==50,'W250 selection dimensions')
prior_windows.append({'batch':'W250-299','firstPosition':250,'lastPosition':299,'keys':oldsel['keys'],'selectionSha256':sha(canon(oldsel['keys']))})
prior_keys=[k for d in prior_windows for k in d['keys']]
uncovered=[k for k in source_keys if k not in historical_ids]
require(len(prior_keys)==300 and uncovered[:300]==prior_keys,'W0-W299 sequential source selections')
keys=uncovered[300:350]
require(len(keys)==50 and len(set(keys))==50 and not any(k in historical_ids for k in keys),'W300-349 Core selection')
for pos,k in enumerate(keys,300):
 require(source_keys.index(k)>=0 and sha_text(source[k]),'selected source key '+str(pos))
require(tree_oid(source_rel)==source_blob,'English source catalog blob pin')

catalogs={}; parsed={}
for loc,name in {'en':'en.json',**LOCALE_FILES}.items():
 rel=f'src/NzbDrone.Core/Localization/Core/{name}';raw=(ROOT/rel).read_bytes();data=json.loads(raw)
 require(len(data)==4165 and set(data)==set(source_keys),'catalog parity '+loc)
 catalogs[loc]={'path':rel,'sha256':sha(raw),'gitBlob':tree_oid(rel),'bytes':len(raw),'keyCount':len(data)}
 parsed[loc]=data

# Verify W250's final readbacks and the separate root supplement against this exact catalog tree.
app_result=readj(W250_APPLY/'apply-result.json'); root_adj=readj(W250_APPLY/'root-adjudication.json')
apply_rows=readjl(W250_APPLY/'apply-readback.jsonl'); w250cells=readjl(W250_INPUT/'candidate-free-cells.jsonl')
w250primary=readjl(W250_PRIMARY/'primary-review-cells.jsonl')
require(len(apply_rows)==len(w250cells)==len(w250primary)==600,'W250 applied-cell row counts')
rbmap={(r['sourceKey'],r['locale']):r for r in apply_rows}; cfm={(r['sourceKey'],r['locale']):r for r in w250cells}
require(len(rbmap)==len(cfm)==600,'W250 applied-cell identities')
applied_n=0; preserved_n=0
for ident,rb in rbmap.items():
 key,loc=ident; cell=cfm[ident]
 require(rb['sourceOrdinal']==cell['sourceOrdinal'] and rb['currentTargetSha256']==cell['currentTargetSha256'],'W250 readback input linkage '+key+'/'+loc)
 observed=sha_text(parsed[loc][key]); require(observed==rb['finalTargetSha256'],'W250 readback current catalog hash '+key+'/'+loc)
 if rb['applied'] is True:
  require(rb['finalTarget'] is not None and sha_text(rb['finalTarget'])==rb['finalTargetSha256'],'W250 applied text/hash '+key+'/'+loc)
  require(rb['finalTargetSha256']!=rb['currentTargetSha256'],'W250 applied diff '+key+'/'+loc)
  applied_n+=1
 else:
  require(rb['finalTarget'] is None and rb['finalTargetSha256']==rb['currentTargetSha256'],'W250 preserved target '+key+'/'+loc)
  preserved_n+=1
require((applied_n,preserved_n)==(42,558),'W250 application counts')
require(app_result['acceptedCurrentPreserved']==558 and app_result['appliedChanges']==42 and app_result['allReviewedCellsReadBack']==600,'W250 apply result counts')
require(app_result['sourceHead']=='2a9995a2bf63f06814bd8780736305f16bd6b33a' and app_result['sourceTree']=='f6ae6530b73bf581c1fbc5a8c13eacd7342e9172','W250 apply source pin')
require(root_adj['exactHead']==app_result['sourceHead'] and root_adj['exactTree']==app_result['sourceTree'],'root supplement source pin')
require(root_adj['cellId']=='AutomaticUpdatesDisabledDocker::id' and root_adj['rootDisposition']=='replace-cross-selected-target-before-apply','root supplement identity')
root_ident=('AutomaticUpdatesDisabledDocker','id'); root_rb=rbmap[root_ident]
require(root_rb['applied'] is True and root_rb['finalTargetSha256']==root_adj['correctedTargetSha256'],'root supplement application readback')
require(parsed['id'][root_ident[0]]==root_adj['correctedTarget'] and sha_text(parsed['id'][root_ident[0]])==root_adj['correctedTargetSha256'],'root supplement target at current head')
require(app_result['rootCorrectedTargetSha256']==root_adj['correctedTargetSha256'],'root supplement apply result hash')

# Reattest W0-W199 and W200 hash-only historical rows at current catalog values.
w0_rows=readjl(W250_INPUT/'prior-selected-hold-reattestations.jsonl'); w200_rows=readjl(W250_INPUT/'prior-W200-application-reattestation.jsonl')
key_by_hash={sha_text(k):k for k in source_keys}; w0_out=[]; w200_out=[]
for old in w0_rows:
 key=old.get('sourceKey') or key_by_hash.get(old.get('sourceKeySha256'));loc=old['locale']
 require(key is not None and key in parsed[loc],'prior W0-W199 key identity')
 require(sha_text(source[key])==old['sourceTextSha256'],'prior W0-W199 source hash '+str(old.get('sourceOrdinal'))+'/'+loc)
 observed=sha_text(parsed[loc][key]);expected=old['expectedTargetSha256']
 require(observed==expected,'prior W0-W199 target hash '+str(old.get('sourceOrdinal'))+'/'+loc)
 hold=old.get('kind')=='hold' or old.get('textFree') is True
 row={'batch':old['batch'],'sourceOrdinal':old['sourceOrdinal'],'locale':loc,'kind':old['kind'],'sourceKeySha256':sha_text(key),'sourceTextSha256':old['sourceTextSha256'],'expectedTargetSha256':expected,'observedTargetSha256':observed,'callerContextSha256':old.get('callerContextSha256'),'callerReferenceCount':old.get('callerReferenceCount'),'targetFile':old['targetFile'],'matches':True,'priorHoldPreserved':hold,'targetTextIncluded':False}
 if not hold:row['sourceKey']=key
 w0_out.append(row)
for old in w200_rows:
 key=old.get('sourceKey') or key_by_hash.get(old.get('sourceKeySha256'));loc=old['locale']
 require(key is not None and key in parsed[loc],'prior W200 key identity')
 require(sha_text(source[key])==old['sourceTextSha256'],'prior W200 source hash '+str(old['sourceOrdinal'])+'/'+loc)
 observed=sha_text(parsed[loc][key]);expected=old['finalTargetSha256']
 require(observed==expected,'prior W200 target hash '+str(old['sourceOrdinal'])+'/'+loc)
 hold=old.get('disposition')=='hold-text-free'
 row={'batch':'W200-249','sourceOrdinal':old['sourceOrdinal'],'locale':loc,'disposition':old['disposition'],'sourceKeySha256':sha_text(key),'cellIdSha256':old['cellIdSha256'],'sourceTextSha256':old['sourceTextSha256'],'originalTargetSha256':old['originalTargetSha256'],'finalTargetSha256':expected,'observedTargetSha256':observed,'targetFile':old['targetFile'],'callerContextSha256':old['callerContextSha256'],'callerReferenceCount':old['callerReferenceCount'],'matches':True,'targetTextIncluded':False,'priorHoldPreserved':hold}
 if not hold:row['sourceKey']=key
 w200_out.append(row)
require(len(w0_out)==1519 and len(w200_out)==600,'previous lineage row counts')
require(sum(r['priorHoldPreserved'] for r in w0_out)==312,'W0-W199 hold count')
require(sum(r['priorHoldPreserved'] for r in w200_out)==12,'W200 hold count')

# Add all W250 final readbacks as hash-only history; the root correction is linked by its supplemental hash.
w250_out=[]
root_adj_sha=sha((W250_APPLY/'root-adjudication.json').read_bytes())
for ident,rb in sorted(rbmap.items(),key=lambda p:(p[1]['sourceOrdinal'],LOCALES.index(p[0][1]))):
 key,loc=ident;cell=cfm[ident]
 is_applied=rb['applied'] is True
 row={'batch':'W250-299','sourceOrdinal':rb['sourceOrdinal'],'locale':loc,'disposition':'applied-change' if is_applied else 'preserved-current','sourceKeySha256':sha_text(key),'cellIdSha256':sha_text(rb['cellId']),'sourceTextSha256':cell['sourceTextSha256'],'originalTargetSha256':rb['currentTargetSha256'],'finalTargetSha256':rb['finalTargetSha256'],'observedTargetSha256':sha_text(parsed[loc][key]),'targetFile':rb['targetFile'],'callerContextSha256':cell['callerContextSha256'],'callerReferenceCount':cell['callerReferenceCount'],'matches':True,'targetTextIncluded':False,'priorHoldPreserved':False,'applyReadbackSha256':sha(canon(rb))}
 if not is_applied:row['sourceKey']=key
 if ident==root_ident:
  row['rootSupplementalAdjudicationSha256']=root_adj_sha
  row['rootCorrectedTargetSha256']=root_adj['correctedTargetSha256']
 w250_out.append(row)
require(len(w250_out)==600 and sum(r['disposition']=='applied-change' for r in w250_out)==42 and sum(r['disposition']=='preserved-current' for r in w250_out)==558,'W250 hash-only lineage counts')

# Pin source/runtime/caller inputs and capture exact per-key caller context.
runtime=[]
for rel in RUNTIME_PATHS:
 raw=(ROOT/rel).read_bytes();runtime.append({'path':rel,'sha256':sha(raw),'gitBlob':tree_oid(rel),'bytes':len(raw)})
tree=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','-z',HEAD,'--','frontend/src','src'])
code=[]
for entry in tree.split(b'\0'):
 if not entry:continue
 meta,rpath=entry.split(b'\t',1);_,kind,oid=meta.decode().split();path=rpath.decode()
 if kind!='blob' or Path(path).suffix not in CODE_EXTS:continue
 parts=Path(path).parts; basename=Path(path).name.lower()
 test_project=any(part.lower() in ('test','tests','__tests__') or part.lower().endswith(('.test','.tests','-test','-tests')) for part in parts[:-1])
 test_file=basename.endswith(('.test.js','.test.jsx','.test.ts','.test.tsx','.spec.js','.spec.jsx','.spec.ts','.spec.tsx','.test.cs','.tests.cs'))
 if test_project or test_file:continue
 data=(ROOT/path).read_bytes();require(tree_oid(path)==oid,'caller source blob '+path)
 try:lines=data.decode('utf-8').splitlines()
 except UnicodeDecodeError:continue
 code.append((path,oid,data,lines))
code.sort(key=lambda x:x[0])
file_pins=[{'path':p,'gitBlob':oid,'sha256':sha(data),'bytes':len(data)} for p,oid,data,_ in code]
contexts={}; dynamic=[]
for path,oid,data,lines in code:
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
  file_hits=[]
  for i,line in enumerate(lines):
   if not rx.search(line):continue
   comment=line.lstrip().startswith(('//','/*','*','#'))
   front=bool(re.search(r'\btranslate\s*\(\s*([\'\"])'+re.escape(key)+r'\1',line))
   server=bool(re.search(r'\bGetLocalizedString\s*\(\s*([\'\"])'+re.escape(key)+r'\1',line))
   kind='literal-translate-call' if front else 'literal-server-call' if server else 'indirect-key-literal-reference'
   refs.append({'referenceKind':kind,'isComment':comment,'isRuntimeReference':not comment,'path':path,'line':i+1,'lineText':line,'lineSha256':sha_text(line),'fileSha256':sha(data),'fileGitBlob':oid,'contextBefore':lines[max(0,i-2):i],'contextAfter':lines[i+1:i+4]})
   file_hits.append(i)
  if file_hits:
   for i,line in enumerate(lines):
    for m in DYNAMIC_CALL.finditer(line):
     arg=m.group(1).strip()
     if arg.startswith(("'",'"','`')) or line.lstrip().startswith(('//','/*','*')):continue
     dyn.append({'path':path,'line':i+1,'lineText':line,'lineSha256':sha_text(line),'callExpression':m.group(0).strip(),'argumentExpression':arg,'fileSha256':sha(data),'fileGitBlob':oid,'contextBefore':lines[max(0,i-2):i],'contextAfter':lines[i+1:i+3]})
 refs.sort(key=lambda r:(r['path'],r['line'],r['referenceKind']));dyn.sort(key=lambda r:(r['path'],r['line'],r['callExpression']))
 actual=[r for r in refs if r['isRuntimeReference']]
 ctx={'sourceKey':key,'literalAndIndirectReferences':refs,'relatedDynamicTranslationCallsites':dyn}
 contexts[key]={'sourceKey':key,'callerContextSha256':sha(canon(ctx).rstrip(b'\n')),'callerReferenceCount':len(actual),'literalCallCount':sum(r['referenceKind']!='indirect-key-literal-reference' for r in actual),'indirectKeyReferenceCount':sum(r['referenceKind']=='indirect-key-literal-reference' for r in actual),'relatedDynamicTranslationCallsiteCount':len(dyn),'callerRefs':refs,'dynamicTranslationCallsites':dyn}

cells=[]; mismatch=collections.Counter()
for pos,key in enumerate(keys,300):
 st=source[key];ctx=contexts[key];protected_literals=protected(st)
 for loc in LOCALES:
  target=parsed[loc][key]
  check={'placeholder':signatures(st)==signatures(target),'inlineCode':INLINE.findall(st)==INLINE.findall(target),'markup':MARKUP.findall(st)==MARKUP.findall(target),'numeric':collections.Counter(NUM.findall(st))==collections.Counter(NUM.findall(target)),'protectedLiteral':all(x in target for x in protected_literals)}
  for name,value in check.items():
   if not value:mismatch[name]+=1
  cells.append({'batch':'W300-349-Core','sourceOrdinal':pos,'sourceKey':key,'locale':loc,'sourceText':st,'sourceTextSha256':sha_text(st),'currentTarget':target,'currentTargetSha256':sha_text(target),'sourceFile':source_rel,'sourceFileSha256':source_sha,'sourceFileGitBlob':source_blob,'targetFile':catalogs[loc]['path'],'targetFileSha256':catalogs[loc]['sha256'],'targetFileGitBlob':catalogs[loc]['gitBlob'],'sourcePlaceholders':signatures(st),'currentPlaceholders':signatures(target),'sourceInlineCode':INLINE.findall(st),'currentInlineCode':INLINE.findall(target),'sourceMarkup':MARKUP.findall(st),'currentMarkup':MARKUP.findall(target),'sourceNumericTokens':NUM.findall(st),'currentNumericTokens':NUM.findall(target),'protectedLiterals':protected_literals,'currentProtectedLiteralsPresent':check['protectedLiteral'],'integrityChecks':check,'callerContextSha256':ctx['callerContextSha256'],'callerReferenceCount':ctx['callerReferenceCount'],'literalCallCount':ctx['literalCallCount'],'indirectKeyReferenceCount':ctx['indirectKeyReferenceCount'],'relatedDynamicTranslationCallsiteCount':ctx['relatedDynamicTranslationCallsiteCount']})

# Hash-only lineages include all preserved prior holds and W250 final readbacks.
prior_selection={'batch':'W300-349-Core','repository':REPO,'pullRequest':PR,'branch':BRANCH,'head':HEAD,'tree':TREE,'firstPosition':300,'lastPosition':349,'keyCount':50,'localeCount':12,'locales':LOCALES,'catalogPath':source_rel,'catalogGitBlob':source_blob,'catalogSha256':source_sha,'catalogKeyCount':len(source_keys),'catalogOrder':'English Core insertion order after excluding direct identifiers in the frozen 392-blob historical evidence scan, continuing from the verified W0-W299 selections.','historicalFileCount':len(frozen_files),'historicalRows':historical_rows,'historicalUniqueDirectIdentifiers':len(historical_ids),'historicalEvidenceScanPath':'prior-historical-evidence-scan.json','historicalEvidenceScanSha256':sha(scan_raw),'priorSelections':prior_windows,'priorSelectedKeysCount':len(prior_keys),'priorSelectedKeysSha256':sha(canon(prior_keys)),'keys':keys,'selectedKeysSha256':sha(canon(keys)),'previousWindowAttestation':{'verifiedPriorWindows':6,'verifiedPriorSelections':300,'w0W199LineageRows':len(w0_out),'w0W199PreservedHolds':sum(r['priorHoldPreserved'] for r in w0_out),'w200LineageRows':len(w200_out),'w200PreservedHolds':sum(r['priorHoldPreserved'] for r in w200_out),'w250ReadbackRows':len(w250_out),'w250AppliedChanges':applied_n,'w250PreservedCurrent':preserved_n,'w250RootSupplementSha256':root_adj_sha,'sourceIdSetOverlap':0}}
write_json(OUT/'source-selection.json',prior_selection)
boundary=[]
for pos,role in [(299,'prior-window-end'),(300,'selected-start'),(349,'selected-end'),(350,'next-window-start')]:
 key=uncovered[pos];boundary.append({'sourceOrdinal':pos,'role':role,'sourceKey':key,'sourceTextSha256':sha_text(source[key])})
write_jsonl(OUT/'selection-boundary.jsonl',boundary)
write_jsonl(OUT/'candidate-free-cells.jsonl',cells)
write_jsonl(OUT/'caller-context.jsonl',[contexts[k] for k in keys])
write_jsonl(OUT/'dynamic-translation-callers.jsonl',dynamic)
write_json(OUT/'caller-scan-file-pins.json',{'exactHead':HEAD,'exactTree':TREE,'runtimeCodeFileCount':len(file_pins),'files':file_pins,'method':'Scan every tracked non-test frontend JS/TS and C# application source line for each selected Core key; record literal translator calls, indirect key references, comment references, and same-file dynamic translate/GetLocalizedString callsites.'})
write_json(OUT/'runtime-source-pins.json',{'exactHead':HEAD,'exactTree':TREE,'runtimeFiles':runtime,'dynamicTranslationCallsiteCount':len(dynamic),'note':'All dynamic calls are listed with file and line pins in dynamic-translation-callers.jsonl.'})
write_jsonl(OUT/'prior-selected-hold-reattestations.jsonl',w0_out)
write_jsonl(OUT/'prior-W200-application-reattestation.jsonl',w200_out)
write_jsonl(OUT/'prior-W250-application-reattestation.jsonl',w250_out)
write_json(OUT/'prior-W250-root-adjudication-attestation.json',{'result':'PASS','evidencePath':'docs/pr-evidence/pr190-localization-2026-11-04/window-250-299-followup/root-adjudication.json','evidenceSha256':root_adj_sha,'applicationResultSha256':sha((W250_APPLY/'apply-result.json').read_bytes()),'cellId':'AutomaticUpdatesDisabledDocker::id','sourceTextSha256':root_adj['sourceTextSha256'],'currentTargetSha256':root_adj['currentTargetSha256'],'replacedSelectedTargetSha256':root_adj['crossSelectedTargetSha256'],'correctedTargetSha256':root_adj['correctedTargetSha256'],'observedTargetSha256':sha_text(parsed['id']['AutomaticUpdatesDisabledDocker']),'rootDisposition':root_adj['rootDisposition'],'rootReason':root_adj['rootReason'],'correctedTargetTextIncluded':False,'applicationReadbackMatched':True,'supplementalRecordUnmodified':True})
write_json(OUT/'prior-W250-application-summary.json',{'result':'PASS','sourceHead':app_result['sourceHead'],'sourceTree':app_result['sourceTree'],'productCommit':app_result['productCommit'],'productCommitTree':app_result['productCommitTree'],'readbackRows':len(apply_rows),'appliedChanges':applied_n,'preservedCurrentCells':preserved_n,'allCurrentTargetsMatchReadback':True,'rootSupplementalAdjudicationSha256':root_adj_sha,'rootCorrectedCell':'AutomaticUpdatesDisabledDocker::id','rootCorrectedTargetSha256':root_adj['correctedTargetSha256'],'productCommitAncestorOfCurrentHead':True})
write_json(OUT/'prior-historical-evidence-scan.json',{'schemaVersion':1,'basis':'Frozen W150 direct-identifier scan over 392 exact Git blobs, reused to keep the Core queue stable while advancing W0-W299 selections.','sourceScanSha256':sha(scan_raw),'files':frozen_files,'rowsScanned':historical_rows,'directIdentifiers':len(historical_ids)})
write_json(OUT/'prior-lineage-summary.json',{'result':'PASS','w0W199Rows':len(w0_out),'w0W199HoldHashesReattested':sum(r['priorHoldPreserved'] for r in w0_out),'w0W199AllCurrentTargetHashesMatch':True,'w0W199AllHoldsTextFree':True,'w200Rows':len(w200_out),'w200Counts':dict(collections.Counter(r['disposition'] for r in w200_out)),'w200AllCurrentTargetsMatchFinal':True,'w250Rows':len(w250_out),'w250AppliedChanges':applied_n,'w250PreservedCurrent':preserved_n,'w250AllCurrentTargetsMatchFinal':True,'w250RootSupplementalAdjudicationIncluded':True,'w250RootSupplementalSha256':root_adj_sha,'totalPriorLineageRows':len(w0_out)+len(w200_out)+len(w250_out),'currentWindowCells':len(cells)})
write_json(OUT/'PR-attestation-before.json',before)
after=capture('after-candidate-free')
require(after['remoteRefs']==before['remoteRefs'] and after['headSha']==before['headSha'] and after['headTree']==before['headTree'],'PR/source refs moved during build')
write_json(OUT/'PR-attestation-after-candidate-free.json',after)
write_json(OUT/'candidate-free-summary.json',{'result':'PASS','exactHead':HEAD,'exactTree':TREE,'scope':{'sourceKeys':50,'locales':12,'cells':600,'positions':[300,349]},'sourceSelectionMethod':'Continue the frozen W0-W299 Core queue from the exact 392-blob historical direct-identifier scan; reattest prior selections and select the next 50 uncovered English Core keys at the exact current head.','callerBackedKeys':sum(contexts[k]['callerReferenceCount']>0 or contexts[k]['indirectKeyReferenceCount']>0 or contexts[k]['relatedDynamicTranslationCallsiteCount']>0 for k in keys),'callerlessKeys':[k for k in keys if not contexts[k]['callerReferenceCount'] and not contexts[k]['indirectKeyReferenceCount'] and not contexts[k]['relatedDynamicTranslationCallsiteCount']],'callerRefs':sum(contexts[k]['callerReferenceCount'] for k in keys),'uniqueCallerFiles':len({r['path'] for c in contexts.values() for r in c['callerRefs'] if r['isRuntimeReference']}),'integrityMismatchCounts':dict(mismatch),'priorW0W199RowsReattested':len(w0_out),'priorW200RowsReattested':len(w200_out),'priorW250RowsReattested':len(w250_out),'priorW250AppliedChanges':applied_n,'priorW250PreservedCurrent':preserved_n,'priorW250RootSupplementSha256':root_adj_sha,'candidateFreeContainsProposals':False,'repositoryModified':False,'testsBuildsCiWorkflowsRun':False,'securityScansOrCiRun':False,'requiredSourceAndCallerInventoryPerformed':True,'currentWindowBlindOrCrossOutputsAccessed':False})
write_json(OUT/'candidate-free-manifest.json',{'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'sourceWorktree':str(ROOT),'sourceWorktreeClean':True,'scope':{'positions':[300,349],'sourceIds':50,'targetLocales':LOCALES,'cells':600},'sourceSelection':{'path':'source-selection.json','sha256':sha((OUT/'source-selection.json').read_bytes()),'firstId':keys[0],'lastId':keys[-1],'selectedKeysSha256':sha(canon(keys))},'sourceCatalog':catalogs['en'],'targetCatalogs':{l:catalogs[l] for l in LOCALES},'candidateFreeCells':{'path':'candidate-free-cells.jsonl','rows':len(cells),'sha256':sha((OUT/'candidate-free-cells.jsonl').read_bytes())},'callerContext':{'path':'caller-context.jsonl','sourceIds':len(keys),'callerRefs':sum(contexts[k]['callerReferenceCount'] for k in keys),'uniqueCallerFiles':len({r['path'] for c in contexts.values() for r in c['callerRefs'] if r['isRuntimeReference']}),'sha256':sha((OUT/'caller-context.jsonl').read_bytes())},'priorLineage':{'w0W199Rows':len(w0_out),'w200Rows':len(w200_out),'w250Rows':len(w250_out),'w250AppliedChanges':applied_n,'w250PreservedCurrent':preserved_n,'w250RootSupplementSha256':root_adj_sha,'w0W199Sha256':sha((OUT/'prior-selected-hold-reattestations.jsonl').read_bytes()),'w200Sha256':sha((OUT/'prior-W200-application-reattestation.jsonl').read_bytes()),'w250Sha256':sha((OUT/'prior-W250-application-reattestation.jsonl').read_bytes())},'nativeSpeakerApproval':False,'repositoryModified':False,'testsBuildsCiWorkflowsRun':False,'sourceAndCallerInventoryScansRun':True})

(OUT/'README.md').write_text(f'''# ChaptarrNG PR #190 Core W300–W349 candidate-free packet\n\nPinned source: `{HEAD}` / tree `{TREE}`. This window contains 50 English Core keys × 12 locales = 600 current cells. Selection continues the frozen W0–W299 queue and verifies the previous selected keys against the current English Core catalog.\n\nThis packet contains exact source/target text, direct caller context and source pins, runtime localization pins, selection boundaries, and hash-only prior-lineage reattestations. It has no current-window proposals or review dispositions. Prior W250–W299 final readbacks are reattested at this head: 42 applied changes, 558 preserved-current cells, and the separate Indonesian root-adjudication supplement is linked by SHA-256 `{root_adj_sha}`. Earlier W0–W199 and W200–W249 holds remain text-free.\n\nOnly current-window candidate-free inputs were produced; no blind or W300–W349 cross-review outputs were accessed. No product files or PR state were modified.\n''',encoding='utf-8')

verify='''#!/usr/bin/env python3\nimport collections,hashlib,json,subprocess\nfrom pathlib import Path\nP=Path(__file__).resolve().parent; ROOT=Path("/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w300-349-source"); HEAD="f0082d1b655c05b8d4019ede523dd695cd6d745a"; TREE="4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"\ndef fail(s):raise SystemExit("FAIL: "+s)\ndef need(v,m):\n if not v:fail(m)\ndef sha(b):return hashlib.sha256(b).hexdigest()\ndef rj(n):return json.loads((P/n).read_text(encoding="utf-8"))\ndef rjl(n):return [json.loads(x) for x in (P/n).read_text(encoding="utf-8").splitlines() if x.strip()]\nneed((rj("candidate-free-manifest.json")["head"],rj("candidate-free-manifest.json")["tree"])==(HEAD,TREE),"head/tree")\nneed(subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==HEAD,"local head")\nneed(subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD^{tree}"],text=True).strip()==TREE,"local tree")\nneed(subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain=v1"],text=True).strip()=="","worktree status")\ns=rj("source-selection.json"); cells=rjl("candidate-free-cells.jsonl"); w0=rjl("prior-selected-hold-reattestations.jsonl"); w200=rjl("prior-W200-application-reattestation.jsonl"); w250=rjl("prior-W250-application-reattestation.jsonl"); b=rjl("selection-boundary.jsonl")\nneed(len(cells)==600 and len(s["keys"])==50 and len(set(s["keys"]))==50,"scope")\nneed(len({(r["sourceOrdinal"],r["locale"]) for r in cells})==600,"cell identities")\nneed([r["sourceOrdinal"] for r in b]==[299,300,349,350],"boundary positions")\nneed(len(w0)==1519 and len(w200)==600 and len(w250)==600,"lineage counts")\nneed(sum(r["priorHoldPreserved"] for r in w0)==312 and sum(r["priorHoldPreserved"] for r in w200)==12,"prior hold counts")\nneed(sum(r["disposition"]=="applied-change" for r in w250)==42 and sum(r["disposition"]=="preserved-current" for r in w250)==558,"W250 disposition counts")\nneed(all(r["targetTextIncluded"] is False for r in w0+w200+w250),"hash-only lineage")\nneed(not any(r["priorHoldPreserved"] and any(k in r for k in ("sourceText","currentTarget","targetText","finalTarget","finalReviewedTarget","recommendedTarget")) for r in w0+w200+w250),"text-free prior holds")\nneed(all(r["matches"] is True for r in w0+w200+w250),"prior hash reattestation")\nfor r in cells:\n need(r["batch"]=="W300-349-Core" and 300<=r["sourceOrdinal"]<=349,"cell position")\n need(sha(r["sourceText"].encode())==r["sourceTextSha256"] and sha(r["currentTarget"].encode())==r["currentTargetSha256"],"cell text hash")\n need(not any(k.lower().find("candidate")>=0 or k.lower().find("proposal")>=0 or k.lower().find("recommend")>=0 for k in r),"proposal field in candidate-free cell")\nneed(rj("prior-W250-root-adjudication-attestation.json")["applicationReadbackMatched"] is True,"root supplement attestation")\nneed(rj("candidate-free-summary.json")["candidateFreeContainsProposals"] is False,"candidate-free summary")\nprint(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":600,"sources":50,"locales":12,"priorW0W199Rows":len(w0),"priorW0W199Holds":312,"priorW200Rows":len(w200),"priorW200Holds":12,"priorW250Rows":len(w250),"priorW250Applied":42,"priorW250Preserved":558,"currentCallerBackedKeys":rj("candidate-free-summary.json")["callerBackedKeys"],"currentCallerlessKeys":len(rj("candidate-free-summary.json")["callerlessKeys"])},sort_keys=True))\n'''
(OUT/'verify_candidate_free.py').write_text(verify,encoding='utf-8')
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files),encoding='utf-8')
subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=OUT,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['python3',str(OUT/'verify_candidate_free.py')],check=True)
print(json.dumps({'candidateFreeOutput':str(OUT),'files':len(files)+1,'manifestSha256':sha((OUT/'candidate-free-manifest.json').read_bytes()),'checksumManifestSha256':sha((OUT/'SHA256SUMS.txt').read_bytes()),'head':HEAD,'tree':TREE,'cells':len(cells),'sourceKeys':len(keys),'callerBackedKeys':sum(contexts[k]['callerReferenceCount']>0 or contexts[k]['indirectKeyReferenceCount']>0 or contexts[k]['relatedDynamicTranslationCallsiteCount']>0 for k in keys),'callerlessKeys':[k for k in keys if not contexts[k]['callerReferenceCount'] and not contexts[k]['indirectKeyReferenceCount'] and not contexts[k]['relatedDynamicTranslationCallsiteCount']],'priorCounts':{'W0-W199':len(w0_out),'W200-W249':len(w200_out),'W250-W299':len(w250_out),'W250Applied':applied_n,'W250Preserved':preserved_n},'selection':{'first':keys[0],'last':keys[-1]},'integrityMismatches':dict(mismatch)},ensure_ascii=False,sort_keys=True,indent=2))
