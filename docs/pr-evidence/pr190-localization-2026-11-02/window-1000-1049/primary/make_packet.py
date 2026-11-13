from __future__ import annotations
import collections, datetime, hashlib, json, pathlib, re, subprocess

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1000-1049-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='c28d0ab23b2c5454a10237496e642b2ad059d8ce'
TREE='bd7a8a32a8bffc2a3168b648ff6e22d368064e5b'
BRANCH='codex/chaptarrng-localization-complete-20261031'
REPO='snapetech-org/ChaptarrNG'; PR=190
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
LOCALE_ORDER=list(LOCALES)
SOURCE='src/NzbDrone.Core/Localization/Core/en.json'
FOLLOW='docs/localization/source-followup-20261101.json'
REGISTRIES={
 'provider':'docs/localization/provider-option-sources.json',
 'server':'docs/localization/server-message-sources.json',
 'loading':'docs/localization/loading-message-sources.json'}
PIPE_SERVER='docs/localization/server-message-callers.json'
TERMS='docs/localization/terminology.json'
PRIOR_ROOT=WORK/'docs/pr-evidence/pr190-localization-2026-11-02/window-0950-0999'

def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def git(*args, binary=False):
 r=subprocess.run(['git','-C',str(WORK),*args],check=True,capture_output=True)
 return r.stdout if binary else r.stdout.decode().strip()
def show(path): return git('show',f'{HEAD}:{path}',binary=True)
def tracked(path):
 b=show(path)
 return {'path':path,'gitBlob':git('rev-parse',f'{HEAD}:{path}'),'sha256':sha(b),'bytes':len(b)}
def writej(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
def lines(path): return show(path).decode('utf-8').splitlines()
def ph(s): return collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def icu(s): return sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
def state(): return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'branch':git('branch','--show-current'),'status':git('status','--porcelain')}

assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},state()
start=json.loads((OUT/'snapshots/start-all-pr-heads.json').read_text())
post=json.loads((OUT/'snapshots/after-source-selection-all-pr-heads.json').read_text())
selection=json.loads((OUT/'selected-queue-window.json').read_text())
assert start['snapshot_kind']=='start-before-source-selection' and post['snapshot_kind']=='after-source-selection'
assert selection['window']=='W1000-W1049' and selection['positions']==list(range(1000,1050))

follow=json.loads(show(FOLLOW)); source=json.loads(show(SOURCE)); queue=follow['currentMissingIds']
assert len(queue)==1210 and selection['selectedSourceIds']==queue[1000:1050]
assert sha(canon(queue))==follow['currentMissingIdsSha256']==selection['currentMissingIdsSha256']
selected=queue[1000:1050]
source_raw=show(SOURCE); follow_raw=show(FOLLOW)
source_info=tracked(SOURCE); follow_info=tracked(FOLLOW)

# Select exact source records from the domain-specific registries and pin their caller context.
reg_data={k:json.loads(show(p)) for k,p in REGISTRIES.items()}
reg_info={k:tracked(p) for k,p in REGISTRIES.items()}
reg_records={k:{x['id']:x for x in d['records']} for k,d in reg_data.items()}
source_rows=[]; source_records={}; caller_rows=[]; caller_file_info={}; stale=[]; gaps=[]
for ordinal,sid in enumerate(selected,1000):
 kind='provider' if sid.startswith('provider.option.') else 'server' if sid.startswith('server.message.') else 'loading' if sid.startswith('ui.loading.') else None
 assert kind and sid in source and sid in reg_records[kind],(ordinal,sid,kind)
 rec=reg_records[kind][sid]
 assert rec['source']==source[sid],(ordinal,sid,rec.get('source'),source.get(sid))
 protected=list(rec.get('protectedLiterals',[]))
 source_records[sid]=(kind,rec)
 row={'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],
      'sourceIdSha256':sha(sid),'sourceTextSha256':sha(source[sid]),
      'sourceCatalogPath':SOURCE,'sourceCatalogGitBlob':source_info['gitBlob'],'sourceCatalogSha256':source_info['sha256'],
      'sourceRegistryPath':REGISTRIES[kind],'sourceRegistryGitBlob':reg_info[kind]['gitBlob'],'sourceRegistrySha256':reg_info[kind]['sha256'],
      'sourceRegistryFingerprint':rec.get('sourceFingerprint'),'sourceRegistryProtectedLiterals':rec.get('protectedLiterals',[]),
      'effectiveProtectedLiterals':protected,'registryCategory':rec.get('category'),'registrySurface':rec.get('surface'),
      'registryParameters':rec.get('parameters',[]),'registryPatterns':rec.get('patterns',[]),'sourceTemplates':rec.get('sourceTemplates',[])}
 source_rows.append(row)
 refs=[]; seen=set()
 for pin in rec.get('callsites',[]):
  path=pin['file']; file_lines=lines(path); n=pin['line']; current=file_lines[n-1] if 1<=n<=len(file_lines) else None
  exact=current is not None and current.strip()==pin.get('sourceLine','').strip() and sha(current.strip())==pin.get('sourceLineSha256')
  hits=[(n,current)] if exact else [(i+1,v) for i,v in enumerate(file_lines) if sid in v]
  if not exact: stale.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':path,'registryLine':n,'expectedLineSha256':pin.get('sourceLineSha256'),'reason':'registry source line differs at exact head'})
  for lineno,text in hits:
   if (path,lineno) in seen: continue
   seen.add((path,lineno)); blob=git('rev-parse',f'{HEAD}:{path}')
   refs.append({'file':path,'line':lineno,'lineText':text.strip(),'lineSha256':sha(text.strip()),'fileGitBlob':blob,
                'fileSha256':sha(show(path)),'contextBefore':[x.strip() for x in file_lines[max(0,lineno-4):lineno-1]],
                'contextAfter':[x.strip() for x in file_lines[lineno:min(len(file_lines),lineno+3)]],
                'registryLine':n,'registrySourceLine':pin.get('sourceLine'),'registrySourceLineSha256':pin.get('sourceLineSha256'),
                'registryPinExact':exact,'category':pin.get('category'),'surface':pin.get('surface'),
                'kind':pin.get('kind'),'enum':pin.get('enum'),'member':pin.get('member')})
   caller_file_info[path]=tracked(path)
 refs.sort(key=lambda x:(x['file'],x['line']))
 if not refs: gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no direct source/caller line pinned'})
 caller_rows.append({'sourceOrdinal':ordinal,'sourceId':sid,'source':source[sid],'registryPath':REGISTRIES[kind],
                     'directCallerReferences':refs,'callerReferenceCount':len(refs),'callerContextSha256':sha(canon(refs)),
                     'callerReferenceStatus':'pinned' if refs else 'gap','registryCategory':rec.get('category'),
                     'registrySurface':rec.get('surface'),'enumOrParameterContext':[{'enum':x.get('enum'),'member':x.get('member'),'kind':x.get('kind')} for x in rec.get('callsites',[])],
                     'protectedLiterals':protected})
assert len(source_rows)==len(caller_rows)==50 and not gaps and not stale

# Pin exact locale catalogs and their current values.
locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{filename}' for loc,filename in LOCALES.items()}
catalogs={}; catalog_info={}
for loc,path in locale_paths.items():
 catalog=json.loads(show(path)); assert set(catalog)==set(source),(loc,'catalog key-set mismatch')
 catalogs[loc]=catalog; catalog_info[loc]=tracked(path)
