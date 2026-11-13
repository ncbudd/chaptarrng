#!/usr/bin/env python3
import collections,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w300-349-source')
HEAD='f0082d1b655c05b8d4019ede523dd695cd6d745a';TREE='4cf2322354e9cf9b12d59cf10d0d8661c68ab4af'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
DIRECT_FIELDS=('sourceKey','source_key','key','sourceId','source_id','id')
def fail(s):raise SystemExit('FAIL: '+s)
def need(v,m):
 if not v:fail(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def stsha(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def readj(n):return json.loads((P/n).read_text(encoding='utf-8'))
def readjl(n):return [json.loads(x) for x in (P/n).read_text(encoding='utf-8').splitlines() if x.strip()]
def tree_oid(path):
 raw=subprocess.check_output(['git','-C',str(ROOT),'ls-tree',HEAD,'--',path],text=True).strip()
 return raw.split('\t',1)[0].split()[-1] if raw else None
def gitblob(oid):return subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',oid])
m=readj('candidate-free-manifest.json'); s=readj('source-selection.json')
need((m['head'],m['tree'])==(HEAD,TREE),'head/tree')
need(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==HEAD,'local head')
need(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD^{tree}'],text=True).strip()==TREE,'local tree')
need(subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain=v1'],text=True).strip()=='','source worktree status')
need(len(s['keys'])==50 and len(set(s['keys']))==50 and (s['firstPosition'],s['lastPosition'])==(300,349),'selection dimensions')
# Exact source and locale catalogs at the pin.
cat_meta={'en':m['sourceCatalog'],**m['targetCatalogs']}; catalogs={}
for loc,meta in cat_meta.items():
 raw=(ROOT/meta['path']).read_bytes();need(sha(raw)==meta['sha256'],'catalog file SHA '+loc)
 need(tree_oid(meta['path'])==meta['gitBlob'],'catalog Git blob '+loc)
 data=json.loads(raw);need(len(data)==4165,'catalog key count '+loc)
 catalogs[loc]=data
source=catalogs['en'];source_keys=list(source)
need(set(source)==set(catalogs['ar']),'English/target key set')
need(all(set(source)==set(catalogs[l]) for l in LOCALES),'locale key parity')
need(sha((ROOT/'src/NzbDrone.Core/Localization/Core/en.json').read_bytes())==m['sourceCatalog']['sha256'],'source catalog bytes')
# Rebuild the frozen direct-identifier set and source order, checking all 392 blobs.
hist=readj('prior-historical-evidence-scan.json'); hist_ids=set(); hist_rows=0
need(len(hist['files'])==392,'historical file count')
for f in hist['files']:
 data=gitblob(f['gitBlob']);need(sha(data)==f['sha256'],'historical blob '+f['path'])
 for line in data.splitlines():
  if not line.strip():continue
  try:r=json.loads(line)
  except Exception:continue
  hist_rows+=1
  if isinstance(r,dict):
   for field in DIRECT_FIELDS:
    v=r.get(field)
    if isinstance(v,str):hist_ids.add(v)
need(hist_rows==211539 and hist_rows==hist['rowsScanned'],'historical row count')
uncovered=[k for k in source_keys if k not in hist_ids]
prior=[k for d in s['priorSelections'] for k in d['keys']]
need(len(prior)==300 and uncovered[:300]==prior,'W0-W299 sequential selection')
need(uncovered[300:350]==s['keys'],'W300-W349 order')
need(sha(canon(s['keys']))==s['selectedKeysSha256'],'selected key digest')
# Every current input row is an exact source/target value at the pinned tree.
cells=readjl('candidate-free-cells.jsonl');need(len(cells)==600,'current cell count')
need(sha((P/'candidate-free-cells.jsonl').read_bytes())==m['candidateFreeCells']['sha256'],'current cells file hash')
seen=set()
for r in cells:
 ident=(r['sourceOrdinal'],r['locale']);need(ident not in seen,'duplicate current cell');seen.add(ident)
 k=r['sourceKey'];loc=r['locale'];need(300<=r['sourceOrdinal']<=349 and k in s['keys'] and loc in LOCALES,'current cell identity')
 need(r['sourceText']==source[k] and r['currentTarget']==catalogs[loc][k],'cell catalog linkage '+k+'/'+loc)
 need(stsha(r['sourceText'])==r['sourceTextSha256'] and stsha(r['currentTarget'])==r['currentTargetSha256'],'cell text hash '+k+'/'+loc)
 need(r['sourceFileGitBlob']==tree_oid(r['sourceFile']) and r['targetFileGitBlob']==tree_oid(r['targetFile']),'cell catalog blob pins '+k+'/'+loc)
need(len(seen)==600 and len({r['sourceKey'] for r in cells})==50 and len({r['locale'] for r in cells})==12,'current cell identities')
# Verify every caller file hash/blob captured by the inventory, plus per-key context hashes.
pins=readj('caller-scan-file-pins.json');need(pins['exactHead']==HEAD and pins['exactTree']==TREE,'caller inventory pin')
for f in pins['files']:
 raw=(ROOT/f['path']).read_bytes();need(sha(raw)==f['sha256'] and tree_oid(f['path'])==f['gitBlob'],'caller source pin '+f['path'])
contexts=readjl('caller-context.jsonl');need(len(contexts)==50,'caller context row count')
for c in contexts:
 body={'sourceKey':c['sourceKey'],'literalAndIndirectReferences':c['callerRefs'],'relatedDynamicTranslationCallsites':c['dynamicTranslationCallsites']}
 need(sha(canon(body).rstrip(b'\n'))==c['callerContextSha256'],'caller context digest '+c['sourceKey'])
# Reattest prior hash-only lineages, including every preserved hold.
key_by_hash={stsha(k):k for k in source_keys}
w0=readjl('prior-selected-hold-reattestations.jsonl');w200=readjl('prior-W200-application-reattestation.jsonl');w250=readjl('prior-W250-application-reattestation.jsonl')
need((len(w0),len(w200),len(w250))==(1519,600,600),'prior lineage row counts')
for r in w0:
 k=r.get('sourceKey') or key_by_hash.get(r['sourceKeySha256']);loc=r['locale']
 need(k is not None and stsha(source[k])==r['sourceTextSha256'],'W0-W199 source hash')
 need(stsha(catalogs[loc][k])==r['observedTargetSha256']==r['expectedTargetSha256'],'W0-W199 target hash')
 need(r['targetTextIncluded'] is False and r['matches'] is True,'W0-W199 hash-only row')
for r in w200:
 k=r.get('sourceKey') or key_by_hash.get(r['sourceKeySha256']);loc=r['locale']
 need(k is not None and stsha(source[k])==r['sourceTextSha256'],'W200 source hash')
 need(stsha(catalogs[loc][k])==r['observedTargetSha256']==r['finalTargetSha256'],'W200 final target hash')
 need(r['targetTextIncluded'] is False and r['matches'] is True,'W200 hash-only row')
for r in w250:
 k=r.get('sourceKey') or key_by_hash.get(r['sourceKeySha256']);loc=r['locale']
 need(k is not None and stsha(source[k])==r['sourceTextSha256'],'W250 source hash')
 need(stsha(catalogs[loc][k])==r['observedTargetSha256']==r['finalTargetSha256'],'W250 final target hash')
 need(r['targetTextIncluded'] is False and r['matches'] is True,'W250 hash-only row')
need(sum(r['priorHoldPreserved'] for r in w0)==312 and sum(r['priorHoldPreserved'] for r in w200)==12,'prior hold counts')
need(sum(r['disposition']=='applied-change' for r in w250)==42 and sum(r['disposition']=='preserved-current' for r in w250)==558,'W250 applied readbacks')
root=readj('prior-W250-root-adjudication-attestation.json')
need(root['applicationReadbackMatched'] is True and root['observedTargetSha256']==root['correctedTargetSha256'],'root adjudication readback')
need(root['evidenceSha256']==s['previousWindowAttestation']['w250RootSupplementSha256'],'root supplement SHA linkage')
final=readj('PR-attestation-final.json'); drift=readj('live-main-caller-drift-final.json')
need(final['result']=='PASS' and final['prBodyRequested'] is False and final['state']=='open' and final['draft'] is True and final['merged'] is False,'final PR attestation')
need((final['headSha'],final['headTree'],final['branchRefSha'],final['pullRefSha'])==(HEAD,TREE,HEAD,HEAD),'final head/ref pins')
need(final['liveMainSha']==drift['liveMainSha'] and final['liveMainTree']==drift['liveMainTree'],'final main drift linkage')
need(drift['exactHead']==HEAD and drift['exactTree']==TREE and drift['selectedLiteralTranslatorCallsitesChanged'] is False,'final caller drift pin')
b=readjl('selection-boundary.jsonl');need([r['sourceOrdinal'] for r in b]==[299,300,349,350],'selection boundary')
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':600,'sources':50,'locales':12,'callerFiles':len(pins['files']),'callerBackedKeys':readj('candidate-free-summary.json')['callerBackedKeys'],'callerlessKeys':len(readj('candidate-free-summary.json')['callerlessKeys']),'priorW0W199Rows':len(w0),'priorW0W199Holds':312,'priorW200Rows':len(w200),'priorW200Holds':12,'priorW250Rows':len(w250),'priorW250Applied':42,'priorW250Preserved':558},sort_keys=True))
