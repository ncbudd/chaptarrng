from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

PARENT=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0250-0299-primary-20261102')
OUT=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0250-0299-crossreview-by-agent-20261102')
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
REPO_NAME='snapetech-org/chaptarrng'; PR=190
HEAD_EXPECTED='46a6abd437c78fafcec73f93f79944b5f84d3a39'
TREE_EXPECTED='90a59b1c329feeb3fb34bdc5050128c8792b573e'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

# Independently judged outcomes for the primary's 67 candidate rows.
# One French attachment phrase is rewritten for email context; all other primary
# proposals are retained after comparing the source, current target, and caller.
REFINED={
 (288,'fr'):('Joindre les livres au courriel lors de l’importation',
              'The source is an email-notification checkbox and its help describes book attachments on import. The primary phrase “en pièces jointes” repeats the attachment idea; this final wording says directly that the books are attached to the email when an import triggers the notification.')
}
ADDITIONAL={
 (265,'es'):('Enviar los libros importados durante los escaneos de la biblioteca',
             'The caller help says books arriving through library scans are forwarded to the content server. The current Spanish “Enviar importaciones de escaneos” names imports abstractly and does not clearly say that the books are sent; this makes the checkbox action and scan-imported books explicit.')
}
SOURCE_MEANINGS={
 250:'adds an AudioBookShelf URL path prefix and preserves the example URL structure',
 251:'identifies the AudioBookShelf API key used for authentication',
 252:'removes missing items after the corresponding deletion',
 253:'distinguishes AudioBookShelf marking deleted books missing from Chaptarr removing items whose files are gone',
 254:'sends library edits outward from the application to the connected library service',
 255:'sends updated book metadata and cover to the matching AudioBookShelf item after a local edit',
 256:'ignores tags on AudioBookShelf items',
 257:'uses tags stored on AudioBookShelf items to protect them from automatic but not manual pushes',
 258:'authenticates with AudioBookShelf through OIDC',
 259:'describes OIDC/SSO key generation, browser reachability, and the callback allowlist path',
 260:'identifies the Calibre content-server URL and requires its scheme and port',
 261:'explains that data and deletions flow one way from Chaptarr to the content server',
 262:'makes authentication optional unless the content server requires it',
 263:'names the permission to edit and delete matching remote books',
 264:'ties remote book edits/deletions to changes or deletions in Chaptarr',
 265:'names books imported through library scans for forwarding to the content server',
 266:'includes scan-arriving books such as books added through calibre-web',
 267:'sends the updated book record after a Chaptarr change',
 268:'labels the custom-script argument field',
 269:'explains which arguments are passed to the script',
 270:'labels the shared Slack/Discord webhook address field',
 271:'identifies a Discord channel webhook URL',
 272:'describes the post username and the Discord webhook default when blank',
 273:'labels the avatar setting',
 274:'explains the avatar used for this integration’s messages',
 275:'explains the notification host override and machine-name fallback',
 276:'labels the email server field',
 277:'identifies the email server hostname or IP address',
 278:'requires encryption for email transport',
 279:'assigns SSL only to port 465 and StartTLS to every other port',
 280:'labels the sender email address',
 281:'labels one or more recipient addresses',
 282:'explains that recipient addresses are comma-separated',
 283:'labels CC recipient addresses',
 284:'explains that CC recipients are a comma-separated list',
 285:'labels BCC recipient addresses',
 286:'explains that BCC recipients are a comma-separated list',
 287:'labels the email-books attachment checkbox',
 288:'explains that books are attached when an email notification is triggered by an import',
 289:'labels the SSL use checkbox shared by Emby/Jellyfin and Plex',
 290:'labels a reverse-proxy URL base/path prefix such as /jellyfin or /emby',
 291:'removes selected books from Goodreads Bookshelves',
 292:'adds books to Goodreads Bookshelves',
 293:'labels the Goodreads user identifier',
 294:'labels the owned-book condition description',
 295:'labels where the Goodreads book was purchased',
 296:'explains that the purchase location is displayed on Goodreads',
 297:'labels the Gotify server field',
 298:'explains the Gotify server URL, including an optional scheme and port',
 299:'labels the Gotify application token credential'
}
CANDIDATE_RATIONALES={
 254:'This shared checkbox sends local library edits outward to integrations; “send” preserves that direction and avoids implying two-way synchronization.',
 256:'The caller is the AudioBookShelf item-tag selector; the proposed locale text explicitly names the Ignore action and the service tags.',
 259:'This help describes AudioBookShelf OIDC/SSO key generation and the callback URL for Chaptarr; the candidates preserve the menu path and make the application callback relation clear.',
 262:'This help accompanies the Calibre Content Server credentials; the target accurately says credentials are needed only when the server requires authentication.',
 263:'The caller is a permission checkbox for remote edits/deletions; the target names both permitted operations in a concise label.',
 264:'The help ties remote edits/deletions to changes or deletions made in Chaptarr; the proposed wording preserves that direction and the matching-book constraint.',
 270:'This shared label is used for Discord and Slack webhook-address fields; the localized forms retain the webhook URL meaning.',
 276:'This is the email server field label; the Taiwan Traditional Chinese term matches the locale terminology used elsewhere in the same settings.',
 277:'This help identifies the email server host or IP address; the proposals clarify the address relation and localize Hostname where appropriate.',
 278:'This is a checkbox requiring encrypted email transport; the direct verb form expresses the setting action.',
 279:'The help describes a strict transport rule: SSL on port 465, StartTLS on all other ports; the proposals retain both conditions and the numeric port.',
 288:'The caller is the email notification “Attach Books” checkbox, and this help ties attachments to import-triggered notifications; the candidates describe book attachments at import time.',
 290:'Both callers use this label for reverse-proxy URL base fields, with help examples such as /jellyfin or /emby; “URL prefix” is the intended user-facing meaning.',
 292:'This is the Goodreads bookshelf selector action; the candidates translate Bookshelves and preserve the add action.',
 296:'This help belongs to the purchase-location field and explains its public display on Goodreads; the candidates name the location and preserve that display meaning.',
 297:'This is the Gotify server field label; the proposals use natural field-label wording and the Taiwan term for server in Traditional Chinese.',
 298:'This is Gotify URL help; the Hindi candidate removes the duplicated port instruction and retains the optional scheme/port requirement.',
 299:'This is the Gotify app-token credential label; the Hindi spelling is the standard rendering of “app”.'
}

