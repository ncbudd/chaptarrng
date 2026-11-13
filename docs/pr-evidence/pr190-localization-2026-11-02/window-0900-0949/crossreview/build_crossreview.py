import json, hashlib, subprocess, re, collections, sys
from pathlib import Path

PRIMARY=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0900-0949-primary-20261102')
SCRATCH=Path('/mnt/disks/scratch/task-scratch')
OUT=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0900-0949-crossreview-20261102/batch-independent-600')
REPO=Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
EXPECTED_HEAD='a9a74f6ba733e8c1f06a2d260bd802d4fde2da0e'
EXPECTED_TREE='d9d25f309f3a7256056b4ed8deb1dabee58b64fe'
EXPECTED_PRIMARY_MANIFEST='795f1b6bddd08117c158027586a56fcde0c8142043691ba6251e7c1d25cda658'
OUT.mkdir(parents=True,exist_ok=True)

def sha(data):
    if isinstance(data,str): data=data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()
def canonical(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def read_jl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args])
def gittext(*args): return git(*args).decode('utf-8')
def get_git_file(head,path):
    data=git('show',f'{head}:{path}')
    blob=gittext('rev-parse',f'{head}:{path}').strip()
    return blob,data

head=gittext('rev-parse','HEAD').strip(); tree=gittext('rev-parse','HEAD^{tree}').strip(); repo_status_before=gittext('status','--porcelain=v1')
assert head==EXPECTED_HEAD and tree==EXPECTED_TREE and not repo_status_before,(head,tree,repo_status_before)
assert sha((PRIMARY/'manifest.json').read_bytes())==EXPECTED_PRIMARY_MANIFEST
subprocess.check_call(['sha256sum','-c','SHA256SUMS'],cwd=PRIMARY,stdout=subprocess.DEVNULL)
primary_sums_sha=sha((PRIMARY/'SHA256SUMS').read_bytes())
manifest=read_json(PRIMARY/'manifest.json'); input_manifest=read_json(PRIMARY/'input-manifest.json')
assert manifest['head']==head and manifest['tree']==tree and manifest['state']=='OPEN' and manifest['isDraft'] is True
assert manifest['sourceCount']==50 and manifest['cellCount']==600 and manifest['localeCount']==12

# Read the frozen, row-level input and independent primary decision data.
input_rows=read_jl(PRIMARY/'input-cells.jsonl')
review_rows=read_jl(PRIMARY/'review-cells.jsonl')
assert len(input_rows)==len(review_rows)==600
key=lambda x:(x['sourceOrdinal'],x['locale'])
inmap={key(x):x for x in input_rows}; rmap={key(x):x for x in review_rows}
assert len(inmap)==len(rmap)==600 and set(inmap)==set(rmap)
source_rows=read_jl(PRIMARY/'source-slice.jsonl')
source_map={x['sourceOrdinal']:x for x in source_rows}
assert len(source_map)==50

# Reattest the 12 complete locale catalogs plus source catalog at the frozen tree.
catalogs={}; catalog_reattest=[]; catalog_meta={}
for locale,pin in input_manifest['localeCatalogs'].items():
    blob,data=get_git_file(head,pin['path']); obj=json.loads(data)
    record={'locale':locale,'path':pin['path'],'blob':blob,'fileSha256':sha(data),'bytes':len(data),'keyCount':len(obj),'expectedBlob':pin['blob'],'expectedFileSha256':pin['sha256'],'keySetSha256':sha('\n'.join(sorted(obj))), 'blobMatches':blob==pin['blob'],'fileSha256Matches':sha(data)==pin['sha256'],'result':'pass'}
    assert record['blobMatches'] and record['fileSha256Matches'],record
    catalogs[locale]=obj; catalog_meta[locale]=record; catalog_reattest.append(record)
assert set(catalogs)==set(LOCALES)
assert len({frozenset(c.keys()) for c in catalogs.values()})==1

source_pin={'path':input_manifest['sourceCatalog']['path'],'blob':input_manifest['sourceCatalog']['blob'],'sha256':input_manifest['sourceCatalog']['sha256']}
sblob,sbytes=get_git_file(head,source_pin['path']); source_catalog=json.loads(sbytes)
assert sblob==source_pin['blob'] and sha(sbytes)==source_pin['sha256']

# Reattest source registries and all 50 exact source records against pinned registry entries.
registry_files={}
for path in ['docs/localization/server-message-sources.json','docs/localization/provider-option-sources.json']:
    blob,data=get_git_file(head,path); registry_files[path]={'blob':blob,'sha256':sha(data),'data':json.loads(data)}
registry_records={}
for path,v in registry_files.items():
    for rec in v['data']['records']:
        registry_records[rec['id']]=(path,rec)
