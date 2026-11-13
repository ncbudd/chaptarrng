#!/usr/bin/env python3
"""Portable and exact-worktree verifier for ChaptarrNG PR #190 W450–W499."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
FORBIDDEN={'recommendedTarget','candidateTarget','suggestedTarget','proposalText','finalTarget','reviewedTarget','translationProposal'}
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def canon(o): return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def readj(name): return json.loads((HERE/name).read_text())
def readjl(name): return [json.loads(x) for x in (HERE/name).read_text().splitlines() if x.strip()]
def require(ok,msg):
 if not ok: raise SystemExit('FAIL: '+msg)
def protected(s): return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def verify_sums():
 expected={}
 for line in (HERE/'SHA256SUMS.txt').read_text().splitlines():
  h,name=line.split('  ',1); expected[name]=h
 actual={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(expected==actual,'SHA256SUMS file set/content')
def verify_packet():
 att0=readj('PR-attestation-before.json'); att1=readj('PR-attestation-after.json'); att=readj('PR-attestation.json')
 require(att==att1,'canonical PR attestation is final snapshot')
 require(att0['headSha']==att1['headSha']=='16c809b4787d70616a1a296ab0d90cf17923ba86','before/after PR head')
 require(att0['headTree']==att1['headTree']=='dbd8343a42476f4e830428cc59efb7f4830251d5','before/after PR tree')
 require(att0['apiBaseSha']==att1['apiBaseSha']=='025498c1a9deb999a4acd1eafc4c807a252e0c29','API base pin')
 require(att0['liveMainSha']==att1['liveMainSha'] and att0['liveMainTree']==att1['liveMainTree'],'live main stable across packet build')
 for x in (att0,att1):
  pr=x['prApi']; refs=x['remoteRefs']
  require(pr['state']=='OPEN' and pr['isDraft'] is True and pr['headRefOid']==x['headSha'] and pr['baseRefOid']==x['apiBaseSha'],'live PR API pins')
  require(refs['refs/heads/codex/chaptarrng-localization-complete-20261031']==x['headSha'] and refs['refs/pull/190/head']==x['headSha'],'branch/pull refs')
  require(refs['refs/heads/main']==x['liveMainSha'],'live main ref')
  require(x['exactWorktreeHead']==x['headSha'] and x['exactWorktreeTree']==x['headTree'] and x['exactWorktreeClean'],'exact worktree attestation')
  require(x['headWorkflowTree']=='d32d228b81852c2f44fdea6511a0bd5df35f61d2' and x['liveMainWorkflowTree']=='aed02ef5ae1eea8a00a4def7850891dc08c47176','workflow trees pinned')
 sel=readj('source-selection.json'); mani=readj('candidate-free-manifest.json'); summ=readj('candidate-free-summary.json')
 require(sel['batch']=='W450-499-Core' and sel['head']==att['headSha'] and sel['tree']==att['headTree'] and sel['liveMain']==att['liveMainSha'],'selection pins')
 require(sel['firstPosition']==450 and sel['lastPosition']==499 and sel['priorSelectedKeysCount']==450 and len(sel['keys'])==50,'source selection dimensions')
 require(mani['scope']=={'firstPosition':450,'lastPosition':499,'sourceIds':50,'locales':LOCALES,'cells':600},'manifest scope')
 require(mani['head']==att['headSha'] and mani['tree']==att['headTree'] and mani['liveMain']==att['liveMainSha'],'manifest exact pins')
 cells=readjl('candidate-free-cells.jsonl'); contexts=readjl('caller-context.jsonl')
 require(len(cells)==600 and len(contexts)==50,'current cell and caller dimensions')
 require([(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in cells]==[(450+i,k,l) for i,k in enumerate(sel['keys']) for l in LOCALES],'cell order')
 cby={r['sourceKey']:r for r in contexts}; require(list(cby)==sel['keys'],'caller key order')
 for c in contexts:
  body={'sourceKey':c['sourceKey'],'literalAndIndirectReferences':c['callerRefs'],'relatedDynamicTranslationCallsites':c['dynamicTranslationCallsites']}
  require(sha(canon(body).rstrip(b'\n'))==c['callerContextSha256'],'caller context hash '+c['sourceKey'])
  require(c['callerReferenceCount']==sum(bool(x['isRuntimeReference']) for x in c['callerRefs']),'caller count '+c['sourceKey'])
  for row in c['callerRefs']+c['dynamicTranslationCallsites']:
   require(shat(row['lineText'])==row['lineSha256'],'caller line hash '+c['sourceKey'])
 integrity=collections.Counter()
 for r in cells:
  c=cby[r['sourceKey']]
  require(shat(r['sourceText'])==r['sourceTextSha256'] and shat(r['currentTarget'])==r['currentTargetSha256'],'cell text hash')
  require(r['callerContextSha256']==c['callerContextSha256'],'cell caller fingerprint')
  require(r['sourcePlaceholders']==dict(sorted(collections.Counter(PH.findall(r['sourceText'])).items())),'source placeholder signature')
  require(r['currentPlaceholders']==dict(sorted(collections.Counter(PH.findall(r['currentTarget'])).items())),'target placeholder signature')
  require(r['sourceInlineCode']==INLINE.findall(r['sourceText']) and r['currentInlineCode']==INLINE.findall(r['currentTarget']),'inline code signature')
  require(r['sourceMarkup']==MARKUP.findall(r['sourceText']) and r['currentMarkup']==MARKUP.findall(r['currentTarget']),'markup signature')
  require(r['protectedLiterals']==protected(r['sourceText']),'protected literal signature')
  checks={'placeholder':r['sourcePlaceholders']==r['currentPlaceholders'],'inlineCode':r['sourceInlineCode']==r['currentInlineCode'],'markup':r['sourceMarkup']==r['currentMarkup'],'numeric':collections.Counter(NUM.findall(r['sourceText']))==collections.Counter(NUM.findall(r['currentTarget'])),'protectedLiteral':all(x in r['currentTarget'] for x in protected(r['sourceText']))}
  require(r['integrityChecks']==checks,'stored integrity flags')
  for name,ok in checks.items():
   if not ok: integrity[name]+=1
 require(summ['integrityCheckFailures']==dict(integrity),'summary integrity counts')
 require(integrity==collections.Counter({'numeric':2}),'only two recorded numeric-token heuristic flags')
 drift=readj('latest-main-drift.json')
 require(drift['prHead']==att['headSha'] and drift['liveMain']==att['liveMainSha'],'main drift pins')
 require(len(drift['sourceDifferences'])==0 and len(drift['targetDifferences'])==0,'source and target comparison vs main')
 require(len(drift['callerContextDifferences'])==6 and drift['workflowPathsInPrDiff']==[],'caller and PR workflow drift recorded')
 require(drift['prWorkflowTree']==att['headWorkflowTree'] and drift['liveMainWorkflowTree']==att['liveMainWorkflowTree'],'workflow trees in drift record')
 for key,name in [('sourceSelection','source-selection.json'),('candidateFreeCells','candidate-free-cells.jsonl'),('callerContext','caller-context.jsonl'),('catalogPins','catalog-pins.json'),('latestMainDrift','latest-main-drift.json')]:
  require(sha((HERE/name).read_bytes())==mani['artifactPins'][key]['sha256'],'manifest hash '+name)
 # W400 selection and committed application continuity.
 prior=readjl('prior-window-reattestation.jsonl'); ps=readj('prior-window-reattestation.json')
 require(len(prior)==600 and all(r['reattested'] and r['sourceMatches'] and r['targetMatchesPostApplication'] and r['callerContextMatchesFrozenInput'] for r in prior),'W400 cell continuity after committed application')
 require(ps['cellsReattested']==600 and ps['sourceHashMismatches']==0 and ps['targetHashMismatchesAfterCommittedApplication']==0 and ps['callerContextHashMismatches']==0,'W400 reattestation summary')
 require(len(readjl('prior-caller-scan-file-reattestation.jsonl'))==4350 and ps['callerScanFilesReattested']==4350,'W400 caller file set continuity')
 app=readjl('w400-application-readback-reattestation.jsonl')
 require(len(app)==140 and all(r['readbackMatchesCurrent'] and r['sourceTextMatchesCurrent'] for r in app),'W400 committed application readback')
 w400holds=readjl('w400-callerless-hold-reattestation.jsonl'); carry=readjl('w400-carried-prior-hold-reattestation.jsonl')
 require(len(w400holds)==12 and all(r['reattested'] and r['sourceTextIncluded'] is False and r['targetTextIncluded'] is False for r in w400holds),'W400 12 hash-only holds')
 require(len(carry)==12 and all(r['reattested'] and r['sourceTextIncluded'] is False and r['targetTextIncluded'] is False for r in carry),'carried prior 12 hash-only holds')
 prev=readj('prior-review-input-reattestation.json')
 require(prev['W400']['applicationCommitIsAncestor'] and prev['W400']['applicationRows']==140 and prev['W400']['applicationReadbackMatchesCurrent']==140,'W400 app lineage')
 require(prev['legacyW450']['primaryWindowKeyOverlap']==0 and prev['legacyW450']['legacyDisposition']=='STALE_SELECTION_NO_KEY_OVERLAP','legacy W450 packets are stale selection')
 require(prev['legacyInputsReattestedAtCurrentHead'] is False and prev['legacyRootReadbackMatchesCurrent'] is False,'legacy packets not treated as current')
 require(prev['legacyW450']['candidateTextsRead'] is False and prev['legacyW450']['proposalLedgersOpened'] is False,'legacy review isolation')
 # Check no proposal/recommendation fields were introduced into this candidate-free packet.
 def scrub(x):
  if isinstance(x,dict):
   require(not (set(x)&FORBIDDEN),'proposal text field found')
   for v in x.values(): scrub(v)
  elif isinstance(x,list):
   for v in x: scrub(v)
 for p in HERE.rglob('*'):
  if p.suffix not in ('.json','.jsonl'): continue
  try:
   if p.suffix=='.json': scrub(json.loads(p.read_text()))
   else:
    for line in p.read_text().splitlines():
     if line.strip(): scrub(json.loads(line))
  except json.JSONDecodeError as e: raise SystemExit(f'FAIL: invalid JSON {p}: {e}')
 return {'result':'PASS','head':att['headSha'],'tree':att['headTree'],'main':att['liveMainSha'],'sourceIds':50,'cells':600,'callerContexts':50,'priorW400CellsReattested':600,'callerFilesReattested':4350,'committedW400ApplicationCellsReattested':140,'w400CallerlessHoldsReattested':12,'carriedPriorHoldsReattested':12,'legacyNov2W450Inputs':'stale; zero source-key overlap','sourceTargetDriftVsMain':0,'callerContextDriftVsMain':6,'numericHeuristicFlags':2,'prWorkflowPaths':0,'candidateFreeOnly':True}
def verify_repo(repo):
 att=readj('PR-attestation.json'); head=att['headSha']; main=att['liveMainSha']
 require(git(repo,'rev-parse','HEAD').decode().strip()==head,'exact PR head')
 require(git(repo,'rev-parse','HEAD^{tree}').decode().strip()==att['headTree'],'exact PR tree')
 require(git(repo,'rev-parse',f'{main}^{{tree}}').decode().strip()==att['liveMainTree'],'exact main tree')
 require(git(repo,'rev-parse',f'{head}:.github/workflows').decode().strip()==att['headWorkflowTree'],'PR workflow tree')
 require(git(repo,'rev-parse',f'{main}:.github/workflows').decode().strip()==att['liveMainWorkflowTree'],'main workflow tree')
 require(git(repo,'status','--porcelain=v1').decode().strip()=='','exact worktree clean')
 sel=readj('source-selection.json'); pins=readj('catalog-pins.json'); srcpath='src/NzbDrone.Core/Localization/Core/en.json'
 raw=git(repo,'show',f'{head}:{srcpath}'); source=json.loads(raw)
 require(sha(raw)==sel['catalogSha256'] and len(source)==4165,'English catalog pin')
 catalogs={}
 for loc in LOCALES:
  pin=pins[loc]; data_raw=git(repo,'show',f'{head}:{pin["path"]}'); data=json.loads(data_raw)
  require(sha(data_raw)==pin['sha256'] and len(data)==4165 and set(data)==set(source),'locale catalog '+loc)
  require(sha(canon(list(data)))==pin['keyOrderSha256'],'locale key order '+loc)
  catalogs[loc]=data
 for r in readjl('candidate-free-cells.jsonl'):
  require(source[r['sourceKey']]==r['sourceText'],'English value '+r['sourceKey'])
  require(catalogs[r['locale']][r['sourceKey']]==r['currentTarget'],'locale value '+r['sourceKey']+'/'+r['locale'])
 # Historical-source queue and W0–W449 selection continuity.
 scan=readj('prior-historical-evidence-scan.json'); ids=set(); seen=0
 require(len(scan['files'])==392 and scan['rowsScanned']==211539,'historical scan dimensions')
 for f in scan['files']:
  data=git(repo,'cat-file','blob',f['gitBlob']); require(sha(data)==f['sha256'],'historical source blob '+f['path'])
  for line in data.splitlines():
   if not line.strip(): continue
   try: obj=json.loads(line)
   except Exception: continue
   seen+=1
   if isinstance(obj,dict):
    for name in ('sourceKey','source_key','key','sourceId','source_id','id'):
     if isinstance(obj.get(name),str): ids.add(obj[name])
 require(seen==211539,'historical source row count')
 uncovered=[k for k in source if k not in ids]
 prior=sel['priorSelections']; prior_keys=[k for w in prior for k in w['keys']]
 require(len(prior)==9 and len(prior_keys)==450 and prior_keys==uncovered[:450],'W0–W449 selection lineage')
 require(sel['keys']==uncovered[450:500],'W450–W499 first uncovered keys')
 # Recheck every prior W400 caller-scan file pin against the current exact head blobs.
 pins400=readj('caller-scan-file-pins.json') if (HERE/'caller-scan-file-pins.json').exists() else None
 prev_pins=readjl('prior-caller-scan-file-reattestation.jsonl')
 tree_rows=git(repo,'ls-tree','-r','-z',head,'--','frontend/src','src').split(b'\0')
 tree_map={}
 for ent in tree_rows:
  if not ent: continue
  meta,path=ent.split(b'\t',1); fields=meta.decode().split(); tree_map[path.decode()]=fields[-1]
 for row in prev_pins:
  require(tree_map.get(row['path'])==row['gitBlobExpected']==row['gitBlobCurrent'],'W400 caller tree pin '+row['path'])
  data=git(repo,'cat-file','blob',row['gitBlobExpected']); require(sha(data)==row['sha256Expected']==row['sha256Current'],'W400 caller blob hash '+row['path'])
 # Current W450 caller scan pins are emitted for PR head and live main.
 for name,rev,field in [('caller-scan-file-pins.json',head,'gitBlob'),('main-caller-scan-file-pins.json',main,'gitBlob')]:
  ob=readj(name); files=ob['files']; count=0
  for f in files:
   oid=git(repo,'rev-parse',f'{rev}:{f["path"]}').decode().strip(); raw=git(repo,'cat-file','blob',oid)
   require(oid==f[field] and sha(raw)==f['sha256'] and len(raw)==f['bytes'],name+' '+f['path']); count+=1
  require(count==ob['gitBlobFileCount'],name+' count')
 # Runtime source-file pins.
 for f in readj('runtime-source-pins.json'):
  oid=git(repo,'rev-parse',f'{head}:{f["path"]}').decode().strip(); raw=git(repo,'cat-file','blob',oid)
  require(oid==f['gitBlob'] and sha(raw)==f['sha256'] and len(raw)==f['bytes'],'runtime source '+f['path'])
 # W400 application result is present in the pinned PR history and catalogs.
 prior_summary=readj('prior-review-input-reattestation.json'); app_commit=prior_summary['W400']['applicationCommit']
 subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',app_commit,head],check=True,stdout=subprocess.DEVNULL)
 print(json.dumps({'exactWorktree':'PASS','head':head,'tree':att['headTree'],'main':main,'catalogs':13,'selectedCellsVerified':600,'historicalRows':seen,'callerSourcePinsVerified':len(prev_pins)+len(readj('caller-scan-file-pins.json')['files'])+len(readj('main-caller-scan-file-pins.json')['files'])},indent=2))
def main():
 verify_sums(); result=verify_packet()
 ap=argparse.ArgumentParser();ap.add_argument('--repo');args=ap.parse_args()
 if args.repo: verify_repo(Path(args.repo))
 print(json.dumps(result,indent=2))
if __name__=='__main__': main()
