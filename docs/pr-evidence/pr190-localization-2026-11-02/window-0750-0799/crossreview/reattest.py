import collections, hashlib, json, pathlib, re, subprocess, sys

REPO = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0750-0799-a58de8c')
PACKET = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-primary-20261102')
OUT = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-crossreview-20261102')
PRIOR = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-crossreview-independent-20261102')
PRIOR_PRIMARY = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-primary-20261102')

errors=[]
checks=collections.Counter()
def sha(b): return hashlib.sha256(b).hexdigest()
def textsha(s): return sha(s.encode('utf-8'))
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def blobsha(b):
    # Match Git's object ID; the content is also pinned with SHA-256.
    return subprocess.check_output(['git','-C',str(REPO),'hash-object','--stdin'],input=b).decode().strip()
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def loadj(path): return [json.loads(line) for line in path.open(encoding='utf-8') if line.strip()]
def dup_load(path):
    dups=[]
    def hook(pairs):
        d={}
        for k,v in pairs:
            if k in d: dups.append(k)
            d[k]=v
        return d
    data=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=hook)
    return data,dups
def verify_sumfile(base, sums_path, label):
    seen=0
    for line in sums_path.read_text().splitlines():
        if not line.strip(): continue
        digest, rel=line.split(None,1); rel=rel.strip().lstrip('*')
        f=base/rel
        if not f.is_file(): errors.append([label,'missing',rel]); continue
        if sha(f.read_bytes())!=digest: errors.append([label,'sha256',rel])
        seen+=1
    checks[label+'_files']=seen
    return seen
def read_rel(rel): return (REPO/rel).read_bytes()
def validate_ref(ref, label):
    f=REPO/ref['file']
    if not f.is_file(): errors.append([label,'missing-file',ref['file']]); return
    b=f.read_bytes(); lines=b.decode('utf-8').splitlines(); line=ref['line']
    checks[label+'_refs']+=1
    if sha(b)!=ref.get('currentFileSha256',ref.get('fileSha256')): errors.append([label,'file-sha',ref['file']])
    if blobsha(b)!=ref.get('currentFileBlob',ref.get('fileBlob')): errors.append([label,'git-blob',ref['file']])
    if not 1<=line<=len(lines): errors.append([label,'line-range',ref['file'],line]); return
    actual=lines[line-1].strip()
    if actual!=ref['currentLineText'] if 'currentLineText' in ref else actual!=ref['lineText']:
        errors.append([label,'line-text',ref['file'],line,actual])
    expected_sha=ref.get('currentLineSha256',ref.get('lineSha256'))
    if textsha(actual)!=expected_sha: errors.append([label,'line-sha',ref['file'],line])
    if 'contextBefore' in ref:
        before=[x.strip() for x in lines[max(0,line-4):line-1]]
        after=[x.strip() for x in lines[line:min(len(lines),line+3)]]
        if before!=ref['contextBefore']: errors.append([label,'before-context',ref['file'],line])
        if after!=ref['contextAfter']: errors.append([label,'after-context',ref['file'],line])

def short_git_state():
    return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain')}

manifest=load(PACKET/'input-manifest.json')
head=git('rev-parse','HEAD'); tree=git('rev-parse','HEAD^{tree}')
checks['head_match']=int(head==manifest['head'])
checks['tree_match']=int(tree==manifest['tree'])
if head!=manifest['head']: errors.append(['head',head,manifest['head']])
if tree!=manifest['tree']: errors.append(['tree',tree,manifest['tree']])
if git('status','--porcelain'): errors.append(['worktree','dirty',git('status','--porcelain')])
verify_sumfile(PACKET,PACKET/'SHA256SUMS','primary_packet')
verify_sumfile(REPO,PACKET/'INPUT-SHA256SUMS','primary_inputs')

