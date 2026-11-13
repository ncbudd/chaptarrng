import collections,hashlib,json,pathlib,re
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0800-0849-primary-20261102')
ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch')
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def verify(folder):
 sums=next((folder/n for n in ['SHA256SUMS','SHA256SUMS.txt'] if (folder/n).is_file()),None)
 if not sums: return {'present':False,'sha256':None,'checkedFiles':0}
 rows=0
 for line in sums.read_text().splitlines():
  if not line.strip(): continue
  digest,name=line.split('  ',1); f=folder/name; assert f.is_file() and sha(f.read_bytes())==digest,(folder/name)
  rows+=1
 return {'present':True,'path':sums.name,'sha256':sha(sums.read_bytes()),'checkedFiles':rows}

specs=[
 (0,49,[('chaptarrng-pr190-window-0000-0049-primary-semantic-20261102','primary-decisions.jsonl')]),
 (50,99,[('chaptarrng-pr190-window-0050-0099-primary-part-a-20261102','review-cells.jsonl'),('chaptarrng-pr190-window-0050-0099-primary-part-b-20261102','review.jsonl')]),
 (100,149,[('chaptarrng-pr190-window-0100-0149-primary-part-a-20261102','review-cells.jsonl'),('chaptarrng-pr190-window-0100-0149-primary-part-b-20261102','review.jsonl')]),
 (150,199,[('chaptarrng-pr190-window-0150-0199-primary-part-a-20261102','review-cells.jsonl'),('chaptarrng-pr190-window-0150-0199-primary-part-b-20261102','review-cells.jsonl')]),
]
for a in range(200,800,50): specs.append((a,a+49,[(f'chaptarrng-pr190-window-{a:04d}-{a+49:04d}-primary-20261102','review-cells.jsonl')]))
queue=json.loads((OUT/'input-manifest.json').read_text())['sourceQueue']['selectedSourceIds']
# input manifest selected ids is the current W800 slice; re-read ordered source queue directly from frozen source-followup data in input manifest data.
# Full currentMissingIds are in source-followup at the pinned head, copied below by the preparer.
full_ids=json.loads((OUT/'current-missing-ids.json').read_text())
assert len(full_ids)==1210 and len(set(full_ids))==1210
id_to_ord={sid:i for i,sid in enumerate(full_ids)}
all_rows=[]; packet_rows=[]; window_counts={}
for lo,hi,files in specs:
 window=[]; file_sources=[]
 for dirname,filename in files:
  folder=ROOT/dirname; fp=folder/filename; assert fp.is_file(),fp
  sm=verify(folder)
  raw_lines=fp.read_text().splitlines(); assert raw_lines
  packet_rows.append({'directory':dirname,'file':filename,'fileSha256':sha(fp.read_bytes()),'rowCount':len(raw_lines),'checksum':sm})
  for lineno,line in enumerate(raw_lines,1):
   x=json.loads(line)
   sid=x.get('sourceId',x.get('id',x.get('catalogKey'))); assert sid in id_to_ord,(dirname,filename,lineno,'unknown source ID',sid)
   ordinal=x.get('sourceOrdinal',x.get('sourcePosition',x.get('windowOrdinal',x.get('sourceIndex',id_to_ord[sid]))))
   if isinstance(ordinal,str):
    mt=re.search(r'\d+',ordinal); ordinal=int(mt.group()) if mt else id_to_ord[sid]
   ordinal=int(ordinal)
   if id_to_ord[sid] not in range(lo,hi+1): continue
   assert ordinal in (id_to_ord[sid],lo+id_to_ord[sid],id_to_ord[sid]-lo) or ordinal==id_to_ord[sid],(dirname,filename,lineno,ordinal,id_to_ord[sid])
   if ordinal not in range(lo,hi+1): ordinal=id_to_ord[sid]
   disp=next((x.get(k) for k in ['disposition','semanticDisposition','primaryVerdict','primaryDisposition','reviewDisposition'] if x.get(k) is not None),None)
   current=x.get('currentTarget',x.get('target',x.get('currentValue')))
   current_hash=next((x.get(k) for k in ['currentTargetSha256','targetSha256','currentValueSha256'] if x.get(k)),sha(current) if isinstance(current,str) else None)
   candidate=next((x.get(k) for k in ['recommendedTarget','candidateTarget','proposedTarget','primaryRecommendedTarget'] if x.get(k) is not None),None)
   candidate_hash=next((x.get(k) for k in ['recommendedTargetSha256','candidateTargetSha256','proposedTargetSha256','primaryRecommendedTargetSha256'] if x.get(k)),sha(candidate) if isinstance(candidate,str) else None)
   final=next((x.get(k) for k in ['finalTarget','independentTarget','primaryFinalTarget'] if x.get(k) is not None),None)
   final_hash=next((x.get(k) for k in ['finalTargetSha256','independentTargetSha256','primaryFinalTargetSha256'] if x.get(k)),sha(final) if isinstance(final,str) else None)
   if final is None and isinstance(current,str): final=current if candidate is None else candidate
   if final_hash is None and isinstance(final,str): final_hash=sha(final)
   row={'sourceOrdinal':id_to_ord[sid],'sourceId':sid,'locale':x.get('locale'),'priorDisposition':disp,'priorCurrentTargetSha256':current_hash,'priorRecommendedTargetSha256':candidate_hash,'priorFinalTargetSha256':final_hash,'priorSourceTextSha256':x.get('sourceTextSha256',x.get('sourceSha256')),'priorPacket':dirname,'priorRecordFile':filename,'priorRecordLine':lineno,'priorRecordSha256':sha(canon(x))}
   window.append(row); file_sources.append(sid)
 assert len(window)==600,(lo,hi,len(window),files)
 assert len({(x['sourceOrdinal'],x['locale']) for x in window})==600,(lo,hi,'duplicate cells')
 assert {x['sourceOrdinal'] for x in window}==set(range(lo,hi+1)),(lo,hi,'ordinal coverage')
 all_rows.extend(window); window_counts[f'{lo}-{hi}']=len(window)
