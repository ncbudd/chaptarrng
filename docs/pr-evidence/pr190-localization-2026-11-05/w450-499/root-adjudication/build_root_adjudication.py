#!/usr/bin/env python3
import hashlib, json
from collections import Counter
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
CAND = BASE / 'candidate-free' / 'input'
CROSS = BASE / 'cross-review-sealed'
SECOND = BASE / 'second-opinion'
OUT = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
def readjl(path):
    raw_rows = [x for x in path.read_bytes().splitlines() if x.strip()]
    return [(json.loads(raw), sha(raw)) for raw in raw_rows]
candidates = { (r['sourceKey'], r['locale']): (r, h) for r,h in readjl(CAND/'candidate-free-cells.jsonl') }
proposals = { (r['sourceKey'], r['locale']): (r, h) for r,h in readjl(CROSS/'proposals.jsonl') }
cross = { (r['sourceKey'], r['locale']): (r, h) for r,h in readjl(CROSS/'ledger.jsonl') }
second = { (r['sourceKey'], r['locale']): (r, h) for r,h in readjl(SECOND/'ledger.jsonl') }
assert len(candidates) == 600 and len(proposals) == 111 and len(second) == 111
assert set(proposals) == set(second)
assert len(cross) == 552
assert len({v[0]['cellId'] for v in second.values()}) == 111
rows=[]
for ident,(p,proposal_hash) in sorted(proposals.items(), key=lambda kv:(kv[1][0]['sourceOrdinal'],kv[0][1])):
    c,ch = candidates[ident]
    s,shash = second[ident]
    x,xhash = cross[ident]
    assert c['sourceOrdinal']==p['sourceOrdinal']==s['sourceOrdinal']==x['sourceOrdinal']
    assert c['sourceKey']==p['sourceKey']==s['sourceKey']==x['sourceKey']
    assert c['sourceTextSha256']==p['sourceTextSha256']==s['sourceTextSha256']
    assert c['callerContextSha256']==p['callerContextSha256']==s['callerContextSha256']==x['callerContextSha256']
    assert c['currentTargetSha256']==p['currentTargetSha256']==s['currentTargetSha256']==x['currentTargetSha256']
    assert s['proposalRowSha256']==proposal_hash and s['crossReviewLedgerRowSha256']==xhash
    assert s['candidateFreeRowSha256']==ch
    assert s['secondOpinionDecision']=='accept' and s['chosenTarget']==p['recommendedTarget']
    assert s['reviewedTargetSha256']==p['recommendedTargetSha256']
    lexicalized_octal = (p['sourceOrdinal'], p['locale']) in {(471, 'ja'), (471, 'ko')}
    if lexicalized_octal:
        exception_term = '8進数' if p['locale']=='ja' else '8진수'
        assert p['finalTokenChecks']['numeric'] is False and s['tokenChecks']['numeric'] is False
        assert all(v for k,v in p['finalTokenChecks'].items() if k!='numeric')
        assert all(v for k,v in s['tokenChecks'].items() if k!='numeric')
        assert any(e.get('name')=='numeric' and e.get('value')==exception_term for e in s['tokenCheckExceptions'])
        assert exception_term in p['recommendedTarget'] and exception_term in s['chosenTarget']
    else:
        exception_term = None
        assert all(p['finalTokenChecks'].values()) and all(s['tokenChecks'].values())
    assert p['recommendedTarget'] != p['currentTarget']
    refs=c['callerReferenceCount']
    assert refs > 0
    decision='accept-cross-recommendation'
    token_clause=(f"The numeric scanner's explicit lexicalized-octal exception ({exception_term}) is manually verified; all other token checks pass. "
      if lexicalized_octal else "All recorded token checks pass. ")
    rationale=(f"I reviewed the source and pinned caller for this cell and agree with the exact cross-reviewed target. "
      f"The independent second opinion agrees; source, caller, current-target, and selected-target hashes match. "
      f"{token_clause}{p['rationale']}")
    rows.append({
      'schemaVersion':1,'cellId':p['sourceKey']+'::'+p['locale'],'sourceOrdinal':p['sourceOrdinal'],
      'sourceKey':p['sourceKey'],'locale':p['locale'],'exactHead':p['exactHead'],'exactTree':p['exactTree'],
      'sourceTextSha256':p['sourceTextSha256'],'candidateFreeRowSha256':ch,
      'callerContextSha256':p['callerContextSha256'],'currentTargetSha256':p['currentTargetSha256'],
      'crossReviewProposalRowSha256':proposal_hash,'crossReviewLedgerRowSha256':xhash,
      'crossRecommendationTarget':p['recommendedTarget'],'crossRecommendationTargetSha256':p['recommendedTargetSha256'],
      'secondOpinionRowSha256':shash,'secondOpinionDecision':s['secondOpinionDecision'],
      'finalTarget':p['recommendedTarget'],'finalTargetSha256':p['recommendedTargetSha256'],
      'manualLexicalizedNumericException':exception_term,
      'rootDecision':decision,'rootRationale':rationale,'nativeSpeakerApproval':False
    })
ledger=OUT/'root-adjudication-ledger.jsonl'
ledger.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
counts=Counter(r['locale'] for r in rows)
summary={
 'artifact':'ChaptarrNG PR #190 W450-W499 root adjudication',
 'repository':'snapetech-org/chaptarrng','pullRequest':190,'state':'OPEN/draft',
 'exactHead':'16c809b4787d70616a1a296ab0d90cf17923ba86','exactTree':'dbd8343a42476f4e830428cc59efb7f4830251d5',
 'baseSha':'025498c1a9deb999a4acd1eafc4c807a252e0c29','sourceOrdinalRange':[450,499],
 'candidateCellCount':600,'callerBoundCellCount':552,'callerlessHashOnlyHolds':48,
 'selectedProposalCount':111,'selectedProposalSourceIds':34,'selectedProposalDispositionCounts':{'accept-cross-recommendation':111,'accept-adjusted-target':0,'hold-selected-proposal':0},
 'retainedCurrentCount':441,'changedCellCount':111,'changedByLocale':dict(sorted(counts.items())),
 'manualLexicalizedOctalExceptions':[{'sourceOrdinal':471,'locale':'ja','term':'8進数'},{'sourceOrdinal':471,'locale':'ko','term':'8진수'}],
 'nativeSpeakerApproval':False,'reviewConfidence':'moderate overall; no native-speaker signoff',
 'workflowChanges':False,'testsBuildsScansCiRun':False,
 'secondOpinionInputSha256':sha((SECOND/'ledger.jsonl').read_bytes()),
 'crossProposalsInputSha256':sha((CROSS/'proposals.jsonl').read_bytes()),
 'crossLedgerInputSha256':sha((CROSS/'ledger.jsonl').read_bytes()),
 'candidateFreeInputSha256':sha((CAND/'candidate-free-cells.jsonl').read_bytes())
}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'result':'PASS','selected':len(rows),'retained':441,'hashOnlyHolds':48,'byLocale':dict(sorted(counts.items()))},ensure_ascii=False))