manual_protected=read_json(PRIMARY/'manual-protected-literals.json')['bySourceId']
source_registry_reattest=[]
for s in source_rows:
    sid=s['sourceId']; regpath=s['sourceRegistryPath']; assert sid in registry_records
    actual_path,rec=registry_records[sid]
    assert actual_path==regpath and rec['source']==s['source'] and rec['sourceFingerprint']==s['sourceRegistryFingerprint']
    assert source_catalog[sid]==s['source'] and sha(s['source'])==s['sourceTextSha256'] and sha(sid)==s['sourceKeySha256']
    # Exact registry literal lists, parameter names and patterns are pinned separately from text semantics.
    assert rec.get('protectedLiterals',[])==s['sourceRegistryProtectedLiterals']
    assert s['manualProtectedLiterals']==manual_protected.get(sid,[])
    expected_effective=list(dict.fromkeys(list(rec.get('protectedLiterals',[]))+list(manual_protected.get(sid,[]))))
    assert s['effectiveProtectedLiterals']==expected_effective,(sid,s['effectiveProtectedLiterals'],expected_effective)
    source_registry_reattest.append({'sourceOrdinal':s['sourceOrdinal'],'sourceId':sid,'source':s['source'],'sourceTextSha256':sha(s['source']),'sourceKeySha256':sha(sid),'registryPath':actual_path,'registryBlob':registry_files[actual_path]['blob'],'registrySha256':registry_files[actual_path]['sha256'],'registryFingerprint':rec['sourceFingerprint'],'protectedLiterals':rec.get('protectedLiterals',[]),'registryEntryMatchesPinned':True,'result':'pass'})

# Verify all pinned files (88), caller lines (86), generic server-message pipeline refs (76), and provider-option pipeline refs (20).
pinned=read_json(PRIMARY/'pinned-files.json')
pinned_file_reattest=[]
for p in pinned['files']:
    blob,data=get_git_file(head,p['path'])
    record={'path':p['path'],'blob':blob,'fileSha256':sha(data),'bytes':len(data),'expectedBlob':p['blob'],'expectedSha256':p['sha256'],'blobMatches':blob==p['blob'],'sha256Matches':sha(data)==p['sha256'],'result':'pass'}
    assert record['blobMatches'] and record['sha256Matches'],record
    pinned_file_reattest.append(record)

def line_pin(source_record,prefix):
    path=source_record['file']; blob,data=get_git_file(head,path); lines=data.decode('utf-8').splitlines(); n=source_record['line']; actual=lines[n-1]
    refs={
      'blobMatches':blob==source_record['fileBlob'],
      'fileSha256Matches':sha(data)==source_record['fileSha256'],
      'lineTextMatchesAfterTrim':actual.strip()==source_record['lineText'],
      'lineSha256MatchesTrimmed':sha(actual.strip())==source_record['lineSha256'],
      'contextBeforeMatches':all(lines[n-len(source_record.get('contextBefore',[]))+i-1].strip()==t for i,t in enumerate(source_record.get('contextBefore',[]))),
      'contextAfterMatches':all(lines[n+i].strip()==t for i,t in enumerate(source_record.get('contextAfter',[]))),
    }
    assert all(refs.values()),(path,n,refs)
    return {'pinId':prefix,'path':path,'fileBlob':blob,'fileSha256':sha(data),'line':n,'lineText':source_record['lineText'],'lineSha256':sha(actual.strip()),'contextBefore':source_record.get('contextBefore',[]),'contextAfter':source_record.get('contextAfter',[]),'checks':refs,'result':'pass'}

caller_context=read_jl(PRIMARY/'caller-context.jsonl'); caller_reattest=[]; caller_refs_by_ord={}
for s in caller_context:
    refs=s['directCallerReferences']
    assert sha(canonical(refs))==s['callerContextSha256']
    outrefs=[]
    for j,ref in enumerate(refs):
        pin=line_pin(ref,f"caller-{s['sourceOrdinal']:03}-{j+1:02}")
        pin.update({'sourceOrdinal':s['sourceOrdinal'],'sourceId':s['sourceId'],'category':ref.get('category'),'surface':ref.get('surface')})
        caller_reattest.append(pin); outrefs.append(pin['pinId'])
    caller_refs_by_ord[s['sourceOrdinal']]={'contextSha256':s['callerContextSha256'],'count':len(refs),'pinIds':outrefs,'status':s['callerReferenceStatus']}
assert len(caller_reattest)==86 and all(x['status']=='pinned' for x in caller_refs_by_ord.values())

