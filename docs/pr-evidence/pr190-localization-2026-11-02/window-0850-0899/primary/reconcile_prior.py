from __future__ import annotations
import hashlib,json,pathlib,subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch')
P800=ROOT/'chaptarrng-pr190-window-0800-0849-primary-20261102'
X800=ROOT/'chaptarrng-pr190-window-0800-0849-crossreview-20261102'
A800=ROOT/'chaptarrng-pr190-window-0800-0849-apply-20261102'
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def git(*args, text=True): return subprocess.check_output(['git','-C',str(WORK),*args],text=text)
def show(path): return git('show',f'{HEAD}:{path}',text=False)
def verify_sum(folder, name='SHA256SUMS'):
 p=folder/name; assert p.exists(),p
 checked=[]
 for line in p.read_text().splitlines():
  h,rel=line.split('  ',1); f=folder/rel; assert f.exists() and sha(f.read_bytes())==h,(f,h)
  checked.append(rel)
 return {'path':name,'sha256':sha(p.read_bytes()),'checkedFiles':len(checked),'files':checked}
def readjl(p): return [json.loads(x) for x in p.read_text().splitlines()]
# Verify prior primary/cross-review evidence and the applied W800-W849 values.
p800_sums=verify_sum(P800)
x800_sums=verify_sum(X800)
p800_m=json.loads((P800/'manifest.json').read_text())
p800_b=json.loads((P800/'prior-disposition-boundary.json').read_text())
assert p800_m['head']=='f0eb9d38b1989bd6e3addeb698ec8c5f9c29d9e9'
assert p800_m['positions']==[800,849] and p800_m['priorOverlapCount']==0
assert p800_b['priorDispositionsCoverEveryPosition0Through799'] and p800_b['exactPriorDispositionOverlapCount']==0
old_prior=readjl(P800/'prior-disposition-hashes.jsonl')
assert len(old_prior)==9600 and len({(x['sourceOrdinal'],x['sourceId'],x['locale']) for x in old_prior})==9600
assert {x['sourceOrdinal'] for x in old_prior}==set(range(800))
primary800=readjl(P800/'primary-review-ledger.jsonl')
cross800=readjl(X800/'crossreview-ledger.jsonl')
apply800=readjl(A800/'apply-readback.jsonl')
assert len(primary800)==len(cross800)==len(apply800)==600
assert len({(x['sourceOrdinal'],x['sourceId'],x['locale']) for x in primary800})==600
assert len({(x['sourceOrdinal'],x['sourceId'],x['locale']) for x in cross800})==600
assert len({(x['sourceOrdinal'],x['sourceId'],x['locale']) for x in apply800})==600
queue=json.loads(show('docs/localization/source-followup-20261101.json'))['currentMissingIds']
assert len(queue)==1210 and len(set(queue))==1210
source=json.loads(show('src/NzbDrone.Core/Localization/Core/en.json'))
ids_by_ordinal={i:sid for i,sid in enumerate(queue)}
# Exact current locale values at 175cff3 must equal the independently reviewed W800 final targets and apply readback.
locale_objs={loc:json.loads(show(f'src/NzbDrone.Core/Localization/Core/{file}')) for loc,file in LOCALES.items()}
apply_map={(x['sourceOrdinal'],x['locale']):x for x in apply800}
cross_map={(x['sourceOrdinal'],x['locale']):x for x in cross800}
primary_map={(x['sourceOrdinal'],x['locale']):x for x in primary800}
reattested=[]
for c in cross800:
 o=c['sourceOrdinal']; sid=c['sourceId']; loc=c['locale']; target=locale_objs[loc][sid]
 assert 800<=o<=849 and queue[o]==sid and source[sid]==c['source']
 assert target==c['finalTarget'] and sha(target)==c['finalTargetSha256']
 a=apply_map[(o,loc)]; p=primary_map[(o,loc)]
 assert a['sourceId']==sid and a['after']==target and a['afterSha256']==sha(target)
 assert p['source']==source[sid]
 reattested.append({'sourceOrdinal':o,'sourceId':sid,'locale':loc,'sourceTextSha256':sha(source[sid]),'appliedTargetSha256':sha(target),'primaryDisposition':p['disposition'],'crossReviewDisposition':c['crossReviewDisposition'],'finalTargetSha256':c['finalTargetSha256'],'applyReadbackMatches':True,'liveCatalogMatches':True})
