#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def readj(name):return json.loads((HERE/name).read_text())
def readjl(name):return [json.loads(x) for x in (HERE/name).read_text().splitlines() if x.strip()]
def require(ok,msg):
 if not ok:raise SystemExit('FAIL: '+msg)
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))

def verify_live(repo):
 att=readj('PR-attestation.json'); head=att['headSha']; main=att['liveMainSha']
 require(git(repo,'rev-parse','HEAD').decode().strip()==head,'live PR head')
 require(git(repo,'rev-parse','HEAD^{tree}').decode().strip()==att['headTree'],'live PR tree')
 require(git(repo,'rev-parse',f'{main}^{{tree}}').decode().strip()==att['liveMainTree'],'live main tree')
 require(git(repo,'rev-parse',f'{head}:.github/workflows').decode().strip()==att['headWorkflowTree'],'live PR workflow tree')
 require(git(repo,'rev-parse',f'{main}:.github/workflows').decode().strip()==att['liveMainWorkflowTree'],'live main workflow tree')
 for rev in (head,main): require(git(repo,'cat-file','-e',f'{rev}^{{commit}}')==b'','live commit exists '+rev)
 selection=readj('source-selection.json'); pins=readj('catalog-pins.json'); rows=readjl('candidate-free-cells.jsonl')
 source=json.loads(git(repo,'show',f'{head}:src/NzbDrone.Core/Localization/Core/en.json'))
 current={}
 for loc,name in {'en':'en.json',**LOCALE_FILES}.items():
  rel=f'src/NzbDrone.Core/Localization/Core/{name}'; data_raw=git(repo,'show',f'{head}:{rel}'); data=json.loads(data_raw)
  pin=pins[loc]
  require(sha(data_raw)==pin['sha256'] and len(data)==4165 and set(data)==set(source), 'live catalog pin/key set '+loc)
  require(sha(canon(list(data)))==pin['keyOrderSha256'],'live catalog order pin '+loc)
  current[loc]=data
 main_source=json.loads(git(repo,'show',f'{main}:src/NzbDrone.Core/Localization/Core/en.json'))
 main_catalogs={loc:json.loads(git(repo,'show',f'{main}:{pins[loc]["path"]}')) for loc in LOCALES}
 for row in rows:
  key=row['sourceKey'];loc=row['locale']
  require(source[key]==row['sourceText'] and shat(source[key])==row['sourceTextSha256'],'live source cell '+key)
  require(current[loc][key]==row['currentTarget'] and shat(current[loc][key])==row['currentTargetSha256'],'live target cell '+key+'/'+loc)
  require(main_source.get(key)==source[key] and main_catalogs[loc].get(key)==current[loc][key],'latest-main source/target '+key+'/'+loc)