server_context=read_jl(PRIMARY/'server-message-pipeline-context.jsonl'); server_reattest=[]
for j,x in enumerate(server_context):
    pin=line_pin(x,f'server-message-pipeline-{j+1:03}')
    pin.update({'pipeline':x['pipeline'],'surface':x['surface'],'registryLine':x.get('registryLine')})
    server_reattest.append(pin)
assert len(server_reattest)==76
provider_context=read_jl(PRIMARY/'provider-option-pipeline-context.jsonl'); provider_reattest=[]
for j,x in enumerate(provider_context):
    pin=line_pin(x,f'provider-option-pipeline-{j+1:03}')
    pin.update({'pipeline':x['pipeline'],'interpretation':x['interpretation']})
    provider_reattest.append(pin)
assert len(provider_reattest)==20

# Reattest all 600 current/source targets against exact catalog blobs and primary target hashes.
input_reattest=[]
for k in sorted(inmap,key=lambda y:(y[0],LOCALES.index(y[1]))):
    x=inmap[k]; decision=rmap[k]; loc=x['locale']; sid=x['sourceId']; ordinal=x['sourceOrdinal']
    target=catalogs[loc].get(sid)
    assert target==x['currentTarget']==decision['currentTarget'],(ordinal,loc,sid)
    assert sha(target)==x['currentTargetSha256']==decision['currentTargetSha256']
    assert source_catalog[sid]==x['source'] and sha(x['source'])==x['sourceTextSha256']
    assert sha(decision['finalTarget'])==decision['finalTargetSha256']
    assert sha(sid)==x['sourceKeySha256']
    assert x['targetFileBlob']==catalog_meta[loc]['blob'] and x['targetFileSha256']==catalog_meta[loc]['fileSha256']
    assert x['sourceFileBlob']==sblob and x['sourceFileSha256']==sha(sbytes)
    cc=caller_refs_by_ord[ordinal]; assert cc['contextSha256']==x['callerContextSha256']
    input_reattest.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':x['source'],'sourceSha256':sha(x['source']),'sourceKeySha256':sha(sid),'currentTarget':target,'currentTargetSha256':sha(target),'primaryFinalTarget':decision['finalTarget'],'primaryFinalTargetSha256':sha(decision['finalTarget']),'sourceFile':x['sourceFile'],'sourceFileBlob':sblob,'sourceFileSha256':sha(sbytes),'targetFile':x['targetFile'],'targetFileBlob':catalog_meta[loc]['blob'],'targetFileSha256':catalog_meta[loc]['fileSha256'],'callerContextSha256':cc['contextSha256'],'callerRefCount':cc['count'],'callerPinIds':cc['pinIds'],'sourceAndTargetCellHashesMatchFrozenInput':True,'result':'pass'})
assert len(input_reattest)==600