source_by={x['sourceId']:x for x in source_rows}; caller_by={x['sourceId']:x for x in caller_rows}
input_cells=[]
for row in source_rows:
 for loc,path in locale_paths.items():
  cur=catalogs[loc][row['sourceId']]; protected=row['effectiveProtectedLiterals']
  checks=[{'literal':lit,'presentInSource':lit in row['source'],'presentInCurrentTarget':lit in cur} for lit in protected]
  input_cells.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':row['sourceOrdinal'],'sourceId':row['sourceId'],'locale':loc,
   'source':row['source'],'sourceIdSha256':row['sourceIdSha256'],'sourceTextSha256':row['sourceTextSha256'],
   'sourceFile':SOURCE,'sourceFileGitBlob':source_info['gitBlob'],'sourceFileSha256':source_info['sha256'],
   'currentTarget':cur,'currentTargetSha256':sha(cur),'targetFile':path,'targetFileGitBlob':catalog_info[loc]['gitBlob'],'targetFileSha256':catalog_info[loc]['sha256'],
   'sourcePlaceholders':dict(sorted(ph(row['source']).items())),'currentTargetPlaceholders':dict(sorted(ph(cur).items())),
   'placeholderParity':ph(row['source'])==ph(cur),'sourceMarkup':markup(row['source']),'currentTargetMarkup':markup(cur),
   'markupParity':markup(row['source'])==markup(cur),'sourceIcuSignature':icu(row['source']),'currentTargetIcuSignature':icu(cur),
   'icuParity':icu(row['source'])==icu(cur),'protectedLiterals':protected,'protectedLiteralChecks':checks,
   'protectedLiteralCurrentFailures':[x['literal'] for x in checks if not x['presentInCurrentTarget']],
   'callerContextSha256':caller_by[row['sourceId']]['callerContextSha256']})
assert len(input_cells)==600

# Capture provider-option localization/display pipeline and all server-message display pins.
provider_pipeline=[]
provider_pipe_specs=[
 ('src/Chaptarr.Http/ClientSchema/SchemaBuilder.cs',[43,47,49,50,246,248],'SchemaBuilder resolves FieldOption label/hint resource IDs into the provider schema.'),
 ('src/NzbDrone.Core/Localization/LocalizationService.cs',[69,79,84],'Server localization reads the selected locale dictionary and returns the key if missing.'),
 ('frontend/src/Components/Form/ProviderFieldFormGroup.js',[52,55,56,122],'Provider schema options and hints are passed into field controls.'),
 ('frontend/src/Components/Form/FormInputGroup.js',[99,100],'Select fields use EnhancedSelectInput.'),
 ('frontend/src/Components/Form/EnhancedSelectInput.js',[546,563,620,637],'Enhanced select renders provider-option values and hints.'),
 ('frontend/src/Components/Form/HintedSelectInputOption.js',[36],'Option component displays the localized value/hint.')]
for path,nums,why in provider_pipe_specs:
 ls=lines(path)
 for n in nums:
  assert 1<=n<=len(ls),(path,n)
  provider_pipeline.append({'file':path,'line':n,'lineText':ls[n-1].strip(),'lineSha256':sha(ls[n-1].strip()),
   'fileGitBlob':git('rev-parse',f'{HEAD}:{path}'),'fileSha256':sha(show(path)),
   'contextBefore':[x.strip() for x in ls[max(0,n-4):n-1]],'contextAfter':[x.strip() for x in ls[n:min(len(ls),n+3)]],
   'interpretation':why})
  caller_file_info[path]=tracked(path)

server_pipe=json.loads(show(PIPE_SERVER)); server_pipeline=[]; server_pipeline_gaps=[]
for pin in server_pipe['callsites']:
 path=pin['file']; ls=lines(path); n=pin['line']; cur=ls[n-1] if 1<=n<=len(ls) else None
 exact=cur is not None and cur.strip()==pin['sourceLine'].strip() and sha(cur.strip())==pin['sourceLineSha256']
 if not exact:
  server_pipeline_gaps.append({'file':path,'line':n,'reason':'server display caller pin mismatch'}); continue
 server_pipeline.append({'file':path,'line':n,'lineText':cur.strip(),'lineSha256':sha(cur.strip()),
  'fileGitBlob':git('rev-parse',f'{HEAD}:{path}'),'fileSha256':sha(show(path)),
  'contextBefore':[x.strip() for x in ls[max(0,n-4):n-1]],'contextAfter':[x.strip() for x in ls[n:min(len(ls),n+3)]],
  'pipeline':'Generic server-message localization and display.'})
 caller_file_info[path]=tracked(path)
assert not server_pipeline_gaps

# Pin loading-message render path, source data and relevant loading message records.
loading_path='frontend/src/Components/Loading/loading-messages.json'
loading_js='frontend/src/Components/Loading/LoadingMessage.js'
loading_runtime=[]
for path in [loading_path,loading_js]:
 ls=lines(path)
 matches=[]
 if path==loading_path:
  selected_set=set(selected)
  for i,line in enumerate(ls,1):
   if any(sid in line for sid in selected_set): matches.append(i)
 else:
  for i,line in enumerate(ls,1):
   if 'messages' in line or 'translate(' in line or 'translateMessage' in line: matches.append(i)
 for n in matches:
  loading_runtime.append({'file':path,'line':n,'lineText':ls[n-1].strip(),'lineSha256':sha(ls[n-1].strip()),
    'fileGitBlob':git('rev-parse',f'{HEAD}:{path}'),'fileSha256':sha(show(path)),
    'contextBefore':[x.strip() for x in ls[max(0,n-4):n-1]],'contextAfter':[x.strip() for x in ls[n:min(len(ls),n+3)]],
    'interpretation':'Loading message source ID and UI rendering path.'})
  caller_file_info[path]=tracked(path)
assert len([x for x in loading_runtime if x['file']==loading_path])>=7

# Read prior dispositions through W999, preserving their actual original packet/file provenance.
prior_primary_path=PRIOR_ROOT/'primary/prior-disposition-hashes.jsonl'
prior_window_path=PRIOR_ROOT/'application/full-window-readback.jsonl'
prior_primary_raw=prior_primary_path.read_bytes(); prior_window_raw=prior_window_path.read_bytes()
prior_0_949=[json.loads(x) for x in prior_primary_raw.decode().splitlines()]
prior_950_999=[json.loads(x) for x in prior_window_raw.decode().splitlines()]
assert len(prior_0_949)==11400 and {x['sourceOrdinal'] for x in prior_0_949}==set(range(950))
assert len(prior_950_999)==600 and {x['sourceOrdinal'] for x in prior_950_999}==set(range(950,1000))
assert len({(x['sourceOrdinal'],x['locale']) for x in prior_0_949})==11400
assert len({(x['sourceOrdinal'],x['locale']) for x in prior_950_999})==600
prior=[]
for x in prior_0_949:
 prior.append({'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'sourceTextSha256':x.get('sourceTextSha256'),
  'priorDisposition':x.get('priorDisposition'),'priorCrossReviewDisposition':x.get('priorCrossReviewDisposition'),
  'priorInputTargetSha256':x.get('priorCurrentTargetSha256'),'priorFinalTargetSha256':x.get('priorFinalTargetSha256'),
  'sourcePacket':x.get('priorPacket'),'sourceRecordFile':x.get('priorRecordFile'),'sourceRecordSha256':x.get('priorRecordSha256'),
  'liveCurrentTargetSha256':x.get('liveCurrentTargetSha256'),'liveTargetMatchesPriorFinalHash':x.get('liveTargetMatchesPriorFinalHash'),
  'originEvidenceFile':'primary/prior-disposition-hashes.jsonl','originEvidenceFileSha256':sha(prior_primary_raw)})
for x in prior_950_999:
 prior.append({'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],
  'sourceTextSha256':sha(x['source']),'priorDisposition':x.get('rootDisposition'),'priorCrossReviewDisposition':None,
  'priorInputTargetSha256':x['inputTargetSha256'],'priorFinalTargetSha256':x['finalTargetSha256'],
  'sourcePacket':'chaptarrng-pr190-window-0950-0999-primary-20261102 + application readback',
  'sourceRecordFile':'application/full-window-readback.jsonl','sourceRecordSha256':sha(canon(x)),
  'liveCurrentTargetSha256':x['finalTargetSha256'],'liveTargetMatchesPriorFinalHash':None,
  'originEvidenceFile':'application/full-window-readback.jsonl','originEvidenceFileSha256':sha(prior_window_raw)})
assert len(prior)==12000 and len({(x['sourceOrdinal'],x['locale']) for x in prior})==12000
# Reattest those prior target hashes against current c28 catalogs; prior records include exact ID and locale.
prior_live=[]
for x in prior:
 loc=x['locale']; sid=x['sourceId']; live=catalogs[loc].get(sid); live_hash=sha(live) if live is not None else None
 final_hash=x['priorFinalTargetSha256']
 prior_live.append({**x,'liveCurrentTargetSha256':live_hash,'liveTargetMatchesPriorFinalHash':live_hash==final_hash})

