#!/usr/bin/env python3
"""Verify the second-opinion ledger against the sealed ChaptarrNG review packet."""
from __future__ import annotations
import hashlib, json
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
INPUT=ROOT/'candidate-free'/'input'
CROSS=ROOT/'cross-review-sealed'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'
EXCEPTIONS={(471,'ja'):'8進数',(471,'ko'):'8진수'}

def sha(x):
    if isinstance(x,str): x=x.encode('utf-8')
    return hashlib.sha256(x).hexdigest()
def readjl(path):
    rows=[]; hashes=[]
    for line in path.read_bytes().splitlines(keepends=True):
        if line.strip():
            rows.append(json.loads(line)); hashes.append(sha(line[:-1] if line.endswith(b'\n') else line))
    return rows,hashes
def fail(msg): raise SystemExit('FAIL: '+msg)

candidates, candidate_hashes=readjl(INPUT/'candidate-free-cells.jsonl')
callers,_=readjl(INPUT/'caller-context.jsonl')
proposals, proposal_hashes=readjl(CROSS/'proposals.jsonl')
cross,cross_hashes=readjl(CROSS/'ledger.jsonl')
ledger, ledger_hashes=readjl(OUT/'ledger.jsonl')
summary=json.loads((OUT/'summary.json').read_text())
candidate_map={(x['sourceKey'],x['locale']):(x,h) for x,h in zip(candidates,candidate_hashes)}
caller_map={x['sourceKey']:x for x in callers}
proposal_map={(x['sourceKey'],x['locale']):(x,h) for x,h in zip(proposals,proposal_hashes)}
cross_map={(x['sourceKey'],x['locale']):(x,h) for x,h in zip(cross,cross_hashes)}
ledger_map={x['cellId']:x for x in ledger}
if len(ledger)!=111 or len(ledger_map)!=111: fail('expected 111 unique ledger rows')
if set(ledger_map)!={f'{key}::{locale}' for key,locale in proposal_map}: fail('ledger/proposal coverage mismatch')
if summary['exactHead']!=HEAD or summary['exactTree']!=TREE or summary['baseSha']!=BASE: fail('summary refs')
if summary['selectedProposalCellsReviewed']!=111 or summary['sourceIdsReviewed']!=34: fail('summary dimensions')
if summary['decisionCounts']!={'accept':111} or summary['adjustments']!=0 or summary['holdsAmongSelectedProposals']!=0: fail('summary disposition counts')
if summary['callerlessHashOnlyHoldsPreserved']!=48 or summary['callerlessHoldTargetTextIncluded'] is not False: fail('hold boundary')

for row in ledger:
    key=(row['sourceKey'],row['locale']); cell,cfhash=candidate_map[key]; proposal,phash=proposal_map[key]; crossrow,xhash=cross_map[key]; caller=caller_map[key[0]]
    if row['exactHead']!=HEAD or row['exactTree']!=TREE or row['baseSha']!=BASE: fail('row refs '+str(key))
    if row['candidateFreeRowSha256']!=cfhash or proposal['candidateFreeRowSha256']!=cfhash: fail('candidate-free row hash '+str(key))
    if row['candidateFreeSourceKeySha256']!=sha(cell['sourceKey']) or proposal['sourceKeySha256']!=sha(cell['sourceKey']): fail('source-key hash '+str(key))
    if row['candidateFreeLocaleSha256']!=sha(cell['locale']): fail('locale hash '+str(key))
    if row['candidateFreeCellIdSha256']!=sha(cell['sourceKey']+'::'+cell['locale']): fail('cell identity hash '+str(key))
    if row['candidateFreeSourceTextSha256']!=cell['sourceTextSha256'] or row['sourceTextSha256']!=cell['sourceTextSha256']: fail('source text hash '+str(key))
    if row['candidateFreeCurrentTargetSha256']!=cell['currentTargetSha256'] or row['currentTargetSha256']!=cell['currentTargetSha256']: fail('current target hash '+str(key))
    if row['callerContextSha256']!=cell['callerContextSha256'] or row['callerContextSha256']!=caller['callerContextSha256']: fail('caller context hash '+str(key))
    if row['proposalRowSha256']!=phash or row['crossReviewLedgerRowSha256']!=xhash: fail('proposal/cross ledger raw row hash '+str(key))
    if row['candidateFreeRowSha256']!=proposal['candidateFreeRowSha256']: fail('proposal input binding '+str(key))
    if row['sourceKeySha256']!=proposal['sourceKeySha256'] or row['reviewedTargetSha256']!=proposal['recommendedTargetSha256']: fail('proposal source/target hash '+str(key))
    if row['currentTarget']!=cell['currentTarget'] or row['sourceText']!=cell['sourceText']: fail('source/current readback '+str(key))
    if row['currentTarget']!=proposal['currentTarget'] or row['currentTargetSha256']!=proposal['currentTargetSha256']: fail('proposal current value '+str(key))
    chosen=row['chosenTarget']
    if chosen!=row['reviewedTarget'] or chosen!=proposal['recommendedTarget'] or chosen!=crossrow['recommendedTarget']: fail('chosen target mismatch '+str(key))
    if sha(chosen)!=row['reviewedTargetSha256'] or sha(chosen)!=proposal['recommendedTargetSha256'] or sha(chosen)!=crossrow['recommendedTargetSha256']: fail('chosen target hash '+str(key))
    if row['secondOpinionDecision']!='accept' or not row['secondOpinionRationale']: fail('missing decision/rationale '+str(key))
    if row['nativeSpeakerApproval'] is not False or row['reviewConfidence']!='moderate': fail('review status '+str(key))
    if not caller['callerRefs']: fail('selected row has no caller '+str(key))
    expected_refs=[{'path':x['path'],'line':x['line'],'lineText':x['lineText']} for x in caller['callerRefs']]
    if row['callerRefs']!=expected_refs: fail('caller references '+str(key))
    exception=EXCEPTIONS.get((row['sourceOrdinal'],row['locale']))
    failed={name for name,ok in row['tokenChecks'].items() if not ok}
    expected_fail={'numeric'} if exception else set()
    if failed!=expected_fail: fail('token checks '+str(key))
    expected_exceptions=([{'name':'numeric','value':exception,'reason':'standard lexicalized octal term; numeral is not a separate source value'}] if exception else [])
    if row['tokenCheckExceptions']!=expected_exceptions: fail('token exception rationale '+str(key))
    if exception and exception not in chosen: fail('octal lexicalization '+str(key))
    if row['crossDecision']!=proposal['crossDecision'] or row['crossDecision']!=crossrow['crossDecision']: fail('cross decision pin '+str(key))
    if not all(row['tokenChecks'][name] for name in ('placeholders','markup','inlineCode','protectedLiterals')): fail('protected token check '+str(key))

if summary['inputSha256']!={
    str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in [INPUT/'candidate-free-cells.jsonl',INPUT/'caller-context.jsonl',CROSS/'proposals.jsonl',CROSS/'ledger.jsonl']
}: fail('input manifest hash')
if sum(1 for x in ledger if x['secondOpinionDecision']=='accept')!=111: fail('accepted-row count')
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'base':BASE,'proposalCells':111,'sourceIds':34,'accepted':111,'adjusted':0,'held':0,'callerlessHoldsRevealed':0,'numericLexicalExceptions':len(EXCEPTIONS),'rawInputRowHashesBound':True},indent=2))
