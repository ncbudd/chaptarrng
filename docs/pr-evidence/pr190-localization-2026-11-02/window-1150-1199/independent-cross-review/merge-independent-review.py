import collections,hashlib,json,re
from pathlib import Path
OUT=Path('.')
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e';TREE='d073e1373021bf715db37461a12654f7e993cdbf'
sha=lambda s:hashlib.sha256(s.encode('utf8')).hexdigest()
inputs=[json.loads(x) for x in open(OUT/'inputs/source-cells.jsonl',encoding='utf8')]
by={(x['sourceOrdinal'],x['locale']):x for x in inputs}
assert len(by)==600
own=[json.loads(x) for x in open(OUT/'independent-review-ar-de-es-fr-hi-id.jsonl',encoding='utf8')]
subp=OUT/'independent-review-ja-ko-ptBR-vi-zh-W1150-1199.jsonl'; sub_bytes=subp.read_bytes(); sub=[json.loads(x) for x in sub_bytes.decode('utf8').splitlines()]
assert len(own)==len(sub)==300 and hashlib.sha256(sub_bytes).hexdigest()=='30ee9831c40378e5e014094465da40577eaf8bcb3d0a2d97dbd3d17dc3f518ae'
ph=lambda s:collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
markup=lambda s: [] if re.fullmatch(r'<[^<>/]+>',s) else re.findall(r'</?[A-Za-z][^>]*>',s)
icu=lambda s: sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
rows=[]
for reviewer,part,srcrows in [('self','ar-de-es-fr-hi-id',own),('subagent','ja-ko-ptBR-vi-zh',sub)]:
 for rr in srcrows:
  n=rr['sourceOrdinal'];loc=rr['locale']; inp=by[(n,loc)]
  assert inp['sourceId']==rr['sourceId'] and inp['source']==rr['source']
  assert inp['sourceTextSha256']==rr['sourceTextSha256'] and inp['sourceIdSha256']==rr['sourceIdSha256']
  assert inp['currentTarget']==rr['currentTarget'] and inp['currentTargetSha256']==rr['currentTargetSha256'] and sha(inp['currentTarget'])==inp['currentTargetSha256']
  if reviewer=='self':
   assert rr['exactHead']==HEAD and rr['exactTree']==TREE
   disp=rr['independentDisposition'];cand=rr['candidateTarget'];reason=rr['rationale'];conf=rr['confidence']
   assert rr['callerContextSha256']==inp['callerContextSha256'] and rr['callerRefs']==inp['callerReferences']
  else:
   assert rr['pins']['exactHead']==HEAD and rr['pins']['exactTree']==TREE
   assert rr['pins']['sourceCatalog']['sha256']==inp['sourceFileSha256'] and rr['pins']['sourceCatalog']['gitBlob']==inp['sourceFileGitBlob']
   assert rr['pins']['targetCatalog']['path']==inp['targetFile'] and rr['pins']['targetCatalog']['sha256']==inp['targetFileSha256'] and rr['pins']['targetCatalog']['gitBlob']==inp['targetFileGitBlob']
   assert rr['pins']['sourceRegistry']['sourceIdSha256']==inp['sourceIdSha256'] and rr['pins']['sourceRegistry']['sourceTextSha256']==inp['sourceTextSha256']
   assert rr['callerContext']['status']=='exact' and rr['callerContext']['sha256']==inp['callerContextSha256'] and rr['callerContext']['references']==inp['callerReferences']
   disp=rr['disposition'];cand=rr['candidate'];reason=rr['rationale'];conf=rr['confidence']
   assert rr['candidateSha256']==(sha(cand) if cand is not None else None)
  assert disp in {'accept-current','correction','refinement','hold'}
  assert (disp in {'correction','refinement'})==(cand is not None)
  if cand is not None: assert cand != inp['currentTarget']
  final=inp['currentTarget'] if cand is None else cand
  assert (disp=='hold') == (n==1187)
  assert ph(inp['source'])==ph(inp['currentTarget'])==ph(final)
  assert markup(inp['source'])==markup(inp['currentTarget'])==markup(final)
  assert icu(inp['source'])==icu(inp['currentTarget'])==icu(final)
  literals=inp['protectedLiterals'];failures=[lit for lit in literals if lit not in final]
  if disp!='hold':assert not failures,(n,loc,failures)
  if disp=='hold':assert n==1187 and failures in ([],['M4B']),(n,loc,failures)
  checks={'sourcePlaceholders':dict(sorted(ph(inp['source']).items())),'currentPlaceholders':dict(sorted(ph(inp['currentTarget']).items())),'finalPlaceholders':dict(sorted(ph(final).items())),
   'placeholderParity':True,'sourceMarkup':markup(inp['source']),'currentMarkup':markup(inp['currentTarget']),'finalMarkup':markup(final),'markupParity':True,
   'sourceIcuSignature':icu(inp['source']),'currentIcuSignature':icu(inp['currentTarget']),'finalIcuSignature':icu(final),'icuParity':True,
   'protectedLiteralChecks':[{'literal':lit,'inSource':lit in inp['source'],'inCurrentTarget':lit in inp['currentTarget'],'inFinalTarget':lit in final,
    'status':'hold-conflict' if disp=='hold' else ('pass' if lit in final else 'fail')} for lit in literals],
   'currentProtectedLiteralFailures':[lit for lit in literals if lit not in inp['currentTarget']],'finalProtectedLiteralFailures':failures,
   'protectedLiteralDisposition':'hold-conflict' if disp=='hold' else 'pass'}
  result={'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':n,'sourceId':inp['sourceId'],'locale':loc,'source':inp['source'],
   'sourceIdSha256':inp['sourceIdSha256'],'sourceTextSha256':inp['sourceTextSha256'],'sourceFile':inp['sourceFile'],'sourceFileGitBlob':inp['sourceFileGitBlob'],'sourceFileSha256':inp['sourceFileSha256'],
   'currentTarget':inp['currentTarget'],'currentTargetSha256':inp['currentTargetSha256'],'targetFile':inp['targetFile'],'targetFileGitBlob':inp['targetFileGitBlob'],'targetFileSha256':inp['targetFileSha256'],
   'callerContextSha256':inp['callerContextSha256'],'callerReferenceCount':len(inp['callerReferences']),'callerRefs':inp['callerReferences'],
   'independentDisposition':disp,'candidateTarget':cand,'candidateTargetSha256':sha(cand) if cand is not None else None,
   'independentFinalTarget':final,'independentFinalTargetSha256':sha(final),'rationale':reason,'confidence':conf,'reviewerPartition':part,'reviewerType':reviewer,
   'protectedLiterals':literals,'sourceRegistryFingerprint':inp['sourceRegistryFingerprint'],'sourceRegistryParameters':inp['sourceRegistryParameters'],
   'structuralChecks':checks,'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True}
  rows.append(result)
assert len(rows)==600 and len({(x['sourceOrdinal'],x['locale']) for x in rows})==600
loc_order=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'];rows.sort(key=lambda x:(x['sourceOrdinal'],loc_order.index(x['locale'])))
def writejl(name,rs):
 with open(OUT/name,'w',encoding='utf8') as f:
  for x in rs:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n')
writejl('independent-review-cells.jsonl',rows)
writejl('independent-correction-candidates.jsonl',[x for x in rows if x['independentDisposition']=='correction'])
writejl('independent-refinement-candidates.jsonl',[x for x in rows if x['independentDisposition']=='refinement'])
writejl('independent-holds.jsonl',[x for x in rows if x['independentDisposition']=='hold'])
writejl('independent-protected-literal-integrity.jsonl',[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'currentTargetSha256':x['currentTargetSha256'],
 'independentDisposition':x['independentDisposition'],'candidateTargetSha256':x['candidateTargetSha256'],'independentFinalTargetSha256':x['independentFinalTargetSha256'],
 'protectedLiterals':x['protectedLiterals'],'checks':x['structuralChecks']} for x in rows])
print(json.dumps({'rows':len(rows),'dispositions':dict(collections.Counter(x['independentDisposition'] for x in rows)),
 'byReviewer':{p:dict(collections.Counter(x['independentDisposition'] for x in rows if x['reviewerPartition']==p)) for p in [ 'ar-de-es-fr-hi-id','ja-ko-ptBR-vi-zh']},
 'confidence':dict(collections.Counter(x['confidence'] for x in rows)),'reviewSha256':hashlib.sha256((OUT/'independent-review-cells.jsonl').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