# The W999 final targets form the backward boundary; W1050 source/targets form forward boundary.
prev_ids=queue[999:1000]; next_ids=queue[1050:1051]
assert len(prev_ids)==len(next_ids)==1
w999_id=prev_ids[0]; w1050_id=next_ids[0]
rows950=[x for x in prior_950_999 if x['sourceOrdinal']==999]
assert len(rows950)==12 and all(x['sourceId']==w999_id for x in rows950)
w999=[]
for x in sorted(rows950,key=lambda z:LOCALE_ORDER.index(z['locale'])):
 loc=x['locale']; live=catalogs[loc][w999_id]
 w999.append({'sourceOrdinal':999,'sourceId':w999_id,'source':source[w999_id],'sourceTextSha256':sha(source[w999_id]),
  'locale':loc,'previousDisposition':x['rootDisposition'],'previousInputTargetSha256':x['inputTargetSha256'],
  'previousFinalTargetSha256':x['finalTargetSha256'],'liveTargetSha256':sha(live),'liveTargetMatchesPreviousFinal':sha(live)==x['finalTargetSha256'],
  'targetFile':locale_paths[loc],'targetFileGitBlob':catalog_info[loc]['gitBlob']})
assert all(x['liveTargetMatchesPreviousFinal'] for x in w999)
w1050=[]
for loc,path in locale_paths.items():
 target=catalogs[loc][w1050_id]
 w1050.append({'sourceOrdinal':1050,'sourceId':w1050_id,'source':source[w1050_id],'sourceTextSha256':sha(source[w1050_id]),
  'locale':loc,'currentTarget':target,'currentTargetSha256':sha(target),'targetFile':path,'targetFileGitBlob':catalog_info[loc]['gitBlob'],
  'scope':'boundary context only; no W1050 disposition assigned'})

# Load internal product terminology used by the selected playful messages.
term_raw=show(TERMS); term_data=json.loads(term_raw); term_info=tracked(TERMS)
terms={x['id']:x for x in term_data.get('terms',[])}
term_extract={k:terms[k] for k in ['domain.audiobook','domain.ebook'] if k in terms}

# Reviewed primary decisions: only high-confidence changes and bounded holds are recommended.
C={}; H={}
def cand(pos,loc,target,kind,why,confidence='high',refs=()):
 C[(pos,loc)]={'target':target,'kind':kind,'why':why,'confidence':confidence,'referenceIds':list(refs)}
def hold(pos,loc,why,confidence='low'):
 H[(pos,loc)]={'why':why,'confidence':confidence}