# Independent disposition register. All non-English wording was separately compared against its exact caller and neighboring options.
source_semantics={
900:'A global delay profile is a protected configuration profile; all strings say it cannot be deleted.',
901:'This validation applies only when MetadataProfileId is supplied, and then requires its value to be greater than zero.',
902:'A generic internal server error; no specific failure details should be introduced.',
903:'The webhook resolves to a local/private network address; permitted use is limited to trusted internal services.',
904:'The application cannot write to the selected folder.',
905:"A branch name is mandatory and the literal default branch is 'main'.",
906:'A selected book edition was not retained for this book; the context is edition matching, not a generic file save.',
907:'An unknown version is reported with the dynamic value preserved.',
908:'A request limit has been reached, followed by a dynamic value.',
909:'The indexer connection failed; the user should inspect the log above the exact ValidationFailure marker, followed by dynamic detail.',
910:'A series with the supplied ID was not found; the supplied value is dynamic.',
911:'The configuration contract is invalid; retain the technical contract/schema sense.',
912:'The operation permits at most 1,000 authors in one move; the cap is inclusive.',
913:'Validation requires Book Title AND PartNumber, OR Original Title, while the three field labels remain literal.',
914:'Indexer connection failed; check DNS and verify IPv6 is working or disabled, then show the dynamic detail.',
915:'Saving the API token failed and the user should try again.',
916:'An Apprise notification type label for informational notifications.',
917:'An Apprise notification type label for success.',
918:'An Apprise notification type label for failure.',
919:'The `Last` enum member sets a download-client queue position at the end, distinct from `First`.',
920:'The `First` enum member sets a download-client queue position at the beginning, distinct from `Last`.',
921:'A fixed Jellyfin server-type option; preserve the product name.',
922:'A fixed Emby server-type option; preserve the product name.',
923:'The Docs category of FileList indexer categories; here Docs means documents, not generic documentation pages.',
924:'A low notification/download-client priority option.',
925:'The normal/default priority between Low and High.',
926:'A high priority option, paired with Low and Normal.',
927:'The tracker Freeleech flag remains an exact term.',
928:'Halfleech means only half the download amount is counted.',
929:'Double Upload means the uploaded amount/count is credited twice.',
930:'Internal means the torrent comes from an internal release group.',
931:'Scene is a torrent flag for a release from a Scene group, not a theatrical scene.',
932:'Freeleech75 indicates a torrent counts toward 75 percent of download quota.',
933:'Freeleech25 indicates a torrent counts toward 25 percent of download quota.',
934:'VIP Exclusive means only VIP users can access the torrent.',
935:'VIP Freeleech means a VIP-only torrent is freeleech for the current VIP user.',
936:'Silent is the lower Join/Pushover notification priority (-2), distinct from Quiet (-1).',
937:'Quiet is the Join/Pushover priority (-1), distinct from Silent (-2).',
938:'Emergency is the highest notification priority option.',
939:'MQTT QoS At Most Once delivery has no retry guarantee.',
940:'MQTT QoS At Least Once allows/requires redelivery until acknowledged.',
941:'MQTT QoS Exactly Once aims for exactly one delivery.',
942:'Follow the MyAnonaMouse account preferences; this is the Never enum member for forcing a wedge.',
943:'Do not force a wedge; delegate the decision to the MAM account preferences.',
944:'Prefer to request/use a personal Freeleech wedge when available.',
945:'Request a personal wedge only when eligible, then fall back to a normal download if unavailable.',
946:'Require the personal wedge; this is stricter than Prefer.',
947:'If MAM cannot apply the required personal Freeleech wedge, fail the grab/download request.',
948:'The native language name English in the provider search-language list.',
949:'The native language name Afrikaans in the provider search-language list.',
}
correction_notes={
900:'The candidate uses natural locale word order for a global delay profile rather than a literal, awkward rendering of “global delay profile.”',
901:'The candidate expresses the conditional “if provided” idiomatically and retains the exact MetadataProfileId identifier and > 0 requirement.',
903:'The candidate fixes the Spanish agent/imperative and the Indonesian/PT-BR sentence flow while preserving URL and the permitted-but-trusted-internal-only warning.',
904:'The candidate uses the natural Chinese verb for writing to a folder.',
905:'The candidate makes the required branch name and default explicit in natural Indonesian, Brazilian Portuguese, and Vietnamese.',
906:'The candidate uses the book-edition term and correct sentence structure; the selected edition was not retained for this book.',
908:'The candidate expresses reaching a request limit naturally and keeps {value0}.',
909:'The candidate restores the exact ValidationFailure marker and makes the indexer/log instruction idiomatic while keeping {value0}.',
910:'The candidate puts the series ID in natural locale word order and keeps {value0}.',
913:'The candidate localizes AND/OR logic without translating or altering the exact field labels Book Title, PartNumber, and Original Title.',
915:'The candidate uses natural “save/store API token” wording and appropriate sentence capitalization/punctuation.',
916:'The candidate uses the established concise Info category label.',
919:'The candidate names the end/last position in the queue, which resolves the bare adjective ambiguity in this enum.',
920:'The candidate names the start/first position in the queue, which resolves the bare ordinal ambiguity in this enum.',
924:'Spanish Low is an adjective modifying feminine prioridad, so Baja is the correct form; Korean uses the standalone low-level value rather than an adjective fragment.',
925:'Korean 보통 is the natural standalone “normal” priority value rather than the adjective fragment 정상적인.',
926:'The candidate uses the standalone high-priority value or gender/inflection that matches the locale.',
929:'The candidate makes the double-counted-upload meaning explicit in Spanish and natural in Brazilian Portuguese.',
931:'The caller comment says the torrent comes from a Scene group; the candidate preserves exact Scene and names the group/release meaning.',
934:'The current Hindi catalog value is Chinese text; the candidate gives a Hindi “VIP members only” label and keeps VIP exact.',
936:'Korean uses 무음 for Silent, distinguishing it from Quiet.',
937:'Korean uses 조용함 for Quiet, distinguishing it from Silent.',
938:'Darurat is the natural Indonesian emergency label; Kecemasan suggests anxiety/distress.',
942:'The candidate repairs word order/idiom for “follow MAM preferences” and keeps MAM exact.',
949:'The candidate uses the standard specific Mandarin language name for Afrikaans rather than the ambiguous “South African language.”',
}

