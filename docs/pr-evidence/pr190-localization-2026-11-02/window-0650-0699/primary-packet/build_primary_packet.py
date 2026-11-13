import collections, hashlib, json, pathlib, re, subprocess, sys

W = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0650-0699-4701933')
O = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-primary-20261102')
REPO = 'snapetech-org/chaptarrng'
PR = 190
EXPECTED_HEAD = '4701933a50d367406fd6749c4baaf4befee22129'
EXPECTED_TREE = '2b22ea480c934d2dc41c6813b1296f1a3c41b027'
LOCALES = {'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
EXPECTED_IDS = ['server.message.m770a27077301', 'server.message.m7731b01b80f7', 'server.message.m77e713c55a04', 'server.message.m78052ec2df88', 'server.message.m783307436ce0', 'server.message.m78430e265616', 'server.message.m794b67a4d3b9', 'server.message.m7973f38eea7b', 'server.message.m79dd817b4295', 'server.message.m7a3bf57a5ad5', 'server.message.m7ab62ae2fee8', 'server.message.m7aeae1412484', 'server.message.m7b1828c8a2bc', 'server.message.m7b1e864e07d8', 'server.message.m7b4ba97e5a80', 'server.message.m7b950bff047b', 'server.message.m7bbc018da582', 'server.message.m7be856d3afbe', 'server.message.m7c5d7fa17f19', 'server.message.m7c8622692c56', 'server.message.m7c8c07fd057d', 'server.message.m7d07b7873b14', 'server.message.m7d348cf76a7f', 'server.message.m7d3d73f7deeb', 'server.message.m7d60eb7d5d9a', 'server.message.m7db986dd5235', 'server.message.m7de0a09b7503', 'server.message.m7dedb6f7c9ac', 'server.message.m7e0e0494a488', 'server.message.m7e14e7c3c085', 'server.message.m7ec433f562a8', 'server.message.m7f3f90a53f61', 'server.message.m8003f71f999e', 'server.message.m8017aa9b7412', 'server.message.m80830c01b9f4', 'server.message.m811e40a07580', 'server.message.m81659583b118', 'server.message.m81fa19be5293', 'server.message.m82487c220074', 'server.message.m826b4cc6c84e', 'server.message.m82b97a21c0a9', 'server.message.m82ecc423019b', 'server.message.m82fee98391f9', 'server.message.m830b47a16041', 'server.message.m8387ff993c50', 'server.message.m843e64bf5198', 'server.message.m847a995ca781', 'server.message.m8500a62118c5', 'server.message.m850540ddf332', 'server.message.m850a1729a9c0']

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

PROTECTED = {
  650:['{value0}'], 651:['Kavita'], 652:['Goodreads','OAuth'], 653:['M4B','CPU','{value0}'],
  654:['Check before download','SABnzbd'], 655:['Chaptarr','{value0}','{value1}'], 656:['API'], 657:['{value0}'],
  660:['foreignBookId','foreignAuthorId'], 662:['PAR'], 663:['Apprise'], 664:['{value0}'],
  665:['Disabled','IndexerOnly','ProxyEverything'], 667:['Join'], 668:['Grimmory'], 671:['Hardcover'], 672:['Chaptarr'],
  676:['Aria2','1.34.0','{value0}'], 678:['BookOrbit','URL'], 679:['Goodreads','{value0}'],
  680:['Synology','synoindex'], 684:['MQTT'], 686:['bookFileIds','downloadId'], 688:['{value0}'],
  689:['Goodreads','RSS'], 690:['{value0}'], 691:['{value0}','{value1}'], 692:['API'],
  693:['mediaType','all','audiobook','ebook','{value0}'], 695:['Mailgun'], 696:['API'],
  697:['foreignSeriesId'], 698:['mediaType'], 699:['Http','Socks4','Socks5']
}
CASEFOLD_PROTECTED = {}

def protected_contains(ordinal, literal, value):
  if literal in CASEFOLD_PROTECTED.get(ordinal, []):
    return literal.casefold() in value.casefold()
  return literal in value

# For messages without a direct source-ID use exact English text/template evidence at the production caller.
FALLBACKS = {
650:[("Path '{path}' is already configured as a root folder",'source-text-exact','src/NzbDrone.Core/Validation/Paths/RootFolderValidator.cs')],
653:[('Converting to M4B (','source-text-fragment','src/NzbDrone.Core/MediaFiles/ConversionJobService.cs')],
655:[("Folder '{path}' is not writable by user '{user}'.",'source-template-fragment','src/NzbDrone.Core/Validation/Paths/FolderWritableValidator.cs')],
657:[('A valid {mediaLabel} quality profile is required','source-template-exact','src/Chaptarr.Api.V1/RootFolders/RootFolderController.cs')],
660:[('foreignBookId and foreignAuthorId are required','source-text-exact','src/Chaptarr.Api.V1/Books/BookController.cs')],
662:[('PAR Status:','source-text-fragment','src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs')],
665:[('Proxy mode must be Disabled, IndexerOnly, or ProxyEverything','source-text-exact','src/Chaptarr.Api.V1/Config/HostConfigController.cs')],
669:[('The library changed after this preview. Preview the move again.','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorMediaMoveController.cs')],
670:[('Ebook-only folders cannot have audiobook settings','source-text-exact','src/Chaptarr.Api.V1/RootFolders/RootFolderResource.cs')],
672:[('Chaptarr is starting up, please try again later','source-text-exact','src/Chaptarr.Http/Middleware/StartingUpMiddleware.cs')],
674:[('term is required','source-text-exact','src/Chaptarr.Api.V1/Books/BookLookupController.cs')],
677:[('Invalid output formats','source-text-exact','src/NzbDrone.Core/Books/Calibre/CalibreSettings.cs')],
681:[('request body is required','source-text-exact','src/Chaptarr.Api.V1/Config/NamingPatternController.cs')],
682:[('One of authorId or bookId must be specified','source-text-exact','src/Chaptarr.Api.V1/Books/RetagBookController.cs')],
683:[('Selected edition {editionId.Value} could not be found: {ex.Message}','source-template-fragment','src/Chaptarr.Api.V1/ManualImport/ManualImportController.cs')],
685:[('Several local records match the selected work. Open the intended record below, then request it from that record.','source-text-exact','src/Chaptarr.Api.V1/ProviderIds/ProviderAmbiguityResource.cs')],
686:[('bookFileIds cannot be combined with downloadId','source-text-exact','src/Chaptarr.Api.V1/ManualImport/ManualImportController.cs')],
688:[('Metadata server is missing required capability','source-text-fragment','src/Chaptarr.Api.V1/Config/DevelopmentConfigController.cs')],
690:[('Successfully added','source-text-fragment','src/NzbDrone.Core/Books/Services/PendingImportService.cs')],
691:[('Unexpected metadata server service','source-text-fragment','src/Chaptarr.Api.V1/Config/DevelopmentConfigController.cs')],
693:[("mediaType must be 'all', 'audiobook', or 'ebook'",'source-text-exact','src/Chaptarr.Api.V1/Commands/CommandController.cs')],
694:[('Selected photo is a provider placeholder','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorController.cs')],
698:[('Book ID matches both audiobook and ebook. Select an edition or provide a mediaType.','source-text-exact','src/Chaptarr.Api.V1/ManualImport/ManualImportController.cs')],
699:[('Proxy type must be Http, Socks4, or Socks5','source-text-exact','src/Chaptarr.Api.V1/Configuration/ProxyController.cs')]
}

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
  remote=run(['git','ls-remote',f'https://github.com/{REPO}.git',f'refs/heads/{pr["headRefName"]}']).split()[0]
  return pr,tree,remote

head=git('rev-parse','HEAD').strip(); tree=git('rev-parse','HEAD^{tree}').strip()
if head!=EXPECTED_HEAD or tree!=EXPECTED_TREE: raise SystemExit(f'expected pinned head/tree {EXPECTED_HEAD}/{EXPECTED_TREE}; found {head}/{tree}')
pr, live_tree, live_remote=live_pr()
if pr['headRefOid']!=head or live_tree!=tree or live_remote!=head or pr['state']!='OPEN' or not pr['isDraft']:
  raise SystemExit('live PR preflight mismatch: '+json.dumps({'pr':pr,'tree':live_tree,'remoteHead':live_remote}))
if git('status','--porcelain').strip(): raise SystemExit('worktree is not clean; refusing scratch packet build')

source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_bytes=read_git(source_path); source_catalog=json.loads(source_bytes)
follow_path='docs/localization/source-followup-20261101.json'; follow_bytes=read_git(follow_path); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
if len(ids)!=1210 or len(set(ids))!=1210: raise SystemExit('source follow-up inventory drift')
source_ids=ids[650:700]
if source_ids!=EXPECTED_IDS: raise SystemExit('W650–699 source ID boundary drift: '+json.dumps(source_ids))
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
for ordinal,sid in enumerate(source_ids,650):
  for fp,n,line in find_needle(sid): raw[sid].append((fp,n,line,'exact-source-id'))
for ordinal,rules in FALLBACKS.items():
  sid=source_ids[ordinal-650]
  for needle,mode,expected_path in rules:
    hits=find_needle(needle,expected_path)
    if not hits: raise SystemExit(f'caller pin missing for {ordinal} {sid}: {needle}')
    for fp,n,line in hits:
      if fp!=expected_path: raise SystemExit(f'caller pin path drift for {ordinal}: {fp} != {expected_path}')
      raw[sid].append((fp,n,line,mode))
# The generic RSS interval and Chaptarr instance-name rows have their validation consumers pinned above.

caller_rows=[]; callers_by_id={}; caller_gaps=[]; caller_mismatches=[]; unique_files=set(); total_refs=0
for ordinal,sid in enumerate(source_ids,650):
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
for ordinal,sid in enumerate(source_ids,650):
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

# W649 is adjacent prior-context only. Verify both frozen W600–649 packets, then reattest its final target, source, and callers at the applied head.
prior_packet=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0600-0649-primary-20261102')
cross_packet=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0600-0649-crossreview-independent-20261102')
def verify_packet(packet):
  manifest=packet/'SHA256SUMS'
  if not manifest.is_file(): raise SystemExit(f'missing prior checksum manifest: {manifest}')
  for line in manifest.read_text().splitlines():
    digest,name=line.split('  ',1)
    file=packet/name
    if not file.is_file() or sha(file.read_bytes())!=digest: raise SystemExit(f'prior packet checksum mismatch: {file}')
verify_packet(prior_packet); verify_packet(cross_packet)
prior_summary=json.loads((prior_packet/'summary.json').read_text())
cross_summary=json.loads((cross_packet/'summary.json').read_text())
if (prior_summary.get('exactHead'),prior_summary.get('exactTree'))!=('f405a6256c2661e48e412ac4471ce70411baf98c','fe3272572b68460f1d8c8083a5dcc44cd3307b74'):
  raise SystemExit('W649 primary prior packet is not pinned to the expected reviewed head/tree')
if (cross_summary.get('head'),cross_summary.get('tree'))!=('f405a6256c2661e48e412ac4471ce70411baf98c','fe3272572b68460f1d8c8083a5dcc44cd3307b74'):
  raise SystemExit('W649 cross-review prior packet is not pinned to the expected reviewed head/tree')
prior_sid=ids[649]; prior_by_locale={}; cross_by_locale={}; boundary_650_by_locale={}
for line in (prior_packet/'review-cells.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==649 and x.get('sourceId')==prior_sid: prior_by_locale[x['locale']]=x
for line in (cross_packet/'final-dispositions.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==649 and x.get('sourceId')==prior_sid: cross_by_locale[x['locale']]=x
for line in (cross_packet/'boundary-next-source-650.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==650 and x.get('sourceId')==source_ids[0]: boundary_650_by_locale[x['locale']]=x
if set(prior_by_locale)!=set(LOCALES) or set(cross_by_locale)!=set(LOCALES) or set(boundary_650_by_locale)!=set(LOCALES):
  raise SystemExit('W649 prior/context or W650 adjacent boundary locale coverage incomplete')
raw[prior_sid]=[]
for fp,n,line in find_needle(prior_sid): raw[prior_sid].append((fp,n,line,'exact-source-id'))
prior_refs=[]
for fp,n,line,mode in sorted(raw.get(prior_sid,[]),key=lambda x:(x[0],x[1],x[3])):
  content=read_git(fp); lines=content.decode('utf-8').splitlines()
  if not 1<=n<=len(lines) or lines[n-1]!=line: raise SystemExit(f'W649 caller drift at {fp}:{n}')
  prior_refs.append({'file':fp,'kind':mode,'currentLine':n,'lineMatchMethod':mode,'matchedSourceId':prior_sid,'matchedSourceText':None,'currentLineText':line,'currentLineSha256':sha(line.encode()),'contextBefore':lines[max(0,n-3):n-1],'contextAfter':lines[n:min(len(lines),n+2)],'currentFileBlob':git('rev-parse',f'HEAD:{fp}').strip(),'currentFileSha256':sha(content)})
prior_refs_hash=sha(jbytes(prior_refs)); prior_records=[]
prior_live_source=source_catalog[prior_sid]
if prior_live_source!=prior_by_locale['es']['source'] or sha(prior_live_source.encode())!=cross_by_locale['es']['sourceTextSha256']:
  raise SystemExit('W649 prior source text differs from live source')
# The previous cross-review packet stores the exact W649 live source/cell/caller attestations.
old_live_rows={}
for line in (cross_packet/'live-cell-reattestation.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==649 and x.get('sourceId')==prior_sid: old_live_rows[x['locale']]=x
if set(old_live_rows)!=set(LOCALES): raise SystemExit('W649 prior cross-review live-cell attestation incomplete')
old_caller_rows=[]
for line in (cross_packet/'caller-ref-reattestation.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==649 and x.get('sourceId')==prior_sid: old_caller_rows.append(x)
old_caller_keys={(x.get('file'),x.get('line'),x.get('lineText')) for x in old_caller_rows}
live_caller_keys={(x.get('file'),x.get('currentLine'),x.get('currentLineText')) for x in prior_refs}
if old_caller_keys!=live_caller_keys: raise SystemExit('W649 caller source references changed after the applied catalog commit')
for loc in LOCALES:
  p=prior_by_locale[loc]; c=cross_by_locale[loc]; old=old_live_rows[loc]
  live_target=catalogs[loc][prior_sid]; live_target_hash=sha(live_target.encode())
  if p.get('source')!=prior_live_source or c.get('sourceTextSha256')!=sha(prior_live_source.encode()) or old.get('source')!=prior_live_source or old.get('sourceTextSha256')!=sha(prior_live_source.encode()):
    raise SystemExit(f'W649 source hash/context changed for {loc}')
  if c.get('finalTarget')!=live_target or c.get('finalTargetSha256')!=live_target_hash:
    raise SystemExit(f'W649 live target does not equal exact cross-review final target for {loc}')
  if old.get('currentTarget')!=p.get('currentTarget') or old.get('currentTargetSha256')!=p.get('currentTargetSha256'):
    raise SystemExit(f'W649 prior primary and cross-review current-cell freeze mismatch for {loc}')
  if old.get('liveCallerContextSha256')!=p.get('callerContextSha256'):
    raise SystemExit(f'W649 prior primary and cross-review caller context hash mismatch for {loc}')
  prior_records.append({'contextSourceOrdinal':649,'sourceId':prior_sid,'source':prior_live_source,'sourceTextSha256':sha(prior_live_source.encode()),'locale':loc,'priorPrimaryHead':p.get('exactHead'),'priorPrimaryTree':p.get('exactTree'),'priorPrimaryDisposition':p.get('disposition'),'priorPrimaryRecommendation':p.get('recommendedTarget'),'priorPrimaryRecommendationSha256':p.get('recommendedTargetSha256'),'priorPrimaryCurrentTarget':p.get('currentTarget'),'priorPrimaryCurrentTargetSha256':p.get('currentTargetSha256'),'priorCrossReviewDisposition':c.get('crossReviewDisposition'),'priorCrossReviewFinalTarget':c.get('finalTarget'),'priorCrossReviewFinalTargetSha256':c.get('finalTargetSha256'),'liveCurrentTarget':live_target,'liveCurrentTargetSha256':live_target_hash,'liveTargetMatchesPriorCrossReviewFinal':True,'primaryCurrentTargetMatchesLive':p.get('currentTarget')==live_target,'primaryRecommendationMatchesLive':p.get('recommendedTarget')==live_target if p.get('recommendedTarget') else None,'priorCallerContextSha256':p.get('callerContextSha256'),'liveCallerContextSha256':prior_refs_hash,'priorCallerRefs':p.get('callerRefs',[]),'liveCallerRefs':prior_refs,'priorCrossReviewLiveAttestation':old,'contextOnly':True})
# Reattest W650's source and all 12 target values against the previous packet's frozen adjacency boundary.
boundary_650_records=[]
for loc in LOCALES:
  old=boundary_650_by_locale[loc]; sid=source_ids[0]; src=source_catalog[sid]; target=catalogs[loc][sid]
  if old.get('source')!=src or old.get('sourceTextSha256')!=sha(src.encode()): raise SystemExit(f'W650 boundary source drift for {loc}')
  if old.get('liveTarget')!=target or old.get('liveTargetSha256')!=sha(target.encode()): raise SystemExit(f'W650 adjacent target changed after W600–649 apply for {loc}')
  boundary_650_records.append({'sourceOrdinal':650,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':sha(src.encode()),'previousBoundaryHead':'f405a6256c2661e48e412ac4471ce70411baf98c','previousBoundaryTree':'fe3272572b68460f1d8c8083a5dcc44cd3307b74','previousTarget':old.get('liveTarget'),'previousTargetSha256':old.get('liveTargetSha256'),'liveTarget':target,'liveTargetSha256':sha(target.encode()),'targetFile':f'src/NzbDrone.Core/Localization/Core/{LOCALES[loc]}','targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'previousCatalogFileBlob':old.get('targetFileBlob'),'previousCatalogFileSha256':old.get('targetFileSha256'),'catalogFileChangedSinceBoundary':old.get('targetFileSha256')!=catalog_info[loc]['sha256'],'callerContextSha256':sha(jbytes(callers_by_id[sid])),'callerRefs':callers_by_id[sid],'contextOnly':True})
# Scan earlier review ledgers for source-ID overlap; current W650–699 remains disjoint.
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
      if isinstance(ordinal,int) and ordinal<650 and sid and disposition is not None:
        parsed.append(x); prior_ids.add(sid); prior_disposition_rows+=1
        if sid in source_ids: overlap_rows.append({'ledger':str(fp),'sourceOrdinal':ordinal,'sourceId':sid,'locale':x.get('locale'),'disposition':disposition})
    if parsed: prior_ledgers.append({'path':str(fp),'sha256':sha(fp.read_bytes()),'dispositionRowsBefore650':len(parsed),'sourceIds':sorted({x.get('sourceId') for x in parsed if x.get('sourceId')})})
if overlap_rows: raise SystemExit('source ID overlap with prior window: '+json.dumps(overlap_rows,ensure_ascii=False))

save_jsonl('source-slice.jsonl',source_rows)
save_jsonl('caller-context.jsonl',caller_rows)
save_jsonl('input-cells.jsonl',input_rows)
save_jsonl('review-cells.jsonl',review_rows)
save_jsonl('protected-literal-integrity.jsonl',literal_rows)
save_jsonl('correction-candidates.jsonl',[x for x in review_rows if x['disposition']!='accept-current'])
save_jsonl('prior-context-dispositions.jsonl',prior_records)
save_jsonl('boundary-next-source-650.jsonl',boundary_650_records)
save_json('prior-disposition-boundary.json',{'scopePositions':[650,699],'searchedPriorPositions':[0,649],'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids),'priorDispositionRows':prior_disposition_rows,'matchingPriorRows':overlap_rows,'matchingPriorRowCount':len(overlap_rows),'disjointCurrentSourceIds':not overlap_rows,'ledgerFiles':prior_ledgers,'contextOnlyPreviousSourceId':prior_sid,'contextOnlyPreviousRows':len(prior_records),'adjacentW649CallerRefs':len(prior_refs),'adjacentW649CallerContextSha256':prior_refs_hash,'adjacentW649TargetsMatchingLive':sum(x['liveTargetMatchesPriorCrossReviewFinal'] for x in prior_records),'adjacentW649PrimaryRecommendationsMatchingLive':sum(bool(x['primaryRecommendationMatchesLive']) for x in prior_records),'adjacentW649SourceHashesMatchLive':sum(x['sourceTextSha256']==sha(prior_live_source.encode()) for x in prior_records),'w649PriorPacketsChecksummed':True,'w649CrossReviewFinalTargetsMatchLive':sum(x['liveTargetMatchesPriorCrossReviewFinal'] for x in prior_records),'w650AdjacentBoundaryRows':len(boundary_650_records),'w650SourceAndTargetsMatchPriorBoundary':len(boundary_650_records)==12,'w650CallerPinsReattested':sum(bool(x['callerRefs']) for x in boundary_650_records),'w650CatalogFileHashesChangedAfterApply':sum(x['catalogFileChangedSinceBoundary'] for x in boundary_650_records)})

# Persist the decision summary used to construct exact-hash review rows.
findings={}
source_rationales={}
for ordinal in range(650,700):
  sid=source_ids[ordinal-650]; source_rationales[str(ordinal)]='The pinned production caller establishes the API, validation, status-toast, or media-operation context for this message; proposals preserve that meaning and its technical identifiers.'
  for loc,target in PROPOSALS.get(ordinal,{}).items():
    disposition='propose-refinement' if (ordinal,loc) in REFINEMENTS else 'propose-correction'
    _plan_entry=PLAN.get(f'{ordinal}|{loc}',{})
    findings[f'{ordinal}|{loc}']=[disposition,target,_plan_entry.get('rationale',f"Revises the {loc} wording while preserving the source meaning in the pinned caller context."),_plan_entry.get('confidence','moderate')]
save_json('review-decisions.json',{'schemaVersion':1,'reviewer':'primary semantic reviewer','scope':[650,699],'findings':findings,'sourceRationales':source_rationales,'acceptedCellRationale':'Current target preserves source meaning in the exact pinned production caller context; no material issue found.','nativeSpeakerApproval':False})
save_json('reviewer-provenance.json',{'reviewerRole':'primary semantic reviewer','reviewType':'independent caller-context-aware language and terminology review of all frozen current cells','exactHead':head,'exactTree':tree,'scope':{'positions':[650,699],'cells':600,'locales':list(LOCALES)},'evidenceSources':['English source catalog','12 locale catalogs','exact production C# source-ID references and pinned English source/template callsites','pinned English-source, normalized-validator-template, or source-fragment production caller pins','W649 adjacent primary and cross-review final dispositions plus current target reattestation','W650 adjacent source/current-target boundary and exact production caller reattestation'],'protectedLiteralPolicy':'Preserve exact source placeholders, product names, API field names, protocol URLs, enum tokens, version and range values, and machine-readable identifiers; localize ordinary user-facing language.','nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False})

counts=collections.Counter(x['disposition'] for x in review_rows)
for key in ('accept-current','propose-refinement','propose-correction','hold'): counts.setdefault(key,0)
per_locale={}
for loc in LOCALES:
  c=collections.Counter(x['disposition'] for x in review_rows if x['locale']==loc)
  per_locale[loc]={key:c.get(key,0) for key in ('accept-current','propose-refinement','propose-correction','hold')}
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'livePullRequest':pr,'remoteBranchHead':live_remote,'scope':{'positions':[650,699],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceIdListSha256':source_id_hash,'sourceSliceIdsSha256':sha(jbytes(source_ids)),'counts':dict(counts),'proposalCount':sum(counts[k] for k in ('propose-refinement','propose-correction')),'perLocale':per_locale,'callerEvidence':{'sourceIdsWithCallerPins':sum(bool(v) for v in callers_by_id.values()),'callerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'mismatches':len(caller_mismatches),'gaps':caller_gaps,'allCallersAttestedAtExactHead':not caller_gaps and not caller_mismatches},'placeholders':{'sourcesWithPlaceholders':sum(bool(placeholders(source_catalog[sid])) for sid in source_ids),'mismatches':sum(not x['placeholderParity'] for x in review_rows)},'markup':{'sourcesWithMarkup':sum(bool(markup(source_catalog[sid])) for sid in source_ids),'mismatches':sum(not x['markupParity'] for x in review_rows)},'protectedLiterals':{'checkedCells':len(literal_rows),'currentMismatches':sum(bool(x['currentMismatches']) for x in literal_rows),'currentMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missing':x['currentMismatches']} for x in literal_rows if x['currentMismatches']],'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows),'recommendedMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missing':x['recommendedMismatches']} for x in literal_rows if x['recommendedMismatches']]},'priorDispositionBoundary':{'priorSourceIdOverlap':len(overlap_rows),'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids),'contextOnlyW649Rows':len(prior_records),'w650AdjacentBoundaryRows':len(boundary_650_records),'w649SourceRowsMatchingLive':sum(x['sourceTextSha256']==sha(prior_live_source.encode()) for x in prior_records),'w649CrossReviewFinalTargetsMatchingLive':sum(x['liveTargetMatchesPriorCrossReviewFinal'] for x in prior_records),'w649PriorPrimaryTargetsMatchingLive':sum(x['primaryCurrentTargetMatchesLive'] for x in prior_records),'w649AppliedRecommendationsMatchingLive':sum(bool(x['primaryRecommendationMatchesLive']) for x in prior_records),'w649CallerRefsReattested':len(prior_refs),'w650BoundaryRows':len(boundary_650_records),'w650CallerPinsReattested':sum(bool(x['callerRefs']) for x in boundary_650_records),'w650CatalogFileHashesChangedAfterApply':sum(x['catalogFileChangedSinceBoundary'] for x in boundary_650_records)},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('summary.json',summary)

final_pr,final_tree,final_remote=live_pr()
final_head=git('rev-parse','HEAD').strip(); final_worktree_tree=git('rev-parse','HEAD^{tree}').strip()
if final_head!=head or final_worktree_tree!=tree or final_pr['headRefOid']!=head or final_tree!=tree or final_remote!=head or final_pr['state']!='OPEN' or not final_pr['isDraft']:
  save_json('final-reattestation.json',{'passed':False,'expectedHead':head,'expectedTree':tree,'finalHead':final_head,'finalWorktreeTree':final_worktree_tree,'finalPullRequest':final_pr,'finalLiveTree':final_tree,'finalRemoteHead':final_remote})
  raise SystemExit('live PR moved during packet construction; preserve packet and report drift')
save_json('final-reattestation.json',{'passed':True,'exactHead':head,'exactTree':tree,'pullRequestState':final_pr['state'],'isDraft':final_pr['isDraft'],'headRefName':final_pr['headRefName'],'remoteBranchHead':final_remote,'sourceIds':50,'localeCells':len(input_rows),'sourceTextHashes':len(source_rows),'callerRefs':total_refs,'callerContextHashes':len(caller_rows),'w649ContextRows':len(prior_records),'w650BoundaryRows':len(boundary_650_records),'w649SourceRowsMatchingLive':sum(x['sourceTextSha256']==sha(prior_live_source.encode()) for x in prior_records),'w649CrossReviewFinalTargetsMatchingLive':sum(x['liveTargetMatchesPriorCrossReviewFinal'] for x in prior_records),'w649LiveTargetHashesRecorded':len(prior_records),'w650BoundaryTargetsMatchingPrior':sum(x['liveTarget']==x['previousTarget'] for x in boundary_650_records),'repositoryClean':not git('status','--porcelain').strip(),'repositoryModified':False})

# Build input checksums from blobs at the frozen exact head, not working-tree paths.
caller_file_infos=[]
for _refs in callers_by_id.values():
  for _ref in _refs:
    caller_file_infos.append({'path':_ref['file'],'sha256':_ref['currentFileSha256']})
caller_file_infos={x['path']:x for x in caller_file_infos}
input_files=[source_info,follow_info,registry_info,*catalog_info.values(),*caller_file_infos.values()]
(O/'INPUT-SHA256SUMS').write_text(''.join(f"{x['sha256']}  {x['path']}\n" for x in input_files))
(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W650–699 primary semantic review\n\n- Exact PR state: OPEN/DRAFT at `{head}` / tree `{tree}`.\n- Scope: source-list positions 650–699 across 12 locales = 50 source IDs / 600 current locale cells.\n- Exact source inventory: `source-slice.jsonl`; source-list SHA-256 `{source_id_hash}`.\n- Production caller pins: {len(caller_rows)} of 50 source IDs, {total_refs} exact C# source-ID/template references across {len(unique_files)} files; gaps and mismatches: 0.\n- Dispositions: {dict(counts)}. Every cell has exact source/current-target hashes and caller context in `review-cells.jsonl`; recommendations are in `correction-candidates.jsonl`.\n- Placeholder mismatches: {summary['placeholders']['mismatches']}; markup mismatches: {summary['markup']['mismatches']}; current protected-literal mismatch cells: {summary['protectedLiterals']['currentMismatches']}; proposed protected-literal mismatches: {summary['protectedLiterals']['recommendedMismatches']}.\n- W649 adjacent context: source hash was reattested; all 12 live targets match the prior cross-review final targets after the apply commit; {summary['priorDispositionBoundary']['w649PriorPrimaryTargetsMatchingLive']} original primary current targets remain unchanged and {summary['priorDispositionBoundary']['w649AppliedRecommendationsMatchingLive']} primary recommendations match the live targets. W650 source/current-target strings and caller pins were reattested against the previous boundary; all 12 target values match, while {summary['priorDispositionBoundary']['w650CatalogFileHashesChangedAfterApply']} locale catalog file hashes changed with the apply commit.\n- Earlier ledger overlap: {len(overlap_rows)} source IDs.\n- Primary model review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.\n\nSee `summary.json`, `manifest.json`, and `SHA256SUMS` for packet inventory and integrity.\n''')

# Record exact input manifest and every packet-file digest before the checksum manifest itself.
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':head,'tree':tree,'livePullRequest':final_pr,'remoteBranchHead':final_remote,'positions':[650,699],'sourceIdCount':50,'locales':list(LOCALES),'cellCount':600,'sourceFollowup':follow_info,'sourceFile':source_info,'registry':registry_info,'catalogs':catalog_info,'sourceListSha256':source_id_hash,'files':[]}
for fp in sorted(O.iterdir()):
  if fp.is_file() and fp.name not in ('manifest.json','SHA256SUMS'):
    manifest['files'].append({'path':fp.name,'bytes':fp.stat().st_size,'sha256':sha(fp.read_bytes())})
save_json('manifest.json',manifest)
all_files=sorted(fp for fp in O.iterdir() if fp.is_file() and fp.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f'{sha(fp.read_bytes())}  {fp.name}\n' for fp in all_files))
# Re-query exact PR state after all evidence writes and verify the checksummed packet.
post_pr,post_tree,post_remote=live_pr(); post_head=git('rev-parse','HEAD').strip(); post_worktree_tree=git('rev-parse','HEAD^{tree}').strip()
if (post_head,post_worktree_tree,post_pr['headRefOid'],post_tree,post_pr['state'],post_pr['isDraft'],post_remote)!=(head,tree,head,tree,'OPEN',True,head):
  raise SystemExit('post-write live PR exact-head verification failed')
for line in (O/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1)
  if sha((O/name).read_bytes())!=digest: raise SystemExit(f'packet checksum failure: {name}')
print(json.dumps({'packet':str(O),'head':head,'tree':tree,'cells':len(review_rows),'counts':dict(counts),'callerRefs':total_refs,'callerFiles':len(unique_files),'placeholdersMismatch':summary['placeholders']['mismatches'],'markupMismatch':summary['markup']['mismatches'],'currentProtectedMismatchCells':summary['protectedLiterals']['currentMismatches'],'proposalProtectedMismatchCells':summary['protectedLiterals']['recommendedMismatches'],'w649PriorPrimaryTargetsMatchingLive':summary['priorDispositionBoundary']['w649PriorPrimaryTargetsMatchingLive'],'w649AppliedRecommendationsMatchingLive':summary['priorDispositionBoundary']['w649AppliedRecommendationsMatchingLive'],'priorOverlap':len(overlap_rows),'postHead':post_head,'packetFiles':len(all_files)+1,'packetBytes':sum(fp.stat().st_size for fp in O.iterdir() if fp.is_file())},ensure_ascii=False,indent=2))