# Language names (provider labels)
cand(1000,'de','Kastilisches Spanisch','correction','The current value mixes the German word for Spanish with the English adjective Castilian. The corrected German compound names the same language variant.', 'high')
cand(1002,'es','tagalo','correction','The bare-language option contains an unnecessary definite article and uses the English-form spelling; Spanish uses tagalo as the language name.', 'high')
cand(1002,'fr','tagalog','refinement','The leading definite article makes this option read as a sentence fragment rather than a bare language name; keep the language label without Le.', 'moderate')
cand(1003,'es','tamil','correction','Remove the definite article from this bare language label.', 'high')
cand(1003,'ja','タミル語','refinement','The current form names Tamil but omits 語, the normal Japanese language-name suffix used on the neighboring language options.', 'moderate')
cand(1003,'zh-Hans','泰米尔语','correction','Add 语 so the label denotes the Tamil language rather than only the ethnic/language stem.', 'high')
cand(1003,'zh-Hant','泰米爾語','correction','Add 語 so the label denotes the Tamil language rather than only the ethnic/language stem.', 'high')
cand(1008,'hi','उर्दू','correction','The current target is written in Urdu/Arabic script inside the Hindi catalog; render the Hindi language name in Devanagari.', 'high')
cand(1008,'ja','ウルドゥー語','refinement','Add the standard Japanese language suffix 語 to the transliterated label.', 'moderate')
cand(1008,'vi','Tiếng Urdu','refinement','Use the Vietnamese language-label prefix Tiếng, as in adjacent Vietnamese language options.', 'moderate')
cand(1009,'de','Vietnamesisch','correction','German standalone language names are nouns and are capitalized; the current lowercase adjective form is not a complete language label.', 'high')
# Search-type labels and hints
cand(1010,'es','Todos los torrents','correction','Torrentes means streams or torrents of water in Spanish; in this file-sharing selector the technical term is torrents.', 'high')
cand(1010,'pt-BR','Todos os torrents','correction','Torrentes means streams in Portuguese; the technical term in this provider filter is torrents.', 'high')
cand(1010,'zh-Hans','所有种子','refinement','Translate torrent with the established seed terminology used by adjacent VIP/freeleech options instead of leaving Torrent untranslated.', 'moderate')
cand(1010,'zh-Hant','所有種子','refinement','Translate torrent with the established 種子 term used by adjacent VIP/freeleech options instead of leaving Torrent untranslated.', 'moderate')
cand(1011,'fr','Tout rechercher','correction','Trouver means find; the source explicitly says search. This changes the action presented by the selector hint.', 'high')
cand(1011,'ko','모든 항목 검색','correction','The current wording is an informal imperative meaning “find everything”; the source is a search hint. Use an explicit search label.', 'high')
cand(1011,'zh-Hans','搜索所有内容','correction','寻找 means look for/find and misses the source action Search; use a direct search phrase.', 'high')
cand(1011,'zh-Hant','搜尋所有內容','correction','尋找 means look for/find and misses the source action Search; use a direct search phrase.', 'high')
cand(1012,'ko','활성 토렌트만','correction','활성화 means activation, not active items. The enum is the Active search type; label the active torrents and preserve the Only restriction.', 'high')
cand(1012,'vi','Chỉ torrent đang hoạt động','correction','The current phrase means only operating/active without naming the item being filtered. The caller is the Active torrent-search type.', 'high')
# Protected torrent terms
cand(1014,'ar','تورنتات Freeleech','refinement','Move the noun before the protected Freeleech brand/flag for natural Arabic ordering; preserve Freeleech exactly.', 'moderate')
cand(1014,'pt-BR','Torrents com Freeleech','correction','Torrentes is a false friend here; state that these are torrents with the protected Freeleech flag.', 'high')
cand(1016,'ar','تورنتات Freeleech أو VIP','refinement','Move “torrents” before the exact protected terms for a readable Arabic hint; keep Freeleech and VIP unchanged.', 'moderate')
cand(1018,'ar','تورنتات VIP','refinement','Use Arabic noun-before-modifier order while preserving the exact VIP literal.', 'moderate')
cand(1019,'ko','VIP 아님','correction','아니 VIP reads as a spoken “no, VIP” correction; VIP 아님 is a concise negative label and preserves VIP exactly.', 'high')
cand(1020,'hi','गैर-VIP टोरेंट','correction','The current word order is malformed. गैर-VIP टोरेंट is a concise non-VIP torrent label and preserves VIP exactly.', 'moderate')
# Priority and Goodreads book-condition values
cand(1021,'de','sehr niedrig','correction','The current adjective is inflected as “lower” for an omitted masculine noun and reads incomplete. The uninflected scale value is sehr niedrig.', 'high')
cand(1021,'ko','매우 낮음','correction','매우 낮은 is an attributive ending that requires a following noun; use the standalone scale form.', 'high')
cand(1022,'ko','매우 높음','correction','매우 높은 is an attributive ending that requires a following noun; use the standalone scale form.', 'high')
cand(1025,'fr','Comme neuf','correction','For an implied masculine book/item, neuf is the natural condition label; nouveau is not the idiomatic condition equivalent.', 'high')
cand(1025,'id','Seperti baru','refinement','Remove the unnecessary yang; the shorter expression is the natural Indonesian “like new” condition label.', 'moderate')
cand(1025,'ja','新品同様','correction','新しいように is a literal and awkward “in a new way” construction; 新品同様 is the natural like-new condition label.', 'high')
cand(1025,'ko','새것과 같음','refinement','The current phrase is an incomplete attributive comparison. Use a complete standalone condition label.', 'moderate')
cand(1026,'ko','아주 좋음','correction','아주 좋은 requires a following noun; use the standalone grade label.', 'high')
cand(1027,'ar','جيد','refinement','Remove the definite article to match the adjacent standalone condition grades.', 'moderate')
cand(1027,'fr','Bon','correction','The source is a standalone condition for an implied masculine book/item; Bonne conflicts with the surrounding masculine Comme neuf / Très bon forms.', 'moderate')
cand(1027,'id','Baik','refinement','The current yang baik is a relative phrase (“that is good”); the standalone condition value is Baik.', 'moderate')
cand(1027,'ko','좋음','correction','좋은 requires a following noun; use the standalone grade label.', 'high')
cand(1028,'id','Dapat diterima','refinement','Remove yang to make this a concise standalone book-condition value.', 'moderate')
# Download-client states and actions
cand(1030,'id','Subfolder','refinement','Normalize the product label casing; Indonesian catalog text should not retain internal English camel case.', 'moderate')
cand(1032,'id','Terhenti','correction','Berhenti is an active stop/quit form, while the qBittorrent enum value is a stopped state.', 'moderate')
cand(1033,'es','Iniciar','refinement','The source is an action label; Inicio is the noun “start/beginning.” Use the verb form used for controls.', 'moderate')
cand(1033,'hi','शुरू करें','refinement','The source is an action label; शुरू करें is a concise polite control action, unlike the noun शुरुआत.', 'moderate')
# Path and validation messages
cand(1038,'es',"La ruta '{value0}' está dentro de la carpeta de la papelera de reciclaje configurada.",'correction','The current bin de reciclaje wording is an English-shaped calque; use the Spanish term papelera de reciclaje and preserve {value0}.', 'high')
cand(1038,'id',"Jalur '{value0}' berada di dalam folder tempat sampah yang dikonfigurasi.",'correction','The current kitar semula is Malay rather than Indonesian. Use Indonesian tempat sampah and localize Path as Jalur.', 'high')
cand(1038,'ja',"パス '{value0}' は、設定済みのごみ箱フォルダー内にあります。",'refinement','Use the Japanese term ごみ箱 and a complete polite sentence instead of the literal “recycle bin” calque and plain-form ending.', 'moderate')
cand(1038,'vi',"Đường dẫn '{value0}' nằm trong thư mục thùng rác đã cấu hình.",'correction','Đường means road; the filesystem term is Đường dẫn. The current bin tái chế is a literal English calque.', 'high')
cand(1039,'es',"El usuario '{value1}' no puede leer la carpeta '{value0}'. Permiso denegado. Asegúrese de que el proceso de Chaptarr tenga permiso de lectura en este directorio y sus subdirectorios. (Entorno: {value2})",'refinement','Use the formal usted imperative Asegúrese to match the corresponding unsuffixed Spanish folder-permission message in the same catalog; preserve the placeholders and Chaptarr.', 'moderate')
cand(1040,'es',"El usuario '{value1}' no puede escribir en la carpeta '{value0}'. Permiso denegado. Asegúrese de que el proceso de Chaptarr tenga permiso de escritura en este directorio y sus subdirectorios. (Entorno: {value2}) Chaptarr lo comprueba intentando crear y eliminar un archivo temporal en la carpeta.",'refinement','Use the formal usted imperative Asegúrese to match the corresponding unsuffixed Spanish folder-permission message in the same catalog; preserve the placeholders and Chaptarr.', 'moderate')
cand(1041,'es',"La ruta '{value0}' no puede estar dentro de la carpeta de inicio.",'correction','Pasta is Portuguese and means pasta in Spanish; use the Spanish filesystem term carpeta.', 'high')
cand(1041,'fr',"Le chemin '{value0}' ne peut pas se trouver dans le dossier de démarrage.",'correction','Voie means road/way in this context; chemin is the filesystem-path term.', 'high')
cand(1041,'id',"Jalur '{value0}' tidak boleh berada di dalam folder startup.",'refinement','Localize the filesystem term Path as Jalur; retain startup only as the established technical folder label.', 'moderate')
cand(1041,'pt-BR',"O caminho '{value0}' não pode estar dentro da pasta de inicialização.",'refinement','Translate start-up as inicialização for a natural Brazilian Portuguese system-folder label.', 'moderate')
cand(1041,'vi',"Đường dẫn '{value0}' không thể nằm trong thư mục khởi động.",'correction','Đường means road; Đường dẫn is the normal Vietnamese filesystem-path term.', 'high')
cand(1042,'es',"La ruta '{value0}' está dentro de la carpeta del sistema {value1}.",'correction','Pasta is Portuguese and means pasta in Spanish; use the Spanish filesystem term carpeta.', 'high')
cand(1042,'fr',"Le chemin '{value0}' se trouve dans le dossier système {value1}.",'correction','Voie means road/way in this context; chemin is the filesystem-path term. Keep the system-folder value after the noun.', 'high')
cand(1042,'id',"Jalur '{value0}' berada di dalam folder sistem {value1}.",'refinement','Localize the filesystem term Path as Jalur and retain the exact dynamic system-folder value.', 'moderate')
cand(1042,'ja',"パス '{value0}' はシステムフォルダー '{value1}' 内にあります。",'correction','The current sentence places {value1} after the predicate. Attach the system-folder value to フォルダー and finish with the polite server-message ending.', 'high')
cand(1042,'ko',"'{value0}' 경로는 시스템 폴더 '{value1}' 안에 있습니다.",'correction','The current sentence puts {value1} after the verb, where it does not modify “system folder.” Place the placeholder inside that noun phrase.', 'high')
cand(1042,'vi',"Đường dẫn '{value0}' nằm bên trong thư mục hệ thống {value1}.",'correction','Đường means road; Đường dẫn is the filesystem-path term. Keep {value1} attached to the system-folder phrase.', 'high')
cand(1042,'zh-Hans',"路径“{value0}”位于系统文件夹“{value1}”中。",'correction','Move {value1} into the system-folder noun phrase; the current placement after 中 breaks the Chinese sentence.', 'high')
cand(1042,'zh-Hant',"路徑「{value0}」位於系統資料夾「{value1}」中。",'correction','Move {value1} into the system-folder noun phrase; use the Traditional Chinese 資料夾 form and preserve both placeholders.', 'high')
# Playful loading strings and their source-specific literals
cand(1043,'hi','आपकी किताबों की अलमारी व्यवस्थित की जा रही है...','correction','The current infinitive means “in order to arrange your books” and drops the bookshelf; use an ongoing loading-state sentence.', 'moderate')
cand(1044,'ar','جارٍ الانتقال إلى chaptarr التالي...','refinement','Make the loading phrase grammatical while preserving the source registry’s protected lowercase product pun chaptarr exactly.', 'moderate')
cand(1044,'hi','अगले chaptarr पर जा रहे हैं...','refinement','The current target means “to go for the next chaptarr”; use a natural ongoing action and keep protected chaptarr exact.', 'moderate')
cand(1047,'ar','لا شيء يضاهي رائحة فتح كتاب إلكتروني جديد... أليس كذلك؟','correction','The current target omits the eBook/digital-book punchline and changes the source into an ordinary new-book smell. Restore the digital-book idea and rhetorical question.', 'moderate')
cand(1047,'hi','नई... ई-पुस्तक खोलने की खुशबू जैसी कोई चीज़ नहीं, है ना?','refinement','Keep the source interruption and question that make the new eBook smell joke work; the current wording loses the interruption after new.', 'moderate')
cand(1047,'zh-Hans','没有什么比打开一本新……电子书时闻到的气味更特别了，对吧？','refinement','The current literal word order is unidiomatic and loses the source’s interruption/punchline. Use a grammatical question while preserving the eBook joke.', 'moderate')
cand(1047,'zh-Hant','沒有什麼比打開一本新……電子書時聞到的氣味更特別了，對吧？','refinement','The current literal word order is unidiomatic and loses the source’s interruption/punchline. Use a grammatical question while preserving the eBook joke.', 'moderate')
cand(1048,'hi','कहानी में आपकी जगह ढूँढ़ी जा रही है...','refinement','The current infinitive is not a natural loading-state sentence; use a polite passive progress phrase.', 'moderate')
cand(1048,'ja','物語の続きを読む位置を探しています…','refinement','The current literal 自分の場所 (“your place”) is awkward in a reading context; identify the place to continue reading.', 'moderate')
cand(1048,'ko','이야기 속에서 읽던 곳을 찾는 중...','correction','The current 당신의 장소를 이야기에서 is an awkward calque. This phrase naturally refers to locating where the reader left off.', 'high')
cand(1049,'hi','दयालु बनें: अपनी ऑडियोबुक रिवाइंड करें।','correction','पीछे करें means move/put behind, not rewind audio. Use the familiar Hindi loan verb रिवाइंड and keep the “Be Kind” slogan.', 'moderate')
cand(1049,'zh-Hans','请友善一点：把有声书倒回去。','refinement','倒回你的有声书 is an awkward direct object; use the natural action “rewind the audiobook” while keeping the slogan.', 'moderate')
cand(1049,'zh-Hant','請友善一點：把有聲書倒回去。','refinement','倒帶你的有聲書 is an awkward direct object; use the natural action “rewind the audiobook” while keeping the slogan.', 'moderate')
# Bounded holds where a native-language equivalent needs confirmation rather than an invented target.
hold(1000,'vi','“Castilian Spanish” distinguishes a Spanish variety. The current Vietnamese calque is awkward, but the preferred local name for this particular variant was not independently verified; retain pending native-speaker/dictionary review.','low')
hold(1049,'ar','The Be Kind: Rewind slogan depends on an English tape-rewind idiom. The current meaning is understandable but awkward; no verified Arabic slogan was available in this non-browser review.','low')
hold(1049,'id','The Indonesian rewind verb needs a natural audio-control idiom while retaining the Be Kind wordplay. The current meaning is recognizable, but hold the phrasing for native-speaker review.','low')
# Incorporate the independent focus reviewer only where its suggestions survive a separate context/formality check.
cand(1021,'es','muy baja','correction','These are priority values; with the implied feminine prioridad noun, the current masculine muy bajo is mismatched.', 'moderate')
cand(1021,'fr','Très basse','correction','These are priority values; with the implied feminine priorité noun, use basse rather than the current masculine bas.', 'moderate')
cand(1021,'pt-BR','Muito baixa','correction','These are priority values; with the implied feminine prioridade noun, the current masculine baixo is mismatched.', 'moderate')
cand(1022,'es','Muy alta','correction','This is a priority value; with the implied feminine prioridad noun, use alta rather than the current masculine alto.', 'moderate')
cand(1022,'pt-BR','Muito alta','correction','This is a priority value; with the implied feminine prioridade noun, use alta rather than the current masculine alto.', 'moderate')
cand(1027,'hi','अच्छा','correction','The current अच्छे is an inflected form that does not stand alone. Use the masculine singular bare grade form that matches the neighboring बहुत अच्छा value.', 'moderate')
cand(1027,'pt-BR','Bom','correction','The enum grades the owned book itself; use masculine Bom to match the neighboring Novo / Muito bom standalone book-grade forms.', 'moderate')
cand(1038,'hi',"पथ '{value0}' कॉन्फ़िगर किए गए रीसायकल बिन फ़ोल्डर के अंदर है",'refinement','मार्ग can mean route/way; पथ is a clearer filesystem-path term. रीसायकल बिन is the familiar computer UI term and avoids “recycled bin.”', 'moderate')
cand(1041,'hi',"'{value0}' पथ स्टार्टअप फ़ोल्डर के अंदर नहीं हो सकता है",'refinement','Use पथ as the filesystem-path term rather than मार्ग (route/way).', 'moderate')
cand(1042,'hi',"पथ '{value0}' सिस्टम फ़ोल्डर {value1} के अंदर है",'refinement','Use पथ as the filesystem-path term rather than मार्ग (route/way); retain the system-folder value.', 'moderate')
cand(1043,'id','Merapikan rak buku Anda...','refinement','The current value says only “organizing your books” and loses bookshelf. Name the rak buku to preserve the source scene.', 'moderate')
cand(1044,'hi','अगले chaptarr की ओर बढ़ रहे हैं...','refinement','Use a natural ongoing transition phrase and preserve the source registry’s protected lowercase product pun chaptarr exactly.', 'moderate')
cand(1048,'ko','이야기에서 읽던 부분을 찾는 중...','correction','The current 당신의 장소를 이야기에서 is an awkward calque. This phrase naturally says the reader is finding where they left off in the story.', 'high')
# The eBook smell line depends on a culture-specific joke; retain current copy and request native review where the gag is awkward or altered.
for loc,reason in {
 'ar':'The current target omits the eBook punchline and question. The joke is clear, but a natural Arabic version needs a native speaker.',
 'hi':'The current target loses the “new... eBook?” interruption. Keep the current literal version pending a native Hindi joke-preserving rendering.',
 'id':'The current sentence is awkward and the interruption/punchline is difficult to reproduce naturally. Hold for an Indonesian native reviewer.',
 'ja':'The current sentence is an awkward literal construction. Hold for a native Japanese rendering of the smell-of-an-eBook joke.',
 'ko':'The current target redundantly mentions an electronic book and then eBook; a native reviewer should settle how to preserve the joke.',
 'vi':'The current wording is awkward and repeats the eBook idea. Hold for a native Vietnamese rendering of the joke.',
 'zh-Hans':'The current literal syntax is awkward. Hold for a native Simplified Chinese rendering of the new…eBook punchline.',
 'zh-Hant':'The current literal syntax is awkward. Hold for a native Traditional Chinese rendering of the new…eBook punchline.'}.items():
 C.pop((1047,loc),None); H[(1047,loc)]={'why':reason,'confidence':'low'}
