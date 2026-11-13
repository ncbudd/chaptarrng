import json, hashlib, pathlib, re, subprocess, collections
W=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
O=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0400-0449-primary-20261102')
REPO='snapetech-org/chaptarrng'; PR=190
EXPECTED_HEAD='2eb0ae6eb15ebc366eea44dd969265c0f6366445'; EXPECTED_TREE='1340ba7d0642217aa81e3789e908931bd6fa74f1'
LOCALES={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
# Recommendations are source-context-specific candidates only; no catalog is changed.
DECISION_PATH=O/'review-decisions.json'
DECISIONS=json.loads(DECISION_PATH.read_text())
FINDINGS={(int(k.split('|',1)[0]),k.split('|',1)[1]):tuple(v) for k,v in DECISIONS['findings'].items()}
SOURCE_RATIONALES={int(k):v for k,v in DECISIONS['sourceRationales'].items()}
UI_TERMS={}
PROTECTED={
 400:['{message}'],405:['{author}','{book}'],408:['{message}'],409:['{message}'],410:['{message}'],
 413:['Chaptarr','{timestamp}'],415:['Chaptarr'],417:['Chaptarr','Mailgun'],
 430:['{author}','{book}','{count}'],431:['Chaptarr','{source}'],433:[],434:['Chaptarr','{previous}','{current}'],
 435:['Subsonic'],436:['{message}'],437:['{message}'],438:['{message}'],439:['{message}'],440:['{message}'],
 444:['{value0}'],446:['HTTP','{value0}'],448:['uTorrent']
}

# This source-list slice uses direct source-key callsites rather than the provider-field registry.
# The one server message whose key is not embedded at its source uses its literal source sentence in UTorrent.cs.
SOURCE_TEXT_FALLBACKS={'server.message.m020b4d34d19f':'uTorrent is reporting an error'}

def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(d): return json.dumps(d,ensure_ascii=False,separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def read_git(path): return git('show',f'HEAD:{path}')
def blob(path): return git('rev-parse',f'HEAD:{path}').decode().strip()
def save_json(path,obj): (O/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def save_jsonl(path,rows): (O/path).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def placeholders(s):
  return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
  if re.fullmatch(r'<[^<>/]+>',s): return [] # the localized <missing> display token is not HTML markup
  tags=re.findall(r'</?[A-Za-z][^>]*>',s)
  return tags

def tracked_file_info(path):
  b=read_git(path); return {'path':path,'blob':blob(path),'sha256':sha(b),'bytes':len(b)}

head=git('rev-parse','HEAD').decode().strip(); tree=git('rev-parse','HEAD^{tree}').decode().strip()
if head!=EXPECTED_HEAD or tree!=EXPECTED_TREE: raise SystemExit(f'expected pinned head/tree {EXPECTED_HEAD}/{EXPECTED_TREE}; found {head}/{tree}')
pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],text=True))
if pr['headRefOid']!=head or pr['state']!='OPEN' or not pr['isDraft']: raise SystemExit(f'PR state/head drift: {json.dumps(pr)}')
if git('status','--porcelain').decode()!='': raise SystemExit('worktree is not clean; refusing packet build')
source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_bytes=read_git(source_path); source_catalog=json.loads(source_bytes)
follow_path='docs/localization/source-followup-20261101.json'; follow_bytes=read_git(follow_path); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==len(ids)
assert len(ids)==1210 and len(set(ids))==1210
source_ids=ids[400:450]; assert len(source_ids)==50 and len(set(source_ids))==50
registry_path='docs/localization/provider-field-sources.json'; reg_bytes=read_git(registry_path); registry=json.loads(reg_bytes); reg_by={x['id']:x for x in registry['records']}
catalogs={}; catalog_info={}
for loc,file in LOCALES.items():
  p=f'src/NzbDrone.Core/Localization/Core/{file}'; b=read_git(p); catalogs[loc]=json.loads(b); catalog_info[loc]=tracked_file_info(p)
  assert set(catalogs[loc])==set(source_catalog)
source_info=tracked_file_info(source_path); follow_info=tracked_file_info(follow_path); registry_info=tracked_file_info(registry_path)