# Rationale for each current value that the primary retained; source and caller
# are attached to every row so these verdicts remain auditable per cell.
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def read_lines(path): return path.read_bytes().splitlines()
def read_jsonl(base,name): return [json.loads(x) for x in read_lines(base/name) if x.strip()]
def write_jsonl(path,rows): path.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
def write_json(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(args): return subprocess.check_output(['git','-C',str(REPO),*args])
def gittext(args): return git(args).decode('utf-8').strip()
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)

# Validate every primary artifact checksum before using the frozen rows.
for manifest in ('INPUT-SHA256SUMS','SHA256SUMS'):
    subprocess.check_call(['sha256sum','-c',manifest],cwd=PARENT,stdout=subprocess.DEVNULL)
pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO_NAME,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],cwd=REPO,text=True))
head=pr['headRefOid']; tree=gittext(['rev-parse',f'{head}^{{tree}}'])
if pr['state']!='OPEN' or pr['isDraft'] is not True or head!=HEAD_EXPECTED or tree!=TREE_EXPECTED:
    raise SystemExit(f'PR state/head/tree changed: {json.dumps(pr)} tree={tree}')
if gittext(['rev-parse','HEAD'])!=HEAD_EXPECTED or gittext(['status','--porcelain']):
    raise SystemExit('review worktree is not clean at the expected head')

source_rows=read_jsonl(PARENT,'source-slice.jsonl')
inputs=read_jsonl(PARENT,'input-cells.jsonl')
primary=read_jsonl(PARENT,'review-cells.jsonl')
candidates=read_jsonl(PARENT,'correction-candidates.jsonl')
callers=read_jsonl(PARENT,'caller-context.jsonl')
protected=read_jsonl(PARENT,'protected-literal-integrity.jsonl')
prior_context=read_jsonl(PARENT,'prior-context-dispositions.jsonl')
source_by={(r['sourceOrdinal'],r['locale']):r for r in inputs}
primary_by={(r['sourceOrdinal'],r['locale']):r for r in primary}
candidate_by={(r['sourceOrdinal'],r['locale']):r for r in candidates}
protected_by={(r['sourceOrdinal'],r['locale']):r for r in protected}
caller_by={r['sourceOrdinal']:r for r in callers}
source_by_ordinal={r['sourceOrdinal']:r for r in source_rows}
raw_input={}
for line in read_lines(PARENT/'input-cells.jsonl'):
    r=json.loads(line); raw_input[(r['sourceOrdinal'],r['locale'])]=line
raw_primary={}
for line in read_lines(PARENT/'review-cells.jsonl'):
    r=json.loads(line); raw_primary[(r['sourceOrdinal'],r['locale'])]=line
