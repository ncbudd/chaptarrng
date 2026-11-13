#!/usr/bin/env python3
import hashlib,json
from collections import Counter
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
CAND=BASE/'candidate-free/input'
CROSS=BASE/'cross-review-sealed'
SECOND=BASE/'second-opinion'
ROOT=BASE/'root-adjudication'
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def readjl(path):
 raw=[x for x in path.read_bytes().splitlines() if x.strip()]
 return [(json.loads(x),sha(x)) for x in raw]
candidates={(r['sourceKey'],r['locale']):(r,h) for r,h in readjl(CAND/'candidate-free-cells.jsonl')}
proposals={(r['sourceKey'],r['locale']):(r,h) for r,h in readjl(CROSS/'proposals.jsonl')}
second={r['cellId']:(r,h) for r,h in readjl(SECOND/'ledger.jsonl')}
root={r['cellId']:(r,h) for r,h in readjl(ROOT/'root-adjudication-ledger.jsonl')}
assert len(candidates)==600 and len(proposals)==111 and len(second)==111 and len(root)==111
changes=[]
for ident,(r,rh) in sorted(root.items(),key=lambda kv:(kv[1][0]['sourceOrdinal'],kv[0].rsplit('::',1)[1])):
 key,locale=ident.rsplit('::',1); c,ch=candidates[(key,locale)];p,ph=proposals[(key,locale)];s,sh=second[r['cellId']]
 assert r['rootDecision']=='accept-cross-recommendation'
 assert r['finalTarget']==p['recommendedTarget']==s['chosenTarget']
 assert r['candidateFreeRowSha256']==ch==s['candidateFreeRowSha256']
 assert r['crossReviewProposalRowSha256']==ph==s['proposalRowSha256']
 assert r['secondOpinionRowSha256']==sh
 assert c['currentTargetSha256']==p['currentTargetSha256']==r['currentTargetSha256']
 assert c['targetFile']==f"src/NzbDrone.Core/Localization/Core/{'pt_BR' if locale=='pt-BR' else {'zh-Hans':'zh_CN','zh-Hant':'zh_TW'}.get(locale,locale)}.json"
 changes.append({
  'cellId':key+'::'+locale,'sourceOrdinal':r['sourceOrdinal'],'sourceKey':key,'locale':locale,
  'catalogPath':c['targetFile'],'sourceText':c.get('sourceText'),'sourceTextSha256':c['sourceTextSha256'],
  'sourceKeySha256':s['sourceKeySha256'],'callerContextSha256':r['callerContextSha256'],
  'candidateFreeRowSha256':ch,'crossReviewProposalRowSha256':ph,
  'crossReviewLedgerRowSha256':r['crossReviewLedgerRowSha256'],'secondOpinionRowSha256':sh,
  'rootAdjudicationRowSha256':rh,'expectedCurrentTarget':c['currentTarget'],
  'expectedCurrentTargetSha256':c['currentTargetSha256'],'finalTarget':r['finalTarget'],
  'finalTargetSha256':r['finalTargetSha256'],'crossDecision':p['crossDecision'],
  'tokenChecks':p['finalTokenChecks'],'manualLexicalizedNumericException':r['manualLexicalizedNumericException'],
  'crossRationale':p['rationale'],'rootRationale':r['rootRationale']
 })
pins=json.loads((CAND/'catalog-pins.json').read_text())
catalogs=[{'locale':loc,**pins[loc]} for loc in ['en','ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']]
counts=Counter(c['locale'] for c in changes)
files={}
for label,path in {
 'candidateFreeCells':CAND/'candidate-free-cells.jsonl','candidateFreeManifest':CAND/'candidate-free-manifest.json','candidateFreeChecksums':CAND/'SHA256SUMS.txt',
 'primaryManifest':BASE/'primary-review/manifest.json','primaryChecksums':BASE/'primary-review/SHA256SUMS.txt',
 'blindManifest':BASE/'blind-review/manifest.json','blindChecksums':BASE/'blind-review/SHA256SUMS.txt',
 'crossManifest':CROSS/'manifest.json','crossLedger':CROSS/'ledger.jsonl','crossProposals':CROSS/'proposals.jsonl','crossChecksums':CROSS/'SHA256SUMS.txt',
 'secondOpinionSummary':SECOND/'summary.json','secondOpinionLedger':SECOND/'ledger.jsonl','secondOpinionChecksums':SECOND/'SHA256SUMS.txt',
 'rootLedger':ROOT/'root-adjudication-ledger.jsonl','rootSummary':ROOT/'summary.json'
}.items(): files[label]={'path':str(path.relative_to(BASE)),'sha256':sha(path.read_bytes())}
plan={
 'artifact':'ChaptarrNG PR #190 W450-W499 hash-guarded application plan',
 'sourcePin':{'head':'16c809b4787d70616a1a296ab0d90cf17923ba86','tree':'dbd8343a42476f4e830428cc59efb7f4830251d5'},
 'baseSha':'025498c1a9deb999a4acd1eafc4c807a252e0c29','window':'W450-W499',
 'candidateCellCount':600,'callerBoundCellCount':552,'hashOnlyHolds':48,
 'crossDecisionCounts':{'accept-current':441,'selectedChanges':111},
 'rootDecisionCounts':{'accept-cross-recommendation':111,'accept-adjusted-target':0,'hold-selected-proposal':0},
 'selectedChanges':len(changes),'changedByLocale':dict(sorted(counts.items())),
 'manualLexicalizedNumericExceptions':[{'sourceOrdinal':471,'locale':'ja','token':'8進数'},{'sourceOrdinal':471,'locale':'ko','token':'8진수'}],
 'catalogs':catalogs,'evidenceInputs':files,'changes':changes,
 'nativeSpeakerApproval':False,'workflowChanges':False,'testsBuildsScansCiRun':False
}
(OUT/'apply-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={k:v for k,v in plan.items() if k not in ('changes','catalogs')};summary.update({'changedCatalogCount':len({c['catalogPath'] for c in changes}),'changedCatalogPaths':sorted({c['catalogPath'] for c in changes})})
(OUT/'plan-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'result':'PASS','selectedChanges':len(changes),'changedCatalogs':summary['changedCatalogCount'],'byLocale':dict(sorted(counts.items()))},ensure_ascii=False))