assert not(set(C)&set(H))

# Formally review each of the 600 cells. Candidate values always pass structural/protected-literal checks.
review=[]; audits=[]; locale_rationale={
 'ar':'reviewed as a localized language/filter/validation/loading label in Arabic context',
 'de':'reviewed as a German UI label or server validation message',
 'es':'reviewed as a Spanish UI label or server validation message; tú/usted register compared against neighboring catalog copy',
 'fr':'reviewed as a French UI label or server validation message',
 'hi':'reviewed as a Hindi UI label or server validation message',
 'id':'reviewed as an Indonesian UI label or server validation message',
 'ja':'reviewed as a Japanese UI label or server validation message',
 'ko':'reviewed as a Korean UI label or server validation message',
 'pt-BR':'reviewed as a Brazilian Portuguese UI label or server validation message',
 'vi':'reviewed as a Vietnamese UI label or server validation message',
 'zh-Hans':'reviewed as a Simplified Chinese UI label or server validation message',
 'zh-Hant':'reviewed as a Traditional Chinese UI label or server validation message'}
for cell in input_cells:
 pos=cell['sourceOrdinal']; loc=cell['locale']; key=(pos,loc); cur=cell['currentTarget']; candrow=C.get(key); holdrow=H.get(key)
 if candrow:
  disposition=candrow['kind']; recommended=candrow['target']; final=recommended; rationale=candrow['why']; confidence=candrow['confidence']
 elif holdrow:
  disposition='hold'; recommended=None; final=cur; rationale=holdrow['why']; confidence=holdrow['confidence']
 else:
  disposition='accept-current'; recommended=None; final=cur
  rationale=f"{locale_rationale[loc]}; the current value preserves the source meaning and is adequate in the pinned caller context, with no material defect identified."
  confidence='moderate'
 src=cell['source']; rec=final
 checks={
  'sourcePlaceholders':dict(sorted(ph(src).items())),'currentPlaceholders':dict(sorted(ph(cur).items())),
  'finalPlaceholders':dict(sorted(ph(rec).items())),'placeholderParity':ph(src)==ph(cur)==ph(rec),
  'sourceMarkup':markup(src),'currentMarkup':markup(cur),'finalMarkup':markup(rec),
  'markupParity':markup(src)==markup(cur)==markup(rec),
  'sourceIcuSignature':icu(src),'currentIcuSignature':icu(cur),'finalIcuSignature':icu(rec),
  'icuParity':icu(src)==icu(cur)==icu(rec),
  'protectedLiteralChecks':[{'literal':lit,'inSource':lit in src,'inCurrentTarget':lit in cur,'inFinalTarget':lit in rec} for lit in cell['protectedLiterals']],
  'currentProtectedLiteralFailures':[lit for lit in cell['protectedLiterals'] if lit not in cur],
  'finalProtectedLiteralFailures':[lit for lit in cell['protectedLiterals'] if lit not in rec]}
 assert checks['placeholderParity'] and checks['markupParity'] and checks['icuParity'],(key,checks)
 assert not checks['finalProtectedLiteralFailures'],(key,checks)
 caller=caller_by[cell['sourceId']]
 srcrow=source_by[cell['sourceId']]
 row={**cell,'primaryDisposition':disposition,'recommendedTarget':recommended,
  'recommendedTargetSha256':sha(recommended) if recommended is not None else None,'finalReviewedTarget':final,
  'finalReviewedTargetSha256':sha(final),'decisionRationale':rationale,'reviewConfidence':confidence,
  'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'semanticInterpretation':{
   'provider.option':'Provider selector label or hint; enum/member semantics are pinned below.',
   'server.message':'Application-authored validation message; interpolated values are dynamic data.',
   'ui.loading':'Playful authored loading copy; product-name puns and ebook/audiobook terminology are retained where applicable.'}[srcrow['sourceId'].split('.',2)[0]+'.'+srcrow['sourceId'].split('.',2)[1]],
  'callerContextSha256':caller['callerContextSha256'],'callerReferenceCount':caller['callerReferenceCount'],
  'callerRefs':caller['directCallerReferences'],'sourceRegistryContext':{'path':srcrow['sourceRegistryPath'],'fingerprint':srcrow['sourceRegistryFingerprint'],
   'category':srcrow['registryCategory'],'surface':srcrow['registrySurface'],'parameters':srcrow['registryParameters'],'patterns':srcrow['registryPatterns'],
   'protectedLiterals':srcrow['effectiveProtectedLiterals']},'structuralChecks':checks,
  'localeFormalityNotes':{
   'es':'Catalog-level mixed address exists. General UI commonly uses tú (e.g. Comprueba/Asegúrate); matching unsuffixed folder-permission messages use usted (Asegúrese). This review recommends usted for W1039–W1040 to match those paired server errors.' if loc=='es' and pos in (1039,1040) else ('Spanish informal tú appears in playful loading text (e.g. tu/Encuentra); no second-person form in this cell.' if loc=='es' and pos>=1043 else ('Spanish direct-address instruction uses informal tú, consistent with many neighboring UI strings.' if loc=='es' and pos not in (1039,1040) else None)),
   'de':'German server guidance uses formal Sie; playful loading text may use informal du (e.g. Dein/Spule). No pronoun choice applies to this cell.' if loc=='de' else None,
   'fr':'Formal/polite vous is used in server guidance; no incompatible register issue found.' if loc=='fr' and pos in (1039,1040,1048) else None,
   'pt-BR':'Imperatives use the standard polite você/third-person form (e.g. Verifique, Seja); no incompatible register issue found.' if loc=='pt-BR' else None,
   'ko':'User-facing requests use polite 해요/세요 forms; selection labels and loading-state fragments do not assign an honorific addressee.' if loc=='ko' else None,
   'hi':'User-facing instructions use respectful imperative forms; no honorific conflict identified.' if loc=='hi' and pos in (1039,1040,1049) else None,
   'ar':'Standard singular imperative phrasing is used in error guidance; no register policy is recorded in the repository.' if loc=='ar' and pos in (1039,1040) else None,
   'id':'Anda conveys a polite/direct user address where present.' if loc=='id' and pos in (1039,1040,1049) else None,
   'vi':'Hãy is a polite/neutral instruction marker in user guidance.' if loc=='vi' and pos in (1039,1040,1049) else None,
   'ja':'ください marks polite user guidance; loading-state values are descriptive.' if loc=='ja' and pos in (1039,1040) else None,
   'zh-Hans':'请 marks a polite instruction in user guidance.' if loc=='zh-Hans' and pos in (1039,1040,1049) else None,
   'zh-Hant':'請 marks a polite instruction in user guidance.' if loc=='zh-Hant' and pos in (1039,1040,1049) else None}.get(loc)}
 review.append(row)
 audits.append({'sourceOrdinal':pos,'sourceId':cell['sourceId'],'locale':loc,'primaryDisposition':disposition,
  'sourceTextSha256':cell['sourceTextSha256'],'currentTargetSha256':cell['currentTargetSha256'],
  'recommendedTarget':recommended,'recommendedTargetSha256':sha(recommended) if recommended is not None else None,
  'finalReviewedTargetSha256':sha(final),'rationale':rationale,'confidence':confidence,'nativeSpeakerApproval':False,
  'callerContextSha256':caller['callerContextSha256'],'placeholderParity':checks['placeholderParity'],'markupParity':checks['markupParity'],
  'icuParity':checks['icuParity'],'protectedLiteralFailures':checks['finalProtectedLiteralFailures']})