assert len(source_rows)==50 and len(inputs)==600 and len(primary)==600 and len(candidates)==67
assert len(callers)==50 and all(len(r['callerRefs'])>=1 for r in callers)
assert len(prior_context)==12 and {r['locale'] for r in prior_context}==set(LOCALES)
PREVIOUS_PRIMARY=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-primary-20261102/review-cells.jsonl')
PREVIOUS_CROSS=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-crossreview-by-agent-20261102/cross-review-cells.jsonl')
prior_primary_rows=[json.loads(x) for x in PREVIOUS_PRIMARY.read_text().splitlines() if x.strip()]
prior_cross_rows=[json.loads(x) for x in PREVIOUS_CROSS.read_text().splitlines() if x.strip()]
prior_primary_by={x['locale']:x for x in prior_primary_rows if x.get('sourceOrdinal')==249}
prior_cross_by={x['locale']:x for x in prior_cross_rows if x.get('sourceOrdinal')==249}
prior_primary_raw={}; prior_cross_raw={}
for line in read_lines(PREVIOUS_PRIMARY):
    row=json.loads(line)
    if row.get('sourceOrdinal')==249: prior_primary_raw[row['locale']]=line
for line in read_lines(PREVIOUS_CROSS):
    row=json.loads(line)
    if row.get('sourceOrdinal')==249: prior_cross_raw[row['locale']]=line
assert len(prior_primary_by)==12 and len(prior_cross_by)==12

# Reattest all source and locale catalogs at the live PR head.
follow_path='docs/localization/source-followup-20261101.json'
follow_raw=git(['show',f'{head}:{follow_path}']); follow=json.loads(follow_raw.decode('utf-8'))
ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
assert [ids.index(r['sourceId']) for r in source_rows]==list(range(250,300))
source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_raw=git(['show',f'{head}:{source_path}']); source_catalog=json.loads(source_raw.decode('utf-8'))
source_file_blob=gittext(['rev-parse',f'{head}:{source_path}'])
source_info={'path':source_path,'blob':source_file_blob,'sha256':sha(source_raw),'bytes':len(source_raw)}
if sha(source_raw)!=source_rows[0]['sourceFileSha256'] or source_file_blob!=source_rows[0]['sourceFileBlob']:
    raise SystemExit('English source catalog blob/hash mismatch')
for s in source_rows:
    if (source_catalog.get(s['sourceId'])!=s['source'] or sha(s['sourceId'].encode())!=s['sourceSha256'] or sha(s['source'].encode())!=s['sourceTextSha256']):
        raise SystemExit(f'source slice mismatch: {s["sourceOrdinal"]} {s["sourceId"]}')
locale_catalogs={}; catalog_pins={}
for r in inputs:
    path=r['targetFile']
    if path not in locale_catalogs:
        raw=git(['show',f'{head}:{path}']); catalog_pins[path]={'blob':gittext(['rev-parse',f'{head}:{path}']),'sha256':sha(raw),'bytes':len(raw)}
        locale_catalogs[path]=json.loads(raw.decode('utf-8'))
for r in inputs:
    val=locale_catalogs[r['targetFile']].get(r['sourceId'])
    if val!=r['target'] or sha(val.encode())!=r['targetSha256'] or catalog_pins[r['targetFile']]['blob']!=r['targetFileBlob']:
        raise SystemExit(f'current cell differs from live PR head: {r["sourceOrdinal"]} {r["locale"]}')

# Reattest exact caller lines, caller file hashes, and source registry metadata.
registry_path='docs/localization/provider-field-sources.json'
registry_raw=git(['show',f'{head}:{registry_path}']); registry=json.loads(registry_raw.decode('utf-8'))
registry_by={r['id']:r for r in registry['records']}
unique_refs={}
for c in callers:
    if c['attestedHead']!=head or c['attestedTree']!=tree or c['callerMismatches']:
        raise SystemExit(f'caller context pin mismatch: {c["sourceOrdinal"]}')
    if c['sourceId'] not in registry_by or c['registrySource']!=registry_by[c['sourceId']]['source']:
        raise SystemExit(f'registry source mismatch: {c["sourceOrdinal"]}')
    for ref in c['callerRefs']:
        unique_refs[(ref['file'],ref['currentLine'],ref['currentLineSha256'])]=ref
for ref in unique_refs.values():
    raw=git(['show',f'{head}:{ref["file"]}']); lines=raw.decode('utf-8').splitlines(); n=ref['currentLine']
    if (gittext(['rev-parse',f'{head}:{ref["file"]}'])!=ref['currentFileBlob'] or sha(raw)!=ref['currentFileSha256'] or
        not 1<=n<=len(lines) or lines[n-1]!=ref['currentLineText'] or sha(lines[n-1].encode())!=ref['currentLineSha256']):
        raise SystemExit(f'caller line mismatch at live head: {ref["file"]}:{n}')

