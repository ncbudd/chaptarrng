#!/usr/bin/env python3
from __future__ import annotations
import collections, datetime, hashlib, json, os, re, subprocess
from pathlib import Path

ROOT = Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w0-49-apply')
OUT = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w50-99-primary-20261104')
EXPECTED_HEAD = 'daa578eaa0d1c252e969d1f5891a364b13d50ec0'
EXPECTED_TREE = 'e0b306dc20596ad7004bdfb9ac2cc0a3021726c7'
PR_NUM = 190
BRANCH = 'codex/chaptarrng-localization-complete-20261031'
PREVIOUS_PACKET = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w0-49-cross-audit-20261104/input/candidate-primary')
PREVIOUS_SELECTION = PREVIOUS_PACKET / 'source-selection.json'
PRIOR_SEMANTIC_MANIFEST = PREVIOUS_PACKET / 'candidate-free-manifest.json'
TARGET_LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
LOCALE_FILES = {'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
DIRECT_FIELDS = ('sourceKey','source_key','key','sourceId','source_id','id')
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')
PROTECTED_RE = re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
PROTECTED_BRANDS = {'Chaptarr','ChaptarrNG','AudioBookShelf'}
CODE_EXTS = {'.js','.jsx','.ts','.tsx'}

def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha_text(s: str) -> str: return sha(s.encode('utf-8'))
def git_blob(path: str) -> str: return git('hash-object','--',path)
def json_bytes(obj) -> bytes: return (json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
def write_json(path: Path,obj): path.write_bytes((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'))
def write_jsonl(path: Path,rows): path.write_bytes(b''.join(json_bytes(r) for r in rows))
def signature(s: str) -> dict: return dict(sorted(collections.Counter(PLACEHOLDER_RE.findall(s)).items()))
def protected_literals(s: str) -> list[str]:
    found=set(PROTECTED_RE.findall(s)) | (PROTECTED_BRANDS & set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*\b",s)))
    return sorted(x for x in found if x in s)
def run_json(args): return json.loads(subprocess.check_output(args,text=True))

assert git('rev-parse','HEAD') == EXPECTED_HEAD
tree=git('rev-parse','HEAD^{tree}')
assert tree == EXPECTED_TREE
assert git('status','--porcelain=v1') == ''
pr=run_json(['gh','pr','view',str(PR_NUM),'--repo','snapetech-org/chaptarrng','--json','state,isDraft,headRefOid,headRefName,url'])
assert pr['state']=='OPEN' and pr['isDraft'] is True and pr['headRefOid']==EXPECTED_HEAD and pr['headRefName']==BRANCH,pr
remote=git('ls-remote','origin',f'refs/heads/{BRANCH}').split('\t')[0]
assert remote==EXPECTED_HEAD,remote
live_tree=run_json(['gh','api',f'repos/snapetech-org/chaptarrng/git/commits/{EXPECTED_HEAD}'])['tree']['sha']
assert live_tree==EXPECTED_TREE,live_tree
attestation={
 'attestedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
 'repository':'snapetech-org/chaptarrng','prNumber':PR_NUM,'prUrl':pr['url'],
 'state':pr['state'],'isDraft':pr['isDraft'],'headRefName':pr['headRefName'],
 'exactHead':pr['headRefOid'],'exactTree':live_tree,'remoteBranchHead':remote,
 'localWorktree':str(ROOT),'localStatus':'clean','result':'PASS'
}
write_json(OUT/'PR-attestation-before.json',attestation)

# Reattest earlier candidate-free source packet and ordered W0 selection.
old_sel=json.loads(PREVIOUS_SELECTION.read_text(encoding='utf-8'))
old_sel_bytes=PREVIOUS_SELECTION.read_bytes()
old_manifest=json.loads(PRIOR_SEMANTIC_MANIFEST.read_text(encoding='utf-8'))
assert old_sel['exactHead']=='7f5d99e24b054cf1437d135328c3dee565e6b318'
assert old_sel['exactTree']=='d39f2fe8cf91a39653679980c0832c5ca400a114'
assert old_sel['keyCount']==50 and old_sel['firstPosition']==0 and old_sel['lastPosition']==49
assert sha(old_sel_bytes)==old_manifest['sourceSelectionSha256']

# Pin and inspect every historical window JSONL from this exact source tree.
listing=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','-z',EXPECTED_HEAD,'--','docs/pr-evidence/pr190-localization-2026-11-02'],text=False)
scan_files=[]
for entry in listing.split(b'\0'):
    if not entry: continue
    meta,raw_path=entry.split(b'\t',1)
    mode,kind,oid=meta.decode().split()
    path=raw_path.decode()
    if kind=='blob' and '/window-' in path and path.endswith('.jsonl'):
        data=(ROOT/path).read_bytes()
        assert git_blob(path)==oid
        scan_files.append({'path':path,'gitBlob':oid,'sha256':sha(data),'rows':sum(1 for line in data.splitlines() if line.strip())})
scan_files.sort(key=lambda x:x['path'])
assert len(scan_files)==392,len(scan_files)
identifiers=set(); row_count=0; malformed=0
for f in scan_files:
    for line in (ROOT/f['path']).read_bytes().splitlines():
        if not line.strip(): continue
        try: row=json.loads(line); row_count+=1
        except Exception: malformed+=1; continue
        if isinstance(row,dict):
            for field in DIRECT_FIELDS:
                value=row.get(field)
                if isinstance(value,str): identifiers.add(value)
assert malformed==0
source_rel='src/NzbDrone.Core/Localization/Core/en.json'
source_path=ROOT/source_rel
source_bytes=source_path.read_bytes()
source_catalog=json.loads(source_bytes)
source_keys=list(source_catalog.keys())
source_sha=sha(source_bytes)
source_blob=git_blob(source_rel)
assert source_sha==old_sel['catalogSha256']
prior_keys=[k for k in source_keys if k in identifiers]
uncovered=[k for k in source_keys if k not in identifiers]
assert len(prior_keys)==1212
assert uncovered[:50]==old_sel['keys']
assert len(uncovered)>=100
keys=uncovered[50:100]
assert len(keys)==50
prior_window_matches=sorted(k for k in keys if k in identifiers)
assert prior_window_matches==[]
core_keys=set(source_keys)
semantic_core_count=old_manifest['counts']['priorDirectCoreKeyCount']
assert semantic_core_count==1160
source_selection={
 'packet':'ChaptarrNG PR #190 full-Core W50-99 candidate-free input selection',
 'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'createdOnHost':'kspld0',
 'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
 'repository':'snapetech-org/chaptarrng','prNumber':PR_NUM,'prState':'OPEN','prIsDraft':True,
 'repoBranch':BRANCH,'repoWorktree':str(ROOT),'repoStatus':'clean',
 'catalogPath':source_rel,'catalogSha256':source_sha,'catalogGitBlob':source_blob,'catalogKeyCount':len(source_keys),
 'catalogOrder':'English Core JSON insertion order after excluding every key directly named in the exact-head historical window JSONL scan.',
 'batch':'W50-99','firstPosition':50,'lastPosition':99,'keyCount':50,'localeCount':len(TARGET_LOCALES),
 'targetLocales':TARGET_LOCALES,'keys':keys,'overlapCoreKeys':prior_window_matches,
 'priorBatch':{'batch':'W0-49','sourceSelectionSha256':sha(old_sel_bytes),'keys':old_sel['keys']},
 'priorHistoricalScan':{
   'pathPrefix':'docs/pr-evidence/pr190-localization-2026-11-02/window-*','fileCount':len(scan_files),
   'rowCount':row_count,'directIdentifierFields':list(DIRECT_FIELDS),
   'uniqueDirectIdentifiers':len(identifiers),'coreIntersectionCount':len(prior_keys),
   'semanticDispositionCoreKeyCount':semantic_core_count,
   'semanticDispositionFileCount':old_manifest['counts']['priorSemanticLedgerFiles'],
   'semanticDispositionRowCount':old_manifest['counts']['priorSemanticDecisionRows'],
   'note':'The broader exact-identifier scan spans all 392 window JSONL files; the 1,160 semantic disposition count is the narrower prior review manifest count. They are recorded separately. W0 keys exactly match the first 50 source-order keys absent from the broader identifier set.'},
 'priorEvidenceScanManifest':'prior-evidence-scan.json',
 'priorEvidenceScanSha256':None,
 'priorWindowJsonlDirectRequestedKeyRowCount':0,
 'priorWindowJsonlDirectRequestedKeyMatches':[],
 'selectionMethod':'Verify W0-49 is the first 50 uncovered English Core insertion-order keys under the historical identifier scan; select the next 50 from the same ordered uncovered list. Candidate selection checked no direct identifier collision in the scanned history.',
 'sourceSelectionSha256':None
}
scan_manifest={'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'files':scan_files,'fileCount':len(scan_files),'rowCount':row_count,'directIdentifierFields':list(DIRECT_FIELDS),'uniqueDirectIdentifiers':len(identifiers),'coreIntersectionCount':len(prior_keys),'w0SelectedKeysDirectlyMentioned':sorted(set(old_sel['keys']) & identifiers),'w50SelectedKeysDirectlyMentioned':prior_window_matches}
assert not scan_manifest['w0SelectedKeysDirectlyMentioned']
write_json(OUT/'prior-evidence-scan.json',scan_manifest)
source_selection['priorEvidenceScanSha256']=sha((OUT/'prior-evidence-scan.json').read_bytes())
write_json(OUT/'source-selection.json',source_selection)
source_selection['sourceSelectionSha256']=sha((OUT/'source-selection.json').read_bytes())
# The manifest binds the source-selection file hash; avoid self-referential hash field.
source_selection.pop('sourceSelectionSha256')
write_json(OUT/'source-selection.json',source_selection)
selection_sha=sha((OUT/'source-selection.json').read_bytes())

# Pin source and every locale catalog and validate insertion-order parity.
catalogs={}
parsed_catalogs={}
for loc,path_name in [('en','en.json'),*[(loc,LOCALE_FILES[loc]) for loc in TARGET_LOCALES]]:
    rel=f'src/NzbDrone.Core/Localization/Core/{path_name}'
    raw=(ROOT/rel).read_bytes()
    parsed=json.loads(raw)
    assert set(parsed.keys())==set(source_keys) and len(parsed)==len(source_keys),(loc,'key set mismatch')
    catalogs[loc]={'path':rel,'sha256':sha(raw),'gitBlob':git_blob(rel),'keyCount':len(parsed),'keySetMatchesEnglish':True}
    parsed_catalogs[loc]=parsed

# Pin all candidate source and caller files from tracked frontend/src sources.
frontend_listing=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','-z',EXPECTED_HEAD,'--','frontend/src'],text=False)
frontend_files=[]
for entry in frontend_listing.split(b'\0'):
    if not entry: continue
    meta,raw_path=entry.split(b'\t',1); mode,kind,oid=meta.decode().split(); path=raw_path.decode()
    if kind=='blob' and Path(path).suffix in CODE_EXTS:
        data=(ROOT/path).read_bytes(); assert git_blob(path)==oid
        frontend_files.append((path,oid,data))
frontend_files.sort(key=lambda x:x[0])
assert frontend_files
caller_scan_pins=[{'path':p,'gitBlob':oid,'sha256':sha(data)} for p,oid,data in frontend_files]
pattern_cache={key:re.compile(r"\btranslate\s*\(\s*(['\"])"+re.escape(key)+r"\1") for key in keys}
callers_by_key={}
for key,pattern in pattern_cache.items():
    refs=[]
    for path,oid,data in frontend_files:
        lines=data.decode('utf-8').splitlines()
        for i,line in enumerate(lines):
            matches=list(pattern.finditer(line))
            for _ in matches:
                refs.append({
                    'path':path,'line':i+1,'lineText':line,'lineSha256':sha_text(line),
                    'contextBefore':lines[max(0,i-2):i],
                    'contextAfter':lines[i+1:i+4],
                    'fileSha256':sha(data),'fileGitBlob':oid
                })
    refs.sort(key=lambda r:(r['path'],r['line']))
    context_obj={'sourceKey':key,'callerRefs':refs}
    context_hash=sha(json_bytes(context_obj).rstrip(b'\n'))
    callers_by_key[key]={'sourceKey':key,'callerContextSha256':context_hash,'callerReferenceCount':len(refs),'callerRefs':refs}
write_jsonl(OUT/'caller-context.jsonl',[callers_by_key[k] for k in keys])
caller_file_hash=sha((OUT/'caller-context.jsonl').read_bytes())

# Build candidate-free cells, in source ordinal then locale order.
rows=[]
for ki,key in enumerate(keys):
    source_text=source_catalog[key]
    context=callers_by_key[key]
    literals=protected_literals(source_text)
    for loc in TARGET_LOCALES:
        target_rel=catalogs[loc]['path']; target_text=parsed_catalogs[loc][key]
        present=all(lit in target_text for lit in literals)
        rows.append({
            'batch':'W50-99','sourceOrdinal':50+ki,'sourceKey':key,'locale':loc,
            'sourceText':source_text,'sourceTextSha256':sha_text(source_text),
            'currentTarget':target_text,'currentTargetSha256':sha_text(target_text),
            'sourceFile':source_rel,'sourceFileSha256':source_sha,'sourceFileGitBlob':source_blob,
            'targetFile':target_rel,'targetFileSha256':catalogs[loc]['sha256'],'targetFileGitBlob':catalogs[loc]['gitBlob'],
            'sourcePlaceholders':signature(source_text),'currentPlaceholders':signature(target_text),
            'protectedLiterals':literals,'currentProtectedLiteralsPresent':present,
            'callerContextSha256':context['callerContextSha256'],'callerReferenceCount':context['callerReferenceCount'],
            'callerRefs':context['callerRefs']
        })
write_jsonl(OUT/'candidate-free-cells.jsonl',rows)
cell_hash=sha((OUT/'candidate-free-cells.jsonl').read_bytes())
manifest={
 'packet':'ChaptarrNG PR #190 full-Core W50-99 candidate-free inputs',
 'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'repoBranch':BRANCH,'repoWorktree':str(ROOT),'repoStatus':'clean','createdOnHost':'kspld0',
 'batch':'W50-99','sourceSelectionSha256':selection_sha,
 'candidateFreeCellsSha256':cell_hash,'callerContextSha256':caller_file_hash,
 'candidateFree':'candidate-free-cells.jsonl contains no suggested wording or decision fields.',
 'placeholderRule':'Placeholder counters are recorded exactly; any mismatch must be addressed or explicitly held during review.',
 'protectedLiteralRule':'Technical/product literals identified from source text must retain exact spelling and case in recommended targets.',
 'counts':{'cells':len(rows),'sourceKeys':len(keys),'keysUncovered':len(keys),'locales':len(TARGET_LOCALES),'keyCountEnglishCore':len(source_keys),'priorDirectCoreKeyCountBroadScan':len(prior_keys),'priorDirectCoreKeyCountSemanticDisposition':semantic_core_count,'overlapCoreKeys':len(prior_window_matches)},
 'catalogs':catalogs,
 'callerScan':{'pathPrefix':'frontend/src','fileCount':len(frontend_files),'fileExtensionAllowlist':sorted(CODE_EXTS),'method':'Exact direct `translate(<string literal key>)` argument matching; line references include two preceding and three following lines.'},
 'callerScanFilesSha256':sha(json_bytes(caller_scan_pins)),
 'priorEvidenceScanSha256':sha((OUT/'prior-evidence-scan.json').read_bytes())
}
write_json(OUT/'candidate-free-manifest.json',manifest)
write_json(OUT/'caller-scan-file-pins.json',{'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'fileCount':len(caller_scan_pins),'files':caller_scan_pins})
readme=f'''# ChaptarrNG PR #190 W50–W99 candidate-free input\n\nPinned to live PR head `{EXPECTED_HEAD}` and tree `{EXPECTED_TREE}` at creation. The PR was OPEN/DRAFT and the remote branch pointed to the same head. This packet covers the next 50 uncovered English Core insertion-order keys and all 12 target locales (600 cells).\n\n`candidate-free-cells.jsonl` contains source text, current catalog text, source/current hashes, exact catalog pins, placeholder and protected-literal signatures, plus direct frontend translation caller context. It contains no suggested wording or review dispositions. `caller-context.jsonl` and `caller-scan-file-pins.json` preserve the caller scan evidence. `prior-evidence-scan.json` pins all 392 historical window JSONL files and records the exact identifier scan. `source-selection.json` documents why this is the next W50–W99 block.\n\nSelection was rederived against the historical window evidence at the exact head. The W0–W49 block in the prior candidate-free packet exactly matched the first 50 uncovered keys under the same scan; these keys are positions 50–99. The broader historical scan intersects 1,212 English Core keys; the earlier semantic-disposition manifest separately reports 1,160 direct Core keys from 102 review files, so both counts are preserved without conflating them.\n\nNo repository files were modified. Primary review recommendations are separate and do not authorize catalog changes. All cells remain pending native-speaker review.\n'''
(OUT/'README-candidate-free.md').write_text(readme,encoding='utf-8')
print(json.dumps({'result':'PASS','exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'candidateCells':len(rows),'sourceKeys':len(keys),'targetLocales':len(TARGET_LOCALES),'historicalWindowJsonlFiles':len(scan_files),'historicalJsonlRows':row_count,'historicalDirectIdentifiers':len(identifiers),'historicalCoreIntersection':len(prior_keys),'frontendFilesScanned':len(frontend_files),'callerRefs':sum(c['callerReferenceCount'] for c in callers_by_key.values()),'keysWithCaller':sum(c['callerReferenceCount']>0 for c in callers_by_key.values()),'placeholderMismatches':sum(r['sourcePlaceholders']!=r['currentPlaceholders'] for r in rows),'protectedLiteralMisses':sum(not r['currentProtectedLiteralsPresent'] for r in rows),'sourceKeysSelected':keys},ensure_ascii=False,sort_keys=True))
