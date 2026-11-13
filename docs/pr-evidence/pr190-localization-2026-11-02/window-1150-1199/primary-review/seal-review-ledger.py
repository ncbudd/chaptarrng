import collections, hashlib, json, re
from pathlib import Path
OUT=Path('.')
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e'; TREE='d073e1373021bf715db37461a12654f7e993cdbf'
sha=lambda b: hashlib.sha256(b if isinstance(b,bytes) else b.encode('utf8')).hexdigest()
inputs=[json.loads(x) for x in open(OUT/'input-cells.jsonl',encoding='utf8')]
sources={json.loads(x)['sourceOrdinal']:json.loads(x) for x in open(OUT/'source-slice.jsonl',encoding='utf8')}
callers={json.loads(x)['sourceOrdinal']:json.loads(x) for x in open(OUT/'caller-context.jsonl',encoding='utf8')}
pins=json.load(open(OUT/'catalog-pins.json',encoding='utf8')); manifest=json.load(open(OUT/'input-manifest.json',encoding='utf8'))
assert manifest['head']==HEAD and manifest['tree']==TREE and manifest['cellCount']==600
assert pins['exactHead']==HEAD and pins['exactTree']==TREE
input_by={(x['sourceOrdinal'],x['locale']):x for x in inputs}; assert len(input_by)==600
own=[json.loads(x) for x in open(OUT/'locale-review-ja-ko-pt-vi-zh.jsonl',encoding='utf8')]
otherpath=OUT/'locale-review-ar-de-es-fr-hi-id.jsonl'
other_bytes=otherpath.read_bytes(); assert sha(other_bytes)==(OUT/'locale-review-ar-de-es-fr-hi-id.jsonl.sha256').read_text().split()[0]
other=[json.loads(x) for x in other_bytes.decode('utf8').splitlines()]
assert len(own)==len(other)==300
assert sha((OUT/'locale-review-ja-ko-pt-vi-zh.jsonl').read_bytes())==(OUT/'locale-review-ja-ko-pt-vi-zh.jsonl.sha256').read_text().split()[0]
ph=lambda s: collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
markup=lambda s: [] if re.fullmatch(r'<[^<>/]+>',s) else re.findall(r'</?[A-Za-z][^>]*>',s)
icu=lambda s: sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
reviews=[]
for part,rows in [('ja-ko-pt-vi-zh',own),('ar-de-es-fr-hi-id',other)]:
 for rr in rows:
  n=rr['sourceOrdinal']; loc=rr['locale']; inp=input_by[(n,loc)]; src=sources[n]; caller=callers[n]
  assert rr['exactHead']==HEAD and rr['exactTree']==TREE
  reported_source=rr.get('sourceText',rr.get('source'))
  assert rr['sourceId']==inp['sourceId'] and reported_source==inp['sourceText'] and rr['sourceTextSha256']==inp['sourceTextSha256']
  assert rr['currentTarget']==inp['currentTarget'] and rr['currentTargetSha256']==inp['currentTargetSha256'] and sha(inp['currentTarget'])==inp['currentTargetSha256']
  assert rr['callerContextSha256']==caller['callerContextSha256']==inp['callerContextSha256'] and caller['callerReferenceStatus']=='exact'
  assert inp['callerReferences']==caller['callerReferences']
  assert all(ref['registryPinExact'] for ref in caller['callerReferences'])
  assert inp['sourceId']==src['sourceId'] and sha(inp['sourceId'])==inp['sourceIdSha256']==src['sourceIdSha256']
  assert sha(inp['sourceText'])==inp['sourceTextSha256']==src['sourceTextSha256']
  catalog_pin=pins['localeCatalogs'][inp['locale']]
  assert inp['targetFile']==catalog_pin['path'] and inp['catalogGitBlob']==catalog_pin['gitBlob'] and inp['catalogFileSha256']==catalog_pin['sha256']
  if part=='ar-de-es-fr-hi-id':
   disp=rr['disposition']; target=rr['proposedTarget']; final=rr['finalTarget']; rationale=rr['semanticRationale']; conf=rr['confidence']
   assert rr['sourceIdSha256']==inp['sourceIdSha256'] and rr['currentTargetSha256']==inp['currentTargetSha256']
   if disp=='hold' and final is None: final=inp['currentTarget']
   if rr['finalTargetSha256'] is not None: assert rr['finalTargetSha256']==sha(final)
   assert (disp=='hold') == (target is None and n==1187)
  else:
   assert rr['primaryDisposition'] in {'accept-current','correction','refinement','hold'}
   disp=rr['primaryDisposition']; target=rr['recommendedTarget']; final=rr['finalReviewedTarget']; rationale=rr['decisionRationale']; conf=rr['reviewConfidence']
   assert rr['finalReviewedTargetSha256']==sha(final)
   assert rr['recommendedTargetSha256']==(sha(target) if target is not None else None)
  assert disp in {'accept-current','correction','refinement','hold'}
  assert (disp in {'correction','refinement'}) == (target is not None)
  assert (disp=='hold') == (n==1187)
  assert final== (inp['currentTarget'] if target is None else target)
  assert ph(inp['sourceText'])==ph(inp['currentTarget'])==ph(final)
  assert markup(inp['sourceText'])==markup(inp['currentTarget'])==markup(final)
  assert icu(inp['sourceText'])==icu(inp['currentTarget'])==icu(final)
  literals=inp['protectedLiterals']
  failures=[lit for lit in literals if lit not in final]
  if disp!='hold': assert not failures,(n,loc,failures)
  elif n==1187: assert failures in ([],['M4B']),(n,loc,failures)
  checks={'sourcePlaceholders':dict(sorted(ph(inp['sourceText']).items())),'currentPlaceholders':dict(sorted(ph(inp['currentTarget']).items())),'finalPlaceholders':dict(sorted(ph(final).items())),
   'placeholderParity':True,'sourceMarkup':markup(inp['sourceText']),'currentMarkup':markup(inp['currentTarget']),'finalMarkup':markup(final),'markupParity':True,
   'sourceIcuSignature':icu(inp['sourceText']),'currentIcuSignature':icu(inp['currentTarget']),'finalIcuSignature':icu(final),'icuParity':True,
   'protectedLiteralChecks':[{'literal':lit,'inSource':lit in inp['sourceText'],'inCurrentTarget':lit in inp['currentTarget'],'inFinalTarget':lit in final,
      'status':'hold-conflict' if disp=='hold' else ('pass' if lit in final else 'fail')} for lit in literals],
   'currentProtectedLiteralFailures':[lit for lit in literals if lit not in inp['currentTarget']],
   'finalProtectedLiteralFailures':failures,'protectedLiteralDisposition':'hold-conflict' if disp=='hold' else 'pass'}
  cinfo=pins['localeCatalogs'][loc]; e=pins['englishCatalog']
  refs=inp['callerReferences']
  sem='Exact registered server/API message and pinned production display/error surface: '+('; '.join(sorted({x.get('surface','') for x in refs if x.get('surface')})) or 'surface is recorded by the caller references.')
  row={'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':n,'sourceId':inp['sourceId'],'locale':loc,'source':inp['sourceText'],
   'sourceIdSha256':inp['sourceIdSha256'],'sourceTextSha256':inp['sourceTextSha256'],'sourceFile':e['path'],'sourceFileGitBlob':e['gitBlob'],'sourceFileSha256':e['sha256'],
   'currentTarget':inp['currentTarget'],'currentTargetSha256':inp['currentTargetSha256'],'targetFile':inp['targetFile'],'targetFileGitBlob':cinfo['gitBlob'],'targetFileSha256':cinfo['sha256'],
   'primaryDisposition':disp,'recommendedTarget':target,'recommendedTargetSha256':sha(target) if target is not None else None,
   'finalReviewedTarget':final,'finalReviewedTargetSha256':sha(final),'decisionRationale':rationale,'reviewConfidence':conf,
   'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'callerContextSha256':inp['callerContextSha256'],'callerReferenceCount':len(refs),'callerRefs':refs,
   'protectedLiterals':literals,'sourceRegistryFingerprint':src['sourceRegistryFingerprint'],'sourceRegistryParameters':inp['registryParameters'],'sourceTemplates':src['sourceTemplates'],
   'structuralChecks':checks,'semanticInterpretation':sem,'reviewerPartition':part}
  reviews.append(row)