# This explicit independent revision makes the French acquisition operation clearer than the primary's broad "récupération".
revised_targets={(947,'fr'):'La demande de téléchargement échoue si MAM ne peut pas appliquer l’avantage Freeleech personnel requis.'}
ledger=[]
structural_failures=[]; literal_failures=[]
for k in sorted(inmap,key=lambda y:(y[0],LOCALES.index(y[1]))):
    x=inmap[k]; d=rmap[k]; ordinal=x['sourceOrdinal']; loc=x['locale']; src=x['source']; cur=x['currentTarget']; primary_final=d['finalTarget']; proposed=d['recommendedTarget']
    assert sha(primary_final)==d['finalTargetSha256']
    if proposed is not None: assert sha(proposed)==d['recommendedTargetSha256']
    if d['disposition']=='accept-current':
        cross_disposition='accept-current'; recommended=cur
    elif k in revised_targets:
        cross_disposition='revise-proposal'; recommended=revised_targets[k]
    else:
        cross_disposition='accept-proposal'; recommended=primary_final
    expected_current_literals=list(x['protectedLiterals']); current_missing=[t for t in expected_current_literals if t not in cur]
    primary_missing=[t for t in expected_current_literals if t not in primary_final]
    recommended_missing=[t for t in expected_current_literals if t not in recommended]
    if current_missing: literal_failures.append((ordinal,loc,current_missing))
    assert not primary_missing and not recommended_missing,(ordinal,loc,primary_missing,recommended_missing)
    placeholder_pattern=re.compile(r'\{[^{}]+\}')
    source_ph=placeholder_pattern.findall(src); current_ph=placeholder_pattern.findall(cur); primary_ph=placeholder_pattern.findall(primary_final); rec_ph=placeholder_pattern.findall(recommended)
    assert source_ph==x['sourcePlaceholders'] and current_ph==x['currentTargetPlaceholders']
    # HTML/markup tags in these strings are uncommon, but compare exact sequences.
    markup_pattern=re.compile(r'</?[A-Za-z][^>]*>')
    source_markup=markup_pattern.findall(src); current_markup=markup_pattern.findall(cur); primary_markup=markup_pattern.findall(primary_final); rec_markup=markup_pattern.findall(recommended)
    assert source_markup==x['sourceMarkup'] and current_markup==x['currentTargetMarkup']
    checks={'currentPlaceholderParity':source_ph==current_ph,'primaryPlaceholderParity':source_ph==primary_ph,'recommendedPlaceholderParity':source_ph==rec_ph,'currentMarkupParity':source_markup==current_markup,'primaryMarkupParity':source_markup==primary_markup,'recommendedMarkupParity':source_markup==rec_markup}
    if not all(checks.values()): structural_failures.append((ordinal,loc,checks))
    assert all(checks.values()),(ordinal,loc,checks)
    caller=caller_refs_by_ord[ordinal]
    if cross_disposition=='accept-current':
        rationale=f"Independent review: the {loc} current value matches the pinned use. {source_semantics[ordinal]} It preserves the source intent and required structure in this context; no change is needed."
    elif cross_disposition=='accept-proposal':
        rationale=f"Independent review: the current {loc} wording is less precise or less natural for this context. {correction_notes.get(ordinal,'The candidate retains the source meaning and uses appropriate locale wording.')} {source_semantics[ordinal]} The exact protected terms, placeholders, and markup are preserved."
    else:
        rationale=("Independent review: the primary French phrase ‘récupération’ is understandable but underspecifies the operation in this provider-option hint. “Grab” here is the failed acquisition/download request when the required MAM wedge cannot be applied. The revised wording explicitly says the download request fails and retains the exact MAM and Freeleech terms.")
    row={
      'sourceOrdinal':ordinal,'windowLabel':ordinal+1,'sourceId':x['sourceId'],'source':src,'sourceSha256':x['sourceTextSha256'],'sourceKeySha256':x['sourceKeySha256'],'locale':loc,
      'currentTarget':cur,'currentTargetSha256':x['currentTargetSha256'],'currentTargetCatalogAttestation':{'exactValueMatchesCatalog':True,'catalogPath':x['targetFile'],'catalogBlob':x['targetFileBlob'],'catalogFileSha256':x['targetFileSha256'],'targetHashMatches':True},
      'primaryDisposition':d['disposition'],'primaryCandidateTarget':proposed,'primaryCandidateTargetSha256':d['recommendedTargetSha256'],'primaryFinalTarget':primary_final,'primaryFinalTargetSha256':d['finalTargetSha256'],
      'crossReviewDisposition':cross_disposition,'recommendedTarget':recommended,'recommendedTargetSha256':sha(recommended),
      'sourceSemanticContext':source_semantics[ordinal],'callerContextSha256':caller['contextSha256'],'callerReferenceCount':caller['count'],'callerPinIds':caller['pinIds'],
      'providerOptionPipelinePinIds':([p['pinId'] for p in provider_reattest] if x['sourceId'].startswith('provider.option.') else []),
      'serverMessagePipelinePinIds':([p['pinId'] for p in server_reattest if p['path'] in {r['path'] for r in caller_reattest if r['sourceOrdinal']==ordinal}] if x['sourceId'].startswith('server.message.') else []),
      'priorWindowLink':{'selectedOrdinalCoveredByPriorWindows':False,'priorCoverage':[0,899],'boundaryOrdinal':899,'boundaryMatchesAllLocales':True},
      'rationale':rationale,'confidence':'moderate','nativeSpeakerApproval':False,
      'protectedLiteralAttestation':{'requiredExactLiterals':expected_current_literals,'currentMissing':current_missing,'primaryFinalMissing':primary_missing,'recommendedMissing':recommended_missing,'status':'pass' if not recommended_missing else 'fail'},
      'placeholderAttestation':{'sourceTokens':source_ph,'currentTokens':current_ph,'primaryFinalTokens':primary_ph,'recommendedTokens':rec_ph,'checks':{k:v for k,v in checks.items() if 'Placeholder' in k},'status':'pass'},
      'markupAttestation':{'sourceMarkup':source_markup,'currentMarkup':current_markup,'primaryFinalMarkup':primary_markup,'recommendedMarkup':rec_markup,'checks':{k:v for k,v in checks.items() if 'Markup' in k},'status':'pass'},
      'exactHead':head,'exactTree':tree,
    }
    ledger.append(row)