input_records=[manifest['sourceCatalog'],manifest['sourceFollowup'],manifest['serverMessageRegistry'],manifest['genericCallerRegistry'],*manifest['localeCatalogs'].values(),*manifest['callerFiles']]
for rec in input_records:
    f=REPO/rec['path']
    if not f.is_file(): errors.append(['input','missing',rec['path']]); continue
    b=f.read_bytes()
    if sha(b)!=rec['sha256']: errors.append(['input','sha256',rec['path']])
    if blobsha(b)!=rec['blob']: errors.append(['input','git-blob',rec['path']])
    if len(b)!=rec['bytes']: errors.append(['input','bytes',rec['path']])
checks['input_manifest_records']=len(input_records)

source_catalog, source_dups=dup_load(REPO/manifest['sourceCatalog']['path'])
if source_dups: errors.append(['source-catalog','duplicate-keys',source_dups[:5]])
followup=load(REPO/manifest['sourceFollowup']['path'])
all_source_ids=followup['currentMissingIds']
selected=all_source_ids[750:800]
source_id_digest=sha(json.dumps(selected,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
all_source_digest=sha(json.dumps(all_source_ids,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
if source_id_digest!=manifest['selectedSourceIdListSha256']: errors.append(['slice','selected ID digest mismatch'])
if len(set(all_source_ids[:800]))!=800 or set(all_source_ids[:750]) & set(selected): errors.append(['slice','prior IDs overlap or duplicates through window'])
if len(all_source_ids)!=manifest['sourceListCount'] or all_source_digest!=manifest['sourceListSha256']: errors.append(['source-list','count/hash mismatch'])
if selected!=manifest['selectedSourceIds']: errors.append(['slice','currentMissingIds mismatch'])
if len(set(selected))!=50: errors.append(['slice','duplicate ids'])
if selected!=[r['sourceId'] for r in loadj(PACKET/'source-slice.jsonl')]: errors.append(['slice','source-slice order mismatch'])
source_slice=loadj(PACKET/'source-slice.jsonl')

catalogs={}; catalog_dups={}
for locale,rec in manifest['localeCatalogs'].items():
    catalogs[locale],catalog_dups[locale]=dup_load(REPO/rec['path'])
    if catalog_dups[locale]: errors.append(['catalog','duplicate-keys',locale,catalog_dups[locale][:5]])
keys=set(source_catalog)
for locale,cat in catalogs.items():
    if set(cat)!=keys: errors.append(['catalog','key-parity',locale,len(keys-set(cat)),len(set(cat)-keys)])
checks['locales']=len(catalogs)
checks['catalog_keys_each']=len(keys)

input_cells=loadj(PACKET/'input-cells.jsonl')
ledger=loadj(PACKET/'primary-review-ledger.jsonl')
candidates=loadj(PACKET/'correction-candidates.jsonl')
review_cells=loadj(PACKET/'review-cells.jsonl')
if len(input_cells)!=600 or len(ledger)!=600 or len(review_cells)!=600: errors.append(['cells','not-600',len(input_cells),len(ledger),len(review_cells)])
key=lambda r:(r['locale'],r['sourceId'])
for label,rows in [('input',input_cells),('ledger',ledger),('review',review_cells)]:
    if len({key(r) for r in rows})!=len(rows): errors.append([label,'duplicate-locale-id'])
input_by={key(r):r for r in input_cells}; ledger_by={key(r):r for r in ledger}
cell_hash_errors=[]
for row in input_cells:
    loc=row['locale']; sid=row['sourceId']; source=row['source']; current=row['currentTarget']
    if row['exactHead']!=head or row['exactTree']!=tree: cell_hash_errors.append([loc,sid,'pin'])
    if textsha(source)!=row['sourceTextSha256']: cell_hash_errors.append([loc,sid,'source-hash'])
    if textsha(current)!=row['currentTargetSha256']: cell_hash_errors.append([loc,sid,'current-hash'])
    if source_catalog.get(sid)!=source: cell_hash_errors.append([loc,sid,'source-value'])
    if catalogs[loc].get(sid)!=current: cell_hash_errors.append([loc,sid,'current-value'])
    if row['sourceFileSha256']!=manifest['sourceCatalog']['sha256'] or row['sourceFileBlob']!=manifest['sourceCatalog']['blob']: cell_hash_errors.append([loc,sid,'source-file-pin'])
    rec=manifest['localeCatalogs'][loc]
    if row['targetFileSha256']!=rec['sha256'] or row['targetFileBlob']!=rec['blob']: cell_hash_errors.append([loc,sid,'target-file-pin'])
if cell_hash_errors: errors.extend([['cell',*e] for e in cell_hash_errors[:20]])
checks['source_id_queue_length']=len(all_source_ids)
checks['selected_source_id_digest_match']=int(source_id_digest==manifest['selectedSourceIdListSha256'])
checks['prior_ids_disjoint_and_unique_through_799']=int(len(set(all_source_ids[:800]))==800 and not (set(all_source_ids[:750]) & set(selected)))
checks['source_list_digest_match']=int(all_source_digest==manifest['sourceListSha256'])
checks['source_cells_rehashed']=len(input_cells)
checks['current_cells_rehashed']=len(input_cells)
checks['cell_hash_errors']=len(cell_hash_errors)

reg=load(REPO/manifest['serverMessageRegistry']['path'])
reg_by={r['id']:r for r in reg['records']}
caller_rows=loadj(PACKET/'caller-context.jsonl')
caller_refs=0
for crow in caller_rows:
    rec=reg_by.get(crow['sourceId'])
    if not rec: errors.append(['caller','missing registry record',crow['sourceId']]); continue
    if rec['source']!=crow['source']: errors.append(['caller','registry source mismatch',crow['sourceId']])
    if rec.get('sourceFingerprint')!=crow['sourceRegistryFingerprint']: errors.append(['caller','fingerprint mismatch',crow['sourceId']])
    if crow['sourceOrdinal'] not in range(750,800): errors.append(['caller','ordinal out of scope',crow['sourceOrdinal']])
    for ref in crow['callerRefs']:
        caller_refs+=1; validate_ref(ref,'source_caller')
        stale_ids={x['sourceId'] for x in manifest.get('staleRegistryPinsRefreshed',[])}
        if ref.get('registryPinReattested') is not True and crow['sourceId'] not in stale_ids: errors.append(['caller','registryPinReattested false',crow['sourceId'],ref['file'],ref['line']])
        context=' '.join((ref.get('contextBefore') or [])+[ref.get('currentLineText','')]+(ref.get('contextAfter') or []))
        source_pattern=re.escape(crow['source'])
        source_pattern=re.sub(r'\\\{value[0-9]+\\\}',r'.+?',source_pattern)
        if not re.search(source_pattern,context): errors.append(['caller','source text absent from pinned caller context',crow['sourceId'],ref['file'],ref['line']])
expected_stale={x['sourceId'] for x in manifest.get('staleRegistryPinsRefreshed',[])}
found_stale={c['sourceId'] for c in caller_rows for r in c['callerRefs'] if r.get('registryPinReattested') is not True}
if found_stale!=expected_stale: errors.append(['caller','stale registry pin exception set mismatch',sorted(found_stale),sorted(expected_stale)])
checks['stale_registry_line_refs_refreshed']=len(found_stale)
checks['source_caller_rows']=len(caller_rows); checks['source_caller_refs']=caller_refs
checks['source_caller_files']=len({r['file'] for c in caller_rows for r in c['callerRefs']})

pipeline=loadj(PACKET/'pipeline-caller-context.jsonl')
for ref in pipeline:
    validate_ref(ref,'pipeline')
checks['pipeline_refs']=len(pipeline); checks['pipeline_files']=len({r['file'] for r in pipeline})

source_registry_by={r['sourceId']:r for r in caller_rows}
manual=load(PACKET/'manual-protected-literals.json')['additionalProtectedLiteralsByOrdinal']
protected_errors=[]; placeholder_errors=[]; markup_errors=[]; final_mismatch=[]; current_mismatch=[]
placeholder_re=re.compile(r'\{[A-Za-z][A-Za-z0-9_.:-]*\}')
markup_re=re.compile(r'</?[A-Za-z][^>]*>')
for row in ledger:
    src=row['source']; cur=row['currentTarget']; final=row['finalTarget']
    ph=lambda s:sorted(placeholder_re.findall(s))
    if ph(src)!=ph(cur): placeholder_errors.append([row['locale'],row['sourceId'],'current',ph(src),ph(cur)])
    if ph(src)!=ph(final): placeholder_errors.append([row['locale'],row['sourceId'],'final',ph(src),ph(final)])
    if row['sourcePlaceholders']!=ph(src) or row['currentTargetPlaceholders']!=ph(cur):
        placeholder_errors.append([row['locale'],row['sourceId'],'packet-token-lists'])
    if row['recommendedPlaceholders'] is not None and row['recommendedPlaceholders']!=ph(final):
        placeholder_errors.append([row['locale'],row['sourceId'],'final-token-lists'])
    if markup_re.findall(src)!=markup_re.findall(cur) or markup_re.findall(src)!=markup_re.findall(final): markup_errors.append([row['locale'],row['sourceId']])
    literals=set(row.get('protectedLiterals') or [])|set(manual.get(str(row['sourceOrdinal']),[]))
    def has_literal(text, lit):
        if re.fullmatch(r'[A-Za-z0-9_]+',lit):
            return re.search(r'(?<![A-Za-z0-9_])'+re.escape(lit)+r'(?![A-Za-z0-9_])',text) is not None
        return lit in text
    for lit in literals:
        cur_has=has_literal(cur,lit); fin_has=has_literal(final,lit); src_has=has_literal(src,lit)
        if (src_has or lit in manual.get(str(row['sourceOrdinal']),[])) and not fin_has: protected_errors.append([row['locale'],row['sourceId'],lit,src_has,cur_has,fin_has])
        if src_has and not cur_has: current_mismatch.append([row['locale'],row['sourceId'],lit])
    if textsha(final)!=row['finalTargetSha256']: errors.append(['final','sha256 mismatch',row['locale'],row['sourceId']])
if placeholder_errors: errors.extend([['placeholder',*e] for e in placeholder_errors[:20]])
if markup_errors: errors.extend([['markup',*e] for e in markup_errors[:20]])
if protected_errors: errors.extend([['protected',*e] for e in protected_errors[:20]])
checks['placeholder_error_cells']=len({(e[0],e[1]) for e in placeholder_errors})
checks['markup_error_cells']=len(markup_errors)
checks['current_protected_mismatch_cells']=len({(e[0],e[1]) for e in current_mismatch})
checks['final_protected_mismatch_cells']=len({(e[0],e[1]) for e in protected_errors})
checks['protected_literal_checks']=sum(len(set(r.get('protectedLiterals') or [])|set(manual.get(str(r['sourceOrdinal']),[]))) for r in ledger)

candidate_errors=[]
if len(candidates)!=215: errors.append(['candidate-count',len(candidates)])
for c in candidates:
    row=ledger_by.get(key(c))
    if not row: candidate_errors.append([c['locale'],c['sourceId'],'no ledger row']); continue
    if row['disposition'] not in ('propose-correction','propose-refinement'): candidate_errors.append([c['locale'],c['sourceId'],'ledger not proposed'])
    if c['recommendedTarget']!=row['recommendedTarget'] or c['finalTarget']!=row['finalTarget']: candidate_errors.append([c['locale'],c['sourceId'],'target mismatch'])
    if textsha(c['recommendedTarget'])!=c['recommendedTargetSha256']: candidate_errors.append([c['locale'],c['sourceId'],'candidate hash'])
    if c['sourceRegistryCallerContext']!=source_registry_by.get(c['sourceId']): candidate_errors.append([c['locale'],c['sourceId'],'caller context mismatch'])
if candidate_errors: errors.extend([['candidate',*e] for e in candidate_errors[:20]])
checks['candidates']=len(candidates); checks['candidate_errors']=len(candidate_errors)

# Verify preceding W700-749 was applied to the live catalog, and W749 remains contiguous.
verify_sumfile(PRIOR,PRIOR/'SHA256SUMS','prior_crossreview')
verify_sumfile(PRIOR_PRIMARY,PRIOR_PRIMARY/'SHA256SUMS','prior_primary')
prior_rows=loadj(PRIOR/'cell-readbacks.jsonl')
prior_xreview=loadj(PRIOR/'cell-crossreview.jsonl')
prior_final={(r['locale'],r['sourceId']):r for r in prior_xreview}
prior_matches=[]
prior_source_mismatches=[]
for pr in prior_rows:
    if pr['sourceOrdinal'] not in range(700,750): continue
    xv=prior_final.get((pr['locale'],pr['sourceId']))
    live_source=source_catalog.get(pr['sourceId'])
    if not xv or live_source!=xv['source'] or textsha(live_source or '')!=xv['sourceTextSha256']:
        prior_source_mismatches.append([pr['locale'],pr['sourceId']])
    live=catalogs[pr['locale']].get(pr['sourceId'])
    if not xv or live!=xv['independentTarget'] or textsha(live or '')!=xv['independentTargetSha256']: prior_matches.append([pr['locale'],pr['sourceId']])
checks['prior_w700_cells']=sum(1 for r in prior_rows if r['sourceOrdinal'] in range(700,750))
checks['prior_w700_live_diffs']=len(prior_matches)
checks['prior_w700_source_diffs']=len(prior_source_mismatches)
if prior_matches: errors.append(['prior-w700','live target diffs',prior_matches[:20]])
if prior_source_mismatches: errors.append(['prior-w700','source diffs',prior_source_mismatches[:20]])
prior_sources={r['sourceId']:r for r in prior_rows if r['locale']=='es'}
for sid in selected:
    if sid in prior_sources: errors.append(['prior-w700','source overlap',sid])

boundary=loadj(PACKET/'w749-boundary-reattestation.jsonl')
if len(boundary)!=12: errors.append(['w749-boundary','row count',len(boundary)])
prior_boundary={(r['locale'],r['sourceId']):r for r in prior_rows if r['sourceOrdinal']==749}
for br in boundary:
    pr=prior_boundary.get((br['locale'],br['sourceId']))
    if not pr: errors.append(['w749-boundary','missing prior row',br['locale'],br['sourceId']]); continue
    live=catalogs[br['locale']].get(br['sourceId'])
    if live!=br['liveTarget'] or live!=br['priorCrossReviewFinalTarget'] or live!=pr['finalTarget']:
        errors.append(['w749-boundary','live/prior diff',br['locale'],br['sourceId']])
    for ref in br['callerContext']:
        validate_ref(ref,'w749_boundary')
checks['w749_boundary_rows']=len(boundary)
checks['w749_boundary_caller_refs']=sum(len(r['callerContext']) for r in boundary)

summary={
 'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'head':head,'tree':tree,'branch':git('branch','--show-current'),
 'livePullRequestExpectedHead':'a58de8cd62a80babdca07a86d6b7d463b4a44773',
 'exactHeadMatch':head=='a58de8cd62a80babdca07a86d6b7d463b4a44773',
 'exactTreeMatch':tree=='3baf8c11efe42c617a286cd37665e946303c6d2a',
 'worktreeStatus':git('status','--porcelain'),'checks':dict(checks),'errors':errors,
 'primaryDispositionCounts':dict(collections.Counter(r['disposition'] for r in ledger)),
 'primaryProposalCount':len(candidates),'sourceCurrentHashPairsRecomputed':len(input_cells),
 'localeCatalogCounts':{l:len(c) for l,c in catalogs.items()},
 'currentProtectedMismatches':current_mismatch,
 'nativeSpeakerApproval':False,'browserReview':False,'testsBuildsCiRun':False,
 'readOnly':True
}
(OUT/'integrity-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'integrity-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
if errors: sys.exit(1)