# Independently review each row's current value and any candidate. All primary
# proposals are kept except the one French attachment phrase refinement.
review=[]; checks=[]; findings=[]
for inp in inputs:
    key=(inp['sourceOrdinal'],inp['locale']); ordinal,locale=key
    prr=primary_by[key]; cand=candidate_by.get(key); prot=protected_by[key]
    final=inp['target']; disposition='accepted-current'; confidence='moderate'
    if cand:
        final=cand['recommendedTarget']; disposition='accepted-candidate'
        rationale=CANDIDATE_RATIONALES[ordinal]
        if key in REFINED:
            final,rationale=REFINED[key]; disposition='refined-candidate'; confidence='high'
    elif key in ADDITIONAL:
        final,rationale=ADDITIONAL[key]; disposition='additional-finding'; confidence='moderate'
    else:
        refs=caller_by[ordinal]['callerRefs']
        kinds=', '.join(sorted({r['kind'] for r in refs}))
        files=', '.join(sorted({Path(r['file']).name for r in refs}))
        rationale=(f'The current {locale} text accurately conveys that it {SOURCE_MEANINGS[ordinal]} in its caller context ({kinds} in {files}); '
                   'the source and usage do not reveal a material omission, reversal, or protected-term issue.')
    src=inp['source']; cur=inp['target']
    source_ph=placeholders(src); current_ph=placeholders(cur); final_ph=placeholders(final)
    source_markup=markup(src); current_markup=markup(cur); final_markup=markup(final)
    if source_ph!=current_ph or source_ph!=final_ph: raise SystemExit(f'placeholder mismatch {key}')
    if source_markup!=current_markup or source_markup!=final_markup: raise SystemExit(f'markup mismatch {key}')
    literal_checks=[]; missing_current=[]; missing_final=[]
    for literal in inp['protectedLiterals']:
        src_has=literal in src; cur_has=literal in cur; final_has=literal in final
        literal_checks.append({'literal':literal,'matchMode':'exact','presentInSource':src_has,'presentInCurrentTarget':cur_has,'presentInFinalTarget':final_has})
        if not cur_has: missing_current.append(literal)
        if not final_has: missing_final.append(literal)
    if missing_current or missing_final: raise SystemExit(f'protected literal mismatch {key}: {missing_current} / {missing_final}')
    cctx=caller_by[ordinal]
    refs=[]
    for ref in cctx['callerRefs']:
        refs.append({'file':ref['file'],'fileBlob':ref['currentFileBlob'],'fileSha256':ref['currentFileSha256'],
          'kind':ref['kind'],'line':ref['currentLine'],'lineNumberShift':ref['lineNumberShift'],
          'lineSha256':ref['currentLineSha256'],'lineText':ref['currentLineText'],
          'contextBefore':ref['contextBefore'],'contextAfter':ref['contextAfter']})
    row={
      'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':inp['sourceId'],'locale':locale,
      'source':src,'sourceSha256':prr['sourceSha256'],'sourceTextSha256':inp['sourceTextSha256'],
      'sourceFile':prr['sourceFile'],'sourceFileBlob':prr['sourceFileBlob'],'sourceFileSha256':prr['sourceFileSha256'],
      'targetFile':inp['targetFile'],'targetFileBlob':catalog_pins[inp['targetFile']]['blob'],'targetFileSha256':catalog_pins[inp['targetFile']]['sha256'],
      'currentTarget':cur,'currentTargetSha256':inp['targetSha256'],
      'primaryRecommendedTarget':prr['recommendedTarget'],'primaryRecommendedTargetSha256':prr['recommendedTargetSha256'],
      'primaryDisposition':prr['disposition'],'primaryRationale':prr['rationale'],
      'crossReviewDisposition':disposition,'crossReviewRationale':rationale,'confidence':confidence,
      'finalTarget':final,'finalTargetSha256':sha(final.encode('utf-8')),
      'sourcePlaceholders':source_ph,'currentPlaceholders':current_ph,'finalPlaceholders':final_ph,
      'placeholderCheck':'pass','sourceMarkup':source_markup,'currentMarkup':current_markup,'finalMarkup':final_markup,'markupCheck':'pass',
      'protectedLiteralCheck':'pass','protectedLiteralChecks':literal_checks,'protectedLiteralsMissingFromFinal':[],
      'callerRefs':refs,'callerContextSha256':inp['callerContextSha256'],
      'inputRecordSha256':sha(raw_input[key]),'primaryReviewRecordSha256':sha(raw_primary[key]),
      'nativeSpeakerApproval':False
    }
    review.append(row)
    checks.append({'sourceOrdinal':ordinal,'sourceId':inp['sourceId'],'locale':locale,
      'sourceTextSha256':inp['sourceTextSha256'],'currentTargetSha256':inp['targetSha256'],'finalTargetSha256':row['finalTargetSha256'],
      'sourcePlaceholders':source_ph,'currentPlaceholders':current_ph,'finalPlaceholders':final_ph,'placeholderCheck':'pass',
      'sourceMarkup':source_markup,'currentMarkup':current_markup,'finalMarkup':final_markup,'markupCheck':'pass',
      'protectedLiteralChecks':literal_checks,'protectedLiteralCheck':'pass'})
    if disposition in ('refined-candidate','additional-finding'):
        findings.append({'sourceOrdinal':ordinal,'sourceId':inp['sourceId'],'locale':locale,
          'findingType':disposition,'primaryTarget':prr['recommendedTarget'],'primaryTargetSha256':prr['recommendedTargetSha256'],
          'currentTarget':cur,'currentTargetSha256':inp['targetSha256'],'crossReviewedTarget':final,
          'crossReviewedTargetSha256':row['finalTargetSha256'],'reason':rationale})