def main():
 sums={}
 for line in (HERE/'SHA256SUMS.txt').read_text().splitlines():
  h,name=line.split('  ',1);sums[name]=h
 actual={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(sums==actual,'packet SHA256SUMS file set/content')
 att=readj('PR-attestation.json'); sel=readj('source-selection.json'); mani=readj('candidate-free-manifest.json')
 require(att['result']=='PASS' and att['headSha']==sel['head']==mani['head'],'head identity')
 require(att['headTree']==sel['tree']==mani['tree'],'tree identity')
 require(att['liveMainSha']==sel['liveMain']==mani['liveMain'],'main identity')
 require(att['liveMainTree']==sel['liveMainTree']==mani['liveMainTree'],'main tree identity')
 require(att['headWorkflowTree']==att['liveMainWorkflowTree'],'workflow tree identity')
 require(mani['sourceSelectionSha256']==sha((HERE/'source-selection.json').read_bytes()),'source selection manifest hash')
 require(mani['candidateFreeCells']['sha256']==sha((HERE/'candidate-free-cells.jsonl').read_bytes()),'candidate cell manifest hash')
 require(mani['callerContext']['sha256']==sha((HERE/'caller-context.jsonl').read_bytes()),'caller manifest hash')
 require(mani['latestMainDriftSha256']==sha((HERE/'latest-main-drift.json').read_bytes()),'main drift manifest hash')
 require(mani['catalogPinsSha256']==sha((HERE/'catalog-pins.json').read_bytes()),'catalog pins manifest hash')
 require(mani['integrityHeuristicFlags']['sha256']==sha((HERE/'integrity-review-flags.jsonl').read_bytes()),'heuristic flags manifest hash')
 require(att['state']=='open' and att['draft'] is True and att['mergedAt'] is None,'PR state')
 require(att['branchRefSha']==att['headSha'] and att['pullRefSha']==att['headSha'],'remote PR refs')
 require(att['prBodySnapshotExactUtf8'] is True,'body snapshot exact')
 require(att['prBodyBytes']==len((HERE.parent.parent/'attestation'/'pr-body-current.txt').read_bytes()),'body byte count')
 require(sha((HERE.parent.parent/'attestation'/'pr-body-current.txt').read_bytes())==att['prBodySha256'],'body exact hash')
 require(sel['firstPosition']==350 and sel['lastPosition']==399 and len(sel['keys'])==50,'selection dimensions')
 require(sel['priorSelectedKeysCount']==350 and len(sel['priorSelections'])==7,'prior selection dimensions')
 prior=[k for win in sel['priorSelections'] for k in win['keys']]
 require(len(prior)==350 and len(set(prior))==350 and prior==sel['priorSelections'][0]['keys']+sum((w['keys'] for w in sel['priorSelections'][1:]),[]),'prior key lineage')
 require(len(set(prior+sel['keys']))==400,'selection uniqueness')
 scan=readj('prior-historical-evidence-scan.json')
 require(scan['sourceScanSha256']==sel['historicalEvidenceScanSha256'] and len(scan['files'])==392 and scan['rowsScanned']==211539,'historical source scan pin')
 require(sha((HERE/'prior-historical-evidence-scan.json').read_bytes())==sel['historicalEvidenceScanPacketFileSha256'],'historical scan packet hash')
 cells=readjl('candidate-free-cells.jsonl'); contexts=readjl('caller-context.jsonl'); pins=readj('catalog-pins.json')
 require(len(cells)==600 and len(contexts)==50,'cell/context counts')
 expect=[(350+i, key, loc) for i,key in enumerate(sel['keys']) for loc in LOCALES]
 require([(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in cells]==expect,'cell identity/order')
 by_key={r['sourceKey']:r for r in contexts}
 require(list(by_key)==sel['keys'],'caller key order')
 require(len(by_key)==50,'caller key uniqueness')
 for row in contexts:
  ctx={'sourceKey':row['sourceKey'],'literalAndIndirectReferences':row['callerRefs'],'relatedDynamicTranslationCallsites':row['dynamicTranslationCallsites']}
  require(sha(canon(ctx).rstrip(b'\n'))==row['callerContextSha256'],'caller context hash '+row['sourceKey'])
  require(row['callerReferenceCount']==sum(r['isRuntimeReference'] for r in row['callerRefs']),'caller ref count '+row['sourceKey'])
  for ref in row['callerRefs']:
   require(shat(ref['lineText'])==ref['lineSha256'],'caller line hash '+row['sourceKey'])
 for row in cells:
  c=by_key[row['sourceKey']]
  require(row['callerContextSha256']==c['callerContextSha256'],'cell caller hash '+row['sourceKey'])
  require(shat(row['sourceText'])==row['sourceTextSha256'] and shat(row['currentTarget'])==row['currentTargetSha256'],'cell content hash')
  require(row['sourcePlaceholders']==dict(sorted(collections.Counter(PH.findall(row['sourceText'])).items())),'source placeholder data')
  require(row['currentPlaceholders']==dict(sorted(collections.Counter(PH.findall(row['currentTarget'])).items())),'target placeholder data')
  require(row['sourceInlineCode']==INLINE.findall(row['sourceText']) and row['currentInlineCode']==INLINE.findall(row['currentTarget']),'inline data')
  require(row['sourceMarkup']==MARKUP.findall(row['sourceText']) and row['currentMarkup']==MARKUP.findall(row['currentTarget']),'markup data')
  require(row['sourceNumericTokens']==NUM.findall(row['sourceText']) and row['currentNumericTokens']==NUM.findall(row['currentTarget']),'numeric data')
  require(row['protectedLiterals']==protected(row['sourceText']),'protected-literal data')
 for loc in LOCALES:
  p=pins[loc]
  require(p['keyCount']==4165 and p['path']==f'src/NzbDrone.Core/Localization/Core/{LOCALE_FILES[loc]}','catalog dimensions '+loc)
 drift=readj('latest-main-drift.json')
 require(drift['prHead']==att['headSha'] and drift['liveMain']==att['liveMainSha'],'drift pin')
 require(drift['prHeadTree']==att['headTree'] and drift['liveMainTree']==att['liveMainTree'],'drift tree pins')
 require(drift['prWorkflowTree']==att['headWorkflowTree'] and drift['liveMainWorkflowTree']==att['liveMainWorkflowTree'],'drift workflow trees')
 require(not drift['sourceDifferences'] and not drift['targetDifferences'],'source/target drift')
 require(not drift['translationCallsiteChangesAgainstMain'],'translation callsite changes')
 require(not drift['prDiffFromMergeBase']['workflowPaths'] and not drift['mainAdvanceWorkflowPaths'],'workflow boundary')
 require(not drift['mainAdvanceCoreCatalogPaths'] and not drift['mainAdvanceEnglishSourcePaths'] and not drift['mainAdvanceLocaleCatalogPaths'],'main source/catalog boundary')
 require(not drift['serverMessageManifestW350IdOverlap'],'manifest source-ID overlap')
 summary=readj('candidate-free-summary.json')
 require(summary['cells']==600 and summary['sourceIds']==50 and summary['locales']==12,'summary dimensions')
 flags=readjl('integrity-review-flags.jsonl')
 require(len(flags)==summary['protectedLiteralHeuristicFlags'],'heuristic flag count')
 forbidden={'proposal','candidateTarget','suggestedTarget','recommendedTarget','primaryDisposition','reviewJudgment'}
 def fields(obj):
  if isinstance(obj,dict):
   for k,v in obj.items():
    if k in forbidden:raise SystemExit('FAIL: candidate-bearing field '+k)
    fields(v)
  elif isinstance(obj,list):
   for v in obj:fields(v)
  elif isinstance(obj,str):
   pass
 for name in ['candidate-free-manifest.json','candidate-free-summary.json','source-selection.json','candidate-free-cells.jsonl','caller-context.jsonl','latest-main-drift.json']:
  fields(readj(name) if name.endswith('.json') else readjl(name))
 parser=argparse.ArgumentParser();parser.add_argument('--repo');args=parser.parse_args()
 if args.repo:verify_live(Path(args.repo))
 print(json.dumps({'result':'PASS','head':att['headSha'],'tree':att['headTree'],'main':att['liveMainSha'],'sourceIds':50,'cells':600,'callerContexts':50,'protectedLiteralHeuristicFlags':len(flags),'workflowPaths':0,'candidateFreeOnly':True},indent=2))
if __name__=='__main__':main()
