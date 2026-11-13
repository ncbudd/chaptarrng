import collections, hashlib, json, pathlib, re, subprocess, sys

W = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0600-0649-f405')
O = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0600-0649-primary-20261102')
REPO = 'snapetech-org/chaptarrng'
PR = 190
EXPECTED_HEAD = 'f405a6256c2661e48e412ac4471ce70411baf98c'
EXPECTED_TREE = 'fe3272572b68460f1d8c8083a5dcc44cd3307b74'
LOCALES = {'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
EXPECTED_IDS = ['server.message.m584bfe0a179c', 'server.message.m5932f2bdbcc6', 'server.message.m596c52f1eb65', 'server.message.m5b6d7aa6820c', 'server.message.m5b910b94aba9', 'server.message.m5c7dc17c0c8a', 'server.message.m5e5d2164fab5', 'server.message.m5e7b4e24492a', 'server.message.m5fb9cde07f1e', 'server.message.m6009908a8660', 'server.message.m609ed5f60975', 'server.message.m611d3cc87d4d', 'server.message.m6139d49128ce', 'server.message.m61760b3f62ff', 'server.message.m61c49aa34607', 'server.message.m61da366a8aae', 'server.message.m623b1093a9c9', 'server.message.m629e576013e4', 'server.message.m62fb6085c79e', 'server.message.m63cf73c14226', 'server.message.m6472be787d0d', 'server.message.m648eddf3f253', 'server.message.m64f4a104ceb4', 'server.message.m65fe7c1758c8', 'server.message.m661c5d4d3f03', 'server.message.m66985c5dac1d', 'server.message.m685f5e4db612', 'server.message.m6a4ba853f563', 'server.message.m6a53e8d74c29', 'server.message.m6b5f4e5a738f', 'server.message.m6b84bc76853e', 'server.message.m6c1fa02a292a', 'server.message.m6c603ef38ec7', 'server.message.m6d50cedf6d28', 'server.message.m6d69cc1ffcc4', 'server.message.m6db923fcd485', 'server.message.m6e47fb747806', 'server.message.m6eacf3f8c517', 'server.message.m6f4b44ab4677', 'server.message.m6f5afb1bfba0', 'server.message.m6f6371d18348', 'server.message.m712918a2c28f', 'server.message.m7132fb6d87f4', 'server.message.m72a9cf77e4de', 'server.message.m730e082c3d8d', 'server.message.m750a8cd4307a', 'server.message.m7549882d4eb5', 'server.message.m755b576eb46b', 'server.message.m7599301a1c84', 'server.message.m760d3d8feb20']

# Frozen cell recommendations from review-plan.json.
PLAN = json.loads((O/'review-plan.json').read_text())
PROPOSALS = collections.defaultdict(dict)
REFINEMENTS = set()
for _cell_key, _entry in PLAN.items():
  _ordinal, _locale = _cell_key.split('|', 1)
  _ordinal = int(_ordinal)
  PROPOSALS[_ordinal][_locale] = _entry['recommendedTarget']
  if _entry.get('disposition') == 'propose-refinement':
    REFINEMENTS.add((_ordinal, _locale))

PROTECTED = {601: ['AudioBookShelf'], 605: ['Windows'], 606: ['provider:id'], 609: ['Chaptarr', 'chaptarrbot', 'discord'], 611: ['{value0}'], 612: ['CloudFlare', 'CAPTCHA'], 614: ['{value0}'], 615: ['{value0}'], 616: ['Torrent Download Station'], 618: ['Plex Media Server'], 620: ['Ignore Download', 'API', 'removeFromClient=false', 'Chaptarr'], 623: ['Goodreads', '{value0}'], 626: ['ids'], 628: ['Goodreads', '{value0}', '{value1}'], 629: ['NzbGet', 'KeepHistory', '0'], 630: ['{value0}'], 633: ['/'], 635: ['Chaptarr', '{value0}'], 636: ['{value0}'], 637: ['bookFileIds'], 638: ['Regex'], 639: ['CPU'], 640: ['provider:id', '0'], 642: ['selectedBooks'], 649: ['Chaptarr', 'URL']}
CASEFOLD_PROTECTED = {609:['discord']}

def protected_contains(ordinal, literal, value):
  if literal in CASEFOLD_PROTECTED.get(ordinal, []):
    return literal.casefold() in value.casefold()
  return literal in value


# For rows whose message key is absent from C# the exact English source text or template is pinned.
FALLBACKS = {600: [('Quality Profile does not exist', 'source-text-exact', 'src/NzbDrone.Core/Validation/QualityProfileExistsValidator.cs')], 603: [('Retry scheduled', 'source-text-exact', 'src/Chaptarr.Api.V1/PendingImport/PendingAuthorImportController.cs')], 604: [('Failed to download image', 'source-text-exact', 'src/Chaptarr.Api.V1/Author/AuthorController.cs')], 605: [('Mapped Network Drive and Windows Service', 'source-text-exact', 'src/NzbDrone.Core/Validation/Paths/MappedNetworkDriveValidator.cs')], 606: [("Invalid provider ID format. Expected 'provider:id'.", 'source-text-exact', 'src/NzbDrone.Core/Validation/ProviderIdValidator.cs')], 608: [('Cannot combine file deletion with re-add.', 'source-text-exact', 'src/Chaptarr.Api.V1/Author/AuthorController.cs')], 609: [("The author isn't available yet on the metadata server. Chaptarr has queued the import and will automatically add them when they become available (you can visit the chaptarrbot channel in our discord to ask for updates).", 'source-text-exact', 'src/Chaptarr.Api.V1/Author/AuthorController.cs')], 610: [('Cannot re-add author: the author is not available on the metadata server.', 'source-text-exact', 'src/Chaptarr.Api.V1/Author/AuthorController.cs')], 611: [("Path '{path}' is already configured for another author", 'normalized-validation-template', 'src/NzbDrone.Core/Validation/Paths/AuthorPathValidator.cs')], 620: [('This torrent is protected by the permanent seeding/download preservation policy. ', 'source-text-fragment', 'src/Chaptarr.Api.V1/Queue/QueueController.cs'), ("Choose 'Ignore Download' (API: removeFromClient=false) to remove it from Chaptarr without deleting it from the client. ", 'source-text-fragment', 'src/Chaptarr.Api.V1/Queue/QueueController.cs'), ('To delete the torrent and its files, remove it directly in your download client.', 'source-text-fragment', 'src/Chaptarr.Api.V1/Queue/QueueController.cs')], 626: [('ids must be provided', 'source-text-exact', 'src/Chaptarr.Api.V1/ProviderControllerBase.cs')], 630: [("Path '{path}' is an ancestor of an existing root folder", 'normalized-validation-template', 'src/NzbDrone.Core/Validation/Paths/RootFolderAncestorValidator.cs')], 632: [('Message = "The author isn\'t available yet on the metadata server."', 'source-text-exact', 'src/Chaptarr.Api.V1/Author/AuthorController.cs')], 633: [("Cannot be set to '/'", 'source-text-exact', 'src/Chaptarr.Api.V1/RemotePathMappings/RemotePathMappingController.cs')], 637: [('bookFileIds must belong to one import unit', 'source-text-exact', 'src/Chaptarr.Api.V1/ManualImport/ManualImportController.cs')], 638: [('Regex Pattern must not be empty', 'source-text-exact', 'src/NzbDrone.Core/CustomFormats/Specifications/RegexSpecificationBase.cs')], 639: [('Max CPU threads must be greater than or equal to concurrent conversions', 'source-text-exact', 'src/Chaptarr.Api.V1/Config/ConversionConfigController.cs')], 640: [("Invalid edition ID format. Expected 'provider:id' or '0'", 'source-text-exact', 'src/Chaptarr.Api.V1/Books/BookController.cs')], 644: [('Must contain Author name', 'source-text-exact', 'src/NzbDrone.Core/Organizer/FileNameValidation.cs')], 646: [('Author IDs must be positive numbers.', 'source-text-exact', 'src/Chaptarr.Api.V1/Author/AuthorMediaMoveController.cs')], 647: [('Must match Password', 'source-text-exact', 'src/Chaptarr.Api.V1/Config/HostConfigController.cs')], 648: [('file must be provided', 'source-text-exact', 'src/Chaptarr.Api.V1/System/Backup/BackupController.cs')]}

def run(args, text=True):
  return subprocess.check_output(args, text=text)
def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def git(*args, text=True): return run(['git','-C',str(W),*args],text=text)
def read_git(path): return git('show',f'HEAD:{path}',text=False)
def tracked_info(path):
  b=read_git(path)
  return {'path':path,'blob':git('rev-parse',f'HEAD:{path}').strip(),'sha256':sha(b),'bytes':len(b)}
def save_json(path,obj): (O/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def save_jsonl(path,rows): (O/path).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
  if re.fullmatch(r'<[^<>/]+>',s): return []
  return re.findall(r'</?[A-Za-z][^>]*>',s)
def live_pr():
  pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
  tree=run(['gh','api',f'repos/{REPO}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
  return pr,tree

head=git('rev-parse','HEAD').strip(); tree=git('rev-parse','HEAD^{tree}').strip()
if head!=EXPECTED_HEAD or tree!=EXPECTED_TREE: raise SystemExit(f'expected pinned head/tree {EXPECTED_HEAD}/{EXPECTED_TREE}; found {head}/{tree}')
pr, live_tree=live_pr()
if pr['headRefOid']!=head or live_tree!=tree or pr['state']!='OPEN' or not pr['isDraft']:
  raise SystemExit('live PR preflight mismatch: '+json.dumps({'pr':pr,'tree':live_tree}))
if git('status','--porcelain').strip(): raise SystemExit('worktree is not clean; refusing scratch packet build')

source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_bytes=read_git(source_path); source_catalog=json.loads(source_bytes)
follow_path='docs/localization/source-followup-20261101.json'; follow_bytes=read_git(follow_path); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
if len(ids)!=1210 or len(set(ids))!=1210: raise SystemExit('source follow-up inventory drift')
source_ids=ids[600:650]
if source_ids!=EXPECTED_IDS: raise SystemExit('W600–649 source ID boundary drift: '+json.dumps(source_ids))
registry_path='docs/localization/provider-field-sources.json'; registry_bytes=read_git(registry_path); registry=json.loads(registry_bytes); reg_by={x['id']:x for x in registry['records']}
catalogs={}; catalog_info={}
for loc,file in LOCALES.items():
  path=f'src/NzbDrone.Core/Localization/Core/{file}'; b=read_git(path); catalogs[loc]=json.loads(b); catalog_info[loc]=tracked_info(path)
  if set(catalogs[loc])!=set(source_catalog): raise SystemExit(f'catalog key inventory drift for {loc}')
source_info=tracked_info(source_path); follow_info=tracked_info(follow_path); registry_info=tracked_info(registry_path)

# Search only production C# trees. Key-based matches are exact; absent-key rows use reviewed literal/template pins.
roots=[str(W/'src/NzbDrone.Core'),str(W/'src/Chaptarr.Api.V1'),str(W/'src/Chaptarr.Http')]
def find_needle(needle, path=None):
  paths=[str(W/path)] if path else roots
  cmd=['rg','--no-heading','--color','never','--with-filename','-n','-F','-e',needle,'--glob','*.cs',*paths]
  p=subprocess.run(cmd,text=True,capture_output=True)
  if p.returncode not in (0,1): raise SystemExit('caller search failed: '+p.stderr)
  out=[]
  for row in p.stdout.splitlines():
    try: fp,lineno,line=row.split(':',2); n=int(lineno)
    except ValueError: continue
    rel=str(pathlib.Path(fp).resolve().relative_to(W.resolve()))
    out.append((rel,n,line))
  return out

raw=collections.defaultdict(list)
for ordinal,sid in enumerate(source_ids,600):
  for fp,n,line in find_needle(sid): raw[sid].append((fp,n,line,'exact-source-id'))
for ordinal,rules in FALLBACKS.items():
  sid=source_ids[ordinal-600]
  for needle,mode,expected_path in rules:
    hits=find_needle(needle,expected_path)
    if not hits: raise SystemExit(f'caller pin missing for {ordinal} {sid}: {needle}')
    for fp,n,line in hits:
      if fp!=expected_path: raise SystemExit(f'caller pin path drift for {ordinal}: {fp} != {expected_path}')
      raw[sid].append((fp,n,line,mode))
# The generic RSS interval and Chaptarr instance-name rows have their validation consumers pinned above.

caller_rows=[]; callers_by_id={}; caller_gaps=[]; caller_mismatches=[]; unique_files=set(); total_refs=0
for ordinal,sid in enumerate(source_ids,600):
  refs=[]; seen=set()
  for fp,n,line,mode in sorted(raw.get(sid,[]),key=lambda x:(x[0],x[1],x[3])):
    if (fp,n) in seen: continue
    seen.add((fp,n)); content=read_git(fp); lines=content.decode('utf-8').splitlines()
    if not 1<=n<=len(lines) or lines[n-1]!=line:
      caller_mismatches.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':fp,'line':n,'reason':'lookup line differs from pinned HEAD content'}); continue
    unique_files.add(fp); total_refs+=1
    refs.append({'file':fp,'kind':mode,'currentLine':n,'lineMatchMethod':mode,'matchedSourceId':sid if mode=='exact-source-id' else None,'matchedSourceText':source_catalog[sid] if mode!='exact-source-id' else None,'currentLineText':line,'currentLineSha256':sha(line.encode()),'contextBefore':lines[max(0,n-3):n-1],'contextAfter':lines[n:min(len(lines),n+2)],'currentFileBlob':git('rev-parse',f'HEAD:{fp}').strip(),'currentFileSha256':sha(content)})
  if not refs: caller_gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no production source key or approved literal/template caller pin'})
  callers_by_id[sid]=refs
  rec=reg_by.get(sid)
  row={'sourceOrdinal':ordinal,'sourceId':sid,'attestedHead':head,'attestedTree':tree,'sourceText':source_catalog[sid],'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'sourceFingerprint':rec.get('sourceFingerprint') if rec else None,'callerReferenceStatus':'pinned' if refs else 'gap','callerRefs':refs,'callerContextSha256':sha(jbytes(refs))}
  caller_rows.append(row)
if caller_gaps or caller_mismatches: raise SystemExit('caller coverage problem: '+json.dumps({'gaps':caller_gaps,'mismatches':caller_mismatches},ensure_ascii=False))

source_rows=[]; input_rows=[]; review_rows=[]; literal_rows=[]
source_id_hash=sha(jbytes(ids)); cat_paths={'en':source_path,**{loc:f'src/NzbDrone.Core/Localization/Core/{file}' for loc,file in LOCALES.items()}}
for ordinal,sid in enumerate(source_ids,600):
  src=source_catalog[sid]; source_ph=placeholders(src); source_markup=markup(src); protected=PROTECTED.get(ordinal,[])
  srow={'sourceOrdinal':ordinal,'sourceId':sid,'source':src,'sourceKeySha256':sha(sid.encode()),'sourceTextSha256':sha(src.encode()),'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'sourceFollowupPath':follow_path,'sourceFollowupBlob':follow_info['blob'],'sourceFollowupSha256':follow_info['sha256'],'sourceIdListCount':len(ids),'sourceIdListSha256':source_id_hash,'registryPath':registry_path if sid in reg_by else None,'registryBlob':registry_info['blob'] if sid in reg_by else None,'registrySha256':registry_info['sha256'] if sid in reg_by else None,'sourceFingerprint':reg_by[sid].get('sourceFingerprint') if sid in reg_by else None,'callerRefs':callers_by_id[sid],'callerContextSha256':sha(jbytes(callers_by_id[sid]))}
  source_rows.append(srow)
  for loc in LOCALES:
    current=catalogs[loc][sid]; current_hash=sha(current.encode()); current_ph=placeholders(current); current_markup=markup(current)
    proposed=PROPOSALS.get(ordinal,{}).get(loc)
    if proposed is not None:
      disposition='propose-refinement' if (ordinal,loc) in REFINEMENTS else 'propose-correction'
      _plan_entry=PLAN.get(f'{ordinal}|{loc}',{})
      confidence=_plan_entry.get('confidence','moderate')
      rationale=_plan_entry.get('rationale',f"This target is revised for natural {loc} phrasing and exact source meaning in the pinned caller context, preserving required placeholders and protected literals.")
    else:
      disposition='accept-current'; proposed=None; confidence='moderate'
      rationale=f"The current {loc} target preserves the source meaning in the pinned caller context and has no material semantic or terminology issue."
    proposed_hash=sha(proposed.encode()) if proposed else None
    checks=[]
    for literal in protected:
      checks.append({'literal':literal,'matchMode':'case-insensitive' if literal in CASEFOLD_PROTECTED.get(ordinal,[]) else 'exact','presentInSource':protected_contains(ordinal,literal,src),'presentInCurrentTarget':protected_contains(ordinal,literal,current),'presentInRecommendedTarget':protected_contains(ordinal,literal,proposed) if proposed is not None else None})
    current_missing=[x['literal'] for x in checks if not x['presentInCurrentTarget']]
    proposed_missing=[x['literal'] for x in checks if proposed is not None and not x['presentInRecommendedTarget']]
    if proposed is not None and placeholders(proposed)!=source_ph:
      raise SystemExit(f'placeholder mismatch in proposed {ordinal}|{loc}: source={source_ph}, proposed={placeholders(proposed)}')
    if proposed is not None and markup(proposed)!=source_markup:
      raise SystemExit(f'markup mismatch in proposed {ordinal}|{loc}')
    if proposed_missing: raise SystemExit(f'protected literal missing from proposal {ordinal}|{loc}: {proposed_missing}')
    input_rows.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':sha(src.encode()),'sourcePlaceholders':source_ph,'sourceMarkup':source_markup,'currentTarget':current,'currentTargetSha256':current_hash,'currentTargetPlaceholders':current_ph,'currentTargetMarkup':current_markup,'targetFile':cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'protectedLiterals':protected,'callerContextSha256':srow['callerContextSha256']})
    review={'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceKeySha256':sha(sid.encode()),'sourceTextSha256':sha(src.encode()),'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'targetFile':cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'currentTarget':current,'currentTargetSha256':current_hash,'disposition':disposition,'recommendedTarget':proposed,'recommendedTargetSha256':proposed_hash,'confidence':confidence,'rationale':rationale,'callerRefs':callers_by_id[sid],'callerContextSha256':srow['callerContextSha256'],'sourcePlaceholders':source_ph,'currentTargetPlaceholders':current_ph,'recommendedPlaceholders':placeholders(proposed) if proposed is not None else None,'placeholderParity':source_ph==current_ph and (proposed is None or source_ph==placeholders(proposed)),'sourceMarkup':source_markup,'currentTargetMarkup':current_markup,'recommendedTargetMarkup':markup(proposed) if proposed is not None else None,'markupParity':source_markup==current_markup and (proposed is None or source_markup==markup(proposed)),'protectedLiterals':protected,'protectedLiteralChecks':checks,'protectedLiteralsPreserved':not current_missing and not proposed_missing,'protectedLiteralMismatches':{'current':current_missing,'recommended':proposed_missing},'nativeSpeakerApproval':False,'priorDisposition':'no prior source ID window disposition; non-overlap scan is recorded in prior-disposition-boundary.json'}
    review_rows.append(review)
    literal_rows.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'sourceText':src,'currentTarget':current,'currentTargetSha256':current_hash,'finalTarget':proposed or current,'finalTargetSha256':proposed_hash or current_hash,'checks':checks,'currentMismatches':current_missing,'recommendedMismatches':proposed_missing,'placeholderParity':review['placeholderParity'],'markupParity':review['markupParity']})
if len(review_rows)!=600: raise SystemExit('expected exactly 600 review cells')

# Adjacent W599 is context only. Re-attest its previous primary ledger and current target/caller hashes.
prior_packet=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0550-0599-primary-20261102')
prior_sid=ids[599]; prior_by_locale={}
for fp,n,line in find_needle(prior_sid):
  raw[prior_sid].append((fp,n,line,'exact-source-id'))
for line in (prior_packet/'review-cells.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==599 and x.get('sourceId')==prior_sid: prior_by_locale[x['locale']]=x
if set(prior_by_locale)!=set(LOCALES): raise SystemExit('W599 prior primary boundary coverage incomplete')
prior_refs=[]
for fp,n,line,mode in sorted(raw.get(prior_sid,[]),key=lambda x:(x[0],x[1],x[3])):
  content=read_git(fp); lines=content.decode('utf-8').splitlines()
  if lines[n-1]!=line: raise SystemExit(f'W599 caller drift at {fp}:{n}')
  prior_refs.append({'file':fp,'kind':mode,'currentLine':n,'lineMatchMethod':mode,'matchedSourceId':prior_sid if mode=='exact-source-id' else None,'currentLineText':line,'currentLineSha256':sha(line.encode()),'contextBefore':lines[max(0,n-3):n-1],'contextAfter':lines[n:min(len(lines),n+2)],'currentFileBlob':git('rev-parse',f'HEAD:{fp}').strip(),'currentFileSha256':sha(content)})
prior_refs_hash=sha(jbytes(prior_refs)); prior_records=[]
for loc,x in sorted(prior_by_locale.items()):
  live_source=source_catalog[prior_sid]; live_target=catalogs[loc][prior_sid]
  prior_refs_saved=x.get('callerRefs',[])
  saved_ref_keys={(r.get('file'),r.get('currentLine'),r.get('currentLineText')) for r in prior_refs_saved}
  live_ref_keys={(r.get('file'),r.get('currentLine'),r.get('currentLineText')) for r in prior_refs}
  prior_records.append({'contextSourceOrdinal':599,'sourceId':prior_sid,'source':live_source,'sourceTextSha256':sha(live_source.encode()),'locale':loc,'priorPrimaryPacketHead':x.get('exactHead'),'priorPrimaryPacketTree':x.get('exactTree'),'priorDisposition':x.get('disposition'),'priorRecommendedTarget':x.get('recommendedTarget'),'priorRecommendedTargetSha256':x.get('recommendedTargetSha256'),'priorCurrentTarget':x.get('currentTarget'),'priorCurrentTargetSha256':x.get('currentTargetSha256'),'liveCurrentTarget':live_target,'liveCurrentTargetSha256':sha(live_target.encode()),'priorTargetMatchesLive':x.get('currentTarget')==live_target,'priorRecommendationMatchesLive':x.get('recommendedTarget')==live_target if x.get('recommendedTarget') else None,'sourceMatchesLive':x.get('source')==live_source,'priorCallerRefs':prior_refs_saved,'liveCallerRefs':prior_refs,'callerContextSha256':prior_refs_hash,'callerRefsMatchPrior':saved_ref_keys==live_ref_keys,'contextOnly':True})

# Scan earlier review ledgers for source-ID overlap; current W600–649 remains disjoint.
prior_ledgers=[]; overlap_rows=[]; prior_ids=set(); prior_disposition_rows=0
for packet in sorted(O.parent.glob('chaptarrng-pr190-*')):
  if packet.resolve()==O.resolve(): continue
  for fp in sorted(packet.rglob('*.jsonl')):
    try: lines=fp.read_text().splitlines()
    except Exception: continue
    parsed=[]
    for line in lines:
      try: x=json.loads(line)
      except Exception: continue
      sid=x.get('sourceId',x.get('id',x.get('catalogKey')))
      ordinal=x.get('sourceOrdinal',x.get('sourcePosition',x.get('windowOrdinal')))
      disposition=next((x.get(k) for k in ('disposition','primaryDisposition','primaryVerdict','crossDisposition','crossReviewDisposition','reviewDisposition','independentVerdict','finalDisposition') if x.get(k) is not None),None)
      if isinstance(ordinal,int) and ordinal<600 and sid and disposition is not None:
        parsed.append(x); prior_ids.add(sid); prior_disposition_rows+=1
        if sid in source_ids: overlap_rows.append({'ledger':str(fp),'sourceOrdinal':ordinal,'sourceId':sid,'locale':x.get('locale'),'disposition':disposition})
    if parsed: prior_ledgers.append({'path':str(fp),'sha256':sha(fp.read_bytes()),'dispositionRowsBefore600':len(parsed),'sourceIds':sorted({x.get('sourceId') for x in parsed if x.get('sourceId')})})
if overlap_rows: raise SystemExit('source ID overlap with prior window: '+json.dumps(overlap_rows,ensure_ascii=False))

save_jsonl('source-slice.jsonl',source_rows)
save_jsonl('caller-context.jsonl',caller_rows)
save_jsonl('input-cells.jsonl',input_rows)
save_jsonl('review-cells.jsonl',review_rows)
save_jsonl('protected-literal-integrity.jsonl',literal_rows)
save_jsonl('correction-candidates.jsonl',[x for x in review_rows if x['disposition']!='accept-current'])
save_jsonl('prior-context-dispositions.jsonl',prior_records)
save_json('prior-disposition-boundary.json',{'scopePositions':[600,649],'searchedPriorPositions':[0,599],'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids),'priorDispositionRows':prior_disposition_rows,'matchingPriorRows':overlap_rows,'matchingPriorRowCount':len(overlap_rows),'disjointCurrentSourceIds':not overlap_rows,'ledgerFiles':prior_ledgers,'contextOnlyPreviousSourceId':prior_sid,'contextOnlyPreviousRows':len(prior_records),'adjacentW599CallerRefs':len(prior_refs),'adjacentW599CallerContextSha256':prior_refs_hash,'adjacentW599TargetsMatchingOlderPrimary':sum(x['priorTargetMatchesLive'] for x in prior_records),'adjacentW599PrimaryRecommendationsMatchingLive':sum(bool(x['priorRecommendationMatchesLive']) for x in prior_records),'adjacentW599SourceHashesMatchLive':sum(x['sourceMatchesLive'] for x in prior_records)})

# Persist the decision summary used to construct exact-hash review rows.
findings={}
source_rationales={}
for ordinal in range(600,650):
  sid=source_ids[ordinal-600]; source_rationales[str(ordinal)]='The pinned production caller establishes the API, validation, status-toast, or media-operation context for this message; proposals preserve that meaning and its technical identifiers.'
  for loc,target in PROPOSALS.get(ordinal,{}).items():
    disposition='propose-refinement' if (ordinal,loc) in REFINEMENTS else 'propose-correction'
    _plan_entry=PLAN.get(f'{ordinal}|{loc}',{})
    findings[f'{ordinal}|{loc}']=[disposition,target,_plan_entry.get('rationale',f"Revises the {loc} wording while preserving the source meaning in the pinned caller context."),_plan_entry.get('confidence','moderate')]
save_json('review-decisions.json',{'schemaVersion':1,'reviewer':'primary semantic reviewer','scope':[600,649],'findings':findings,'sourceRationales':source_rationales,'acceptedCellRationale':'Current target preserves source meaning in the exact pinned production caller context; no material issue found.','nativeSpeakerApproval':False})
save_json('reviewer-provenance.json',{'reviewerRole':'primary semantic reviewer','reviewType':'independent caller-context-aware language and terminology review of all frozen current cells','exactHead':head,'exactTree':tree,'scope':{'positions':[600,649],'cells':600,'locales':list(LOCALES)},'evidenceSources':['English source catalog','12 locale catalogs','exact production C# source-ID references and pinned English source/template callsites','pinned English-source, normalized-validator-template, or source-fragment production caller pins','W599 adjacent primary packet and current target reattestation'],'protectedLiteralPolicy':'Preserve exact source placeholders, product names, API field names, protocol URLs, enum tokens, version and range values, and machine-readable identifiers; localize ordinary user-facing language.','nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False})

counts=collections.Counter(x['disposition'] for x in review_rows)
for key in ('accept-current','propose-refinement','propose-correction','hold'): counts.setdefault(key,0)
per_locale={}
for loc in LOCALES:
  c=collections.Counter(x['disposition'] for x in review_rows if x['locale']==loc)
  per_locale[loc]={key:c.get(key,0) for key in ('accept-current','propose-refinement','propose-correction','hold')}
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'livePullRequest':pr,'scope':{'positions':[600,649],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceIdListSha256':source_id_hash,'sourceSliceIdsSha256':sha(jbytes(source_ids)),'counts':dict(counts),'proposalCount':sum(counts[k] for k in ('propose-refinement','propose-correction')),'perLocale':per_locale,'callerEvidence':{'sourceIdsWithCallerPins':sum(bool(v) for v in callers_by_id.values()),'callerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'mismatches':len(caller_mismatches),'gaps':caller_gaps,'allCallersAttestedAtExactHead':not caller_gaps and not caller_mismatches},'placeholders':{'sourcesWithPlaceholders':sum(bool(placeholders(source_catalog[sid])) for sid in source_ids),'mismatches':sum(not x['placeholderParity'] for x in review_rows)},'markup':{'sourcesWithMarkup':sum(bool(markup(source_catalog[sid])) for sid in source_ids),'mismatches':sum(not x['markupParity'] for x in review_rows)},'protectedLiterals':{'checkedCells':len(literal_rows),'currentMismatches':sum(bool(x['currentMismatches']) for x in literal_rows),'currentMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missing':x['currentMismatches']} for x in literal_rows if x['currentMismatches']],'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows),'recommendedMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missing':x['recommendedMismatches']} for x in literal_rows if x['recommendedMismatches']]},'priorDispositionBoundary':{'priorSourceIdOverlap':len(overlap_rows),'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids),'contextOnlyW599Rows':len(prior_records),'w599SourceRowsMatchingLive':sum(x['sourceMatchesLive'] for x in prior_records),'w599TargetsMatchingOlderPrimary':sum(x['priorTargetMatchesLive'] for x in prior_records),'w599AppliedRecommendationsMatchingLive':sum(bool(x['priorRecommendationMatchesLive']) for x in prior_records),'w599CallerRefsReattested':len(prior_refs)},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('summary.json',summary)

final_pr,final_tree=live_pr()
final_head=git('rev-parse','HEAD').strip(); final_worktree_tree=git('rev-parse','HEAD^{tree}').strip()
if final_head!=head or final_worktree_tree!=tree or final_pr['headRefOid']!=head or final_tree!=tree or final_pr['state']!='OPEN' or not final_pr['isDraft']:
  save_json('final-reattestation.json',{'passed':False,'expectedHead':head,'expectedTree':tree,'finalHead':final_head,'finalWorktreeTree':final_worktree_tree,'finalPullRequest':final_pr,'finalLiveTree':final_tree})
  raise SystemExit('live PR moved during packet construction; preserve packet and report drift')
save_json('final-reattestation.json',{'passed':True,'exactHead':head,'exactTree':tree,'pullRequestState':final_pr['state'],'isDraft':final_pr['isDraft'],'headRefName':final_pr['headRefName'],'sourceIds':50,'localeCells':len(input_rows),'sourceTextHashes':len(source_rows),'callerRefs':total_refs,'callerContextHashes':len(caller_rows),'w599ContextRows':len(prior_records),'w599SourceRowsMatchingLive':sum(x['sourceMatchesLive'] for x in prior_records),'w599LiveTargetHashesRecorded':len(prior_records),'repositoryClean':not git('status','--porcelain').strip(),'repositoryModified':False})

# Build input checksums from blobs at the frozen exact head, not working-tree paths.
caller_file_infos=[]
for _refs in callers_by_id.values():
  for _ref in _refs:
    caller_file_infos.append({'path':_ref['file'],'sha256':_ref['currentFileSha256']})
caller_file_infos={x['path']:x for x in caller_file_infos}
input_files=[source_info,follow_info,registry_info,*catalog_info.values(),*caller_file_infos.values()]
(O/'INPUT-SHA256SUMS').write_text(''.join(f"{x['sha256']}  {x['path']}\n" for x in input_files))
(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W600–649 primary semantic review\n\n- Exact PR state: OPEN/DRAFT at `{head}` / tree `{tree}`.\n- Scope: source-list positions 600–649 across 12 locales = 50 source IDs / 600 current locale cells.\n- Exact source inventory: `source-slice.jsonl`; source-list SHA-256 `{source_id_hash}`.\n- Production caller pins: {len(caller_rows)} of 50 source IDs, {total_refs} exact C# source-ID/template references across {len(unique_files)} files; gaps and mismatches: 0.\n- Dispositions: {dict(counts)}. Every cell has exact source/current-target hashes and caller context in `review-cells.jsonl`; recommendations are in `correction-candidates.jsonl`.\n- Placeholder mismatches: {summary['placeholders']['mismatches']}; markup mismatches: {summary['markup']['mismatches']}; current protected-literal mismatch cells: {summary['protectedLiterals']['currentMismatches']}; proposed protected-literal mismatches: {summary['protectedLiterals']['recommendedMismatches']}.\n- W599 adjacent context: source hash was reattested; {summary['priorDispositionBoundary']['w599TargetsMatchingOlderPrimary']} of 12 previous current targets still match, while {summary['priorDispositionBoundary']['w599AppliedRecommendationsMatchingLive']} prior recommendations match the live targets after the apply commit. All 12 live target hashes and caller refs are recorded.\n- Earlier ledger overlap: {len(overlap_rows)} source IDs.\n- Primary model review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.\n\nSee `summary.json`, `manifest.json`, and `SHA256SUMS` for packet inventory and integrity.\n''')

# Record exact input manifest and every packet-file digest before the checksum manifest itself.
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':head,'tree':tree,'livePullRequest':final_pr,'positions':[600,649],'sourceIdCount':50,'locales':list(LOCALES),'cellCount':600,'sourceFollowup':follow_info,'sourceFile':source_info,'registry':registry_info,'catalogs':catalog_info,'sourceListSha256':source_id_hash,'files':[]}
for fp in sorted(O.iterdir()):
  if fp.is_file() and fp.name not in ('manifest.json','SHA256SUMS'):
    manifest['files'].append({'path':fp.name,'bytes':fp.stat().st_size,'sha256':sha(fp.read_bytes())})
save_json('manifest.json',manifest)
all_files=sorted(fp for fp in O.iterdir() if fp.is_file() and fp.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f'{sha(fp.read_bytes())}  {fp.name}\n' for fp in all_files))
# Re-query exact PR state after all evidence writes and verify the checksummed packet.
post_pr,post_tree=live_pr(); post_head=git('rev-parse','HEAD').strip(); post_worktree_tree=git('rev-parse','HEAD^{tree}').strip()
if (post_head,post_worktree_tree,post_pr['headRefOid'],post_tree,post_pr['state'],post_pr['isDraft'])!=(head,tree,head,tree,'OPEN',True):
  raise SystemExit('post-write live PR exact-head verification failed')
for line in (O/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1)
  if sha((O/name).read_bytes())!=digest: raise SystemExit(f'packet checksum failure: {name}')
print(json.dumps({'packet':str(O),'head':head,'tree':tree,'cells':len(review_rows),'counts':dict(counts),'callerRefs':total_refs,'callerFiles':len(unique_files),'placeholdersMismatch':summary['placeholders']['mismatches'],'markupMismatch':summary['markup']['mismatches'],'currentProtectedMismatchCells':summary['protectedLiterals']['currentMismatches'],'proposalProtectedMismatchCells':summary['protectedLiterals']['recommendedMismatches'],'w599TargetsMatchingOlderPrimary':summary['priorDispositionBoundary']['w599TargetsMatchingOlderPrimary'],'w599AppliedRecommendationsMatchingLive':summary['priorDispositionBoundary']['w599AppliedRecommendationsMatchingLive'],'priorOverlap':len(overlap_rows),'postHead':post_head,'packetFiles':len(all_files)+1,'packetBytes':sum(fp.stat().st_size for fp in O.iterdir() if fp.is_file())},ensure_ascii=False,indent=2))
