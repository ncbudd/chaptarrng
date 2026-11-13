#!/usr/bin/env python3
"""Portable verifier for the W400–W449 ChaptarrNG Core candidate-free packet."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def canon(o): return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def readj(name): return json.loads((HERE/name).read_text())
def readjl(name): return [json.loads(x) for x in (HERE/name).read_text().splitlines() if x.strip()]
def require(ok,msg):
 if not ok: raise SystemExit('FAIL: '+msg)
def protected(s): return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def verify_repo(repo):
 att=readj('PR-attestation.json'); head=att['headSha']; main=att['liveMainSha']
 require(git(repo,'rev-parse','HEAD').decode().strip()==head,'exact PR head')
 require(git(repo,'rev-parse','HEAD^{tree}').decode().strip()==att['headTree'],'exact PR tree')
 require(git(repo,'rev-parse',f'{main}^{{tree}}').decode().strip()==att['liveMainTree'],'exact live-main tree')
 require(git(repo,'rev-parse',f'{head}:.github/workflows').decode().strip()==att['headWorkflowTree'],'PR workflow tree pin')
 require(git(repo,'rev-parse',f'{main}:.github/workflows').decode().strip()==att['liveMainWorkflowTree'],'main workflow tree pin')
 require(git(repo,'status','--porcelain=v1').decode().strip()=='','exact-head worktree clean')
 selection=readj('source-selection.json'); pins=readj('catalog-pins.json')
 srcpath='src/NzbDrone.Core/Localization/Core/en.json'
 raw=git(repo,'show',f'{head}:{srcpath}'); source=json.loads(raw)
 require(sha(raw)==selection['catalogSha256'] and len(source)==4165,'English source catalog pin')
 catalogs={}
 for loc in LOCALES:
  pin=pins[loc]; raw=git(repo,'show',f'{head}:{pin["path"]}'); data=json.loads(raw)
  require(sha(raw)==pin['sha256'] and set(data)==set(source) and len(data)==4165,'locale catalog pin/key parity '+loc)
  require(sha(canon(list(data)))==pin['keyOrderSha256'],'locale key order '+loc)
  catalogs[loc]=data
 for row in readjl('candidate-free-cells.jsonl'):
  require(source[row['sourceKey']]==row['sourceText'],'source catalog value '+row['sourceKey'])
  require(catalogs[row['locale']][row['sourceKey']]==row['currentTarget'],'locale catalog value '+row['sourceKey']+'/'+row['locale'])
 # Reconstruct the source queue from exact frozen Git blobs.
 scan=readj('prior-historical-evidence-scan.json'); ids=set(); seen=0
 require(len(scan['files'])==392 and scan['rowsScanned']==211539,'historical scan dimensions')
 for f in scan['files']:
  data=git(repo,'cat-file','blob',f['gitBlob']); require(sha(data)==f['sha256'],'frozen historical blob '+f['path'])
  for line in data.splitlines():
   if not line.strip(): continue
   try: obj=json.loads(line)
   except Exception: continue
   seen+=1
   if isinstance(obj,dict):
    for name in ('sourceKey','source_key','key','sourceId','source_id','id'):
     val=obj.get(name)
     if isinstance(val,str): ids.add(val)
 require(seen==211539,'historical rows scanned')
 uncovered=[key for key in source if key not in ids]
 prior=selection['priorSelections']; prior_keys=[key for win in prior for key in win['keys']]
 require(len(prior)==8 and len(prior_keys)==400 and prior_keys==uncovered[:400],'W0–W399 lineage')
 require(selection['keys']==uncovered[400:450],'W400–W449 uncovered selection')

def main():
 sums={}
 for line in (HERE/'SHA256SUMS.txt').read_text().splitlines():
  h,name=line.split('  ',1); sums[name]=h
 actual={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(sums==actual,'SHA256SUMS file set/content')
 att=readj('PR-attestation.json'); sel=readj('source-selection.json'); mani=readj('candidate-free-manifest.json')
 require(att['result']=='PASS' and att['state']=='open' and att['draft'] is True and att['mergedAt'] is None,'PR attestation state')
 require(att['headSha']==sel['head']==mani['head']=='8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7','head pins')
 require(att['headTree']==sel['tree']==mani['tree']=='018e46cd14424204a01be46e13e5b50f9f26ce07','tree pins')
 require(att['branchRefSha']==att['pullRefSha']==att['headSha'],'remote head refs')
 require(att['liveMainSha']==sel['liveMain']==mani['liveMain'],'live-main pins')
 require(att['headWorkflowTree']==mani['headWorkflowTree'] and att['liveMainWorkflowTree']==mani['liveMainWorkflowTree'],'workflow tree pins')
 require(mani['scope']=={'firstPosition':400,'lastPosition':449,'sourceIds':50,'locales':LOCALES,'cells':600},'manifest scope')
 require(sha((HERE/'source-selection.json').read_bytes())==mani['sourceSelectionSha256'],'source-selection checksum')
 require(sha((HERE/'candidate-free-cells.jsonl').read_bytes())==mani['candidateFreeCells']['sha256'],'cell checksum')
 require(sha((HERE/'caller-context.jsonl').read_bytes())==mani['callerContext']['sha256'],'caller-context checksum')
 require(sha((HERE/'catalog-pins.json').read_bytes())==mani['catalogPinsSha256'],'catalog pins checksum')
 require(sha((HERE/'latest-main-drift.json').read_bytes())==mani['latestMainDriftSha256'],'main-drift checksum')
 require(sha((HERE/'prior-window-reattestation.json').read_bytes())==mani['priorWindowReattestation']['sha256'],'prior-window reattestation checksum')
 require(sha((HERE/'prior-window-reattestation.jsonl').read_bytes())==mani['priorWindowCells']['sha256'],'prior-window cell checksum')
 require(sha((HERE/'prior-hold-reattestation.jsonl').read_bytes())==mani['priorHoldReattestation']['sha256'],'prior-hold checksum')
 require(sel['firstPosition']==400 and sel['lastPosition']==449 and len(sel['keys'])==50 and sel['priorSelectedKeysCount']==400,'selection dimensions')
 require([w['firstPosition'] for w in sel['priorSelections']]==list(range(0,400,50)),'prior window sequence')
 require([w['lastPosition'] for w in sel['priorSelections']]==list(range(49,400,50)),'prior window boundaries')
 cells=readjl('candidate-free-cells.jsonl'); contexts=readjl('caller-context.jsonl')
 require(len(cells)==600 and len(contexts)==50,'cell/context dimensions')
 require([(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in cells]==[(400+i,k,l) for i,k in enumerate(sel['keys']) for l in LOCALES],'cell identity/order')
 ctxmap={r['sourceKey']:r for r in contexts}; require(list(ctxmap)==sel['keys'],'caller context key order')
 for c in contexts:
  body={'sourceKey':c['sourceKey'],'literalAndIndirectReferences':c['callerRefs'],'relatedDynamicTranslationCallsites':c['dynamicTranslationCallsites']}
  require(sha(canon(body).rstrip(b'\n'))==c['callerContextSha256'],'caller context hash '+c['sourceKey'])
  require(c['callerReferenceCount']==sum(bool(x['isRuntimeReference']) for x in c['callerRefs']),'caller reference count '+c['sourceKey'])
  for ref in c['callerRefs']:
   require(shat(ref['lineText'])==ref['lineSha256'],'caller line hash '+c['sourceKey'])
  for call in c['dynamicTranslationCallsites']:
   require(shat(call['lineText'])==call['lineSha256'],'dynamic caller line hash '+c['sourceKey'])
 for row in cells:
  c=ctxmap[row['sourceKey']]
  require(row['callerContextSha256']==c['callerContextSha256'],'cell caller hash '+row['cellId'] if 'cellId' in row else row['sourceKey'])
  require(shat(row['sourceText'])==row['sourceTextSha256'] and shat(row['currentTarget'])==row['currentTargetSha256'],'cell text hash')
  require(row['sourcePlaceholders']==dict(sorted(collections.Counter(PH.findall(row['sourceText'])).items())),'source placeholders')
  require(row['currentPlaceholders']==dict(sorted(collections.Counter(PH.findall(row['currentTarget'])).items())),'target placeholders')
  require(row['sourcePlaceholders']==row['currentPlaceholders'],'placeholder parity')
  require(row['sourceInlineCode']==INLINE.findall(row['sourceText']) and row['currentInlineCode']==INLINE.findall(row['currentTarget']),'inline-code integrity')
  require(row['sourceMarkup']==MARKUP.findall(row['sourceText']) and row['currentMarkup']==MARKUP.findall(row['currentTarget']),'markup integrity')
  require(collections.Counter(NUM.findall(row['sourceText']))==collections.Counter(NUM.findall(row['currentTarget'])),'numeric integrity')
  require(all(x in row['currentTarget'] for x in protected(row['sourceText'])),'protected literal integrity')
  for name,value in row['integrityChecks'].items(): require(value,'candidate-free integrity check '+name+'/'+row['sourceKey'])
 prior=readjl('prior-window-reattestation.jsonl'); prior_summary=readj('prior-window-reattestation.json')
 require(len(prior)==prior_summary['priorWindowCellsReattested']==600,'prior window reattestation rows')
 require(all(r['reattested'] and r['currentTargetSha256']==r['priorExpectedAfterSha256']==r['priorReadbackObservedSha256'] for r in prior),'prior window target reattestation')
 holds=readjl('prior-hold-reattestation.jsonl')
 require(len(holds)==12 and all(r['reattested'] and not r['textIncluded'] for r in holds),'prior text-free holds')
 require(len(readj('prior-window-reattestation.json')['priorCallerScanFilesUnchanged']) if isinstance(readj('prior-window-reattestation.json')['priorCallerScanFilesUnchanged'],list) else readj('prior-window-reattestation.json')['priorCallerScanFilesUnchanged']==readj('prior-window-reattestation.json')['priorCallerScanFileCount'],'prior caller files')
 drift=readj('latest-main-drift.json')
 require(drift['sourceDifferences']==[] and drift['targetDifferences']==[],'source/target latest-main comparison')
 require(drift['workflowPathsInPrDiff']==[],'PR workflow path boundary')
 require(drift['mainWorkflowTreeChangedAgainstPr'] is True and drift['mainAdvanceWorkflowPaths']==['.github/workflows/build.yml'],'latest-main workflow drift recorded')
 require(len(drift['callerContextDifferences'])==6,'caller drift count')
 summary=readj('candidate-free-summary.json')
 require(summary['cells']==600 and summary['sourceIds']==50 and summary['locales']==12 and summary['candidateFreeOnly'],'candidate-free summary dimensions')
 require(summary['callerContextChangedAgainstMain']==len(drift['callerContextDifferences']),'summary caller drift count')
 forbidden={'recommendedTarget','candidateTarget','suggestedTarget','proposal','primaryDisposition','reviewJudgment','finalReviewedTarget'}
 def check(obj):
  if isinstance(obj,dict):
   require(not (set(obj)&forbidden),'candidate/review field in candidate-free data')
   for v in obj.values(): check(v)
  elif isinstance(obj,list):
   for v in obj: check(v)
 for p in HERE.rglob('*'):
  if p.suffix not in ('.json','.jsonl') or p.name in ('PR-attestation.json',): continue
  try:
   if p.suffix=='.json': check(json.loads(p.read_text()))
   else:
    for line in p.read_text().splitlines():
     if line.strip(): check(json.loads(line))
  except json.JSONDecodeError as e: raise SystemExit(f'FAIL: invalid JSON {p}: {e}')
 parser=argparse.ArgumentParser(); parser.add_argument('--repo'); args=parser.parse_args()
 if args.repo: verify_repo(Path(args.repo))
 print(json.dumps({'result':'PASS','head':att['headSha'],'tree':att['headTree'],'main':att['liveMainSha'],'sourceIds':50,'cells':600,'callerContexts':50,'priorCellsReattested':600,'priorHoldsReattested':12,'hashOnlySourceKeys':[r['sourceKey'] for r in contexts if r['literalCallCount']==0],'prWorkflowPaths':0,'mainWorkflowAdvancePaths':drift['mainAdvanceWorkflowPaths'],'candidateFreeOnly':True},indent=2))
if __name__=='__main__': main()