assert len(review)==len(audits)==600 and len({(x['sourceOrdinal'],x['locale']) for x in review})==600
assert {(x['sourceOrdinal'],x['locale']) for x in review if x['primaryDisposition'] in ('correction','refinement')}==set(C)
assert {(x['sourceOrdinal'],x['locale']) for x in review if x['primaryDisposition']=='hold'}==set(H)

# Internal terminology and protected-literal evidence.
writej('internal-terminology-references.json',{'sourcePath':TERMS,'gitBlob':term_info['gitBlob'],'sha256':term_info['sha256'],
 'terminologyRecords':term_extract,'reviewNotes':['The internal eBook term asks translators to preserve eBook capitalization where the target language permits.','The protected-literal registries independently require exact POST, PUT, Freeleech, VIP, Chaptarr and chaptarr tokens in the relevant selected strings.','No external dictionary/CLDR browsing was performed in this task, which prohibits browser work.']})
writejl('source-slice.jsonl',source_rows); writejl('caller-context.jsonl',caller_rows); writejl('input-cells.jsonl',input_cells)
writejl('provider-option-pipeline-context.jsonl',provider_pipeline); writejl('server-message-pipeline-context.jsonl',server_pipeline); writejl('loading-message-pipeline-context.jsonl',loading_runtime)
writejl('review-cells.jsonl',review); writejl('language-audit.jsonl',audits)
writejl('correction-candidates.jsonl',[x for x in review if x['primaryDisposition']=='correction'])
writejl('refinement-candidates.jsonl',[x for x in review if x['primaryDisposition']=='refinement'])
writejl('holds.jsonl',[x for x in review if x['primaryDisposition']=='hold'])
writejl('protected-literal-integrity.jsonl',[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],
 'sourceTextSha256':x['sourceTextSha256'],'currentTargetSha256':x['currentTargetSha256'],'primaryDisposition':x['primaryDisposition'],
 'recommendedTargetSha256':x['recommendedTargetSha256'],'finalReviewedTargetSha256':x['finalReviewedTargetSha256'],
 'protectedLiterals':x['protectedLiterals'],'checks':x['structuralChecks']} for x in review])
writejl('prior-dispositions-through-W999.jsonl',prior_live); writej('w999-boundary-reattestation.json',{'sourceOrdinal':999,'sourceId':w999_id,'source':source[w999_id],'rows':w999,'all12MatchPreviousFinal':all(x['liveTargetMatchesPreviousFinal'] for x in w999)})
writej('w1050-forward-boundary.json',{'sourceOrdinal':1050,'sourceId':w1050_id,'source':source[w1050_id],'rows':w1050,'dispositionsAssigned':False})
writej('selected-queue-window.json',{**selection,'sourceFileGitBlob':source_info['gitBlob'],'sourceFileSha256':source_info['sha256'],'sourceQueueFileGitBlob':follow_info['gitBlob'],'sourceQueueFileSha256':follow_info['sha256']})

