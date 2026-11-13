import collections,hashlib,json
from pathlib import Path
OUT=Path('.')
PRIMARY=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1150-1199-primary-20261102')
sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode('utf8')).hexdigest()
ind=[json.loads(x) for x in open(OUT/'independent-review-cells.jsonl',encoding='utf8')]
pri=[json.loads(x) for x in open(PRIMARY/'review-cells.jsonl',encoding='utf8')]
assert len(ind)==len(pri)==600
im=json.load(open(OUT/'independent-review-manifest.json',encoding='utf8'))
pm=json.load(open(PRIMARY/'input-manifest.json',encoding='utf8'))
assert im['exactHead']==pm['head']=='6e7a5341b7ccac31d950c73db68277f9a1f18f8e' and im['exactTree']==pm['tree']=='d073e1373021bf715db37461a12654f7e993cdbf'
iby={(x['sourceOrdinal'],x['locale']):x for x in ind}; pby={(x['sourceOrdinal'],x['locale']):x for x in pri}; assert len(iby)==len(pby)==600 and iby.keys()==pby.keys()
rows=[]; classes=collections.Counter(); per=collections.defaultdict(collections.Counter)
caller_pin_mismatches=[]
def norm_ref(r):
 return {'category':r.get('category'),'file':r.get('file',r.get('path')),'line':r.get('line'),'lineText':r.get('lineText',r.get('sourceLine')),
  'lineSha256':r.get('lineSha256',r.get('sourceLineSha256')),'fileSha256':r.get('fileSha256'),'fileGitBlob':r.get('fileGitBlob'),
  'registryLine':r.get('registryLine'),'registryPinExact':r.get('registryPinExact'),'registrySourceLineSha256':r.get('registrySourceLineSha256'),
  'surface':r.get('surface'),'contextBefore':[x.strip() for x in r.get('contextBefore',[])],'contextAfter':[x.strip() for x in r.get('contextAfter',[])]}
for k in sorted(iby):
 a=iby[k]; b=pby[k]
 assert a['sourceId']==b['sourceId'] and a['sourceTextSha256']==b['sourceTextSha256'] and a['currentTargetSha256']==b['currentTargetSha256']
 assert a['source']==b['source'] and a['currentTarget']==b['currentTarget']
 an=[norm_ref(x) for x in a['callerRefs']];bn=[norm_ref(x) for x in b['callerRefs']]
 if an!=bn: caller_pin_mismatches.append({'ordinal':k[0],'locale':k[1],'independentPins':an,'primaryPins':bn})
 ad=a['independentDisposition']; pd=b['primaryDisposition']; ac=a['candidateTarget']; pc=b['recommendedTarget']
 if ad==pd and ac==pc:
  cls='exact-agreement'
 elif ad=='hold' or pd=='hold':
  cls='hold-disagreement' if ad!=pd or ac!=pc else 'exact-agreement'
 elif ad in ('correction','refinement') and pd in ('correction','refinement'):
  cls='same-candidate-different-kind' if ac==pc else 'different-candidate-targets'
 elif ad=='accept-current' and pd in ('correction','refinement'):
  cls='primary-proposal-not-independently-confirmed'
 elif pd=='accept-current' and ad in ('correction','refinement'):
  cls='independent-proposal-omitted-by-primary'
 else: cls='other-disagreement'
 classes[cls]+=1; per[a['locale']][cls]+=1
 if cls!='exact-agreement':
  rows.append({'sourceOrdinal':k[0],'sourceId':a['sourceId'],'locale':k[1],'currentTargetSha256':a['currentTargetSha256'],
   'independentDisposition':ad,'independentCandidate':ac,'independentCandidateSha256':a['candidateTargetSha256'],'independentRationale':a['rationale'],
   'primaryDisposition':pd,'primaryRecommendedTarget':pc,'primaryRecommendedTargetSha256':b['recommendedTargetSha256'],'primaryRationale':b['decisionRationale'],
   'comparison':cls,'callerContextSha256':a['callerContextSha256']})
# Hash-check the exact primary evidence packet before accepting the comparison inputs.
summary={'independentLedgerSha256':sha((OUT/'independent-review-cells.jsonl').read_bytes()),'primaryLedgerSha256':sha((PRIMARY/'review-cells.jsonl').read_bytes()),
 'primaryPacketManifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),'primaryChecksumFileSha256':sha((PRIMARY/'SHA256SUMS').read_bytes()),
 'exactHead':'6e7a5341b7ccac31d950c73db68277f9a1f18f8e','exactTree':'d073e1373021bf715db37461a12654f7e993cdbf',
 'crossComparedCells':600,'sourceCurrentHashMismatches':0,'exactCallerPinMismatches':len(caller_pin_mismatches),
 'callerContextHashSchemaNote':'Per-cell caller-context digests differ because the two packets canonicalize reference records differently; exact normalized source line, context, file blob/SHA, registry line and surface pins were compared directly.',
 'comparisonClasses':dict(sorted(classes.items())),
 'perLocaleComparison':{loc:dict(sorted(c.items())) for loc,c in sorted(per.items())},
 'holdsAgreed':classes['hold-disagreement']==0,'w1187HoldRows':sum(a['sourceOrdinal']==1187 and a['independentDisposition']=='hold' for a in ind),
 'crossReviewInterpretation':'Independent disposition is preserved. Candidate target differences are reported for coordinator adjudication; primary recommendations were not used to construct the independent ledger.'}
(OUT/'primary-comparison-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
with open(OUT/'primary-comparison-differences.jsonl','w',encoding='utf8') as f:
 for x in rows:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n')
(OUT/'caller-pin-comparison.json').write_text(json.dumps({'comparedRows':600,'exactNormalizedPinMismatches':len(caller_pin_mismatches),'mismatches':caller_pin_mismatches},ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
print(json.dumps({'summary':summary,'differenceRows':len(rows)},ensure_ascii=False,indent=2))