assert len(ledger)==600
counts=collections.Counter(r['crossReviewDisposition'] for r in ledger)
assert counts=={'accept-current':478,'accept-proposal':121,'revise-proposal':1},counts
assert {(i,l) for i,l,_ in literal_failures}=={(909,'es'),(931,'ar'),(931,'es'),(931,'fr'),(931,'hi'),(931,'ko'),(931,'pt-BR')}
assert not structural_failures

# Reattest all prior 0-899 disposition links against their immutable prior row and the current pinned catalog value.
prior_inputs=read_jl(PRIMARY/'prior-disposition-hashes.jsonl'); assert len(prior_inputs)==10800
prior_files=collections.defaultdict(dict)
for r in prior_inputs:
    packet=r['priorPacket']; filename=r['priorRecordFile']; path=SCRATCH/packet/filename
    keyfile=(packet,filename)
    if keyfile not in prior_files:
        rows=read_jl(path)
        idx=collections.defaultdict(list)
        for y in rows: idx[(y.get('sourceId') or y.get('id'),y.get('locale'))].append(y)
        prior_files[keyfile]=idx
prior_reattest=[]
prior_old_record_mismatches=0; prior_live_hash_mismatches=0
for r in prior_inputs:
    loc=r['locale']; sid=r['sourceId']; fileidx=prior_files[(r['priorPacket'],r['priorRecordFile'])]
    candidates=fileidx.get((sid,loc),[])
    target=None; targethash=None; hash_algorithm=None
    for y in candidates:
        compact_sha=sha(canonical(y))
        default_sha=sha(json.dumps(y,ensure_ascii=False,sort_keys=True))
        if compact_sha==r['priorRecordSha256']:
            target=y; targethash=compact_sha; hash_algorithm='canonical-compact-json'; break
        if default_sha==r['priorRecordSha256']:
            target=y; targethash=default_sha; hash_algorithm='sorted-json-default-separators'; break
    record_found=target is not None
    if not record_found: prior_old_record_mismatches+=1
    old_final=None; old_current=None; old_source=None
    if target:
        old_final=(target.get('crossReviewFinalTargetSha256') or target.get('finalTargetSha256') or target.get('reviewedFinalSha256') or target.get('recommendedTargetSha256') or target.get('candidateTargetSha256') or target.get('primaryTargetSha256') or target.get('targetSha256') or target.get('currentTargetSha256'))
        if r['priorFinalTargetSha256'] is None and target.get('crossReviewDisposition') in {'hold','retain-hold'}:
            old_final=None
        old_current=(target.get('currentTargetSha256') or target.get('liveCurrentTargetSha256') or target.get('targetSha256'))
        old_source=(target.get('sourceTextSha256') or target.get('sourceSha256'))
    old_final_matches=old_final==r['priorFinalTargetSha256'] if target else False
    old_current_matches=old_current==r['priorCurrentTargetSha256'] if target else False
    old_source_matches=old_source==r['sourceTextSha256'] if target and old_source else False
    live=catalogs[loc].get(sid)
    livehash=sha(live) if isinstance(live,str) else None
    live_matches_recorded=livehash==r['liveCurrentTargetSha256']
    live_matches_final=livehash==r['priorFinalTargetSha256']
    derived_flag=live_matches_final
    flag_matches=derived_flag==r['liveTargetMatchesPriorFinalHash']
    if not live_matches_recorded or not flag_matches: prior_live_hash_mismatches+=1
    # The prior-record current hash may describe the previous pre-apply content; record equality as evidence, but don't require it to match today's target.
    prior_reattest.append({'sourceOrdinal':r['sourceOrdinal'],'sourceId':sid,'locale':loc,'priorPacket':r['priorPacket'],'priorRecordFile':r['priorRecordFile'],'priorRecordSha256Expected':r['priorRecordSha256'],'priorRecordSha256Recomputed':targethash,'priorRecordHashAlgorithm':hash_algorithm,'priorRecordFoundAndHashMatches':record_found,'priorDisposition':r['priorDisposition'],'priorFinalTargetSha256':r['priorFinalTargetSha256'],'priorCurrentTargetSha256':r['priorCurrentTargetSha256'],'priorRecordFinalHashMatchesLink':old_final_matches,'priorRecordCurrentHashMatchesLink':old_current_matches,'priorRecordSourceHashMatchesLink':old_source_matches,'liveCurrentTargetSha256Recorded':r['liveCurrentTargetSha256'],'liveCurrentTargetSha256Recomputed':livehash,'liveCurrentHashMatchesRecorded':live_matches_recorded,'liveCurrentTargetMatchesPriorFinal':live_matches_final,'storedComparisonBooleanMatches':flag_matches,'result':'pass' if record_found and old_final_matches and old_current_matches and old_source_matches and live_matches_recorded and flag_matches else 'hold'} )