# Explicit locale formality/register audit; a bare label usually has no address form.
formality={
 'ar':{'register':'Modern Standard Arabic; direct imperatives are singular masculine/neutral in form.','reviewedCellsWithDirectAddress':[1039,1040,1049],'nativeSpeakerReviewOutstanding':True},
 'de':{'register':'Formal Sie in permission-error guidance; informal du may be used in playful loading copy.','examples':{'formal':['Stellen Sie sicher'], 'informal':['Dein Bücherregal','Spule deine Hörbücher']},'nativeSpeakerReviewOutstanding':True},
 'es':{'register':'Catalog is mixed: tú occurs in general copy and playful loading messages; usted occurs in some server validations. Exact paired folder-permission messages use Asegúrese.','decision':'Recommend Asegúrese at W1039/W1040 to align the corresponding unsuffixed messages; keep informal tú in conversational loading copy.','nativeSpeakerReviewOutstanding':True},
 'fr':{'register':'Polite vous for server guidance and user-directed loading prompt; no informal address detected in these rows.','nativeSpeakerReviewOutstanding':True},
 'hi':{'register':'Respectful imperative/progress constructions where direct guidance appears; no second-person pronoun policy found in repo.','nativeSpeakerReviewOutstanding':True},
 'id':{'register':'Anda is used for direct address; descriptive labels do not need a pronoun.','nativeSpeakerReviewOutstanding':True},
 'ja':{'register':'Polite ください/ます forms for user-directed guidance; loading status lines are descriptive.','nativeSpeakerReviewOutstanding':True},
 'ko':{'register':'Polite 하세요/세요 forms for user guidance; provider labels and loading states are not honorific address.','nativeSpeakerReviewOutstanding':True},
 'pt-BR':{'register':'Polite você/third-person imperative forms (e.g. Verifique, Seja); possessive sua.','nativeSpeakerReviewOutstanding':True},
 'vi':{'register':'Neutral/polite Hãy for user guidance; descriptive values do not address the reader.','nativeSpeakerReviewOutstanding':True},
 'zh-Hans':{'register':'请 used for user-directed guidance; other values are labels or descriptive copy.','nativeSpeakerReviewOutstanding':True},
 'zh-Hant':{'register':'請 used for user-directed guidance; other values are labels or descriptive copy.','nativeSpeakerReviewOutstanding':True}}
writej('locale-formality-review.json',{'localeOrder':LOCALE_ORDER,'locales':formality,'reviewScope':'All 600 cells checked for formality/register where the source or target uses direct address, an imperative, or a loading instruction.'})

# Pin manifest input files and local state.
pinned={x['path']:x for x in [source_info,follow_info,term_info,tracked(PIPE_SERVER),*reg_info.values(),*catalog_info.values(),*caller_file_info.values()]}
writej('pinned-files.json',{'exactHead':HEAD,'exactTree':TREE,'fileCount':len(pinned),'files':sorted(pinned.values(),key=lambda x:x['path'])})
writej('caller-context-summary.json',{'sourceRows':len(caller_rows),'directCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),
 'uniqueDirectCallerFiles':len({r['file'] for x in caller_rows for r in x['directCallerReferences']}),'callerGaps':gaps,'staleRegistryPins':stale,
 'providerOptionPipelineReferences':len(provider_pipeline),'serverMessagePipelineReferences':len(server_pipeline),'serverMessagePipelineGaps':server_pipeline_gaps,
 'loadingMessagePipelineReferences':len(loading_runtime),'loadingCallerRows':sum(1 for x in caller_rows if x['registryPath']==REGISTRIES['loading'])})