assert len(reviews)==600
assert len({(r['sourceOrdinal'],r['locale']) for r in reviews})==600
locales={loc for loc in (r['locale'] for r in reviews)}
assert len(locales)==12
reviews.sort(key=lambda r:(r['sourceOrdinal'],list(pins['localeCatalogs']).index(r['locale'])))
counts=collections.Counter(r['primaryDisposition'] for r in reviews)
assert sum(counts.values())==600 and counts['hold']==12
for n in range(1150,1200): assert sum(r['sourceOrdinal']==n for r in reviews)==12

def writejl(name,rows):
 with open(OUT/name,'w',encoding='utf8') as f:
  for r in rows: f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
writejl('review-cells.jsonl',reviews)
writejl('correction-candidates.jsonl',[r for r in reviews if r['primaryDisposition']=='correction'])
writejl('refinement-candidates.jsonl',[r for r in reviews if r['primaryDisposition']=='refinement'])
writejl('holds.jsonl',[r for r in reviews if r['primaryDisposition']=='hold'])
writejl('protected-literal-integrity.jsonl',[{'sourceOrdinal':r['sourceOrdinal'],'sourceId':r['sourceId'],'locale':r['locale'],'currentTargetSha256':r['currentTargetSha256'],
 'primaryDisposition':r['primaryDisposition'],'recommendedTargetSha256':r['recommendedTargetSha256'],'finalReviewedTargetSha256':r['finalReviewedTargetSha256'],
 'protectedLiterals':r['protectedLiterals'],'checks':r['structuralChecks']} for r in reviews])