assert len(reattested)==600
# Reattest the W849 boundary's actual caller file/hash/context at the current exact tree.
current_boundary=[]
for old in readjl(X800/'crossreview-ledger.jsonl'):
 if old['sourceOrdinal']!=849: continue
 refs=[]
 for ref in old.get('callerRefs',[]):
  raw=show(ref['file']); lines=raw.decode().splitlines(); i=ref['line']-1
  assert sha(raw)==ref['fileSha256'] and git('rev-parse',f'{HEAD}:{ref["file"]}').strip()==ref['fileBlob']
  assert 0<=i<len(lines) and lines[i].strip()==ref['lineText'] and sha(lines[i].strip())==ref['lineSha256']
  before=[v.strip() for v in lines[max(0,i-3):i]]; after=[v.strip() for v in lines[i+1:i+1+len(ref.get('contextAfter',[]))]]
  assert before==ref['contextBefore'] and after==ref['contextAfter']
  refs.append({**ref,'currentTreeReattested':True})
 assert old['sourceId']==queue[849] and old['source']==source[old['sourceId']]
 loc=old['locale']; live=locale_objs[loc][old['sourceId']]
 assert live==old['finalTarget'] and sha(live)==old['finalTargetSha256']
 current_boundary.append({'sourceOrdinal':849,'sourceId':old['sourceId'],'locale':loc,'source':source[old['sourceId']],'sourceTextSha256':sha(source[old['sourceId']]),'previousPrimaryDisposition':old['primaryDisposition'],'previousCrossReviewDisposition':old['crossReviewDisposition'],'previousFinalTarget':old['finalTarget'],'previousFinalTargetSha256':old['finalTargetSha256'],'liveTarget':live,'liveTargetSha256':sha(live),'targetMatchesPreviousFinal':True,'callerRefs':refs,'callerContextReattested':True})
assert len(current_boundary)==12
# Build a canonical prior-cell disposition hash ledger for positions 0-849.
normalized=list(old_prior)
for row in primary800:
 o=row['sourceOrdinal']; sid=row['sourceId']; loc=row['locale']
 assert queue[o]==sid and 800<=o<=849
 normalized.append({'sourceOrdinal':o,'sourceId':sid,'locale':loc,'priorDisposition':row['disposition'],'priorRecommendedTargetSha256':row.get('recommendedTargetSha256'),'priorCurrentTargetSha256':row['currentTargetSha256'],'priorFinalTargetSha256':row['finalTargetSha256'],'priorSourceTextSha256':row['sourceTextSha256'],'priorPacket':'chaptarrng-pr190-window-0800-0849-primary-20261102','priorRecordFile':'primary-review-ledger.jsonl','priorRecordLine':next(i for i,x in enumerate(primary800,1) if (x['sourceOrdinal'],x['sourceId'],x['locale'])==(o,sid,loc)),'priorRecordSha256':sha(jbytes(row))})