writej('input-manifest.json',{'schemaVersion':1,'repository':REPO,'pullRequest':PR,'url':'https://github.com/snapetech-org/ChaptarrNG/pull/190',
 'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'worktreeState':state(),'scope':{'window':'W1000-W1049','positionsAreZeroBasedQueueIndexes':True,
 'positions':[1000,1049],'sourceCount':50,'localeCount':12,'locales':LOCALE_ORDER,'cells':600},
 'selection':selection,'sourceQueueFile':follow_info,'sourceCatalogFile':source_info,'sourceRegistries':reg_info,'localeCatalogs':catalog_info,
 'callerContextRows':len(caller_rows),'callerReferenceCount':sum(x['callerReferenceCount'] for x in caller_rows),'callerGaps':gaps,'staleRegistryPins':stale,
 'providerOptionPipelineReferences':len(provider_pipeline),'serverMessageDisplayPipelineReferences':len(server_pipeline),'loadingPipelineReferences':len(loading_runtime),
 'priorDispositionRowsThroughW999':len(prior_live),'priorDispositionPositionCoverage':[0,999],'priorPositionOverlapWithSelected':0,
 'w999BoundaryRows':len(w999),'w999BoundaryAll12Match':all(x['liveTargetMatchesPreviousFinal'] for x in w999),
 'w1050BoundaryRows':len(w1050),'w1050BoundaryDispositionsAssigned':False,
 'allSevenPRStartSnapshot':{'path':'snapshots/start-all-pr-heads.json','queryStartedUtc':start['query_started_utc'],'queryCompletedUtc':start['query_completed_utc']},
 'allSevenPRAfterSourceSelectionSnapshot':{'path':'snapshots/after-source-selection-all-pr-heads.json','queryStartedUtc':post['query_started_utc'],'queryCompletedUtc':post['query_completed_utc']},
 'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'browserReviewPerformed':False})

# Build summary and README.
counts=collections.Counter(x['primaryDisposition'] for x in review)
per_locale={loc:dict(collections.Counter(x['primaryDisposition'] for x in review if x['locale']==loc)) for loc in LOCALES}
summary={'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'window':'W1000-W1049','queuePositionsAreZeroBased':True,
 'sourceCount':50,'localeCellCount':600,'locales':LOCALE_ORDER,'dispositionCounts':dict(sorted(counts.items())),
 'perLocaleDispositionCounts':per_locale,'placeholderMismatchCells':sum(not x['structuralChecks']['placeholderParity'] for x in review),
 'markupMismatchCells':sum(not x['structuralChecks']['markupParity'] for x in review),'icuMismatchCells':sum(not x['structuralChecks']['icuParity'] for x in review),
 'currentProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['currentProtectedLiteralFailures']) for x in review),
 'finalProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['finalProtectedLiteralFailures']) for x in review),
 'protectedLiteralCellCount':sum(bool(x['protectedLiterals']) for x in review),'directCallerReferences':sum(x['callerReferenceCount'] for x in caller_rows),
 'directCallerGaps':len(gaps),'staleRegistryPins':len(stale),'priorDispositionRowsThroughW999':len(prior_live),
 'priorLiveTargetsMatchingFinalHash':sum(x['liveTargetMatchesPriorFinalHash'] for x in prior_live),
 'priorLiveTargetsDifferingFromFinalHash':sum(not x['liveTargetMatchesPriorFinalHash'] for x in prior_live),
 'w999BoundaryAll12Match':all(x['liveTargetMatchesPreviousFinal'] for x in w999),'w1050BoundaryDispositionsAssigned':False,
 'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'overallConfidence':'moderate',
 'limitations':'Static machine-assisted review; no native speaker, browser, runtime, or external dictionary approval is claimed.'}
writej('summary.json',summary)

# Final live query to ensure the reviewed target is still the PR head at seal.
prs=[('seerr','SeerrNG',418),('chaptarr','ChaptarrNG',190),('questarr','QuestarrNG',155),('romarr','ROMarrNG',70),('slskr','slskR',204),('slskdn','slskdN',409),('torrent','TorrentNG',243)]
fields='number state isDraft headRefName headRefOid baseRefName baseRefOid updatedAt url headRepository { name owner { login } } headRef { target { oid ... on Commit { tree { oid } } } }'
query='query { '+' '.join(f'{a}: repository(owner: "snapetech-org", name: "{r}") {{ pullRequest(number: {n}) {{ {fields} }} }}' for a,r,n in prs)+' }'
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(['gh','api','graphql','-f',f'query={query}'],capture_output=True,text=True,check=True)
finished=datetime.datetime.now(datetime.timezone.utc).isoformat(); gd=json.loads(r.stdout)
if gd.get('errors'): raise RuntimeError(gd['errors'])
final={'snapshot_kind':'final-seal-reattestation','query_started_utc':started,'query_completed_utc':finished,'query':query,'pull_requests':gd['data']}
writej('snapshots/final-seal-all-pr-heads.json',final)
for a,repo,num in prs:
 p=gd['data'][a]['pullRequest']; p0=post['pull_requests'][a]['pullRequest']
 assert p['headRefOid']==p0['headRefOid'] and p['headRefName']==p0['headRefName'] and p['headRef']['target'].get('tree',{}).get('oid')==p0['headRef']['target'].get('tree',{}).get('oid'),(repo,num,p,p0)
ch=gd['data']['chaptarr']['pullRequest']
assert ch['state']=='OPEN' and ch['isDraft'] and ch['headRefOid']==HEAD and ch['headRefName']==BRANCH and ch['headRef']['target']['tree']['oid']==TREE
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
writej('final-reattestation.json',{'passed':True,'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'worktreeState':state(),
 'allSevenHeadsUnchangedFromAfterSourceSelection':True,'queryStartedUtc':started,'queryCompletedUtc':finished,
 'chaptarrPrState':ch['state'],'chaptarrPrDraft':ch['isDraft'],'chaptarrPrHead':ch['headRefOid'],'chaptarrPrTree':ch['headRef']['target']['tree']['oid']})

readme=f'''# ChaptarrNG PR #190 primary localization review — W1000–W1049

## Exact scope and snapshot

This packet reviews queue positions 1000–1049 from `docs/localization/source-followup-20261101.json`. Positions are zero-based queue offsets, not English catalog key order. The selection contains 50 provider/source labels and 600 locale cells across ar, de, es, fr, hi, id, ja, ko, pt-BR, vi, zh-Hans, and zh-Hant.

ChaptarrNG PR #190 was OPEN and DRAFT on branch `{BRANCH}` at head `{HEAD}`, tree `{TREE}` when this packet was sealed. Seven localization PR heads and trees were queried before the source slice was frozen ({start['query_started_utc']}–{start['query_completed_utc']} UTC) and immediately after source selection ({post['query_started_utc']}–{post['query_completed_utc']} UTC). A final seven-PR reattestation ({started}–{finished} UTC) found no head/tree movement. Full GraphQL responses are under `snapshots/`.

The worktree at `{WORK}` was clean at the exact head. All review artifacts are in task scratch; no repository, PR, workflow, release, or remote state was changed.

## Review result

All 600 current values were reviewed against the English source, pinned enum/validator/loading caller, and the current locale catalog. The packet records {counts['accept-current']} accept-current decisions, {counts['correction']} correction candidates, {counts['refinement']} refinements, and {counts['hold']} holds.

| Disposition | Count |
| --- | ---: |
| Accept current | {counts['accept-current']} |
| Correction candidate | {counts['correction']} |
| Refinement candidate | {counts['refinement']} |
| Hold for native-language review | {counts['hold']} |

Candidate detail is in `correction-candidates.jsonl`, `refinement-candidates.jsonl`, and `holds.jsonl`; `review-cells.jsonl` contains all 600 decisions and exact UTF-8 hashes. Candidate text is a review proposal, not an applied repository change.

Structural checks cover placeholder multiplicity/order-insensitive parity, markup, ICU signatures, and exact registered protected literals. Final reviewed values have {summary['placeholderMismatchCells']} placeholder, {summary['markupMismatchCells']} markup, {summary['icuMismatchCells']} ICU, and {summary['finalProtectedLiteralFailureCells']} protected-literal failures. Registered literals include `POST`, `PUT`, `Freeleech`, `VIP`, `Chaptarr`, and `chaptarr`; every proposed final preserves its exact source-registered literal. For the eBook joke, the internal terminology record calls for preserving `eBook` casing where the language permits, but it is a soft terminology instruction rather than a protected literal.

## Caller, terminology, and formality evidence

`source-slice.jsonl`, `caller-context.jsonl`, `pinned-files.json`, and the three pipeline context files pin all 50 selected sources to their exact caller lines and the provider-option, server-message, and loading-message presentation paths. All direct caller pins resolved; no registry line was stale.

`internal-terminology-references.json` records the exact repository terminology guidance for eBook and audiobook, plus source-registered protected literals. No external dictionary/CLDR browsing was performed because this task prohibited browser work; candidate language-name spellings that would benefit from an external authority remain subject to native-language review.

`locale-formality-review.json` summarizes all 12 locale registers. Spanish is mixed across the existing catalog: general UI often uses informal tú, while corresponding unsuffixed folder-permission errors use usted. The W1039/W1040 refinements align with the paired error messages. German uses formal Sie for error guidance and may use informal du in playful loading copy; French uses polite vous in user-directed guidance; pt-BR uses polite você/third-person imperatives. Other locales use their normal polite/neutral user-instruction forms where direct address appears. Bare enum labels have no addressee.

## Boundary and prior-decision continuity

`prior-dispositions-through-W999.jsonl` preserves all 12,000 prior cell dispositions and final hashes from positions 0–999. It also records current-head live-value hash comparisons. W999's 12 final targets all match the current catalogs (`w999-boundary-reattestation.json`). W1050 is pinned with its exact English source and all 12 current targets as boundary context only; no W1050 disposition is assigned (`w1050-forward-boundary.json`). No prior positions were reopened.

## Native-speaker status and limitations

Native-speaker approval is **not present** and remains outstanding for all 12 locales. This is a static, machine-assisted primary review with overall moderate confidence; several candidates and all holds are explicitly marked moderate/low. There was no browser, runtime, or native-speaker review. The packet does not claim final linguistic certification.

## Packet contents

- `input-manifest.json`, `selected-queue-window.json`, `source-slice.jsonl`: exact queue selection and source pins.
- `input-cells.jsonl`, `pinned-files.json`: exact current translation values, hashes, Git blobs, and catalogs.
- `caller-context.jsonl`, `caller-context-summary.json`, `*-pipeline-context.jsonl`: direct caller and display-path evidence.
- `review-cells.jsonl`, `language-audit.jsonl`: full per-cell primary decisions.
- `correction-candidates.jsonl`, `refinement-candidates.jsonl`, `holds.jsonl`: proposed changes and held cells.
- `protected-literal-integrity.jsonl`, `internal-terminology-references.json`, `locale-formality-review.json`: structural, terminology, and register review.
- `prior-dispositions-through-W999.jsonl`, `w999-boundary-reattestation.json`, `w1050-forward-boundary.json`: continuity and boundaries.
- `snapshots/`, `final-reattestation.json`: exact live PR-head snapshots.
- `manifest.json`, `SHA256SUMS`: sealed inventory and integrity hashes.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Manifest hashes every artifact except itself/SHA256SUMS; sums file covers manifest too.
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'})
content=[{'path':str(p.relative_to(OUT)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in files]
manifest={'schemaVersion':1,'packet':'ChaptarrNG PR #190 primary localization review W1000-W1049','sealedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'exactHead':HEAD,'exactTree':TREE,'branch':BRANCH,'artifactCountExcludingManifestAndSums':len(content),'artifacts':content,
 'summary':summary,'liveHeadSnapshots':['snapshots/start-all-pr-heads.json','snapshots/after-source-selection-all-pr-heads.json','snapshots/final-seal-all-pr-heads.json']}
writej('manifest.json',manifest)
all_files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT)}\n' for p in all_files),encoding='utf-8')
# Verify final hashes and coverage.
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1); assert sha((OUT/n).read_bytes())==h,(n,h)
assert len([x for x in review if x['sourceOrdinal'] in range(1000,1050)])==600
print(json.dumps({'path':str(OUT),'summary':summary,'callerPins':len(caller_rows),'callerReferences':sum(x['callerReferenceCount'] for x in caller_rows),
 'callerGaps':gaps,'stalePins':stale,'w999All12':all(x['liveTargetMatchesPreviousFinal'] for x in w999),
 'priorRows':len(prior_live),'shaCount':len(all_files),'sealedAtUtc':manifest['sealedAtUtc']},ensure_ascii=False,indent=2))
