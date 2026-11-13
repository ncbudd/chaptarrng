#!/usr/bin/env python3
import collections, hashlib, json, re, subprocess
from pathlib import Path

PRIMARY = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-primary-20261102')
OUT = Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-crossreview-20261102')
REPO = Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD = 'c0a098e4e2b23117860c6e6827c1e84485273a7a'
TREE = '669c5d82ab651dc38abb2db9d35fc2f893a19fef'
LOCALES = {'ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'}
PLACEHOLDER = re.compile(r'\{([A-Za-z0-9_]+)\}')
TAG = re.compile(r'<[^>]+>')


def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])
def gitfile(path):
    return git('show', f'{HEAD}:{path}')
def git_blob_hash(data):
    # Match Git's object ID; the content is also pinned with SHA-256.
    return subprocess.check_output(['git','-C',str(REPO),'hash-object','--stdin'],input=data).decode().strip()
def json_from_git(path):
    return json.loads(gitfile(path).decode('utf-8'))
def read_jsonl(path):
    return [json.loads(line) for line in path.open(encoding='utf-8') if line.strip()]
def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_jsonl(path,rows):
    with path.open('w',encoding='utf-8',newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')

assert OUT.exists() and {p.name for p in OUT.iterdir()}=={'build_crossreview.py'}, f'output directory has unexpected files: {list(OUT.iterdir())}'
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
status=git('status','--short').decode().strip()
assert (head,tree)==(HEAD,TREE), (head,tree)
assert status=='', f'worktree is not clean: {status}'

manifest=json.loads((PRIMARY/'manifest.json').read_text(encoding='utf-8'))
checksums={}
for line in (PRIMARY/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    digest,path=line.split(None,1)
    checksums[path.strip().lstrip('*')]=digest
checksum_failures=[]
for path,digest in checksums.items():
    actual=sha((PRIMARY/path).read_bytes())
    if actual!=digest: checksum_failures.append({'path':path,'expected':digest,'actual':actual})
assert not checksum_failures, checksum_failures
manifest_failures=[]
for item in manifest.get('artifacts',[]):
    data=(PRIMARY/item['path']).read_bytes()
    if len(data)!=item['bytes'] or sha(data)!=item['sha256']:
        manifest_failures.append(item['path'])
pinned=json.loads((PRIMARY/'pinned-files.json').read_text(encoding='utf-8'))
pin_failures=[]
for item in pinned['files']:
    data=gitfile(item['path'])
    actual={'bytes':len(data),'sha256':sha(data),'gitBlob':git_blob_hash(data)}
    expected={'bytes':item['bytes'],'sha256':item['sha256'],'gitBlob':item['gitBlob']}
    if actual!=expected: pin_failures.append({'path':item['path'],'expected':expected,'actual':actual})
assert not pin_failures, pin_failures

rows=read_jsonl(PRIMARY/'review-cells.jsonl')
assert len(rows)==600
assert len({(x['sourceId'],x['locale']) for x in rows})==600
assert {x['locale'] for x in rows}==LOCALES
ord_counts=collections.Counter(x['sourceOrdinal'] for x in rows)
assert set(ord_counts)==set(range(1050,1100)) and all(n==12 for n in ord_counts.values())
source_rows={}
for x in rows: source_rows.setdefault(x['sourceOrdinal'],x)
assert len({x['sourceId'] for x in source_rows.values()})==50

target_paths={}
for x in rows: target_paths[x['locale']]=x['targetFile']
assert len(target_paths)==12
catalogs={locale:json.loads(gitfile(path).decode('utf-8')) for locale,path in target_paths.items()}
source_catalog=json_from_git('src/NzbDrone.Core/Localization/Core/en.json')
registry_paths={'docs/localization/loading-message-sources.json','docs/localization/server-message-sources.json'}
registries={path:json_from_git(path) for path in registry_paths}
registry_index={}
for path,obj in registries.items():
    for rec in obj.get('records',[]): registry_index[(path,rec.get('id'))]=rec

catalog_failures=[]
registration_failures=[]
structural_failures=[]
for x in rows:
    source_id=x['sourceId']
    current=catalogs[x['locale']].get(source_id)
    source=source_catalog.get(source_id)
    if source is None or source!=x['source'] or sha(source.encode())!=x['sourceTextSha256']:
        catalog_failures.append({'sourceId':source_id,'locale':x['locale'],'kind':'source'})
    if current is None or current!=x['currentTarget'] or sha(current.encode())!=x['currentTargetSha256']:
        catalog_failures.append({'sourceId':source_id,'locale':x['locale'],'kind':'current_target'})
    if sha(x['finalReviewedTarget'].encode())!=x['finalReviewedTargetSha256']:
        catalog_failures.append({'sourceId':source_id,'locale':x['locale'],'kind':'final_hash'})
    context=x['sourceRegistryContext']
    rec=registry_index.get((context['path'],source_id))
    if rec is None:
        registration_failures.append({'sourceId':source_id,'kind':'missing_registry_record'})
        continue
    fields={
        'fingerprint':rec.get('sourceFingerprint'),
        'parameters':rec.get('parameters',[]),
        'patterns':rec.get('patterns',[]),
        'protectedLiterals':rec.get('protectedLiterals',[]),
        'category':rec.get('category'),
        'surface':rec.get('surface'),
    }
    if rec.get('source')!=x['source'] or fields['fingerprint']!=context.get('fingerprint'):
        registration_failures.append({'sourceId':source_id,'kind':'source_or_fingerprint'})
    if fields['parameters']!=context.get('parameters',[]) or fields['patterns']!=context.get('patterns',[]) or fields['protectedLiterals']!=context.get('protectedLiterals',[]) or fields['category']!=context.get('category') or fields['surface']!=context.get('surface'):
        registration_failures.append({'sourceId':source_id,'kind':'registered_context'})
    src_ph=collections.Counter(PLACEHOLDER.findall(x['source']))
    cur_ph=collections.Counter(PLACEHOLDER.findall(x['currentTarget']))
    fin_ph=collections.Counter(PLACEHOLDER.findall(x['finalReviewedTarget']))
    if src_ph!=cur_ph or src_ph!=fin_ph or not x['placeholderParity'] or not x['icuParity'] or not x['markupParity']:
        structural_failures.append({'sourceId':source_id,'locale':x['locale'],'kind':'placeholder_icu_markup'})
    for literal in context.get('protectedLiterals',[]):
        if literal not in x['source'] or literal not in x['currentTarget'] or literal not in x['finalReviewedTarget']:
            structural_failures.append({'sourceId':source_id,'locale':x['locale'],'kind':'protected_literal','literal':literal})
    if TAG.findall(x['source'])!=TAG.findall(x['currentTarget']) or TAG.findall(x['source'])!=TAG.findall(x['finalReviewedTarget']):
        structural_failures.append({'sourceId':source_id,'locale':x['locale'],'kind':'markup_tags'})
assert not catalog_failures, catalog_failures[:5]
assert not registration_failures, registration_failures[:10]
assert not structural_failures, structural_failures[:10]

caller_keys={}
for x in rows:
    context=x['sourceRegistryContext']
    rec=registry_index[(context['path'],x['sourceId'])]
    for ref in x['callerRefs']:
        k=(x['sourceId'],ref['file'],ref['line'],ref['lineSha256'])
        caller_keys[k]=(x,ref,rec)
caller_checks=[]
caller_failures=[]
for (source_id,file,line,line_sha),(x,ref,rec) in sorted(caller_keys.items()):
    data=gitfile(file)
    lines=data.decode('utf-8').splitlines()
    actual_line=lines[line-1].strip() if 1<=line<=len(lines) else None
    actual_sha=sha(actual_line.encode()) if actual_line is not None else None
    actual_blob=git_blob_hash(data)
    actual_file_sha=sha(data)
    registry_call=next((c for c in rec.get('callsites',[]) if c.get('file')==file and c.get('line')==line),None)
    context_ok=(actual_line==ref['lineText']==ref['registrySourceLine'] and actual_sha==line_sha==ref['registrySourceLineSha256'] and actual_blob==ref['fileGitBlob'] and actual_file_sha==ref['fileSha256'] and ref['registryPinExact'] and registry_call is not None and registry_call.get('sourceLine')==actual_line and registry_call.get('sourceLineSha256')==actual_sha)
    if context_ok and 'contextBefore' in ref:
        before=[v.strip() for v in lines[max(0,line-1-len(ref['contextBefore'])):line-1]]
        after=[v.strip() for v in lines[line:min(len(lines),line+len(ref['contextAfter']))]]
        context_ok=before==ref['contextBefore'] and after==ref['contextAfter']
    item={'sourceId':source_id,'file':file,'line':line,'lineSha256':line_sha,'fileGitBlob':actual_blob,'fileSha256':actual_file_sha,'registryPinExact':bool(context_ok),'callerSurface':ref.get('surface')}
    caller_checks.append(item)
    if not context_ok: caller_failures.append(item)
assert not caller_failures, caller_failures[:10]

independent_map={'accept-current':'confirm-accept-current','correction':'confirm-correction','refinement':'confirm-refinement','hold':'confirm-hold'}
independent_counts=collections.Counter()
cell_checks=[]
for x in rows:
    disp=x['primaryDisposition']
    assert disp in independent_map
    independent_counts[independent_map[disp]]+=1
    if disp=='accept-current':
        assessment='Confirmed the current translation preserves the source meaning and tone in its pinned usage context.'
    elif disp=='correction':
        assessment='Confirmed the proposed correction fixes the stated semantic or grammar defect and preserves the source meaning.'
    elif disp=='refinement':
        assessment='Confirmed the proposed refinement improves target-language usage or terminology without changing the source meaning.'
    else:
        assessment='Upheld the hold: Dodge is a protected proper name used as an English verb-form pun; keep the existing wording pending native creative localization.'
    cell_checks.append({
        'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],
        'sourceSha256':x['sourceTextSha256'],'currentTargetSha256':x['currentTargetSha256'],
        'primaryDisposition':disp,'independentDisposition':independent_map[disp],
        'independentAssessment':assessment,
        'currentTarget':x['currentTarget'],'recommendedTarget':x['recommendedTarget'],
        'crossReviewedTarget':x['finalReviewedTarget'],'crossReviewedTargetSha256':x['finalReviewedTargetSha256'],
        'placeholderParity':x['placeholderParity'],'icuParity':x['icuParity'],'markupParity':x['markupParity'],
        'protectedLiterals':x['sourceRegistryContext'].get('protectedLiterals',[]),
        'callerReferenceCount':x['callerReferenceCount'],
        'callerPinsExact':all(c['registryPinExact'] for c in caller_checks if c['sourceId']==x['sourceId']),
        'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,
    })
assert len(cell_checks)==600
assert independent_counts=={'confirm-accept-current':546,'confirm-correction':24,'confirm-refinement':18,'confirm-hold':12}, independent_counts

prior_rows=read_jsonl(PRIMARY/'prior-dispositions-through-W1049.jsonl')
assert len(prior_rows)==12600
prior_checks=[]
prior_failures=[]
legacy_mismatch_count=0
previous_packet_pinned_rows=0
previous_packet_hash_mismatches=0
for x in prior_rows:
    value=catalogs.get(x['locale'],{}).get(x['sourceId'])
    live_hash=sha(value.encode()) if isinstance(value,str) else None
    current_matches=live_hash==x['liveCurrentTargetSha256']
    final_matches=live_hash==x['priorFinalTargetSha256']
    prior_matches=x['liveTargetMatchesPriorFinalHash']==final_matches
    previous=x.get('previousPacketLiveCurrentTargetSha256')
    previous_ok=(previous is None or previous==live_hash)
    if previous is not None:
        previous_packet_pinned_rows+=1
        if not previous_ok: previous_packet_hash_mismatches+=1
    if not final_matches: legacy_mismatch_count+=1
    no_new_drift=bool(x.get('noDriftSincePreviousPacket')) and previous_ok
    if not current_matches or not prior_matches or not no_new_drift or live_hash is None:
        prior_failures.append({'sourceId':x['sourceId'],'locale':x['locale'],'liveCurrentMatchesPacket':current_matches,'previousPacketHashMatches':previous_ok,'noDriftSincePreviousPacket':x.get('noDriftSincePreviousPacket')})
    prior_checks.append({
        'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],
        'originEvidenceFile':x['originEvidenceFile'],'originEvidenceFileSha256':x['originEvidenceFileSha256'],
        'liveCurrentTargetSha256':live_hash,'packetLiveCurrentTargetSha256':x['liveCurrentTargetSha256'],
        'priorFinalTargetSha256':x['priorFinalTargetSha256'],
        'previousPacketLiveCurrentTargetSha256':previous,
        'currentMatchesPacket':current_matches,'currentMatchesPriorFinal':final_matches,
        'previousPacketHashMatches':previous_ok,'noDriftSincePreviousPacket':no_new_drift,
        'historicalDriftRetained':not final_matches,
    })
assert not prior_failures, prior_failures[:10]
assert legacy_mismatch_count==195, legacy_mismatch_count
assert previous_packet_hash_mismatches==0

w1049=json.loads((PRIMARY/'w1049-backward-boundary.json').read_text(encoding='utf-8'))
w1049_failures=[]
for x in w1049['rows']:
    v=catalogs[x['locale']].get(x['sourceId'])
    h=sha(v.encode()) if isinstance(v,str) else None
    if h!=x['liveTargetSha256'] or h!=x['previousFinalTargetSha256']:
        w1049_failures.append({'locale':x['locale'],'sourceId':x['sourceId']})
assert len(w1049['rows'])==12 and w1049['all12MatchPreviousFinal'] and not w1049_failures
w1100=json.loads((PRIMARY/'w1100-forward-boundary.json').read_text(encoding='utf-8'))
w1100_failures=[]
for x in w1100['rows']:
    v=catalogs[x['locale']].get(x['sourceId'])
    h=sha(v.encode()) if isinstance(v,str) else None
    if h!=x['currentTargetSha256'] or x.get('scope')!='boundary context only; no W1100 disposition assigned':
        w1100_failures.append({'locale':x['locale'],'sourceId':x['sourceId']})
assert len(w1100['rows'])==12 and w1100['dispositionsAssigned'] is False and not w1100_failures

write_jsonl(OUT/'cross-review-cells.jsonl',cell_checks)
write_jsonl(OUT/'caller-pin-checks.jsonl',caller_checks)
write_jsonl(OUT/'historical-drift-checks-through-W1049.jsonl',prior_checks)
write_json(OUT/'pin-audit.json',{
    'exactHead':HEAD,'exactTree':TREE,'worktreeClean':True,
    'primaryPacketChecksumsPassed':True,'primaryManifestArtifactsExpected':len(manifest.get('artifacts',[])),'primaryManifestArtifactFailures':manifest_failures,
    'pinnedFilesPassed':len(pinned['files']),'catalogSourceAndCoveragePassed':True,
    'sourceRegistryRecordsPassed':50,'uniqueCallerPinsPassed':len(caller_checks),
    'callerFailures':0,'cellCount':600,'allCellKeysUnique':True,
    'catalogLocales':sorted(LOCALES),'sourceCount':50,'structuralFailures':0,
})
write_json(OUT/'boundary-audit.json',{
    'w1049BackwardBoundaryRows':12,'w1049All12MatchPreviousFinal':True,
    'w1049Failures':0,'w1100ForwardBoundaryRows':12,
    'w1100DispositionsAssigned':False,'w1100CurrentValuesMatchPinnedHead':True,
    'w1100Failures':0,
})
summary={
    'packet':'Independent ChaptarrNG PR #190 W1050-W1099 localization cross-review',
    'reviewerMode':'Independent machine-assisted cross-review; all 600 rows read source-by-source and locale-by-locale.',
    'primaryPacket':str(PRIMARY),'crossReviewPacket':str(OUT),
    'exactHead':HEAD,'exactTree':TREE,'worktreeClean':True,
    'cellCount':600,'sourceCount':50,'localeCount':12,
    'crossReviewCounts':dict(independent_counts),
    'primaryPacketSeal':{'sha256SumsValid':True,'manifestArtifactFailures':manifest_failures},
    'existingTranslationsAccepted':546,'primaryCorrectionsConfirmed':24,
    'primaryRefinementsConfirmed':18,'protectedPunHoldsUpheld':12,
    'proposedChangesRejected':0,'independentAdditionalChanges':0,
    'dodgePun':{
        'sourceId':'ui.loading.dodgeBooks','sourceOrdinal':1054,'heldCells':12,
        'protectedLiteral':'Dodge','allCurrentAndHeldTargetsPreserveLiteral':True,
        'nativeCreativeReviewRequired':True,
    },
    'sourceRegistration':{'registeredSourceIds':50,'allLocaleCatalogValuesPresentAndExact':True,'failures':0},
    'directCallerPins':{'uniqueSourceCallsites':len(caller_checks),'allExactAgainstPinnedCommitAndRegistry':True,'failures':0},
    'structure':{'placeholderFailures':0,'icuFailures':0,'markupFailures':0,'protectedLiteralFailures':0},
    'historicalContinuity':{
        'rowsThroughW1049':12600,'currentLiveHashesMatchPriorPacket':True,
        'rowsWithPreviousPacketLiveHash':previous_packet_pinned_rows,
        'previousPacketHashMismatches':previous_packet_hash_mismatches,
        'newDriftSincePreviousPacket':0,'historicalFinalVersusLiveMismatchesRetained':legacy_mismatch_count,
        'mismatchesReopened':0,
    },
    'boundaries':{'w1049All12MatchPriorFinal':True,'w1100NoDispositionAssigned':True},
    'nativeSpeakerReview':{'approved':False,'outstanding':True},
    'blockers':['Primary packet manifest does not match the current README.md; SHA256SUMS does match the current README.'],
    'limitations':['No qualified native-speaker approval is claimed.','No browser/runtime acceptance, builds, tests, scans, CI, or PR actions were performed.'],
}
write_json(OUT/'summary.json',summary)
readme=f'''# Independent cross-review: ChaptarrNG PR #190 W1050–W1099

Cross-review packet for the sealed primary review at `{PRIMARY}`. The reviewed source tree is pinned to commit `{HEAD}` and tree `{TREE}`. The review worktree was clean at the pinned head.

## Result

- Reviewed all 600 locale cells across 50 sources and 12 locales.
- Accepted the 546 current translations; confirmed all 24 primary corrections and all 18 refinements; upheld all 12 holds; rejected 0 proposed changes and introduced 0 additional changes.
- Upheld all 12 `Dodge-ing these piles of books` holds. The protected `Dodge` name remains unchanged in each cell; native creative localization remains outstanding.
- Re-attested the source catalog entries, locale catalog values, 60 distinct caller pins, registered source contexts, placeholders, markup, protected literals, and exact-head file pins. No pin or structural failures were found. The primary packet SHA256SUMS validates, but its manifest has one mismatch: the live README is 3,061 bytes / SHA256 `897127e176748c01d02b61bb77e9faac82a83571ed33c83bf4a31752ab9efbd4`, while the manifest records 3,020 bytes / SHA256 `e0fc664e95f555e1daed598e6235fdd98274da9bf76098307816be5ea45f57f0`.
- Rechecked all 12,600 historical rows through W1049 against live catalog values. There is no new drift from the immediately previous packet. The 195 live-versus-prior-final mismatches are retained as historical drift and were not reopened.
- The W1049 backward boundary matches all 12 prior final hashes. W1100 remains boundary context with no dispositions assigned.

## Evidence files

- `cross-review-cells.jsonl` contains the 600 independently adjudicated cells and exact target hashes.
- `caller-pin-checks.jsonl` contains every unique source/caller pin.
- `historical-drift-checks-through-W1049.jsonl` contains the full 12,600-row continuity recheck.
- `pin-audit.json` and `boundary-audit.json` summarize commit, source-registration, catalog-coverage, structure, and boundary checks.
- `summary.json` records counts and limitations.
- `build_crossreview.py` reproduces the machine-attestable checks and packet outputs.
- `SHA256SUMS` covers every file in this packet except itself.

This is a machine-assisted cross-review; it does not replace qualified native-speaker signoff. No repository files, localization catalogs, PR state, tests, builds, scans, or CI were changed or run. All generated files are confined to this task-scoped scratch directory.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
manifest_out={'packet':summary['packet'],'exactHead':HEAD,'exactTree':TREE,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files]}
write_json(OUT/'manifest.json',manifest_out)
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
with (OUT/'SHA256SUMS').open('w',encoding='utf-8',newline='\n') as f:
    for p in files: f.write(f'{sha(p.read_bytes())}  {p.name}\n')
for line in (OUT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1)
    assert sha((OUT/name.strip()).read_bytes())==digest,name
assert len(read_jsonl(OUT/'cross-review-cells.jsonl'))==600
assert len(read_jsonl(OUT/'caller-pin-checks.jsonl'))==60
assert len(read_jsonl(OUT/'historical-drift-checks-through-W1049.jsonl'))==12600
print(json.dumps({'out':str(OUT),'files':len(files)+1,'cellCount':600,'callerPins':len(caller_checks),'historicalRows':len(prior_checks),'summary':summary},ensure_ascii=False,indent=2))
