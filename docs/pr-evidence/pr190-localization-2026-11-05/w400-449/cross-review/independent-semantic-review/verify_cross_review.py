#!/usr/bin/env python3
"""Portable verifier for ChaptarrNG PR #190 W400-W449 cross-review."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
TASK=HERE.parents[1]
HEAD='8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7'; TREE='018e46cd14424204a01be46e13e5b50f9f26ce07'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def canon(o): return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def need(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def sums(d):
    f=d/'SHA256SUMS.txt'; need(f.is_file(),'missing checksums '+str(d)); listed={}
    for line in f.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,n=line.split('  ',1); p=Path(n)
        need(not p.is_absolute() and '..' not in p.parts,'unsafe checksum path')
        need(n not in listed,'duplicate checksum entry '+n); need((d/p).is_file(),'missing file '+n)
        need(sha((d/p).read_bytes())==h,'checksum mismatch '+n); listed[n]=h
    actual={p.relative_to(d).as_posix() for p in d.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    need(set(listed)==actual,'checksum inventory mismatch '+str(d)); return listed
def input_sums(d):
    f=d/'SHA256SUMS.txt'; need(f.is_file(),'missing input checksum list '+str(d)); expected={}
    for line in f.read_text(encoding='utf-8').splitlines():
        if line.strip():
            h,n=line.split('  ',1); expected[n]=h
    actual={p.relative_to(d).as_posix():sha(p.read_bytes()) for p in d.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    need(expected==actual,'input checksum mismatch '+str(d)); return sha(f.read_bytes())
def tokens(c,t):
    s=c['sourceText']; return {
      'placeholderParity':collections.Counter(PH.findall(s))==collections.Counter(PH.findall(t)),
      'inlineCodeParity':INLINE.findall(s)==INLINE.findall(t),
      'markupParity':MARKUP.findall(s)==MARKUP.findall(t),
      'numericTokenParity':collections.Counter(NUM.findall(s))==collections.Counter(NUM.findall(t)),
      'protectedLiteralParity':all(x in t for x in c.get('protectedLiterals',[])),
    }
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidate-free-input',type=Path,default=TASK/'candidate-free/input'); ap.add_argument('--primary',type=Path,default=TASK/'primary-review'); ap.add_argument('--blind',type=Path,default=TASK/'blind-review'); ap.add_argument('--repo',type=Path); a=ap.parse_args()
    inp=a.candidate_free_input.resolve(); primary=a.primary.resolve(); blind=a.blind.resolve()
    packet_sums=sums(HERE); cfs=input_sums(inp); ps=input_sums(primary); bs=input_sums(blind)
    m=readj(HERE/'manifest.json'); s=readj(HERE/'summary.json'); pr=readj(HERE/'packet-provenance.json')
    for o,n in [(m,'manifest'),(s,'summary')]: need(o.get('exactHead')==HEAD and o.get('exactTree')==TREE,n+' pin')
    need(pr.get('headSha')==HEAD and pr.get('headTree')==TREE and pr.get('verification')=='PASS','provenance pin')
    need(pr['liveRefs']['branchSha']==HEAD and pr['liveRefs']['pullHeadSha']==HEAD,'branch/pull refs')
    need(m['inputSeals']==s['inputSeals'],'manifest seals')
    seal=s['inputSeals']
    need(seal['candidateFreeChecksumListSha256']==cfs and seal['primaryChecksumListSha256']==ps and seal['blindChecksumListSha256']==bs,'input checksum-list seals')
    need(seal['candidateFreeCellsSha256']==sha((inp/'candidate-free-cells.jsonl').read_bytes()),'candidate-free rows seal')
    need(seal['callerContextSha256']==sha((inp/'caller-context.jsonl').read_bytes()),'caller context seal')
    need(seal['primaryProposalFileSha256']==sha((primary/'primary-review-proposals.jsonl').read_bytes()),'primary proposal seal')
    need(seal['blindProposalFileSha256']==sha((blind/'proposals.jsonl').read_bytes()),'blind proposal seal')
    candidates=readjl(inp/'candidate-free-cells.jsonl'); contexts={r['sourceKey']:r for r in readjl(inp/'caller-context.jsonl')}
    rows=readjl(HERE/'cross-review-ledger.jsonl'); holds=readjl(HERE/'holds-hash-only.jsonl')
    need(len(candidates)==len(rows)==600,'cell coverage')
    first=readjl(HERE/'candidate-only-first-pass.jsonl')
    need(len(first)==600 and s['independentCandidateOnlyAssessment']['cells']==600,'candidate-only pass coverage')
    need(s['independentCandidateOnlyAssessment']['ledgerSha256']==sha((HERE/'candidate-only-first-pass.jsonl').read_bytes()),'candidate-only pass seal')
    first_counts=collections.Counter(x['decision'] for x in first)
    need(dict(first_counts)==s['independentCandidateOnlyAssessment']['decisionCounts'],'candidate-only pass decision counts')
    for c,f in zip(candidates,first):
        key=c['sourceKey']; loc=c['locale']; cid=f'{key}::{loc}'
        callerless=(c['literalCallCount']==0 and contexts[key]['literalCallCount']==0)
        need(f['exactHead']==HEAD and f['exactTree']==TREE,'candidate-only pass pin')
        need(f['candidateFreeRowSha256']==sha(canon(c)) and f['callerContextSha256']==c['callerContextSha256'],'candidate-only source/context binding')
        need(f['sourceTextSha256']==c['sourceTextSha256'] and f['currentTargetSha256']==c['currentTargetSha256'],'candidate-only source/current hashes')
        if callerless:
            need(f['decision']=='hold-hash-only' and f['cellIdSha256']==shat(cid) and f['sourceKeySha256']==shat(key),'candidate-only hash-only hold')
            need(not any(k in f for k in ('sourceKey','sourceOrdinal','sourceText','currentTarget','assessedTarget','cellId')),'candidate-only hold contains text/key')
        else:
            need(f.get('cellId')==cid and f.get('sourceKey')==key and f.get('sourceOrdinal')==c['sourceOrdinal'] and f.get('locale')==loc,'candidate-only cell identity')
            need(f.get('sourceText')==c['sourceText'] and f.get('currentTarget')==c['currentTarget'],'candidate-only text binding')
            t=f['assessedTarget']; need(f['assessedTargetSha256']==shat(t),'candidate-only target hash')
            need(all(tokens(c,t).values()),'candidate-only target tokens')
            if f['decision']=='accept-current': need(t==c['currentTarget'],'candidate-only acceptance')
            else: need(f['decision'] in ('correction','refinement') and t!=c['currentTarget'],'candidate-only recommendation')
    cell_map={}; held=[]
    for c,r in zip(candidates,rows):
        key=c['sourceKey']; loc=c['locale']; cid=f'{key}::{loc}'; ctx=contexts[key]
        callerless=(c['literalCallCount']==0 and ctx['literalCallCount']==0)
        need(loc in LOCALES,'locale '+loc); need(c['callerContextSha256']==ctx['callerContextSha256'],'candidate caller-context binding')
        need(r['exactHead']==HEAD and r['exactTree']==TREE,'cell head/tree')
        need(r['candidateFreeRowSha256']==sha(canon(c)),'candidate row hash')
        need(r['callerContextSha256']==c['callerContextSha256'],'caller-context hash')
        need(r['sourceTextSha256']==c['sourceTextSha256'] and r['currentTargetSha256']==c['currentTargetSha256'],'source/current hashes')
        need(r['sourceFileSha256']==c['sourceFileSha256'] and r['targetFileSha256']==c['targetFileSha256'],'catalog file hashes')
        if callerless:
            held.append(r)
            need(r['decision']=='hold-hash-only' and r['reasonCode']=='zero-literal-caller-hash-only','hold classification')
            need(r['sourceKeyOmitted'] and r['sourceOrdinalOmitted'] and r['sourceAndTargetTextOmitted'],'hold omission flags')
            need(not any(k in r for k in ('sourceKey','sourceOrdinal','sourceText','currentTarget','reviewedTarget','recommendedTarget','cellId')),'hold has no key/text')
            need(r['cellIdSha256']==shat(cid) and r['sourceKeySha256']==shat(key),'hold identity hashes')
            need(c['literalCallCount']==ctx['literalCallCount']==r['literalCallCount']==0,'callerless hold')
            continue
        need(r['cellId']==cid and r['cellIdSha256']==shat(cid),'cell identity')
        need(r['sourceKey']==key and r['sourceOrdinal']==c['sourceOrdinal'] and r['locale']==loc,'cell identity fields')
        need(r['sourceText']==c['sourceText'] and r['currentTarget']==c['currentTarget'],'input text binding')
        t=r['reviewedTarget']; need(isinstance(t,str) and r['reviewedTargetSha256']==shat(t),'reviewed target hash')
        tc=tokens(c,t); need(all(tc.values()) and all(r['tokenChecks'][k]==v for k,v in tc.items()),'token parity')
        if r['decision']=='accept-current': need(t==c['currentTarget'] and r['changeKind'] is None,'accept-current target')
        else: need(r['decision']=='recommend-revision' and t!=c['currentTarget'],'revision target')
        cell_map[cid]=r
    need(len(held)==len(holds)==12,'hash-only hold count')
    need(holds==held,'hold ledger parity'); need({x['locale'] for x in held}==set(LOCALES),'hold locale coverage')
    noncand=[(c['sourceOrdinal'],c['sourceKey'],c['locale']) for c in candidates if not (c['literalCallCount']==0 and contexts[c['sourceKey']]['literalCallCount']==0)]
    nonrows=[(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in rows if r['decision']!='hold-hash-only']
    need(noncand==nonrows,'cell source/locale order')
    pprops=readjl(primary/'primary-review-proposals.jsonl'); bprops=readjl(blind/'proposals.jsonl'); recs=readjl(HERE/'proposal-reconciliation.jsonl')
    need(len(pprops)==75 and len(bprops)==76 and len(recs)==151,'proposal counts')
    expected={('primary',sha(canon(x))):x for x in pprops}; expected.update({('blind',sha(canon(x))):x for x in bprops})
    need(len(expected)==151,'unique source proposal records'); seen=set()
    by_candidate={f"{c['sourceKey']}::{c['locale']}":c for c in candidates}
    for r in recs:
        side=r['proposalSide']; ident=(side,r['proposalRecordSha256']); need(ident in expected and ident not in seen,'proposal identity'); seen.add(ident); p=expected[ident]
        cid=p['cellId'] if side=='primary' else f"{p['sourceKey']}::{p['locale']}"; c=by_candidate[cid]; final=cell_map[cid]['reviewedTarget']
        pt=p['recommendedTarget'] if side=='primary' else p['proposedTarget']; ph=p['recommendedTargetSha256'] if side=='primary' else p['proposalSha256']
        need(r['exactHead']==HEAD and r['exactTree']==TREE,'proposal pin')
        need(r['proposalTarget']==pt and r['proposalTargetSha256']==shat(pt) and r['proposalTargetSourceSha256']==ph,'proposal target binding')
        need(r['proposalRationale']==(p['decisionRationale'] if side=='primary' else p['rationale']),'proposal rationale binding')
        need(r['crossReviewTarget']==final and r['crossReviewTargetSha256']==shat(final),'review target binding')
        need(r['crossReviewOutcome']==('endorsed-exact' if pt==final else 'endorsed-with-adjustment'),'proposal outcome')
        need(r['candidateFreeRowSha256']==sha(canon(c)) and r['callerContextSha256']==c['callerContextSha256'],'proposal source/context')
        need(r['cellId']==cid and r['cellIdSha256']==shat(cid),'proposal cell binding')
        expected_tokens=tokens(c,final)
        need(all(expected_tokens.values()) and all(r['tokenChecks'].get(k)==v for k,v in expected_tokens.items()),'proposal tokens')
    need(seen==set(expected),'all proposals reconciled')
    cd=collections.Counter(x['decision'] for x in rows); od=collections.Counter(x['crossReviewOutcome'] for x in recs)
    need(cd['accept-current']==s['acceptCurrent'] and cd['recommend-revision']==s['recommendedRevisions'] and cd['hold-hash-only']==s['hashOnlyHolds'],'summary cell counts')
    need(sum(cd.values())==600,'summary cell total')
    first_changes=first_counts['correction']+first_counts['refinement']
    need(s['additionalRecommendationsAfterProposalReview']==cd['recommend-revision']-first_changes,'post-proposal recommendation delta')
    need(od['endorsed-exact']==s['proposalOutcomes']['endorsedExact'] and od['endorsed-with-adjustment']==s['proposalOutcomes']['endorsedWithAdjustment'],'summary proposal outcomes')
    if a.repo:
        repo=a.repo.resolve(); need(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==HEAD,'repo head')
        need(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD^{tree}'],text=True).strip()==TREE,'repo tree')
        need(not subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).strip(),'repo clean')
    print(json.dumps({'result':'PASS','exactHead':HEAD,'exactTree':TREE,'cells':600,'acceptCurrent':cd['accept-current'],'recommendedRevisions':cd['recommend-revision'],'hashOnlyHolds':cd['hold-hash-only'],'proposalRecords':151,'primaryProposalRecords':75,'blindProposalRecords':76,'proposalOutcomes':dict(od),'packetFilesVerified':len(packet_sums)},ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