assert len(review)==600 and len(checks)==600
cross_counts=collections.Counter(r['crossReviewDisposition'] for r in review)
assert cross_counts=={'accepted-current':532,'accepted-candidate':66,'refined-candidate':1,'additional-finding':1},cross_counts
assert len(findings)==2

# Reattest the adjacent W249 source, every locale value, its original decisions,
# and its exact current caller at this live head. It is context only.
prior_sid=prior_context[0]['sourceId']; assert all(r['sourceId']==prior_sid and r['contextSourceOrdinal']==249 for r in prior_context)
assert ids[249]==prior_sid
prior_source=source_catalog[prior_sid]
prior_registry=registry_by[prior_sid]
prior_caller_refs=[]
for call in prior_registry['callsites']:
    raw=git(['show',f'{head}:{call["file"]}']); lines=raw.decode().splitlines()
    matches=[i for i,line in enumerate(lines,1) if line.strip()==call['sourceLine'].strip()]
    if len(matches)!=1: raise SystemExit(f'W249 caller source-line mismatch: {call["file"]}')
    n=matches[0]; line=lines[n-1]
    prior_caller_refs.append({'file':call['file'],'fileBlob':gittext(['rev-parse',f'{head}:{call["file"]}']),'fileSha256':sha(raw),
      'kind':call['kind'],'line':n,'registryLine':call['line'],'lineSha256':sha(line.encode()),'lineText':line,
      'contextBefore':lines[max(0,n-3):n-1],'contextAfter':lines[n:min(len(lines),n+2)]})
