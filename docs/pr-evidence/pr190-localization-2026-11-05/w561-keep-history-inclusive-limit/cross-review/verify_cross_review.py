#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, subprocess, sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
P=OUT.parent/'primary-review'
B=OUT.parent/'blind-review'
REPO=Path(__file__).resolve().parents[5]
HEAD='c01c3974a01dfcab6a1aa09401c66d412bc88e60'; TREE='55ea7696f4981fc56a774f38be477f89e454a7a3'
EXPECTED=['es','zh-CN','hi','de','ja','fr','pt-BR','ar','ko','zh-TW','vi','id']
BLIND_LOCALE={'zh-CN':'zh_CN','zh-TW':'zh_TW','pt-BR':'pt_BR'}
CURRENT_ID='server.message.m453c42aa8de5'; PROPOSED_ID='server.message.m3a79390fb21e'
CURRENT_EN='NzbGet setting KeepHistory should be less than 25000'; PROPOSED_EN='NzbGet setting KeepHistory must not exceed 25000'
FINAL_CHOICES={'es':'primary','zh-CN':'both-agree','hi':'both-agree','de':'blind','ja':'blind','fr':'blind','pt-BR':'primary','ar':'primary','ko':'both-agree','zh-TW':'both-agree','vi':'primary','id':'both-agree'}
TEXT_KEYS={'currentTarget','primaryTarget','blindTarget','finalTarget','currentEnglishSource','proposedEnglishSource','rationale','primaryRationale','blindRationale','crossRationale','currentEnglish','proposedEnglish'}
def fail(s): raise SystemExit('FAIL: '+s)
def sha(b): return hashlib.sha256(b).hexdigest()
def textsha(s): return sha(s.encode('utf-8'))
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def check_dir(p):
    listed={}
    for line in (p/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        h,n=line.split('  ',1)
        if n in listed or not (p/n).is_file() or sha((p/n).read_bytes())!=h: fail(f'input checksum {p}/{n}')
        listed[n]=h
    actual={x.relative_to(p).as_posix() for x in p.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt'}
    if actual!=set(listed): fail(f'input checksum coverage {p}')
    return listed
def main():
    ps=check_dir(P); bs=check_dir(B); pins=j(OUT/'input-pins.json')
    if (pins.get('head'),pins.get('tree'),pins.get('currentSourceId'),pins.get('proposedSourceId'))!=(HEAD,TREE,CURRENT_ID,PROPOSED_ID): fail('exact product/source pin')
    for role,root,sums,manifest_name in [('primary',P,ps,'primary-manifest.json'),('blind',B,bs,'blind-manifest.json')]:
        expected_sum=(OUT/f'input-{role}-SHA256SUMS.txt').read_bytes()
        expected_manifest=(OUT/manifest_name).read_bytes()
        if expected_sum!=(root/'SHA256SUMS.txt').read_bytes() or expected_manifest!=(root/'manifest.json').read_bytes(): fail(f'{role} input copy')
        if sha(expected_sum)!=pins[f'{role}ChecksumListSha256'] or sha(expected_manifest)!=pins[f'{role}ManifestSha256']: fail(f'{role} input pin')
    pm=j(P/'manifest.json'); bm=j(B/'manifest.json'); sr=j(OUT/'source-review.json'); sc=j(OUT/'source-caller-evidence.json')
    if (pm.get('head'),pm.get('tree'),bm.get('head'),bm.get('tree'))!=(HEAD,TREE,HEAD,TREE): fail('input head/tree')
    if pm.get('sourceId')!=PROPOSED_ID or bm.get('currentSourceId')!=CURRENT_ID or bm.get('proposedSourceId')!=PROPOSED_ID: fail('source ID transition')
    expectedCurrentHash='453c42aa8de536feb62fa62896136529ab6d16edf996511f0fb44b037ba2dc1f'
    expectedProposedHash='3a79390fb21e5a7e7e4ea479d3d5f2643862a645f76312b3f107817fde29c5b4'
    if textsha(CURRENT_EN)!=expectedCurrentHash or textsha(PROPOSED_EN)!=expectedProposedHash: fail('English text SHA')
    if CURRENT_ID!='server.message.m'+expectedCurrentHash[:12] or PROPOSED_ID!='server.message.m'+expectedProposedHash[:12]: fail('English ID/hash relation')
    source=sr.get('sourceKey',{})
    if (source.get('currentId'),source.get('currentText'),source.get('currentTextSha256'),source.get('proposedId'),source.get('proposedText'),source.get('proposedTextSha256'))!=(CURRENT_ID,CURRENT_EN,expectedCurrentHash,PROPOSED_ID,PROPOSED_EN,expectedProposedHash): fail('primary source decision')
    caller=sr.get('callerEvidence',{}); bc=sc.get('caller',{})
    if (caller.get('file'),caller.get('fileSha256'),caller.get('gitBlob'),caller.get('conditionLine'),caller.get('conditionText'),caller.get('messageLine'))!=('src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs','637b63deba408a62402ee9532b72202fa81034d0374de6d331cc24b9ab3cf32c','a3a899a8b318a9739e03c7b34eea630b8ef418d1',348,'            else if (value > 25000)',350): fail('primary caller predicate pin')
    if (bc.get('path'),bc.get('fileSha256'),bc.get('gitBlob'),bc.get('predicateLine'),bc.get('branchPredicate'),bc.get('validationKeyLine'))!=('src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs',caller.get('fileSha256'),caller.get('gitBlob'),348,'value > 25000',350): fail('blind caller predicate pin')
    if not caller.get('value25000Accepted') or not caller.get('valuesAbove25000Rejected') or not bc.get('behavior','').find('exactly 25000 does not enter this error branch')>=0: fail('inclusive predicate conclusion')
    if subprocess.check_output(['git','-C',str(REPO),'rev-parse',f'{HEAD}^{{tree}}'],text=True).strip()!=TREE: fail('pinned review commit/tree unavailable')
    path=caller['file']; content=subprocess.check_output(['git','-C',str(REPO),'show',f'{HEAD}:{path}'])
    # Match Git's object ID; the content is also pinned with SHA-256.
    blob=subprocess.check_output(['git','-C',str(REPO),'hash-object','--stdin'],input=content).decode().strip()
    lines=content.decode('utf-8').splitlines()
    if sha(content)!=caller['fileSha256'] or blob!=caller['gitBlob'] or lines[347].strip()!='else if (value > 25000)' or CURRENT_EN not in lines[349] or CURRENT_ID not in lines[349]: fail('live source/caller content')
    pl={r['locale']:r for r in jl(OUT/'primary-locale-translations.jsonl')}; bl={r['locale']:r for r in jl(OUT/'blind-locale-review.jsonl')}; led=jl(OUT/'cross-review-ledger.jsonl')
    if set(pl)!=set(EXPECTED) or set(bl)!=set(BLIND_LOCALE.get(x,x) for x in EXPECTED) or len(led)!=12: fail('locale coverage')
    by={r['locale']:r for r in led}
    if set(by)!=set(EXPECTED): fail('cross ledger locales')
    choices=collections.Counter(); matches=0
    for loc in EXPECTED:
        p=pl[loc]; b=bl[BLIND_LOCALE.get(loc,loc)]; r=by[loc]
        if r.get('head')!=HEAD or r.get('tree')!=TREE or r.get('window')!='W561' or r.get('blindLocale')!=b['locale']: fail('row pin/locale '+loc)
        if p.get('currentSourceId')!=CURRENT_ID or b.get('currentSourceId')!=CURRENT_ID or p.get('proposedSourceId')!=PROPOSED_ID or b.get('proposedSourceId')!=PROPOSED_ID: fail('row source ID '+loc)
        if p.get('currentEnglishSource')!=CURRENT_EN or p.get('proposedEnglishSource')!=PROPOSED_EN or b.get('englishAnchor')!=PROPOSED_EN: fail('row English anchor '+loc)
        if (p.get('oldTarget'),p.get('oldTargetSha256'))!=(b.get('currentTarget'),b.get('currentTargetSha256')): fail('current target disagreement '+loc)
        if p.get('proposedTargetSha256')!=textsha(p.get('proposedTarget','')) or b.get('proposedTargetSha256')!=textsha(b.get('proposedTarget','')): fail('input target hash '+loc)
        if r.get('currentTarget')!=p.get('oldTarget') or r.get('currentTargetSha256')!=p.get('oldTargetSha256'): fail('cross current target binding '+loc)
        if r.get('primaryTarget')!=p.get('proposedTarget') or r.get('blindTarget')!=b.get('proposedTarget') or r.get('primaryTargetSha256')!=p.get('proposedTargetSha256') or r.get('blindTargetSha256')!=b.get('proposedTargetSha256'): fail('cross proposal join '+loc)
        if r.get('catalogPath')!=p.get('catalogLocaleFile') or r.get('catalogFileSha256')!=p.get('catalogFileSha256') or r.get('catalogGitBlob')!=p.get('catalogGitBlob'): fail('catalog pin '+loc)
        req=('NzbGet','KeepHistory','25000')
        if not all(x in p['proposedTarget'] and x in b['proposedTarget'] and x in r['finalTarget'] for x in req): fail('literal preservation '+loc)
        if not all(p.get('literalPreservation',{}).get(x) is True for x in req): fail('primary literal attestation '+loc)
        if not all(b.get('proposedTokensPreserved',{}).get(x+'Preserved') is True for x in req): fail('blind literal attestation '+loc)
        if r.get('finalTargetSha256')!=textsha(r.get('finalTarget','')) or r.get('finalTarget')==r.get('currentTarget'): fail('final correction/hash '+loc)
        choice=FINAL_CHOICES[loc]; choices[choice]+=1
        if r.get('crossChoice')!=choice or r.get('finalDecision')!='correction': fail('cross choice '+loc)
        if choice=='primary' and r['finalTarget']!=r['primaryTarget']: fail('primary selected target '+loc)
        if choice=='blind' and r['finalTarget']!=r['blindTarget']: fail('blind selected target '+loc)
        if choice=='both-agree' and (r['primaryTarget']!=r['blindTarget'] or r['finalTarget']!=r['primaryTarget']): fail('agreement selection '+loc)
        if r.get('proposalAgreement')!=(r['primaryTarget']==r['blindTarget']): fail('agreement marker '+loc)
        if not r.get('crossRationale') or r.get('confidence')!='moderate' or r.get('nativeSpeakerApproval') is not False: fail('rationale/confidence '+loc)
        matches += int(r['proposalAgreement'])
    if choices!={'both-agree':5,'primary':4,'blind':3} or matches!=5: fail('decision comparison counts')
    sm=j(OUT/'summary.json')
    if sm.get('cellCount')!=12 or sm.get('finalActions')!={'correction':12,'retain':0,'hold':0} or sm.get('finalChoices')!=dict(choices) or sm.get('identicalPrimaryBlindTargets')!=5 or sm.get('differentPrimaryBlindTargets')!=7: fail('summary totals')
    # Execute source packets' own semantic/token verifiers after verifying their full checksum manifests.
    subprocess.run([sys.executable,str(P/'verify_primary_review.py')],check=True,stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable,str(B/'verify_packet.py')],check=True,stdout=subprocess.DEVNULL)
    listed={}
    for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1)
        if n in listed or not (OUT/n).is_file() or sha((OUT/n).read_bytes())!=h: fail('output checksum '+n)
        listed[n]=h
    actual={x.relative_to(OUT).as_posix() for x in OUT.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt'}
    if actual!=set(listed): fail('output checksum coverage')
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'window':'W561','cells':12,'englishDecision':'accept inclusive “must not exceed 25000”','currentSourceId':CURRENT_ID,'prospectiveNewSourceId':PROPOSED_ID,'callerPredicate':'value > 25000','primaryBlindIdentical':matches,'primaryBlindDifferent':12-matches,'finalChoices':dict(choices),'corrections':12,'requiredLiteralsPreserved':True,'nativeSpeakerApproval':False,'inputVerifiers':'PASS','portablePinnedGitObject':True,'checksumEntries':len(listed)},ensure_ascii=False,sort_keys=True,indent=2))
if __name__=='__main__': main()