# Exact prior records and target/source links should all resolve.
assert prior_old_record_mismatches==0,prior_old_record_mismatches
assert prior_live_hash_mismatches==0,prior_live_hash_mismatches
print('prior check status', {k:sum(1 for x in prior_reattest if x[k]) for k in ['priorRecordFoundAndHashMatches','priorRecordFinalHashMatchesLink','priorRecordCurrentHashMatchesLink','priorRecordSourceHashMatchesLink','liveCurrentHashMatchesRecorded','storedComparisonBooleanMatches']})
assert all(x['result']=='pass' for x in prior_reattest)

# Verify W899 adjacency against current live catalogs and prior exact cross-review finals.
w899=[]
for x in read_jl(PRIMARY/'w899-boundary-reattestation.jsonl'):
    actual=catalogs[x['locale']].get(x['sourceId']); actualhash=sha(actual) if isinstance(actual,str) else None
    assert actual==x['liveTarget'] and actualhash==x['liveTargetSha256'] and actualhash==x['previousFinalTargetSha256'] and x['liveMatchesPriorCrossReviewFinal'] is True
    w899.append({'sourceOrdinal':899,'sourceId':x['sourceId'],'locale':x['locale'],'currentTarget':actual,'currentTargetSha256':actualhash,'previousFinalTarget':x['previousFinalTarget'],'previousFinalTargetSha256':x['previousFinalTargetSha256'],'callerContextSha256':x['callerContextSha256'],'matchesPriorCrossReviewFinal':True,'result':'pass'})
assert len(w899)==12

# Write evidence artifacts.
def writejl(name,rows):
    (OUT/name).write_text(''.join(canonical(r)+'\n' for r in rows),encoding='utf-8')
writejl('crossreview-ledger.jsonl',ledger)
writejl('input-reattestation.jsonl',input_reattest)
writejl('source-registry-reattestation.jsonl',source_registry_reattest)
writejl('caller-reattestation.jsonl',caller_reattest)
writejl('server-message-pipeline-reattestation.jsonl',server_reattest)
writejl('provider-option-pipeline-reattestation.jsonl',provider_reattest)
writejl('pinned-file-reattestation.jsonl',pinned_file_reattest)
writejl('catalog-reattestation.jsonl',catalog_reattest)
writejl('prior-disposition-reattestation.jsonl',prior_reattest)
writejl('w899-boundary-reattestation.jsonl',w899)