assert len(normalized)==10200
pairs={(x['sourceOrdinal'],x['sourceId'],x['locale']) for x in normalized}
assert len(pairs)==10200
assert {x[0] for x in pairs}==set(range(850))
assert all(sid==queue[o] for o,sid,_ in pairs)
selected=queue[850:900]
assert len(selected)==50 and len(set(selected))==50 and not(set(selected)&{sid for _,sid,_ in pairs})
assert not any(x['sourceOrdinal']>=850 and x['sourceId'] in set(selected) for x in normalized)
# Include prior evidence file summary plus the W800 primary packet and its applied cross-review state.
prior_boundary={
 'exactHead':HEAD,'exactTree':TREE,
 'priorPrimaryWindowCount':17,'priorPrimaryArtifactDirectoryCount':20,
 'priorCellDispositionCount':len(normalized),'priorUniqueSourcePositions':850,
 'priorPositionsCovered':{'start':0,'endInclusive':849,'count':850,'complete':True},
 'priorRowsByPositionLocaleUnique':True,'priorSourceIdsMatchPinnedQueue':True,
 'previousW800PrimaryEvidence':{'path':str(P800),'manifestSha256':sha((P800/'manifest.json').read_bytes()),'sha256sums':p800_sums,'priorDispositionBoundarySha256':sha((P800/'prior-disposition-boundary.json').read_bytes()),'priorDispositionHashesSha256':sha((P800/'prior-disposition-hashes.jsonl').read_bytes()),'priorRows':9600,'priorCoverage0Through799':True,'priorOverlap0Through799':0},
 'w800W849Primary':{'path':str(P800),'primaryLedgerSha256':sha((P800/'primary-review-ledger.jsonl').read_bytes()),'rows':len(primary800),'sourcePositions':[800,849]},
 'w800W849CrossReview':{'path':str(X800),'manifestSha256':sha((X800/'manifest.json').read_bytes()),'sha256sums':x800_sums,'ledgerSha256':sha((X800/'crossreview-ledger.jsonl').read_bytes()),'rows':len(cross800)},
 'w800W849ApplyReadback':{'path':str(A800),'summarySha256':sha((A800/'apply-summary.json').read_bytes()),'readbackSha256':sha((A800/'apply-readback.jsonl').read_bytes()),'rows':len(apply800),'all600CurrentCatalogValuesMatchFinalCrossReview':True},
 'w800W849CurrentTargetReattestationRows':reattested,
 'w849BoundaryRows':len(current_boundary),'w849All12MatchCrossReviewFinalAndLiveCatalog':True,
 'selectedWindow':[850,899],'selectedSourceIds':50,'selectedIdsSha256':sha(jbytes(selected)),
 'selectedIdsDisjointFromAllPriorSourcesAndCells':True,'priorOverlapCount':0,
 'priorEvidenceLimitation':'Earlier W0-W799 dispositions are re-attested through the exact checksummed prior packet manifest and its complete 9,600-cell disposition-hash ledger; their old target values are historical hashes, not live catalog contents.'
}
(OUT/'prior-disposition-hashes.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in normalized))
(OUT/'w800-w849-applied-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in reattested))
(OUT/'w849-boundary-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in current_boundary))
(OUT/'prior-disposition-boundary.json').write_text(json.dumps(prior_boundary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
# Fix top-level input manifest facts to the verified complete predecessor coverage.
mp=OUT/'input-manifest.json'; m=json.loads(mp.read_text())
m['priorDispositionPacketCount']=17;m['priorDispositionPacketDirectoryCount']=20;m['priorDispositionsRecorded']=len(normalized);m['noPriorDispositionOverlap']=True;m['priorWindowBoundaryOrdinal']=849;m['w849BoundaryMatchesPriorCrossReview']=12;m['w800W849AppliedCellsReattested']=600;m['priorCoverageCompleteThrough849']=True;m['priorOverlapCount']=0
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
prep=OUT/'prepare-reattestation.json'; prep_obj=json.loads(prep.read_text())
prep_obj.update({'priorPrimaryPacketCount':17,'priorPrimaryArtifactDirectoryCount':20,'priorDispositionsRecorded':len(normalized),'priorOverlapCount':0,'priorPositionsCovered':[0,849],'priorCoverageCompleteThrough849':True,'w800W849AppliedTargetsReattested':600,'w849BoundaryRows':12,'w849BoundaryMatches':12})
prep.write_text(json.dumps(prep_obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(OUT/'reconciliation-reattestation.json').write_text(json.dumps({'exactHead':HEAD,'exactTree':TREE,'priorEvidenceVerified':True,'priorDispositionsRecorded':len(normalized),'sourcePositionsCovered':[0,849],'w800W849AppliedCellsReattested':600,'w849BoundaryMatches':12,'selectedWindow':[850,899],'priorOverlapCount':0,'checksumsVerified':{'w800PrimaryFiles':p800_sums['checkedFiles'],'w800CrossreviewFiles':x800_sums['checkedFiles']}},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'priorRows':len(normalized),'priorPositions':850,'w800CurrentReattestRows':len(reattested),'w849Boundary':len(current_boundary),'selected':len(selected),'overlap':0,'primarySumsVerified':p800_sums['checkedFiles'],'crossreviewSumsVerified':x800_sums['checkedFiles']},indent=2))