context_reviews=[]
for p in prior_context:
    loc=p['locale']; file={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}[loc]
    path=f'src/NzbDrone.Core/Localization/Core/{file}'
    target=locale_catalogs.get(path)
    if target is None:
        raw=git(['show',f'{head}:{path}']); catalog_pins[path]={'blob':gittext(['rev-parse',f'{head}:{path}']),'sha256':sha(raw),'bytes':len(raw)}; target=json.loads(raw.decode())
        locale_catalogs[path]=target
    val=target[prior_sid]
    if val!=p['currentLiveTarget'] or sha(val.encode())!=p['currentLiveTargetSha256']:
        raise SystemExit(f'W249 locale drift: {loc}')
    pp=prior_primary_by[loc]; pc=prior_cross_by[loc]
    if (p['primaryDisposition']!='accept-current' or p['crossReviewDisposition']!='accepted' or p['crossReviewFinalTarget']!=val or
        pp.get('disposition')!='accept-current' or pp.get('exactHead')!=p['priorPacketHead'] or
        pc.get('crossReviewDisposition')!='accepted' or pc.get('exactHead')!=p['priorPacketHead'] or pc.get('finalTarget')!=val):
        raise SystemExit(f'W249 prior disposition mismatch: {loc}')
    source_ph=placeholders(prior_source); target_ph=placeholders(val)
    source_markup=markup(prior_source); target_markup=markup(val)
    if source_ph!=target_ph or source_markup!=target_markup: raise SystemExit(f'W249 placeholder/markup mismatch: {loc}')
    literal_checks=[]
    for literal in prior_registry.get('protectedLiterals',[]):
        literal_checks.append({'literal':literal,'matchMode':'exact','presentInSource':literal in prior_source,
          'presentInCurrentTarget':literal in val,'presentInIndependentFinalTarget':literal in val})
    if any(not x['presentInCurrentTarget'] or not x['presentInIndependentFinalTarget'] for x in literal_checks):
        raise SystemExit(f'W249 protected-literal mismatch: {loc}')
    context_reviews.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':249,'sourceId':prior_sid,'locale':loc,
      'source':prior_source,'sourceTextSha256':sha(prior_source.encode()),'sourceIdSha256':sha(prior_sid.encode()),
      'sourceFile':source_path,'sourceFileBlob':source_file_blob,'sourceFileSha256':sha(source_raw),
      'targetFile':path,'targetFileBlob':catalog_pins[path]['blob'],'targetFileSha256':catalog_pins[path]['sha256'],
      'currentTarget':val,'currentTargetSha256':sha(val.encode()),'priorPacketHead':p['priorPacketHead'],
      'primaryDisposition':p['primaryDisposition'],'primaryRecommendedTarget':p['primaryRecommendedTarget'],
      'priorPrimaryRecordSha256':sha(prior_primary_raw[loc]),'priorCrossReviewDisposition':p['crossReviewDisposition'],
      'priorCrossReviewFinalTarget':p['crossReviewFinalTarget'],'priorCrossReviewFinalTargetSha256':sha(p['crossReviewFinalTarget'].encode()),
      'priorCrossReviewRecordSha256':sha(prior_cross_raw[loc]),'independentContextDisposition':'accepted-current',
      'independentContextFinalTarget':val,'independentContextFinalTargetSha256':sha(val.encode()),
      'rationale':'The checkbox help accurately says to connect AudioBookShelf over HTTPS rather than HTTP; that protocol instruction fits the adjacent AudioBookShelf settings and preserves the service/protocol names.',
      'sourcePlaceholders':source_ph,'currentPlaceholders':target_ph,'finalPlaceholders':target_ph,'placeholderCheck':'pass',
      'sourceMarkup':source_markup,'currentMarkup':target_markup,'finalMarkup':target_markup,'markupCheck':'pass',
      'protectedLiteralChecks':literal_checks,'protectedLiteralCheck':'pass','callerRefs':prior_caller_refs,
      'callerContextSha256':sha(canon(prior_caller_refs)),'contextOnly':True,'nativeSpeakerApproval':False})

# Final live-head/content reattestation after review construction.
final_pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO_NAME,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],cwd=REPO,text=True))
final_head=gittext(['rev-parse','HEAD']); final_tree=gittext(['rev-parse','HEAD^{tree}'])
if final_pr['headRefOid']!=head or final_head!=head or final_tree!=tree or gittext(['status','--porcelain']):
    raise SystemExit('live PR/worktree changed during cross-review')
# Recheck every caller reference and every frozen source/target row.
for r in review:
    inp=source_by[(r['sourceOrdinal'],r['locale'])]
    if (source_catalog[r['sourceId']]!=r['source'] or locale_catalogs[r['targetFile']][r['sourceId']]!=r['currentTarget'] or
        sha(locale_catalogs[r['targetFile']][r['sourceId']].encode())!=r['currentTargetSha256']):
        raise SystemExit(f'final cell reattestation mismatch: {r["sourceOrdinal"]}/{r["locale"]}')
for ref in unique_refs.values():
    raw=git(['show',f'{head}:{ref["file"]}']); lines=raw.decode().splitlines(); n=ref['currentLine']
    if sha(raw)!=ref['currentFileSha256'] or not 1<=n<=len(lines) or lines[n-1]!=ref['currentLineText']:
        raise SystemExit(f'final caller reattestation mismatch: {ref["file"]}:{n}')

write_jsonl(OUT/'cross-review-cells.jsonl',review)
write_jsonl(OUT/'protected-literal-placeholder-checks.jsonl',checks)
write_jsonl(OUT/'additional-findings.jsonl',findings)
write_jsonl(OUT/'w249-context-crossreview.jsonl',context_reviews)

