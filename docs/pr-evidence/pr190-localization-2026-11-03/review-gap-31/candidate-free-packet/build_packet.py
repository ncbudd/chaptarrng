#!/usr/bin/env python3
import collections, hashlib, json, pathlib, re, subprocess

REPO=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261103/chaptarrng-pr190-ar-rtl-fix-20261103')
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-review-gap-packet-20261103')
HEAD='580538d38f92e0ec005366ff6bea3f2634400c2e'
TREE='b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1'
BASE='03274100af783fdffaca4dd8436e163dc6b18795'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES=[('ar','ar'),('de','de'),('es','es'),('fr','fr'),('hi','hi'),('id','id'),('ja','ja'),('ko','ko'),('pt-BR','pt_BR'),('vi','vi'),('zh-Hans','zh_CN'),('zh-Hant','zh_TW')]
CATDIR='src/NzbDrone.Core/Localization/Core'
QUEUE_PATH='docs/localization/source-followup-20261101.json'
CORRECTION_PATH='docs/pr-evidence/pr190-localization-2026-11-02/window-0650-0699/application/source-corrections.json'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(s):return sha_bytes(s.encode('utf-8'))
def fsha(p):return sha_bytes(pathlib.Path(p).read_bytes())
def blob(p):return subprocess.check_output(['git','hash-object',str(p)],cwd=REPO,text=True).strip()
def jload(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def dump(p,obj):pathlib.Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def jsonl(p,rows):
 with open(p,'w',encoding='utf-8') as f:
  for row in rows:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
def locale_norm(x):return {'zh-cn':'zh-Hans','zh-tw':'zh-Hant','zh-hans':'zh-Hans','zh-hant':'zh-Hant','pt-br':'pt-BR'}.get(str(x).replace('_','-').lower(),str(x))
def run(args):return subprocess.check_output(args,cwd=REPO,text=True).strip()

# Exact local pin gate; no PR API request is made.
head=run(['git','rev-parse','HEAD']); tree=run(['git','rev-parse','HEAD^{tree}']); status=run(['git','status','--porcelain=v1'])
if head!=HEAD or tree!=TREE or status:raise SystemExit(f'worktree pin/cleanliness mismatch: {head} {tree} {status!r}')
remote=run(['git','ls-remote','origin',f'refs/heads/{BRANCH}']).split()[0]
if remote!=HEAD:raise SystemExit(f'remote branch differs: {remote}')
queue=jload(REPO/QUEUE_PATH); ids=queue['currentMissingIds']
source_path=REPO/f'{CATDIR}/en.json'; english=jload(source_path)
queue_ids_sha=sha(json.dumps(ids,ensure_ascii=False,separators=(',',':')))

# Focus scope: all 12 locales for the two corrected-source positions, plus seven changed existing cells.
source_positions=[(654,ids[654],'source-pin-recheck'),(695,ids[695],'source-pin-recheck')]
changed_cells=[
 ('hi','MqttGatewayPublishHomeAssistantDiscovery'),
 ('hi','notification.heading.renamed'),
 ('id','notification.field.links'),
 ('ja','notification.sensor.missingBooks'),
 ('ko','notification.sensor.health'),
 ('zh-Hans','notification.heading.renamed'),
 ('zh-Hant','notification.heading.renamed'),
]
reason_by_cell={(locale,sid):'changed-existing-target-without-exact-review-hash' for locale,sid in changed_cells}
source_ord={sid:pos for pos,sid,_ in source_positions}
selected=set()
for pos,sid,reason in source_positions:
 for locale,_ in LOCALES:selected.add((sid,locale))
for locale,sid in changed_cells:selected.add((sid,locale))
source_ids=list(dict.fromkeys([sid for _,sid,_ in source_positions]+[sid for _,sid in changed_cells]))

# Catalog and source pins.
catalogs={};catalog_pins=[]
for locale,filetag in LOCALES:
 p=REPO/f'{CATDIR}/{filetag}.json'; data=jload(p);catalogs[locale]=data
 catalog_pins.append({'locale':locale,'catalogPath':f'{CATDIR}/{filetag}.json','keyCount':len(data),'catalogSha256':fsha(p),'catalogGitBlob':blob(p)})
source_pin={'path':f'{CATDIR}/en.json','sha256':fsha(source_path),'gitBlob':blob(source_path),'keyCount':len(english)}

# Corrected-source packet pins for the two stale-source ranks.
correction_file=REPO/CORRECTION_PATH;corrections=jload(correction_file)
corrections_by_id={x['sourceId']:x for x in corrections['corrections']}
prior_by_id={x['sourceId']:x for x in corrections['callers']}

# Source snapshots are source text only; no candidate translations.
source_rows=[]
for sid in source_ids:
 text=english[sid]
 correction=corrections_by_id.get(sid)
 prior=prior_by_id.get(sid)
 source_rows.append({'sourceId':sid,'sourceOrdinal':source_ord.get(sid),'sourceText':text,'sourceTextSha256':sha(text),'sourceFile':f'{CATDIR}/en.json','sourceFileSha256':source_pin['sha256'],'sourceFileGitBlob':source_pin['gitBlob'],'sourceCorrectionEvidence':({'path':CORRECTION_PATH,'sha256':fsha(correction_file),'gitBlob':blob(correction_file),'priorSourceTextSha256':prior.get('oldSourceTextSha256') if prior else None,'correctedSourceTextSha256':correction.get('sourceTextSha256'),'correctionMatchesLiveSourceHash':correction.get('sourceTextSha256')==sha(text)} if correction else None)})

# Build source/caller snapshots from registered caller records, corrected-source evidence, and direct UI field use.
registry_paths=['docs/localization/server-message-sources.json','docs/localization/outbound-message-sources.json','docs/localization/provider-field-sources.json','docs/localization/provider-option-sources.json','docs/localization/followup-ui-sources.json','docs/localization/loading-message-sources.json']
registry_data={p:jload(REPO/p) for p in registry_paths}
records_by_id=collections.defaultdict(list)
for path,data in registry_data.items():
 for rec in data.get('records',[]):
  sid=rec.get('id') or rec.get('sourceId')
  if sid:records_by_id[sid].append((path,rec))

def line_snapshot(filepath,needle,preferred_line=None,context=2):
 p=REPO/filepath
 if not p.exists():return []
 lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
 indices=[]
 if preferred_line and 0<preferred_line<=len(lines):indices.append(preferred_line-1)
 for i,line in enumerate(lines):
  if needle and needle in line and i not in indices:indices.append(i)
 out=[]
 for i in indices:
  lo=max(0,i-context);hi=min(len(lines),i+context+1)
  out.append({'path':filepath,'line':i+1,'lineSha256':sha(lines[i]),'lineText':lines[i],'contextStartLine':lo+1,'contextLines':lines[lo:hi],'fileSha256':fsha(p),'fileGitBlob':blob(p)})
 return out

caller_rows=[]
for sid in source_ids:
 refs=[]
 for regpath,rec in records_by_id.get(sid,[]):
  for call in rec.get('callsites',[]):
   filepath=call.get('file') or call.get('path')
   if not filepath:continue
   preferred=call.get('line')
   matches=line_snapshot(filepath,sid,preferred)
   # Some old direct callers are pinned by source text rather than a literal ID in the code.
   if not matches and call.get('sourceLine'):
    matches=line_snapshot(filepath,call['sourceLine'].strip(),preferred)
   refs.append({'registryPath':regpath,'registryFileSha256':fsha(REPO/regpath),'registryFileGitBlob':blob(REPO/regpath),'registeredLine':preferred,'registeredSourceLineSha256':call.get('sourceLineSha256'),'currentSnapshots':matches})
 # Current exact source correction callsites for the corrected positions.
 if sid in prior_by_id:
  correction=prior_by_id[sid]
  for occ in correction.get('postEditCallerOccurrences',[]):
   refs.append({'registryPath':CORRECTION_PATH,'registryFileSha256':fsha(correction_file),'registryFileGitBlob':blob(correction_file),'registeredLine':occ.get('line'),'registeredSourceLineSha256':sha(occ.get('lineText','')),'currentSnapshots':line_snapshot(correction['callerFile'],sid,occ.get('line')),'correctionPinsCurrentSource':correction.get('newSourceTextSha256')==sha(english[sid])})
 # Mqtt gateway field label is an exact user-facing field binding, even though this historic label has no provider-field registry entry.
 if sid=='MqttGatewayPublishHomeAssistantDiscovery':
  filepath='src/NzbDrone.Core/Notifications/MqttGateway/MqttGatewaySettings.cs'
  refs.append({'registryPath':None,'registeredLine':94,'registeredSourceLineSha256':None,'currentSnapshots':line_snapshot(filepath,sid,94),'bindingKind':'FieldDefinition(Label=sourceId)'})
 caller_rows.append({'sourceId':sid,'sourceOrdinal':source_ord.get(sid),'callerReferences':refs})

# Current target snapshots for every locale for all seven IDs; only 31 rows are selected for exact review.
all_locale_rows=[]; selected_rows=[]
base_target_hashes={}
for locale,filetag in LOCALES:
 base_path=f'{CATDIR}/{filetag}.json'
 try:base_catalog=json.loads(subprocess.check_output(['git','show',f'{BASE}:{base_path}'],cwd=REPO))
 except subprocess.CalledProcessError:base_catalog={}
 for sid in source_ids:
  target=catalogs[locale][sid]
  is_selected=(sid,locale) in selected
  reason='source-pin-recheck' if sid in [x[1] for x in source_positions] else reason_by_cell.get((locale,sid),'cross-locale-context-only')
  row={'sourceId':sid,'sourceOrdinal':source_ord.get(sid),'locale':locale,'selectedForReview':is_selected,'selectionReason':reason,'sourceText':english[sid],'sourceTextSha256':sha(english[sid]),'currentTarget':target,'currentTargetSha256':sha(target),'catalogPath':base_path,'catalogSha256':fsha(REPO/base_path),'catalogGitBlob':blob(REPO/base_path),'baseTargetSha256':sha(base_catalog[sid]) if sid in base_catalog and isinstance(base_catalog[sid],str) else None}
  all_locale_rows.append(row)
  if is_selected:selected_rows.append({'sourceId':sid,'sourceOrdinal':source_ord.get(sid),'locale':locale,'selectionReason':reason,'sourceTextSha256':row['sourceTextSha256'],'currentTargetSha256':row['currentTargetSha256'],'catalogPath':base_path,'catalogSha256':row['catalogSha256'],'catalogGitBlob':row['catalogGitBlob'],'baseTargetSha256':row['baseTargetSha256']})

jsonl(OUT/'source-cells.jsonl',source_rows)
jsonl(OUT/'locale-context-cells.jsonl',all_locale_rows)
jsonl(OUT/'caller-snapshots.jsonl',caller_rows)
jsonl(OUT/'selected-cells.jsonl',selected_rows)

# Exact per-cell manifest, including catalog/source/target hashes and review reason.
manifest={'schemaVersion':1,'packetType':'candidate-free semantic review input','repository':'snapetech-org/ChaptarrNG','pullRequest':190,'branch':BRANCH,'baseHead':BASE,'head':head,'tree':tree,'remoteBranchHead':remote,'worktreeClean':True,'containsProposedTranslations':False,'directLocaleCount':12,'selectedCellCount':len(selected_rows),'contextCellCount':len(all_locale_rows)-len(selected_rows),'sourceRecordCount':len(source_rows),'sourceIds':source_ids,'selectedCells':selected_rows,'selectionCounts':{'correctedSourceCells':24,'changedExistingCellsWithoutExactReviewEvidence':7},'sourceQueue':{'path':QUEUE_PATH,'sha256':fsha(REPO/QUEUE_PATH),'gitBlob':blob(REPO/QUEUE_PATH),'currentMissingIdsCount':len(ids),'compactIdListSha256':queue_ids_sha},'sourceCatalog':source_pin,'correctedSourceEvidence':{'path':CORRECTION_PATH,'sha256':fsha(correction_file),'gitBlob':blob(correction_file)},'catalogPins':catalog_pins,'callerRegistryPins':[{'path':p,'sha256':fsha(REPO/p),'gitBlob':blob(REPO/p)} for p in registry_paths]}
dump(OUT/'manifest.json',manifest)
dump(OUT/'attestation.json',{'head':head,'tree':tree,'baseHead':BASE,'branch':BRANCH,'remoteBranchHead':remote,'worktreeClean':True,'PRAPIQueried':False,'repoStatus':status,'meaning':'Local exact-head checkout and existing remote branch agree; no PR query or mutation was made.'})

# Read-only caller check for the retained 61 active holds. Search current production paths only;
# keep mappings and tests visible as non-caller evidence but do not count them as direct callers.
hold_groups=[
 (447,'server.message.m00dbcd234174','no exact production caller; nearest dynamic AuthorController validation is not this stable message ID'),
 (498,'server.message.m23e7ac60ea9c','no exact direct caller or pinned UI role; server-message map/test references alone do not establish a production caller'),
 (561,'server.message.m453c42aa8de5','direct Nzbget validation result; source/caller boundary mismatch remains'),
 (884,'server.message.mf00d6bc38ae8','direct qBittorrent validation rules; English source/caller literal mismatch remains'),
 (963,'provider.option.oe4d40d318e99','direct MyAnonaMouse language-option label; Indonesian label choice held for native review'),
 (1000,'provider.option.o7285d46b982d','direct MyAnonaMouse enum-option label; Vietnamese label held for native review'),
 (1047,'ui.loading.newEbookSmell','direct loading-message entry rendered by UI; locale wording held for native review'),
 (1049,'ui.loading.rewindAudiobooks','direct loading-message entry rendered by UI; locale wording held for native review'),
 (1054,'ui.loading.dodgeBooks','direct loading-message entry rendered by UI; protected-name pun held for native creative localization'),
]
def find_code_refs(sid):
 out=[]
 for root in [REPO/'src',REPO/'frontend/src']:
  for p in root.rglob('*'):
   if not p.is_file() or p.suffix not in ('.cs','.ts','.tsx','.js','.jsx','.json','.cjs'):continue
   rel=str(p.relative_to(REPO))
   if rel.startswith(f'{CATDIR}/') or 'test' in p.name.lower() or 'tests' in rel.lower():continue
   try:lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
   except:continue
   for i,line in enumerate(lines):
    if sid in line:
     kind='direct-production-reference'
     if rel=='frontend/src/Utilities/Localization/server-messages.json':kind='translation-mapping-only'
     if rel=='frontend/src/Components/Loading/loading-messages.json':kind='runtime-loading-message-entry'
     out.append({'path':rel,'line':i+1,'lineText':line,'lineSha256':sha(line),'fileSha256':fsha(p),'fileGitBlob':blob(p),'kind':kind})
 return out
hold_status=[]
for ordinal,sid,reason in hold_groups:
 refs=find_code_refs(sid)
 direct=[r for r in refs if r['kind'] in ('direct-production-reference','runtime-loading-message-entry')]
 hold_status.append({'sourceOrdinal':ordinal,'sourceId':sid,'activeHoldCellCount':{'447':12,'498':12,'561':12,'884':1,'963':1,'1000':1,'1047':8,'1049':2,'1054':12}[str(ordinal)],'exactUserFacingCallerFound':bool(direct),'directCallerRefs':direct,'otherReferences':[r for r in refs if r not in direct],'holdRemains':True,'holdReasonSummary':reason,'holdEvidencePath':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-full-coverage-audit-20261103/active-holds.jsonl'})
dump(OUT/'active-hold-caller-status.json',{'scope':'caller existence only; no hold release or new translation recommendation','activeHoldCellCount':sum(x['activeHoldCellCount'] for x in hold_status),'holdSourceCount':len(hold_status),'groups':hold_status,'summary':{'groupsWithExactUserFacingCaller':sum(bool(x['exactUserFacingCallerFound']) for x in hold_status),'groupsWithoutExactUserFacingCaller':[x['sourceOrdinal'] for x in hold_status if not x['exactUserFacingCallerFound']]}})

readme=f'''# ChaptarrNG PR #190 review-gap input packet

Candidate-free exact-head input at `{head}` / tree `{tree}`. Local branch `{BRANCH}` and its remote branch resolve to the same head. This packet includes current source and catalog targets only; it contains no proposed translations and makes no PR query or change.

## Selected cells

- Source positions 654 (`{ids[654]}`) and 695 (`{ids[695]}`): all 12 locales each, 24 selected cells, pinned to corrected English source hashes and current production caller snapshots. Their earlier locale review source pins are stale; the source-correction record is included.
- Seven changed existing cells without exact target-hash review evidence: `hi:MqttGatewayPublishHomeAssistantDiscovery`, `hi:notification.heading.renamed`, `id:notification.field.links`, `ja:notification.sensor.missingBooks`, `ko:notification.sensor.health`, `zh-Hans:notification.heading.renamed`, and `zh-Hant:notification.heading.renamed`.
- All 12 locale values are included as context for each of the seven source IDs, for 84 locale snapshots total. The remaining context-only rows are clearly marked in `locale-context-cells.jsonl`; the selection manifest lists exactly 31 cells.

## Files

- `manifest.json`: selected cell IDs/locales, exact source/current-target/catalog hashes, and pin set.
- `selected-cells.jsonl`: hash-only list of 31 review selections.
- `source-cells.jsonl`: current English source text and hashes, plus corrected-source ancestry pins.
- `locale-context-cells.jsonl`: current target text/hash and catalog file pins for 84 rows; no candidates.
- `caller-snapshots.jsonl`: current production caller lines and neighboring context with registry/file hashes.
- `active-hold-caller-status.json`: caller-existence check for the 61 held cells; no hold was released.
- `attestation.json`: local/remote exact-head pins and clean worktree state.
- `build_packet.py`: reproducible packet builder.

'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Checksums cover all packet outputs other than the checksum file itself.
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
with open(OUT/'SHA256SUMS','w',encoding='utf-8') as f:
 for p in files:f.write(f'{fsha(p)}  {p.name}\n')
print(json.dumps({'output':str(OUT),'head':head,'tree':tree,'remote':remote,'selectedCells':len(selected_rows),'allLocaleContextRows':len(all_locale_rows),'sourceRows':len(source_rows),'callerRows':len(caller_rows),'holdGroupsWithDirectCaller':sum(bool(x['exactUserFacingCallerFound']) for x in hold_status),'holdGroupsWithoutDirectCaller':[x['sourceOrdinal'] for x in hold_status if not x['exactUserFacingCallerFound']],'files':[p.name for p in files]+['SHA256SUMS']},ensure_ascii=False))
