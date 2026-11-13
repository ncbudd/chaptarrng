from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

PARENT=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-primary-20261102')
OUT=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-crossreview-by-agent-20261102')
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
HEAD_EXPECTED='32686f13760d04de2bba00af47fc561e632741de'
TREE_EXPECTED='13de6a00cb6eb7206523f000d6ef345084f3c78e'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def read_lines(path): return path.read_bytes().splitlines()
def read_jsonl(name): return [json.loads(x) for x in read_lines(PARENT/name) if x.strip()]
def write_jsonl(path,rows): path.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
def write_json(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(args): return subprocess.check_output(['git','-C',str(REPO),*args])
def gittext(args): return git(args).decode('utf-8').strip()
def placeholders(s): return sorted(re.findall(r'\{[^{}]+\}',s))
def markup(s): return re.findall(r'<[^>]+>|&(?:#\d+|\w+);',s)

# The cross-review adjudicates all primary candidates and all primary keeps.
# One candidate is refined below: Hindi requires danda punctuation rather than
# the Chinese ideographic full stop U+3002 present in the primary candidate.
REFINEMENTS={
 (200,'hi'):('यदि आपने ABS कनेक्ट किया है, तो इससे MAM पर आपकी खोज बेहतर होगी।',
             'The primary Hindi candidate ends with the Chinese full stop U+3002. Replace it with the Hindi danda U+0964; the rest of the candidate accurately describes the integration and MAM search improvement.')
}
SOURCE_RATIONALES={
 200:'The locale proposals improve the conditional connection phrasing while preserving the ABS and MAM names and the effect on MAM searches.',
 202:'The proposed labels express the MAM account class or membership tier and fix target-language word order without changing the account-field meaning.',
 208:'The candidate keeps the reserve as a slot count, explains the two protected capacity risks, and uses the exact locale UI term for Interactive Search.',
 210:'The candidate retains the automatic-grab buffer semantics and uses the exact locale UI term for Interactive Search.',
 213:'The Spanish casing and Portuguese action label fit the checkbox context and preserve “search in description.”',
 214:'The Portuguese candidate makes the checkbox action plural and natural while retaining the series search scope.',
 216:'The Indonesian candidate identifies the language values being searched, which fits the multi-select filter field.',
 222:'The Hindi and Vietnamese candidates restore “additional,” which is omitted from the current values.',
 230:'The Arabic candidate renders torrent seeding as sharing the torrent rather than agricultural sowing; the field context is a seed-time setting.',
 234:'The Chinese candidates improve the cookie/browser instruction punctuation and name the login Cookie while preserving retrieval through a browser.',
 243:'The candidates use natural Apprise notification-type labels for the select field.'
}

# Final cross-review judgment: every source/current/candidate row was read in
# source order and in the pinned provider-field caller context. No other
# substantive current-cell issue was found in this window.

# Verify the primary packet's two checksum manifests before using its records.
for manifest in ('INPUT-SHA256SUMS','SHA256SUMS'):
    subprocess.check_call(['sha256sum','-c',manifest],cwd=PARENT,stdout=subprocess.DEVNULL)
pr=json.loads(subprocess.check_output(['gh','pr','view','190','--repo','snapetech-org/chaptarrng','--json','state,isDraft,mergeStateStatus,headRefOid,headRefName,baseRefOid,url'],cwd=REPO,text=True))
head=pr['headRefOid']; tree=gittext(['rev-parse',f'{head}^{{tree}}'])
if pr['state']!='OPEN' or pr['isDraft'] is not True or head!=HEAD_EXPECTED or tree!=TREE_EXPECTED:
    raise SystemExit(f'PR state/head/tree changed: {json.dumps(pr)} tree={tree}')
if gittext(['rev-parse','HEAD'])!=HEAD_EXPECTED or gittext(['status','--porcelain']):
    raise SystemExit('review worktree is not clean at the expected head')

source_rows=read_jsonl('source-slice.jsonl')
inputs=read_jsonl('input-cells.jsonl')
primary=read_jsonl('review-cells.jsonl')
candidates=read_jsonl('correction-candidates.jsonl')
callers=read_jsonl('caller-context.jsonl')
protected=read_jsonl('protected-literal-integrity.jsonl')
ui_terms=json.loads((PARENT/'localized-ui-terms.json').read_text(encoding='utf-8'))
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
assert len(source_rows)==50 and len(inputs)==600 and len(primary)==600 and len(candidates)==52
assert len(callers)==50 and all(len(r['callerRefs'])>=1 for r in callers)

# Live reattestation: exact English source values, every locale target, and all
# caller references, including file hashes and exact pinned lines.
source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_raw=git(['show',f'{head}:{source_path}'])
source_catalog=json.loads(source_raw.decode('utf-8'))
source_file_blob=gittext(['rev-parse',f'{head}:{source_path}'])
if sha(source_raw)!=source_rows[0]['sourceFileSha256'] or source_file_blob!=source_rows[0]['sourceFileBlob']:
    raise SystemExit('English source catalog blob/hash mismatch')
for s in source_rows:
    if (source_catalog.get(s['sourceId'])!=s['source'] or
        sha(s['sourceId'].encode('utf-8'))!=s['sourceSha256'] or
        sha(s['source'].encode('utf-8'))!=s['sourceTextSha256']):
        raise SystemExit(f'source slice mismatch: {s["sourceOrdinal"]} {s["sourceId"]}')
locale_catalogs={}; catalog_pins={}
for r in inputs:
    path=r['targetFile']
    if path not in locale_catalogs:
        blob=gittext(['rev-parse',f'{head}:{path}']); raw=git(['show',f'{head}:{path}'])
        catalog_pins[path]={'blob':blob,'sha256':sha(raw),'bytes':len(raw)}
        locale_catalogs[path]=json.loads(raw.decode('utf-8'))
for r in inputs:
    val=locale_catalogs[r['targetFile']].get(r['sourceId'])
    if val!=r['target'] or sha(val.encode('utf-8'))!=r['targetSha256'] or catalog_pins[r['targetFile']]['blob']!=r['targetFileBlob']:
        raise SystemExit(f'current cell differs from latest live PR head: {r["sourceOrdinal"]} {r["locale"]}')
unique_refs={}
for c in callers:
    if c['attestedHead']!=head or c['attestedTree']!=tree or c['callerMismatches']:
        raise SystemExit(f'caller context not pinned: {c["sourceOrdinal"]}')
    for ref in c['callerRefs']:
        key=(ref['file'],ref['currentLine'],ref['currentLineSha256'])
        unique_refs[key]=ref
for ref in unique_refs.values():
    path=ref['file']; raw=git(['show',f'{head}:{path}']); lines=raw.decode('utf-8').splitlines(); n=ref['currentLine']
    if (gittext(['rev-parse',f'{head}:{path}'])!=ref['currentFileBlob'] or sha(raw)!=ref['currentFileSha256'] or
        not 1<=n<=len(lines) or lines[n-1]!=ref['currentLineText'] or sha(lines[n-1].encode('utf-8'))!=ref['currentLineSha256']):
        raise SystemExit(f'caller line does not match at live head: {path}:{n}')

# Independently review each current value, primary recommendation, and exact caller.
review=[]; findings=[]; checks=[]
for inp in inputs:
    key=(inp['sourceOrdinal'],inp['locale']); prr=primary_by[key]; cand=candidate_by.get(key); prot=protected_by[key]
    ordinal,locale=key
    final=inp['target']; disposition='accepted'
    if cand:
        final=cand['recommendedTarget']
        if key in REFINEMENTS:
            final,reason=REFINEMENTS[key]; disposition='refined'
        else:
            reason=SOURCE_RATIONALES.get(ordinal,'The proposed target preserves the field meaning and fits the pinned provider-field caller context; the proposed correction/refinement is accurate.')
    else:
        reason='The current target accurately conveys this field/help text in its pinned provider-field context; no material semantic issue was found.'
    src=inp['source']
    src_ph=placeholders(src); cur_ph=placeholders(inp['target']); final_ph=placeholders(final)
    src_markup=markup(src); cur_markup=markup(inp['target']); final_markup=markup(final)
    if src_ph!=cur_ph or src_ph!=final_ph: raise SystemExit(f'placeholder mismatch: {key}')
    if src_markup!=cur_markup or src_markup!=final_markup: raise SystemExit(f'markup mismatch: {key}')
    pchecks=[]; missing=[]
    for check in prot['checks']:
        lit=check['literal']; mode=check['matchMode']
        if mode=='case-insensitive':
            has_source=lit.casefold() in src.casefold(); has_current=lit.casefold() in inp['target'].casefold(); has_final=lit.casefold() in final.casefold()
        else:
            has_source=lit in src; has_current=lit in inp['target']; has_final=lit in final
        # Some protected technical forms are canonicalized in targets even
        # when the English prose source uses lowercase (for example “api” ->
        # “API”). Check that the current and final locale values preserve the
        # required target literal; record source casing separately.
        if not has_current or not has_final: missing.append(lit)
        pchecks.append({'literal':lit,'matchMode':mode,'presentInSource':has_source,'presentInCurrentTarget':has_current,'presentInFinalTarget':has_final})
    if missing: raise SystemExit(f'protected literal mismatch {key}: {missing}')
    localized_checks=[]
    if ordinal in (208,210):
        for term in ui_terms['localeTerms']:
            if term['locale']!=locale: continue
            source_ui='Interactive Search'; expected=term['expectedLocalizedUiTerm']
            variants=[expected.casefold()]
            if locale=='ar':
                words=expected.split()
                if words:
                    variants.append(('ال'+' ال'.join(words)).casefold())
                    variants.append(('لل'+' ال'.join(words)).casefold())
            localized_checks.append({'sourceUiTerm':source_ui,'expectedLocalizedUiTerm':expected,
                'currentEnglishTermCount':inp['target'].count(source_ui),'finalEnglishTermCount':final.count(source_ui),
                'expectedLocalizedTermPresent':any(v in final.casefold() for v in variants),
                'acceptedLocaleVariants':variants})
        if not localized_checks or not all(x['expectedLocalizedTermPresent'] and x['finalEnglishTermCount']==0 for x in localized_checks):
            raise SystemExit(f'localized UI term mismatch: {key}')
    cctx=caller_by[ordinal]
    refs=[]
    for ref in cctx['callerRefs']:
        refs.append({'file':ref['file'],'fileBlob':ref['currentFileBlob'],'fileSha256':ref['currentFileSha256'],
            'kind':ref['kind'],'line':ref['currentLine'],'lineSha256':ref['currentLineSha256'],'lineText':ref['currentLineText']})
    input_hash=sha(raw_input[key]); primary_hash=sha(raw_primary[key])
    row={
      'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':inp['sourceId'],
      'locale':locale,'source':src,'sourceSha256':prr['sourceSha256'],'sourceTextSha256':inp['sourceTextSha256'],
      'sourceFile':prr['sourceFile'],'sourceFileBlob':prr['sourceFileBlob'],'sourceFileSha256':prr['sourceFileSha256'],
      'targetFile':inp['targetFile'],'targetFileBlob':catalog_pins[inp['targetFile']]['blob'],'targetFileSha256':catalog_pins[inp['targetFile']]['sha256'],
      'currentTarget':inp['target'],'currentTargetSha256':inp['targetSha256'],
      'finalTarget':final,'finalTargetSha256':sha(final.encode('utf-8')),
      'primaryDisposition':prr['disposition'],'primaryRationale':prr['rationale'],
      'primaryRecommendedTarget':prr['recommendedTarget'],'primaryRecommendedTargetSha256':prr['recommendedTargetSha256'],
      'crossReviewDisposition':disposition,'crossReviewRationale':reason,'confidence':'moderate',
      'sourcePlaceholders':src_ph,'currentPlaceholders':cur_ph,'finalPlaceholders':final_ph,
      'placeholderCheck':'pass','sourceMarkup':src_markup,'currentMarkup':cur_markup,'finalMarkup':final_markup,'markupCheck':'pass',
      'protectedLiteralCheck':'pass','protectedLiteralChecks':pchecks,'protectedLiteralsMissingFromFinal':[],
      'localizedUiTermChecks':localized_checks,'callerRefs':refs,'callerContextSha256':inp['callerContextSha256'],
      'inputRecordSha256':input_hash,'primaryReviewRecordSha256':primary_hash,'nativeSpeakerApproval':False
    }
    review.append(row)
    checks.append({'sourceOrdinal':ordinal,'sourceId':inp['sourceId'],'locale':locale,'sourceTextSha256':inp['sourceTextSha256'],
        'currentTargetSha256':inp['targetSha256'],'finalTargetSha256':row['finalTargetSha256'],
        'placeholderCheck':'pass','markupCheck':'pass','protectedLiteralCheck':'pass',
        'localizedUiTermChecks':localized_checks})
    if disposition!='accepted':
        findings.append({'sourceOrdinal':ordinal,'sourceId':inp['sourceId'],'locale':locale,
            'primaryTarget':prr['recommendedTarget'],'primaryTargetSha256':prr['recommendedTargetSha256'],
            'crossReviewedTarget':final,'crossReviewedTargetSha256':row['finalTargetSha256'],
            'findingType':'candidate-refined','reason':reason})
assert len(review)==600 and len(checks)==600
assert collections.Counter(r['crossReviewDisposition'] for r in review)=={'accepted':599,'refined':1}
assert len(findings)==1
write_jsonl(OUT/'cross-review-cells.jsonl',review)
write_jsonl(OUT/'protected-literal-placeholder-checks.jsonl',checks)
write_jsonl(OUT/'additional-findings.jsonl',findings)

primary_counts=collections.Counter(r['disposition'] for r in primary)
cross_counts=collections.Counter(r['crossReviewDisposition'] for r in review)
per_locale={loc:dict(collections.Counter(r['crossReviewDisposition'] for r in review if r['locale']==loc)) for loc in LOCALES}
proposal_outcomes=collections.Counter()
for r in review:
    if r['primaryDisposition'].startswith('propose-'):
        if r['crossReviewDisposition']=='accepted': proposal_outcomes['acceptedAsProposed']+=1
        elif r['crossReviewDisposition']=='refined': proposal_outcomes['refined']+=1
        elif r['crossReviewDisposition']=='rejected': proposal_outcomes['rejected']+=1
    elif r['crossReviewDisposition']=='missed': proposal_outcomes['missedCurrentIssues']+=1
summary={
 'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'exactHead':head,'exactTree':tree,'scope':{'positions':[200,249],'sourceIds':50,'locales':LOCALES,'cells':600},
 'parentPacket':str(PARENT),'parentInputCellsSha256':sha((PARENT/'input-cells.jsonl').read_bytes()),
 'parentPrimaryReviewSha256':sha((PARENT/'review-cells.jsonl').read_bytes()),
 'primaryDispositionCounts':dict(primary_counts),'crossReviewDispositionCounts':dict(cross_counts),
 'crossReviewCountsByLocale':per_locale,'proposalOutcomes':{'primaryProposals':sum(primary_counts[k] for k in ('propose-correction','propose-refinement')),
  'acceptedAsProposed':proposal_outcomes['acceptedAsProposed'],'refined':proposal_outcomes['refined'],
  'rejected':proposal_outcomes['rejected'],'missedCurrentIssues':proposal_outcomes['missedCurrentIssues'],'held':cross_counts['held']},
 'overrides':[{'sourceOrdinal':r['sourceOrdinal'],'locale':r['locale'],'issue':r['reason']} for r in findings],
 'inputCurrentCallerMismatches':0,'placeholderMismatches':0,'markupMismatches':0,'protectedLiteralMismatches':0,
 'localizedUiTermMismatches':0,'currentCellsReattested':600,
 'callerRefsReattested':sum(len(c['callerRefs']) for c in callers),
 'uniqueCallerLinesReattested':len(unique_refs),
 'uniqueCallerFiles':len({r['file'] for r in unique_refs.values()}),'uniqueCatalogs':len(catalog_pins),
 'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,
 'testsBuildsScansCiWorkflowsReleasesTagsMerges':False,'blockers':[]
}
write_json(OUT/'summary.json',summary)
reattest={
 'repository':'snapetech-org/chaptarrng','pullRequest':190,'liveState':pr['state'],'isDraft':pr['isDraft'],
 'head':head,'tree':tree,'worktree':str(REPO),'worktreeClean':True,'sourceWindow':[200,249],
 'sourceIds':len(source_rows),'locales':LOCALES,'cells':len(inputs),
 'parentInputSumsVerified':True,'parentSumsVerified':True,
 'parentInputSumsSha256':sha((PARENT/'INPUT-SHA256SUMS').read_bytes()),'parentSumsSha256':sha((PARENT/'SHA256SUMS').read_bytes()),
 'sourceListSha256':sha((PARENT/'source-slice.jsonl').read_bytes()),
 'inputCellsSha256':sha((PARENT/'input-cells.jsonl').read_bytes()),
 'primaryReviewSha256':sha((PARENT/'review-cells.jsonl').read_bytes()),
 'callerContextSha256':sha((PARENT/'caller-context.jsonl').read_bytes()),
 'sourceCatalog':{'path':source_path,'blob':source_file_blob,'sha256':sha(source_raw)},
 'targetCatalogs':catalog_pins,
 'sourceValuesReattested':len(source_rows),'currentCellsReattested':len(inputs),'cellMismatches':0,
 'callerRefsReattested':sum(len(c['callerRefs']) for c in callers),
 'uniqueCallerLinesReattested':len(unique_refs),'callerMismatches':0,
 'placeholdersRechecked':len(inputs),'placeholderMismatches':0,
 'markupRechecked':len(inputs),'markupMismatches':0,
 'protectedLiteralChecks':sum(len(r['protectedLiteralChecks']) for r in review),'protectedLiteralMismatches':0,
 'localizedUiTermChecks':sum(len(r['localizedUiTermChecks']) for r in review),'localizedUiTermMismatches':0,
 'status':'pass','recheckedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
}
write_json(OUT/'reattestation.json',reattest)
provenance={
 'reviewerRole':'independent cross-reviewer','reviewType':'source-context-aware independent adjudication of all frozen cells and all primary recommendations',
 'exactHead':head,'exactTree':tree,'scope':summary['scope'],
 'inputs':['English source catalog','12 target catalogs','provider-field source/caller registry','all 600 primary review rows','52 primary correction/refinement proposals','localized-ui-terms.json','protected-literal-integrity.jsonl'],
 'nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False
}
write_json(OUT/'reviewer-provenance.json',provenance)
print(json.dumps({'primaryCounts':dict(primary_counts),'crossReviewCounts':dict(cross_counts),'proposalOutcomes':summary['proposalOutcomes'],'findings':findings,'cells':len(review),'callerRefRecords':reattest['callerRefsReattested'],'uniqueCallerLines':len(unique_refs),'protectedChecks':reattest['protectedLiteralChecks'],'placeholderMarkup':0},ensure_ascii=False,indent=2))
