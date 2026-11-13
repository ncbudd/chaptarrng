#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
DEFAULT_REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w0-49-apply')
HEAD='daa578eaa0d1c252e969d1f5891a364b13d50ec0'
TREE='e0b306dc20596ad7004bdfb9ac2cc0a3021726c7'
TARGET_LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
DIRECT_FIELDS=('sourceKey','source_key','key','sourceId','source_id','id')
PLACEHOLDER_RE=re.compile(r'\{[^{}]+\}')
PROTECTED_RE=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
PROTECTED_BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
CODE_EXTS={'.js','.jsx','.ts','.tsx'}

def sha(b):return hashlib.sha256(b).hexdigest()
def sha_text(s):return sha(s.encode('utf-8'))
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def signature(s):return dict(sorted(collections.Counter(PLACEHOLDER_RE.findall(s)).items()))
def literals(s):
    return sorted(set(PROTECTED_RE.findall(s)) | (PROTECTED_BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def read_jsonl(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def fail(s):raise SystemExit('FAIL: '+s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-worktree',type=Path,default=DEFAULT_REPO);a=ap.parse_args();repo=a.source_worktree.resolve()
    if git(repo,'rev-parse','HEAD')!=HEAD:fail('source HEAD differs')
    if git(repo,'rev-parse','HEAD^{tree}')!=TREE:fail('source tree differs')
    if git(repo,'status','--porcelain=v1'):fail('source worktree is not clean')
    sel=json.loads((HERE/'source-selection.json').read_text(encoding='utf-8'))
    manifest=json.loads((HERE/'candidate-free-manifest.json').read_text(encoding='utf-8'))
    scan=json.loads((HERE/'prior-evidence-scan.json').read_text(encoding='utf-8'))
    caller_pins=json.loads((HERE/'caller-scan-file-pins.json').read_text(encoding='utf-8'))
    if sha((HERE/'prior-evidence-scan.json').read_bytes())!=sel['priorEvidenceScanSha256']:fail('prior evidence scan hash')
    if sel['exactHead']!=HEAD or sel['exactTree']!=TREE or sel['batch']!='W50-99':fail('source selection pin/batch')
    if len(sel['keys'])!=50 or sel['firstPosition']!=50 or sel['lastPosition']!=99:fail('selection size/position')
    if manifest['exactHead']!=HEAD or manifest['exactTree']!=TREE:fail('candidate manifest pin')
    if sha((HERE/'source-selection.json').read_bytes())!=manifest['sourceSelectionSha256']:fail('selection hash in manifest')
    prior_selection_bytes=(HERE/'prior-W0-49-source-selection.json').read_bytes()
    if sha(prior_selection_bytes)!=sel['priorBatch']['sourceSelectionSha256']:fail('prior W0 selection hash')
    old_sel=json.loads(prior_selection_bytes.decode('utf-8'))
    if scan['exactHead']!=HEAD or scan['exactTree']!=TREE or len(scan['files'])!=392:fail('prior scan pin or file count')
    identifiers=set(); scanned_rows=0
    for f in scan['files']:
        p=repo/f['path']; data=p.read_bytes()
        if sha(data)!=f['sha256'] or git(repo,'hash-object','--',f['path'])!=f['gitBlob']:fail('prior file pin '+f['path'])
        for line in data.splitlines():
            if not line.strip():continue
            row=json.loads(line);scanned_rows+=1
            if isinstance(row,dict):
                for field in DIRECT_FIELDS:
                    v=row.get(field)
                    if isinstance(v,str):identifiers.add(v)
    en_path=repo/'src/NzbDrone.Core/Localization/Core/en.json';en_bytes=en_path.read_bytes();en=json.loads(en_bytes);enkeys=list(en)
    uncovered=[k for k in enkeys if k not in identifiers]
    if uncovered[:50]!=old_sel['keys'] or uncovered[50:100]!=sel['keys']:fail('next 50 key selection not reproducible')
    if any(k in identifiers for k in sel['keys']):fail('selected key collides with historical direct identifier')
    if scanned_rows!=scan['rowCount']:fail('prior JSONL row count')
    if len(identifiers)!=scan['uniqueDirectIdentifiers']:fail('prior direct ID count')
    if sum(k in identifiers for k in enkeys)!=scan['coreIntersectionCount']:fail('prior Core intersection count')
    catalogs=manifest['catalogs'];parsed={}
    for loc,info in catalogs.items():
        data=(repo/info['path']).read_bytes();obj=json.loads(data)
        if sha(data)!=info['sha256'] or git(repo,'hash-object','--',info['path'])!=info['gitBlob']:fail('catalog file pin '+loc)
        if len(obj)!=4165 or set(obj)!=set(enkeys):fail('catalog key set '+loc)
        parsed[loc]=obj
    rows=read_jsonl(HERE/'candidate-free-cells.jsonl');callers=read_jsonl(HERE/'caller-context.jsonl')
    if len(rows)!=600 or len(callers)!=50:fail('candidate/caller row count')
    if sha((HERE/'candidate-free-cells.jsonl').read_bytes())!=manifest['candidateFreeCellsSha256']:fail('candidate-free cell hash')
    if sha((HERE/'caller-context.jsonl').read_bytes())!=manifest['callerContextSha256']:fail('caller context file hash')
    if len({(r['sourceKey'],r['locale']) for r in rows})!=600:fail('duplicate candidate cell')
    if [r['sourceKey'] for r in rows[::12]]!=sel['keys']:fail('candidate source order')
    if [r['locale'] for r in rows[:12]]!=TARGET_LOCALES:fail('target locale order')
    callermap={r['sourceKey']:r for r in callers};refs_total=0
    for c in callers:
        key=c['sourceKey'];pattern=re.compile(r"\btranslate\s*\(\s*(['\"])" + re.escape(key) + r"\1")
        canonical=json.dumps({'sourceKey':key,'callerRefs':c['callerRefs']},ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
        if sha(canonical.encode('utf-8').rstrip(b'\n'))!=c['callerContextSha256']:fail('caller context hash '+key)
        if c['callerReferenceCount']!=len(c['callerRefs']):fail('caller ref count '+key)
        refs_total+=len(c['callerRefs'])
        for ref in c['callerRefs']:
            p=repo/ref['path'];data=p.read_bytes();lines=data.decode('utf-8').splitlines();n=ref['line']
            if sha(data)!=ref['fileSha256'] or git(repo,'hash-object','--',ref['path'])!=ref['fileGitBlob']:fail('caller file pin '+ref['path'])
            if not 1<=n<=len(lines) or lines[n-1]!=ref['lineText'] or sha_text(lines[n-1])!=ref['lineSha256']:fail('caller line pin '+ref['path'])
            if not pattern.search(lines[n-1]):fail('caller direct translation match '+key)
    tracked=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z',HEAD,'--','frontend/src'])
    expected_paths=[]
    for ent in tracked.split(b'\0'):
        if not ent:continue
        meta,path=ent.split(b'\t',1);mode,kind,oid=meta.decode().split();name=path.decode()
        if kind=='blob' and Path(name).suffix in CODE_EXTS:expected_paths.append((name,oid))
    pin_map={x['path']:x for x in caller_pins['files']}
    if len(expected_paths)!=caller_pins['fileCount'] or set(pin_map)!={p for p,_ in expected_paths}:fail('caller scan source file inventory')
    for path,oid in expected_paths:
        data=(repo/path).read_bytes();pin=pin_map[path]
        if pin['gitBlob']!=oid or pin['sha256']!=sha(data):fail('caller scan file pin '+path)
    for r in rows:
        key,loc=r['sourceKey'],r['locale']
        if key not in sel['keys'] or loc not in TARGET_LOCALES:fail('candidate key/locale')
        if r['sourceText']!=en[key] or r['sourceTextSha256']!=sha_text(en[key]):fail('source text '+key)
        target=parsed[loc][key]
        if r['currentTarget']!=target or r['currentTargetSha256']!=sha_text(target):fail('current target '+key+'/'+loc)
        if r['sourcePlaceholders']!=signature(r['sourceText']) or r['currentPlaceholders']!=signature(r['currentTarget']):fail('placeholder signatures '+key+'/'+loc)
        if r['protectedLiterals']!=literals(r['sourceText']):fail('protected literal source set '+key)
        if r['currentProtectedLiteralsPresent']!=all(x in target for x in r['protectedLiterals']):fail('protected literal status '+key+'/'+loc)
        ctx=callermap[key]
        if r['callerContextSha256']!=ctx['callerContextSha256'] or r['callerReferenceCount']!=ctx['callerReferenceCount'] or r['callerRefs']!=ctx['callerRefs']:fail('candidate caller context '+key+'/'+loc)
        forbidden=('candidate','suggestion','recommended','finalReviewed','disposition','decisionRationale')
        if any(x in r for x in forbidden):fail('candidate-free cell contains review field')
    result={'result':'PASS','exactHead':HEAD,'exactTree':TREE,'cells':600,'sourceKeys':50,'targetLocales':12,'historicalWindowJsonlFiles':len(scan['files']),'historicalJsonlRows':scanned_rows,'historicalUniqueIdentifiers':len(identifiers),'historicalCoreIntersection':scan['coreIntersectionCount'],'priorDirectOverlap':0,'placeholderSignaturesRecorded':True,'protectedLiteralChecksRecorded':True,'candidateSuggestionFieldsAbsent':True,'frontendFilesScanned':len(expected_paths),'callerReferences':refs_total,'catalogFilesPinned':len(catalogs),'repositoryClean':True}
    (HERE/'candidate-free-verification.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