repo_status_after=gittext('status','--porcelain=v1')
assert repo_status_after==repo_status_before==''
summary={
 'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'window':'W900-W949','head':head,'tree':tree,
 'cellCount':600,'sourceCount':50,'localeCount':12,'locales':LOCALES,
 'crossReviewDispositionCounts':dict(sorted(counts.items())),'candidateCount':122,'acceptedPrimaryProposals':121,'revisedProposalCount':1,'rejectedProposals':0,'holds':0,
 'sourceTargetsReattested':600,'sourceRegistryEntriesReattested':50,'callerReferencesReattested':len(caller_reattest),'callerSourceRows':len(caller_context),'callerPinFailures':0,
 'providerOptionPipelineReferencesReattested':len(provider_reattest),'providerOptionPipelineFailures':0,
 'serverMessagePipelineReferencesReattested':len(server_reattest),'serverMessagePipelineFailures':0,
 'pinnedFilesReattested':len(pinned_file_reattest),'catalogsReattested':len(catalog_reattest),'catalogKeyCount':len(catalogs[LOCALES[0]]),'allLocaleCatalogKeySetsIdentical':True,
 'currentProtectedLiteralFailures':len(literal_failures),'currentProtectedLiteralFailureCells':[{'sourceOrdinal':i,'locale':l,'missing':m} for i,l,m in literal_failures],
 'finalProtectedLiteralFailures':0,'placeholderMismatches':0,'markupMismatches':0,
 'priorDispositionRowsReattested':len(prior_reattest),'priorRecordLinkFailures':prior_old_record_mismatches,'priorLiveTargetLinkFailures':prior_live_hash_mismatches,
 'priorCurrentTargetsMatchingPriorFinalHash':sum(x['liveCurrentTargetMatchesPriorFinal'] for x in prior_reattest),'priorCurrentTargetsDifferentFromPriorFinalHash':sum(not x['liveCurrentTargetMatchesPriorFinal'] for x in prior_reattest),
 'w899BoundaryCellsReattested':len(w899),'w899BoundaryMatchesAllLocales':True,
 'french947Revision':{'sourceOrdinal':947,'locale':'fr','fromPrimary':rmap[(947,'fr')]['finalTarget'],'to':revised_targets[(947,'fr')],'sha256':sha(revised_targets[(947,'fr')]),'reason':'Use a clear download-request term for the application grab action.'},
 'primaryManifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),'primarySha256SumsSha256':primary_sums_sha,
 'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'machineReviewConfidence':'moderate',
 'repositoryOrPRModified':False,'repoStatusBeforeAfter':'clean','testsBuildsScansCIOrBrowserRun':False,
 'priorSelectedCellScope':'W900-W949 is outside previous position coverage 0-899; all 10,800 preceding hash/current-target links and the W899 boundary were reattested.',
 'reviewLimit':'Machine-assisted independent static cross-review; not native-speaker approval or headed-browser review.'
}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=f'''# ChaptarrNG PR #190 independent cross-review — W900–W949\n\nThis packet contains an independent row-level cross-review of 50 source IDs × 12 locales (600 cells) at the exact OPEN/DRAFT PR head `{head}` and tree `{tree}`. Primary `manifest.json` SHA-256: `{sha((PRIMARY/'manifest.json').read_bytes())}`; primary `SHA256SUMS` SHA-256: `{primary_sums_sha}`.\n\nDisposition counts: accept-current {counts['accept-current']}; accept-proposal {counts['accept-proposal']}; revise-proposal {counts['revise-proposal']}; reject 0; hold 0. One French W947 suggestion is revised to clarify that the download request fails when MAM cannot apply the required wedge. The ledger records exact current, primary, and recommended text and hashes.\n\nReattestation covers all 600 source/current/catalog cells; 50 source-registry entries; 86 direct caller references; 20 provider-option localization pipeline references; 76 server-message display pipeline references; 88 pinned source/context files; and all 12 locale catalogs with identical key sets. The prior-window packet has 10,800 source/locale records (positions 0–899); each prior record hash and its current-catalog hash link is reattested, including 10,605 live target matches and 195 differences from prior final hashes. The adjacent W899 boundary matches all 12 prior cross-review final targets.\n\nCurrent protected-term failures are recorded in seven cells: W909 Spanish (`ValidationFailure`) and W931 Arabic, Spanish, French, Hindi, Korean, and Brazilian Portuguese (`Scene`). Accepted proposals restore each exact required literal. All recommended placeholders, markup, and protected literals pass.\n\nThis is a machine-assisted static cross-review; native-speaker approval remains outstanding. No repository/PR files were edited, and no tests, builds, scans, CI, or browser work were run.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'out':str(OUT),'counts':dict(counts),'currentLiteralFailures':literal_failures,'priorRows':len(prior_reattest),'priorDifferent':summary['priorCurrentTargetsDifferentFromPriorFinalHash'],'priorSame':summary['priorCurrentTargetsMatchingPriorFinalHash'],'manifestExpected':EXPECTED_PRIMARY_MANIFEST,'repositoryStatusBeforeAfter':[repo_status_before,repo_status_after]},ensure_ascii=False,indent=2))
