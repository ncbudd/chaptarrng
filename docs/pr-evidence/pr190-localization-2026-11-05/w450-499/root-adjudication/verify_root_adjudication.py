#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
readjl=lambda p:[(json.loads(raw),hashlib.sha256(raw).hexdigest()) for raw in p.read_bytes().splitlines() if raw.strip()]
cand=[r for r,h in readjl(BASE/'candidate-free/input/candidate-free-cells.jsonl')]
props={r['sourceKey']+'::'+r['locale']:(r,h) for r,h in readjl(BASE/'cross-review-sealed/proposals.jsonl')}
cross={r['sourceKey']+'::'+r['locale']:(r,h) for r,h in readjl(BASE/'cross-review-sealed/ledger.jsonl')}
second={r['cellId']:(r,h) for r,h in readjl(BASE/'second-opinion/ledger.jsonl')}
root={r['cellId']:(r,h) for r,h in readjl(HERE/'root-adjudication-ledger.jsonl')}
holds=[r for r,h in readjl(BASE/'cross-review-sealed/holds.jsonl')]
assert len(cand)==600 and len(props)==111 and len(cross)==552 and len(second)==111 and len(root)==111
assert len(holds)==48 and all(not any(k in r for k in ('sourceText','currentTarget','recommendedTarget','targetText')) for r in holds)
for cell,(r,rh) in root.items():
 p,ph=props[cell]; x,xh=cross[cell]; s,sh=second[cell]
 assert r['rootDecision']=='accept-cross-recommendation' and r['finalTarget']==p['recommendedTarget']==s['chosenTarget']
 assert r['finalTargetSha256']==p['recommendedTargetSha256']==s['reviewedTargetSha256']
 assert r['crossReviewProposalRowSha256']==ph==s['proposalRowSha256']
 assert r['crossReviewLedgerRowSha256']==xh==s['crossReviewLedgerRowSha256']
 assert r['secondOpinionRowSha256']==sh and r['candidateFreeRowSha256']==s['candidateFreeRowSha256']
 assert r['sourceTextSha256']==p['sourceTextSha256']==s['sourceTextSha256']
 assert r['callerContextSha256']==p['callerContextSha256']==s['callerContextSha256']
 assert r['currentTargetSha256']==p['currentTargetSha256']==s['currentTargetSha256']
 assert r['exactHead']==p['exactHead']=='16c809b4787d70616a1a296ab0d90cf17923ba86'
 assert r['exactTree']==p['exactTree']=='dbd8343a42476f4e830428cc59efb7f4830251d5'
 assert s['secondOpinionDecision']=='accept' and not s['nativeSpeakerApproval'] and not r['nativeSpeakerApproval']
 assert s['chosenTarget']==s['reviewedTarget']
 assert all(v for k,v in s['tokenChecks'].items() if k!='numeric')
 if r['manualLexicalizedNumericException']:
  assert cell in {'ChmodFolderHelpText::ja','ChmodFolderHelpText::ko'}
  assert s['tokenChecks']['numeric'] is False
  assert any(e['name']=='numeric' for e in s['tokenCheckExceptions'])
 else:
  assert all(s['tokenChecks'].values())
summary=json.loads((HERE/'summary.json').read_text())
assert summary['selectedProposalCount']==111 and summary['changedCellCount']==111
assert summary['callerlessHashOnlyHolds']==48 and summary['selectedProposalDispositionCounts']=={'accept-cross-recommendation':111,'accept-adjusted-target':0,'hold-selected-proposal':0}
assert summary['nativeSpeakerApproval'] is False
print('PASS: 111 root dispositions bind candidate-free, cross proposal/ledger, and independent second-opinion hashes; 48 callerless holds remain text-free; octal exceptions are explicit.')