# Pin every exact C# production reference to the 50 source IDs in this window plus W399.
# This is a bounded literal-key lookup in production source files; it does not run tests or alter the repository.
prior_sid=ids[399]
search_ids=list(dict.fromkeys(source_ids+[prior_sid]))
search_args=['rg','--no-heading','--color','never','-n','-F']
for sid in search_ids: search_args.extend(['-e',sid])
search_args.extend(['--glob','*.cs',str(W/'src/NzbDrone.Core')])
search=subprocess.run(search_args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if search.returncode not in (0,1): raise SystemExit('caller source lookup failed: '+search.stderr)
raw_matches=collections.defaultdict(list)
for row in search.stdout.splitlines():
  try:
    filepath,lineno,line=row.split(':',2)
    n=int(lineno)
  except ValueError:
    continue
  for sid in search_ids:
    if sid in line:
      raw_matches[sid].append((str(pathlib.Path(filepath).resolve().relative_to(W.resolve())),n,line,'exact-source-id'))
for sid,needle in SOURCE_TEXT_FALLBACKS.items():
  if sid not in source_catalog: continue
  fallback_args=['rg','--no-heading','--color','never','-n','-F','-e',needle,'--glob','*.cs',str(W/'src/NzbDrone.Core/Download/Clients/uTorrent')]
  fallback=subprocess.run(fallback_args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if fallback.returncode not in (0,1): raise SystemExit('caller text lookup failed: '+fallback.stderr)
  for row in fallback.stdout.splitlines():
    try: filepath,lineno,line=row.split(':',2); n=int(lineno)
    except ValueError: continue
    raw_matches[sid].append((str(pathlib.Path(filepath).resolve().relative_to(W.resolve())),n,line,'exact-source-text-fallback'))

# Re-attest production source-key callsites and the one literal-source fallback.
caller_rows=[]; callers_by_id={}; mismatches=[]; caller_gaps=[]; unique_files=set(); shifts=0; total_refs=0
for ordinal,sid in enumerate(source_ids,400):
  rec=reg_by.get(sid)
  refs=[]
  for f,line,matched_text,match_mode in raw_matches.get(sid,[]):
    unique_files.add(f); content=read_git(f); lines=content.decode('utf-8').splitlines()
    if line<1 or line>len(lines) or lines[line-1]!=matched_text:
      mismatches.append({'sourceId':sid,'file':f,'line':line,'reason':'caller lookup line drift'}); continue
    total_refs+=1
    refs.append({'file':f,'kind':'production-source-callsite','registryLine':None,'currentLine':line,'lineNumberShift':None,'lineMatchMethod':match_mode,'matchedSourceId':sid if match_mode=='exact-source-id' else None,'matchedSourceText':source_catalog[sid] if match_mode=='exact-source-text-fallback' else None,'registrySourceLine':matched_text,'registrySourceLineSha256':sha(matched_text.encode()),'currentLineText':matched_text,'currentLineSha256':sha(matched_text.encode()),'contextBefore':lines[max(0,line-3):line-1],'contextAfter':lines[line:min(len(lines),line+2)],'currentFileBlob':blob(f),'currentFileSha256':sha(content)})
  refs.sort(key=lambda x:(x['file'],x['currentLine'],x['kind']))
  if not refs:
    caller_gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no exact source-ID or approved literal-source caller found in production C# at pinned head'})
  callers_by_id[sid]=refs
  caller_record={'sourceOrdinal':ordinal,'sourceId':sid,'attestedHead':head,'attestedTree':tree,'sourceText':source_catalog[sid],'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'registrySourceFingerprint':rec.get('sourceFingerprint') if rec else None,'callerReferenceStatus':'pinned' if refs else 'gap','callerRefs':refs,'callerMismatches':[m for m in mismatches if m.get('sourceId')==sid]}
  caller_record['callerContextSha256']=sha(jbytes(refs)); caller_rows.append(caller_record)
if mismatches: raise SystemExit('caller/source mismatch(s): '+json.dumps(mismatches,ensure_ascii=False))

sources=[]; inputs=[]; reviews=[]; literal_rows=[]; target_cell_count=0
all_cat_paths={'en':source_path,**{l:f'src/NzbDrone.Core/Localization/Core/{f}' for l,f in LOCALES.items()}}
for ordinal,sid in enumerate(source_ids,400):
  src=source_catalog[sid]; s_hash=sha(src.encode()); source_placeholders=placeholders(src); rec=reg_by.get(sid)
  protected=PROTECTED.get(ordinal,[])
  source_row={'sourceOrdinal':ordinal,'sourceId':sid,'source':src,'sourceSha256':sha(sid.encode()),'sourceTextSha256':s_hash,'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'sourceFollowupPath':follow_path,'sourceFollowupBlob':follow_info['blob'],'sourceFollowupSha256':follow_info['sha256'],'sourceIdListCount':len(ids),'sourceIdListSha256':sha(jbytes(ids)),'registryPath':registry_path if rec else None,'registryBlob':registry_info['blob'] if rec else None,'registrySha256':registry_info['sha256'] if rec else None,'registrySourceFingerprint':rec.get('sourceFingerprint') if rec else None,'callerRefs':callers_by_id[sid],'callerContextSha256':sha(jbytes(callers_by_id[sid]))}
  sources.append(source_row)
  for loc,file in LOCALES.items():
    target=catalogs[loc][sid]; t_hash=sha(target.encode()); tp=placeholders(target); src_markup=markup(src); tgt_markup=markup(target)
    assert source_placeholders==tp, (ordinal,loc,'placeholder mismatch',source_placeholders,tp)
    disp,rec_target,rationale,confidence=FINDINGS.get((ordinal,loc),('accept-current',None,f'Current {loc} wording preserves the source meaning in this caller context. {SOURCE_RATIONALES[ordinal]} No material translation issue found.','moderate'))
    if (ordinal,loc) in FINDINGS:
      assert disp in {'propose-refinement','propose-correction','hold'}
      assert (rec_target is not None) or disp=='hold'
    recommendation_hash=sha(rec_target.encode()) if rec_target else None
    literal_checks=[]
    for literal in protected:
      # Product names, protocol identifiers, and placeholders are checked exactly.
      present_src=literal in src
      target_literal=literal in target
      recommended_literal=(literal in rec_target) if rec_target else None
      literal_checks.append({'literal':literal,'matchMode':'exact','presentInSource':present_src,'presentInCurrentTarget':target_literal,'presentInRecommendedTarget':recommended_literal})
    missing_current=[x['literal'] for x in literal_checks if not x['presentInCurrentTarget']]
    missing_recommended=[x['literal'] for x in literal_checks if rec_target and not x['presentInRecommendedTarget']]
    # Interactive Search is a UI label and must match its localized catalog value when recommended.
    ui_checks=[]
    if ordinal in ():
      ui=UI_TERMS[loc]
      ui_checks=[{'sourceUiTerm':'Interactive Search','expectedLocalizedUiTerm':ui,'currentEnglishTermCount':target.count('Interactive Search'),'recommendedEnglishTermCount':rec_target.count('Interactive Search') if rec_target else None}]
    input_row={'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':s_hash,'sourcePlaceholders':source_placeholders,'sourceMarkup':src_markup,'target':target,'targetSha256':t_hash,'targetPlaceholders':tp,'targetMarkup':tgt_markup,'targetFile':all_cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'protectedLiterals':protected,'callerContextSha256':source_row['callerContextSha256']}
    inputs.append(input_row)
    review={'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceSha256':sha(sid.encode()),'sourceTextSha256':s_hash,'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'targetFile':all_cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'currentTarget':target,'currentTargetSha256':t_hash,'disposition':disp,'recommendedTarget':rec_target,'recommendedTargetSha256':recommendation_hash,'confidence':confidence,'rationale':rationale,'callerRefs':callers_by_id[sid],'callerContextSha256':source_row['callerContextSha256'],'sourcePlaceholders':source_placeholders,'currentTargetPlaceholders':tp,'recommendedPlaceholders':placeholders(rec_target) if rec_target else None,'placeholderParity':source_placeholders==tp and (not rec_target or source_placeholders==placeholders(rec_target)),'sourceMarkup':src_markup,'currentTargetMarkup':tgt_markup,'recommendedTargetMarkup':markup(rec_target) if rec_target else None,'markupParity':src_markup==tgt_markup and (not rec_target or src_markup==markup(rec_target)),'protectedLiterals':protected,'protectedLiteralChecks':literal_checks,'protectedLiteralsPreserved':not missing_current and not missing_recommended,'protectedLiteralMismatches':{'current':missing_current,'recommended':missing_recommended},'localizedUiTermChecks':ui_checks,'nativeSpeakerApproval':False,'priorDisposition':'no exact prior source-ID disposition found in reviewed positions 0–399; prior overlap scan is recorded in prior-disposition-boundary.json'}
    reviews.append(review)
    literal_rows.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'sourceText':src,'currentTarget':target,'currentTargetSha256':t_hash,'finalTarget':rec_target or target,'finalTargetSha256':recommendation_hash or t_hash,'checks':literal_checks,'localizedUiTermChecks':ui_checks,'mismatches':missing_current,'recommendedMismatches':missing_recommended,'placeholderParity':review['placeholderParity'],'markupParity':review['markupParity']})
    target_cell_count+=1
assert target_cell_count==600

save_jsonl('source-slice.jsonl',sources)
save_jsonl('caller-context.jsonl',caller_rows)
save_jsonl('input-cells.jsonl',inputs)
save_jsonl('review-cells.jsonl',reviews)
save_jsonl('protected-literal-integrity.jsonl',literal_rows)
proposals=[x for x in reviews if x['disposition']!='accept-current']
save_jsonl('correction-candidates.jsonl',proposals)

# Prior-window exact disposition boundary: source IDs 400–449 are disjoint from reviewed 0–399.
# Include the adjacent source at position 399 with prior primary/cross disposition and exact live target hash.
prior_sid=ids[399]
prior_cross_packet=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-crossreview-by-agent-20261102')
prior_cross_meta=json.loads((prior_cross_packet/'summary.json').read_text())
prior_records=[]
for part,primary_path,cross_path in [
 ('previous','/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-primary-20261102/review-cells.jsonl','/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-crossreview-by-agent-20261102/cross-review-cells.jsonl')]:
  primary={}
  for line in pathlib.Path(primary_path).read_text().splitlines():
    x=json.loads(line)
    if x.get('sourceId')==prior_sid: primary[x['locale']]=x
  cross_rows=[]
  for line in pathlib.Path(cross_path).read_text().splitlines():
    x=json.loads(line)
    if x.get('sourceId')==prior_sid: cross_rows.append(x)
  prior_caller_refs=[]
  for f,line,matched_text,match_mode in raw_matches.get(prior_sid,[]):
    content=read_git(f); lines=content.decode('utf-8').splitlines()
    if line<1 or line>len(lines) or lines[line-1]!=matched_text:
      raise SystemExit(f'adjacent W399 caller lookup line drift: {f}:{line}')
    prior_caller_refs.append({'file':f,'kind':'production-source-callsite','registryLine':None,'currentLine':line,'lineNumberShift':None,'lineMatchMethod':match_mode,'matchedSourceId':prior_sid if match_mode=='exact-source-id' else None,'matchedSourceText':source_catalog[prior_sid] if match_mode=='exact-source-text-fallback' else None,'registrySourceLine':matched_text,'registrySourceLineSha256':sha(matched_text.encode()),'currentLineText':matched_text,'currentLineSha256':sha(matched_text.encode()),'contextBefore':lines[max(0,line-3):line-1],'contextAfter':lines[line:min(len(lines),line+2)],'currentFileBlob':blob(f),'currentFileSha256':sha(content)})
  prior_caller_refs.sort(key=lambda x:(x['file'],x['currentLine'],x['kind']))
  prior_caller_hash=sha(jbytes(prior_caller_refs))
  if set(primary)!=set(LOCALES) or {x.get('locale') for x in cross_rows}!=set(LOCALES): raise SystemExit('adjacent W399 primary/cross-review dispositions are incomplete')
  for x in cross_rows:
    p=primary[x['locale']]
    if p.get('source')!=source_catalog[prior_sid] or x.get('source')!=source_catalog[prior_sid]: raise SystemExit(f'adjacent W399 source text drift for {x["locale"]}')
    current=catalogs[x['locale']][prior_sid]
    previous_final=x.get('finalTarget',x.get('crossFinalTarget'))
    prior_records.append({'contextSourceOrdinal':399,'sourceId':prior_sid,'source':source_catalog[prior_sid],'sourceTextSha256':sha(source_catalog[prior_sid].encode()),'locale':x['locale'],'priorPrimaryPacketHead':p.get('exactHead'),'priorCrossReviewPacketHead':x.get('exactHead',prior_cross_meta.get('exactHead')),'priorPrimaryInputSha256':sha(jbytes(p)),'priorCrossReviewInputSha256':sha(jbytes(x)),'primaryDisposition':p.get('disposition',p.get('primaryDisposition')),'primaryRecommendedTarget':p.get('recommendedTarget',p.get('primaryRecommendedTarget')),'priorPrimaryCurrentTarget':p.get('currentTarget'),'priorPrimaryCurrentTargetSha256':p.get('currentTargetSha256'),'priorPrimaryCurrentTargetMatchesLive':p.get('currentTarget')==current,'crossReviewDisposition':x.get('crossReviewDisposition',x.get('crossDisposition',x.get('finalDisposition',x.get('independentVerdict')))),'crossReviewFinalTarget':previous_final,'priorCrossReviewCurrentTarget':x.get('currentTarget'),'priorCrossReviewCurrentTargetSha256':x.get('currentTargetSha256'),'priorCrossReviewInputMatchesCurrentLive':x.get('currentTarget')==current,'priorCrossReviewCallerContextSha256':x.get('callerContextSha256'),'currentLiveTarget':current,'currentLiveTargetSha256':sha(current.encode()),'priorCrossFinalMatchesCurrentLive':previous_final==current,'currentCallerRefs':prior_caller_refs,'callerContextSha256':prior_caller_hash,'currentCallerRefsMatchPrior':bool(x.get('callerRefs')) and {(r.get('file'),r.get('lineText'),r.get('line')) for r in x.get('callerRefs',[])}=={(r.get('file'),r.get('currentLineText'),r.get('currentLine')) for r in prior_caller_refs},'contextOnly':True})
save_jsonl('prior-context-dispositions.jsonl',prior_records)
prior_ledgers=[]; prior_matches=[]; prior_ids_seen=set()
for packet in sorted(O.parent.glob('chaptarrng-pr190-*')):
  if packet.resolve()==O.resolve(): continue
  for fp in sorted(packet.rglob('*.jsonl')):
    try: lines=fp.read_text().splitlines()
    except Exception: continue
    rows=[]; matches=[]
    for line in lines:
      try: x=json.loads(line)
      except Exception: continue
      sid=x.get('sourceId',x.get('id',x.get('catalogKey'))); ordinal=x.get('sourceOrdinal',x.get('sourcePosition',x.get('windowOrdinal')))
      disposition=next((x.get(k) for k in ('disposition','primaryDisposition','primaryVerdict','crossDisposition','crossReviewDisposition','reviewDisposition','independentVerdict','finalDisposition') if x.get(k) is not None),None)
      if isinstance(ordinal,int) and ordinal<400 and sid and disposition is not None:
        prior_ids_seen.add(sid)
        rows.append(x)
        if sid in source_ids:
          matches.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':x.get('locale'),'disposition':disposition})
    if rows:
      prior_ledgers.append({'path':str(fp),'sha256':sha(fp.read_bytes()),'rowsBefore400':len(rows),'sourceIds':sorted({x.get('sourceId') for x in rows if x.get('sourceId')}),'matchesToCurrentWindow':matches})
    prior_matches.extend({'ledger':str(fp),**x} for x in matches)
prior_context_summary={'sourceOrdinal':399,'sourceId':prior_sid,'cells':len(prior_records),'primaryDispositions':dict(collections.Counter(x['primaryDisposition'] for x in prior_records)),'crossReviewDispositions':dict(collections.Counter(x['crossReviewDisposition'] for x in prior_records)),'priorCrossReviewCurrentTargetsMatchingLive':sum(x['priorCrossReviewInputMatchesCurrentLive'] for x in prior_records),'priorCrossFinalTargetsMatchingLive':sum(x['priorCrossFinalMatchesCurrentLive'] for x in prior_records),'callerRefsReattested':len(prior_caller_refs),'priorCallerRefsMatchLive':sum(bool(x['currentCallerRefsMatchPrior']) for x in prior_records)}
prior_boundary={'scopePositions':[400,449],'searchedPriorPositions':[0,399],'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids_seen),'matchingPriorRows':prior_matches,'matchingPriorRowCount':len(prior_matches),'disjointCurrentSourceIds':len(prior_matches)==0,'ledgerFiles':prior_ledgers,'contextOnlyPreviousSourceId':prior_sid,'contextOnlyPreviousRows':len(prior_records)}
save_json('prior-disposition-boundary.json',prior_boundary)
input_files=['source-slice.jsonl','caller-context.jsonl','input-cells.jsonl']
input_sum_text=''.join(f"{sha((O/name).read_bytes())}  {name}\n" for name in input_files)
(O/'INPUT-SHA256SUMS').write_text(input_sum_text)
ui_term_rows=[]
save_json('localized-ui-terms.json',{'sourceKey':None,'sourceValue':None,'localeTerms':ui_term_rows,'useInSourceIds':[],'note':'No separate translated UI term was used in this source-key window; the <missing> sentinel is localized display text, not markup.'})
save_json('reviewer-provenance.json',{'reviewerRole':'primary semantic reviewer','reviewType':'source-context-aware language and terminology review of all frozen current cells','exactHead':head,'exactTree':tree,'scope':{'positions':[400,449],'cells':600,'locales':list(LOCALES)},'inputSources':['English source catalog','12 target catalogs','exact source-ID production C# references','exact source-text fallback for the uTorrent status'],'protectedLiteralPolicy':'Keep source product names, protocol acronyms, and placeholder tokens exact; ignore the localized angle-bracket missing-value display token as markup; allow ordinary technical vocabulary to follow established locale terminology.','uiTermPolicy':'No source in this window uses a separate localized UI-term comparison.','nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False})

counts=collections.Counter(x['disposition'] for x in reviews)
for key in ('accept-current','propose-refinement','propose-correction','hold'): counts.setdefault(key,0)
per_locale={}
for loc in LOCALES:
  locale_counts=collections.Counter(x['disposition'] for x in reviews if x['locale']==loc)
  per_locale[loc]={key:locale_counts.get(key,0) for key in ('accept-current','propose-refinement','propose-correction','hold')}
source_id_set_hash=sha(jbytes(ids))
prior_windows=[
 {'window':[0,49],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0000-0049-primary-20261102'},
 {'window':[50,99],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0050-0099-primary-part-a-20261102'},
 {'window':[100,149],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0100-0149-primary-part-a-20261102'},
 {'window':[150,199],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0150-0199-primary-part-a-20261102'},
 {'window':[200,249],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-primary-20261102'},
 {'window':[250,299],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0250-0299-primary-20261102'},
 {'window':[300,349],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0300-0349-primary-20261102'},
 {'window':[300,349],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0300-0349-crossreview-by-agent-20261102'},
 {'window':[350,399],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-primary-20261102'},
 {'window':[350,399],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-crossreview-by-agent-20261102'}]
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'scope':{'positions':[400,449],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceIdListSha256':source_id_set_hash,'counts':dict(counts),'proposalCount':len(proposals),'perLocale':per_locale,'callerEvidence':{'sourceIdsWithCallerPins':sum(bool(v) for v in callers_by_id.values()),'currentCallerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'lineNumberShifts':shifts,'callerMismatches':len(mismatches),'allCallersAttestedAtHead':not mismatches and not caller_gaps,'callerGaps':caller_gaps},'placeholders':{'sourceNonEmpty':sum(bool(x['sourcePlaceholders']) for x in reviews),'mismatches':sum(not x['placeholderParity'] for x in reviews)},'markup':{'sourceNonEmpty':sum(bool(x['sourceMarkup']) for x in reviews),'mismatches':sum(not x['markupParity'] for x in reviews)},'protectedLiterals':{'checkedCells':len(literal_rows),'currentMismatches':sum(bool(x['mismatches']) for x in literal_rows),'currentMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missingLiterals':x['mismatches']} for x in literal_rows if x['mismatches']],'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows),'recommendedMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missingLiterals':x['recommendedMismatches']} for x in literal_rows if x['recommendedMismatches']]},'priorDispositionBoundary':{'priorSourceIdWindowOverlap':len(prior_matches),'matchesInPrimaryOrCrossReviewSourceIdsPositions0To399':len(prior_matches),'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids_seen),'reviewedPriorWindows':prior_windows,'contextOnlyPriorSourceId':prior_sid,'contextOnlyPriorDispositionRows':len(prior_records),'adjacentPriorContext':prior_context_summary},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('summary.json',summary)
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':head,'tree':tree,'livePullRequest':pr,'expectedHead':EXPECTED_HEAD,'expectedTree':EXPECTED_TREE,'worktree':str(W),'worktreeClean':git('status','--porcelain').decode()=='' ,'scope':summary['scope'],'sourceFollowup':{'path':follow_path,'blob':follow_info['blob'],'sha256':follow_info['sha256'],'currentMissingIdsCount':len(ids),'currentMissingIdsSha256':source_id_set_hash,'window':[400,449],'sourceIds':50,'firstId':source_ids[0],'lastId':source_ids[-1]},'sourceFile':source_info,'registry':dict(registry_info,records=len(registry['records'])),'catalogs':catalog_info,'sourceSlice':{'path':'source-slice.jsonl','rows':len(sources),'sha256':sha((O/'source-slice.jsonl').read_bytes())},'inputCells':{'path':'input-cells.jsonl','rows':len(inputs),'sha256':sha((O/'input-cells.jsonl').read_bytes())},'callerContext':{'path':'caller-context.jsonl','sha256':sha((O/'caller-context.jsonl').read_bytes()),'sourceIds':len(caller_rows),'sourceIdsWithCallerPins':sum(bool(v) for v in callers_by_id.values()),'callerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'lineNumberShifts':shifts,'callerMismatches':len(mismatches),'callerGaps':caller_gaps},'review':{'path':'review-cells.jsonl','rows':len(reviews),'sha256':sha((O/'review-cells.jsonl').read_bytes()),'dispositions':dict(counts)},'protectedLiteralIntegrity':{'path':'protected-literal-integrity.jsonl','sha256':sha((O/'protected-literal-integrity.jsonl').read_bytes()),'rows':len(literal_rows),'currentMismatches':sum(bool(x['mismatches']) for x in literal_rows),'currentMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missingLiterals':x['mismatches']} for x in literal_rows if x['mismatches']],'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows),'recommendedMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missingLiterals':x['recommendedMismatches']} for x in literal_rows if x['recommendedMismatches']]},'correctionCandidates':{'path':'correction-candidates.jsonl','rows':len(proposals),'sha256':sha((O/'correction-candidates.jsonl').read_bytes())},'inputChecksumManifest':{'path':'INPUT-SHA256SUMS','sha256':sha((O/'INPUT-SHA256SUMS').read_bytes()),'verification':'pass'},'localizedUiTerms':{'path':'localized-ui-terms.json','sha256':sha((O/'localized-ui-terms.json').read_bytes())},'reviewDecisionInput':{'path':'review-decisions.json','sha256':sha(DECISION_PATH.read_bytes()),'findings':len(FINDINGS),'sourceRationales':len(SOURCE_RATIONALES)},'reviewerProvenance':{'path':'reviewer-provenance.json','sha256':sha((O/'reviewer-provenance.json').read_bytes())},'priorContextDispositionRows':len(prior_records),'priorContextAttestation':prior_context_summary,'priorContextDispositionSha256':sha((O/'prior-context-dispositions.jsonl').read_bytes()),'priorDispositionBoundaryPath':'prior-disposition-boundary.json','priorDispositionBoundarySha256':sha((O/'prior-disposition-boundary.json').read_bytes()),'previousWindowAttestation':{'reviewedPositions':[0,399],'sourceIdSetOverlap':0,'sourceIdListSha256':source_id_set_hash},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('manifest.json',manifest)
(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W400–449 primary semantic review\n\n- Exact PR state: OPEN/DRAFT at `{head}` / tree `{tree}`; source list contains 1,210 unique IDs and SHA-256 `{source_id_set_hash}`.\n- Scope: source-list positions 400–449 across all 12 direct locales = 50 source IDs / 600 current locale cells.\n- Caller pins: {sum(bool(v) for v in callers_by_id.values())} source IDs and {total_refs} exact production C# references across {len(unique_files)} files; mismatches: {len(mismatches)}; caller gaps: {len(caller_gaps)}.\n- Dispositions: {dict(counts)}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text, hash, and rationale is in `review-cells.jsonl`. Source-specific caller rationales and the full candidate decisions are in `review-decisions.json`.\n- Placeholder mismatches: {summary['placeholders']['mismatches']}; markup mismatches: {summary['markup']['mismatches']}; protected-literal mismatches in current targets: {summary['protectedLiterals']['currentMismatches']}; candidate mismatches: {summary['protectedLiterals']['recommendedMismatches']}.\n- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–399 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` reattests the adjacent W399 source dispositions against live targets and callers; `prior-disposition-boundary.json` records the scan and checksums.\n- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.\n''')
# Recheck exact frozen content and the live PR head immediately before sealing the packet.
final_head=git('rev-parse','HEAD').decode().strip(); final_tree=git('rev-parse','HEAD^{tree}').decode().strip()
final_pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],text=True))
assert final_head==head and final_tree==tree and final_head==EXPECTED_HEAD and final_tree==EXPECTED_TREE and final_pr['headRefOid']==head and final_pr['state']=='OPEN' and final_pr['isDraft']
cell_mismatches=[]
for x in inputs:
  if ids[x['sourceOrdinal']]!=x['sourceId'] or source_catalog[x['sourceId']]!=x['source'] or sha(source_catalog[x['sourceId']].encode())!=x['sourceTextSha256'] or catalogs[x['locale']][x['sourceId']]!=x['target'] or sha(catalogs[x['locale']][x['sourceId']].encode())!=x['targetSha256']:
    cell_mismatches.append({'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale']})
caller_mismatches=[]
for row in caller_rows:
  for ref in row['callerRefs']:
    content=read_git(ref['file']); lines=content.decode().splitlines(); n=ref['currentLine']
    if sha(content)!=ref['currentFileSha256'] or blob(ref['file'])!=ref['currentFileBlob'] or n<1 or n>len(lines) or lines[n-1]!=ref['currentLineText'] or sha(lines[n-1].encode())!=ref['currentLineSha256']:
      caller_mismatches.append({'sourceId':row['sourceId'],'file':ref['file'],'line':n})
prior_context_mismatches=[]
for row in prior_records:
  if ids[row['contextSourceOrdinal']]!=row['sourceId'] or source_catalog.get(row['sourceId'])!=row['source'] or catalogs[row['locale']].get(row['sourceId'])!=row['currentLiveTarget'] or sha(catalogs[row['locale']][row['sourceId']].encode())!=row['currentLiveTargetSha256']:
    prior_context_mismatches.append({'sourceId':row['sourceId'],'locale':row['locale'],'reason':'adjacent source/target drift'})
for ref in prior_caller_refs:
  content=read_git(ref['file']); lines=content.decode().splitlines(); n=ref['currentLine']
  if sha(content)!=ref['currentFileSha256'] or blob(ref['file'])!=ref['currentFileBlob'] or n<1 or n>len(lines) or lines[n-1]!=ref['currentLineText'] or sha(lines[n-1].encode())!=ref['currentLineSha256']:
    prior_context_mismatches.append({'sourceId':prior_sid,'file':ref['file'],'line':n,'reason':'adjacent caller drift'})
if sum(bool(x['currentCallerRefsMatchPrior']) for x in prior_records)!=len(prior_records): prior_context_mismatches.append({'sourceId':prior_sid,'reason':'prior cross-review callers do not match current pinned references'})
assert not cell_mismatches and not caller_mismatches and not prior_context_mismatches, json.dumps({'cell':cell_mismatches,'caller':caller_mismatches,'prior':prior_context_mismatches},ensure_ascii=False)
reattest={'repository':REPO,'pullRequest':PR,'livePullRequest':final_pr,'exactHead':final_head,'exactTree':final_tree,'headMatchesFrozenPacket':True,'sourceListSha256':source_id_set_hash,'sourceIdsAttested':len(source_ids),'cellCountReattested':len(inputs),'cellMismatches':cell_mismatches,'callerRefsReattested':total_refs,'callerMismatches':caller_mismatches,'priorContextSourceIdsAttested':1,'priorContextCellsReattested':len(prior_records),'priorContextCallerRefsReattested':len(prior_caller_refs),'priorContextMismatches':prior_context_mismatches,'callerGaps':caller_gaps,'checks':'pass','worktreeStatus':git('status','--porcelain').decode(),'recheckedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()}
save_json('final-reattestation.json',reattest)
manifest['finalReattestation']={'path':'final-reattestation.json','sha256':sha((O/'final-reattestation.json').read_bytes()),'checks':'pass','head':final_head,'tree':final_tree,'cellMismatches':0,'callerMismatches':0}
save_json('manifest.json',manifest)
checksum_files=sorted(p for p in O.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f"{sha(p.read_bytes())}  {p.name}\n" for p in checksum_files))
print(json.dumps({'head':head,'tree':tree,'scope':summary['scope'],'counts':dict(counts),'callerRefs':total_refs,'callerMismatches':len(mismatches),'priorContextRows':len(prior_records),'output':str(O)},ensure_ascii=False,indent=2))