primary_counts=collections.Counter(r['disposition'] for r in primary)
per_locale={loc:dict(collections.Counter(r['crossReviewDisposition'] for r in review if r['locale']==loc)) for loc in LOCALES}
proposal_outcomes=collections.Counter(r['crossReviewDisposition'] for r in review if r['primaryDisposition'].startswith('propose-'))
summary={'schemaVersion':1,'repository':REPO_NAME,'pullRequest':PR,'exactHead':head,'exactTree':tree,
 'scope':{'positions':[250,299],'sourceIds':50,'locales':LOCALES,'cells':600},
 'parentPacket':str(PARENT),'parentInputCellsSha256':sha((PARENT/'input-cells.jsonl').read_bytes()),
 'parentPrimaryReviewSha256':sha((PARENT/'review-cells.jsonl').read_bytes()),
 'parentCandidateSha256':sha((PARENT/'correction-candidates.jsonl').read_bytes()),
 'primaryDispositionCounts':dict(primary_counts),'crossReviewDispositionCounts':dict(cross_counts),
 'crossReviewCountsByLocale':per_locale,
 'proposalOutcomes':{'primaryProposals':sum(primary_counts[k] for k in ('propose-correction','propose-refinement')),
   'acceptedAsProposed':proposal_outcomes['accepted-candidate'],'refined':proposal_outcomes['refined-candidate'],
   'rejected':proposal_outcomes['rejected'],'additionalCurrentIssues':sum(r['crossReviewDisposition']=='additional-finding' for r in review),'held':proposal_outcomes['hold']},
 'findings':[{'sourceOrdinal':r['sourceOrdinal'],'sourceId':r['sourceId'],'locale':r['locale'],'type':r['findingType'],'finalTargetSha256':r['crossReviewedTargetSha256']} for r in findings],
 'currentCellsReattested':600,'callerSourceIdsReattested':50,'callerRefsReattested':sum(len(c['callerRefs']) for c in callers),
 'uniqueCallerLinesReattested':len(unique_refs),'uniqueCallerFiles':len({r['file'] for r in unique_refs.values()}),
 'uniqueCatalogs':len(catalog_pins),'priorW249ContextCells':len(context_reviews),'priorW249CallerRefs':len(prior_caller_refs),'priorW249ProtectedLiteralChecks':sum(len(r['protectedLiteralChecks']) for r in context_reviews),
 'placeholderMismatches':0,'markupMismatches':0,'protectedLiteralMismatches':0,
 'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,
 'testsBuildsScansCiWorkflowsReleasesTagsMerges':False,'blockers':[]}