# The first four windows are split across six locales each; every 800 prior positions are represented exactly once.
assert len(all_rows)==9600 and len({(x['sourceOrdinal'],x['locale']) for x in all_rows})==9600
assert not any(x['sourceId'] in set(full_ids[800:850]) for x in all_rows)
(OUT/'prior-disposition-hashes.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in all_rows))
existing=json.loads((OUT/'prior-disposition-boundary.json').read_text())
existing.update({'priorPrimaryPackets':packet_rows,'priorPrimaryPacketFiles':len(packet_rows),'priorSourcePositionsCovered':800,'priorCellDispositionHashes':len(all_rows),'priorWindowCellCounts':window_counts,'priorDispositionsCoverEveryPosition0Through799':True,'priorDispositionSourceIdsUniqueByPosition':True,'noOverlapWithPositions0Through799':True,'exactPriorDispositionOverlapCount':0,'exactPriorDispositionOverlapRows':[],'priorDispositionRecordHashAlgorithm':'SHA-256 of canonical JSON encoding of each prior primary review record.'})
(OUT/'prior-disposition-boundary.json').write_text(json.dumps(existing,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
# Update input manifest with correct preceding-window evidence totals.
mp=OUT/'input-manifest.json'; m=json.loads(mp.read_text()); m['priorDispositionPacketCount']=len(packet_rows); m['priorDispositionsRecorded']=len(all_rows); m['priorPositionCoverage']={'start':0,'end':799,'positionCount':800,'cellCount':9600,'fullyCovered':True,'overlapWithSelectedWindow':0}
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
pp=OUT/'prepare-reattestation.json'; p=json.loads(pp.read_text()); p['priorPrimaryPacketFiles']=len(packet_rows); p['priorDispositionsRecorded']=len(all_rows); p['priorPositionCoverageComplete']=True; p['priorOverlapCount']=0
pp.write_text(json.dumps(p,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'priorPositions':800,'priorCells':len(all_rows),'packetFiles':len(packet_rows),'windowCounts':window_counts,'selectedOverlap':0,'checksumsVerified':sum(x['checksum']['checkedFiles'] for x in packet_rows)},ensure_ascii=False,indent=2))