conf=collections.Counter(r['reviewConfidence'] for r in reviews)
struct={'placeholderMismatchCells':sum(not r['structuralChecks']['placeholderParity'] for r in reviews),
 'markupMismatchCells':sum(not r['structuralChecks']['markupParity'] for r in reviews),'icuMismatchCells':sum(not r['structuralChecks']['icuParity'] for r in reviews),
 'currentProtectedLiteralFailureCells':sum(bool(r['structuralChecks']['currentProtectedLiteralFailures']) for r in reviews),
 'finalProtectedLiteralFailureCells':sum(bool(r['structuralChecks']['finalProtectedLiteralFailures']) for r in reviews),
 'callerGaps':sum(1 for n in range(1150,1200) if callers[n]['callerReferenceStatus']!='exact')}
summary={'repository':'snapetech-org/chaptarrng','pullRequest':190,'state':'OPEN','isDraft':True,'branch':'codex/chaptarrng-localization-complete-20261031','head':HEAD,'tree':TREE,
 'window':'W1150-W1199','zeroBasedQueuePositions':[1150,1199],'sourceCount':50,'localeCount':12,'cellCount':600,
 'dispositionCounts':dict(sorted(counts.items())),'proposalKindCounts':{'correction':counts['correction'],'refinement':counts['refinement']},'proposedValueChanges':counts['correction']+counts['refinement'],
 'holdCellCount':counts['hold'],'perLocaleDispositionCounts':{loc:dict(collections.Counter(r['primaryDisposition'] for r in reviews if r['locale']==loc)) for loc in pins['localeCatalogs']},
 'directCallerReferences':sum(len(callers[n]['callerReferences']) for n in range(1150,1200)),
 'callerFiles':len({p['path'] for n in range(1150,1200) for p in callers[n]['callerReferences']}),**struct,
 'confidenceCounts':dict(sorted(conf.items())),'holdSourceIds':['server.message.md764ed5e74b4'],'holdRationale':'For W1187, both callers provide TargetQualityName ?? "M4B" as {value0}; the dynamic name can differ from M4B while source registry requires protected literal M4B. Hold rather than insert a possibly false M4B label or infer that dynamic values are always M4B.',
 'history':{'priorRowsReattested':13800,'oldLiveCurrentDriftThroughW1149':0,'historicFinalVsCurrentMismatchesStable':195,'w1050DodgeHoldsPreserved':12,'w1100AppliedReadbackMismatches':0,'w1149BackwardBoundaryRows':12,'w1149BoundaryMatches':12,'w1150ForwardBoundaryRows':12,'w1150BoundaryMatches':12},
 'nativeSpeakerApproval':False,'headedBrowserAcceptance':False,'overallConfidence':'moderate','limitations':'Static machine-assisted primary semantic review. No native-speaker approval, headed browser acceptance, runtime validation, or CI/test/build evidence is claimed. One source registry/caller conflict is held in all locales.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
review_parts={'schemaVersion':1,'partitions':[{'name':'ja-ko-pt-vi-zh','artifact':'locale-review-ja-ko-pt-vi-zh.jsonl','rows':len(own),'sha256':sha((OUT/'locale-review-ja-ko-pt-vi-zh.jsonl').read_bytes()),'dispositions':dict(collections.Counter(r['primaryDisposition'] for r in own))},
 {'name':'ar-de-es-fr-hi-id','artifact':'locale-review-ar-de-es-fr-hi-id.jsonl','rows':len(other),'sha256':sha(other_bytes),'dispositions':dict(collections.Counter(r['disposition'] for r in other))}],
 'mergedRows':600,'exactHead':HEAD,'exactTree':TREE,'mergedArtifact':'review-cells.jsonl','mergedArtifactSha256':sha((OUT/'review-cells.jsonl').read_bytes()),'rowsNormalizedAgainstFrozenInputs':True}
(OUT/'review-parts-manifest.json').write_text(json.dumps(review_parts,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
print(json.dumps({'summary':summary,'reviewSha256':sha((OUT/'review-cells.jsonl').read_bytes()),'candidateRows':counts['correction']+counts['refinement']},ensure_ascii=False,indent=2))