write_json(OUT/'summary.json',summary)
reattest={'repository':REPO_NAME,'pullRequest':PR,'livePullRequest':final_pr,'head':head,'tree':tree,
 'worktree':str(REPO),'worktreeClean':True,'sourceWindow':[250,299],'sourceIds':50,'locales':LOCALES,'cells':600,
 'primaryPacketInputSumsVerified':True,'primaryPacketSumsVerified':True,
 'primaryInputSumsSha256':sha((PARENT/'INPUT-SHA256SUMS').read_bytes()),'primarySumsSha256':sha((PARENT/'SHA256SUMS').read_bytes()),
 'sourceSliceSha256':sha((PARENT/'source-slice.jsonl').read_bytes()),'inputCellsSha256':sha((PARENT/'input-cells.jsonl').read_bytes()),
 'primaryReviewSha256':sha((PARENT/'review-cells.jsonl').read_bytes()),'candidateRowsSha256':sha((PARENT/'correction-candidates.jsonl').read_bytes()),
 'callerContextSha256':sha((PARENT/'caller-context.jsonl').read_bytes()),'sourceCatalog':source_info,
 'followupFile':{'path':follow_path,'blob':gittext(['rev-parse',f'{head}:{follow_path}']),'sha256':sha(follow_raw),'sourceIdCount':len(ids),'sourceIdListSha256':sha(canon(ids))},
 'registry':{'path':registry_path,'blob':gittext(['rev-parse',f'{head}:{registry_path}']),'sha256':sha(registry_raw),'records':len(registry['records'])},
 'targetCatalogs':catalog_pins,'sourceValuesReattested':50,'currentCellsReattested':600,'cellMismatches':0,
 'callerRefsReattested':sum(len(c['callerRefs']) for c in callers),'uniqueCallerLinesReattested':len(unique_refs),'callerMismatches':0,
 'w249Context':{'sourceId':prior_sid,'source':prior_source,'cellsReattested':len(context_reviews),'callerRefsReattested':len(prior_caller_refs),'protectedLiteralChecks':sum(len(r['protectedLiteralChecks']) for r in context_reviews),'priorPrimaryPacketSha256':sha(PREVIOUS_PRIMARY.read_bytes()),'priorCrossReviewPacketSha256':sha(PREVIOUS_CROSS.read_bytes()),'mismatches':0},
 'placeholdersRechecked':600,'placeholderMismatches':0,'markupRechecked':600,'markupMismatches':0,
 'protectedLiteralChecks':sum(len(r['protectedLiteralChecks']) for r in review),'protectedLiteralMismatches':0,'w249ProtectedLiteralMismatches':0,
 'status':'pass','recheckedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()}
write_json(OUT/'reattestation.json',reattest)
provenance={'reviewerRole':'independent cross-reviewer','reviewType':'independent source-context-aware adjudication of every frozen target and every primary recommendation',
 'exactHead':head,'exactTree':tree,'scope':summary['scope'],
 'inputs':['English source catalog','12 direct locale catalogs','provider-field source/caller registry','600 primary input/review rows','all 67 primary correction/refinement proposals','W249 prior primary and cross-review dispositions'],
 'nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False}
write_json(OUT/'reviewer-provenance.json',provenance)
manifest={'schemaVersion':1,'repository':REPO_NAME,'pullRequest':PR,'head':head,'tree':tree,'livePullRequest':final_pr,
 'parentPacket':str(PARENT),'scope':summary['scope'],'primaryPacket':{
   'inputCellsSha256':summary['parentInputCellsSha256'],'reviewCellsSha256':summary['parentPrimaryReviewSha256'],
   'candidateCount':len(candidates),'candidateSha256':summary['parentCandidateSha256']},
 'crossReview':{'path':'cross-review-cells.jsonl','rows':len(review),'sha256':sha((OUT/'cross-review-cells.jsonl').read_bytes()),'dispositions':dict(cross_counts)},
 'integrityChecks':{'path':'protected-literal-placeholder-checks.jsonl','rows':len(checks),'sha256':sha((OUT/'protected-literal-placeholder-checks.jsonl').read_bytes()),
   'placeholderMismatches':0,'markupMismatches':0,'protectedLiteralMismatches':0},
 'additionalFindings':{'path':'additional-findings.jsonl','rows':len(findings),'sha256':sha((OUT/'additional-findings.jsonl').read_bytes())},
 'w249ContextCrossReview':{'path':'w249-context-crossreview.jsonl','rows':len(context_reviews),'sha256':sha((OUT/'w249-context-crossreview.jsonl').read_bytes())},
 'summarySha256':sha((OUT/'summary.json').read_bytes()),'reattestationSha256':sha((OUT/'reattestation.json').read_bytes()),
 'reviewerProvenanceSha256':sha((OUT/'reviewer-provenance.json').read_bytes()),
 'nativeSpeakerApproval':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowsTouched':False}
write_json(OUT/'manifest.json',manifest)
readme=f'''# ChaptarrNG PR #190 W250–299 independent cross-review

- Reattested live PR state: OPEN/DRAFT at `{head}`, tree `{tree}`; the audit worktree is clean.
- Frozen scope: positions 250–299 across 12 direct locales, 50 source IDs and 600 current target cells.
- Cross-review verdicts: {dict(cross_counts)}. All {summary['proposalOutcomes']['primaryProposals']} primary recommendations were considered: {summary['proposalOutcomes']['acceptedAsProposed']} accepted as proposed, {summary['proposalOutcomes']['refined']} refined, {summary['proposalOutcomes']['rejected']} rejected. One additional current Spanish issue was found at source position 265.
- Every cell has exact current/final target hashes, source hashes, caller-context references, and an independent rationale in `cross-review-cells.jsonl`. `additional-findings.jsonl` records the French W288 refinement and the additional Spanish W265 finding.
- W249 context review includes all 12 locales, the prior accepted primary/cross-review dispositions, and live caller/source reattestation in `w249-context-crossreview.jsonl`.
- Placeholder, markup, and protected-literal checks passed across the full 600-cell scope. Catalog and caller hashes plus final live reattestation are recorded in `reattestation.json` and `manifest.json`.
- This is model-based cross-review; native-speaker approval is not claimed. No repository/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were made.
- The output directory is task scratch; `SHA256SUMS` covers every packet file other than itself.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
# Final reread of PR and packet inputs before writing the final checksum manifest.
last_pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO_NAME,'--json','state,isDraft,headRefOid'],cwd=REPO,text=True))
if last_pr['headRefOid']!=head or gittext(['rev-parse','HEAD'])!=head or gittext(['rev-parse','HEAD^{tree}'])!=tree:
    raise SystemExit('PR/worktree changed before packet seal')
for name in ['cross-review-cells.jsonl','protected-literal-placeholder-checks.jsonl','additional-findings.jsonl','w249-context-crossreview.jsonl']:
    if not (OUT/name).exists(): raise SystemExit(f'missing packet file {name}')
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files),encoding='utf-8')
print(json.dumps({'head':head,'tree':tree,'crossReviewCounts':dict(cross_counts),'proposalOutcomes':summary['proposalOutcomes'],
 'findings':findings,'cells':len(review),'callerRefs':reattest['callerRefsReattested'],'uniqueCallerLines':len(unique_refs),
 'w249ContextCells':len(context_reviews),'output':str(OUT)},ensure_ascii=False,indent=2))
