#!/usr/bin/env python3
"""Capture exact pre-apply evidence for ChaptarrNG W250-W299; never read PR body."""
import collections, hashlib, json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

TASK=Path('/home/keith/Documents/code/task-scratch')
OUT=TASK/'chaptarrng-pr190-w250-299-apply-20261104'
CROSS=TASK/'chaptarrng-pr190-w250-299-cross-20261104'
INPUT=TASK/'chaptarrng-pr190-w250-299-core-20261104/candidate-free/input'
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w250-299-apply')
HEAD='2a9995a2bf63f06814bd8780736305f16bd6b33a'
TREE='f6ae6530b73bf581c1fbc5a8c13eacd7342e9172'
BRANCH='codex/chaptarrng-localization-complete-20261031'
CELL='AutomaticUpdatesDisabledDocker::id'
ROOT_TARGET='Pemutakhiran otomatis tidak didukung secara langsung saat menggunakan mekanisme pemutakhiran Docker. Anda perlu memperbarui gambar kontainer di luar {appName} atau menggunakan skrip.'

def sha(data): return hashlib.sha256(data).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def row_sha(r): return sha(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def run(argv): return subprocess.check_output(argv,text=True).strip()
def writej(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

start=datetime.now(timezone.utc).isoformat(timespec='seconds')
pr_view=json.loads(run(['gh','pr','view','190','--repo','snapetech-org/ChaptarrNG','--json','state,isDraft,headRefOid,baseRefOid,headRefName,baseRefName,url']))
pr_api=json.loads(run(['gh','api','repos/snapetech-org/ChaptarrNG/pulls/190','--jq','{state:.state,draft:.draft,headRefName:.head.ref,headSha:.head.sha,baseRefName:.base.ref,baseSha:.base.sha,url:.html_url}']))
remote=run(['git','ls-remote','https://github.com/snapetech-org/chaptarrng.git',f'refs/heads/{BRANCH}','refs/pull/190/head','refs/heads/main'])
refs={line.split('\t')[1]:line.split('\t')[0] for line in remote.splitlines() if line.strip()}
main=refs['refs/heads/main']
compare=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/compare/17bde320915af42de73b8646ad56f8ba2ccebf4e...{main}','--jq','{status:.status,aheadBy:.ahead_by,behindBy:.behind_by,totalCommits:.total_commits,changedFiles:[.files[].filename]}']))
local_head=run(['git','-C',str(REPO),'rev-parse','HEAD'])
local_tree=run(['git','-C',str(REPO),'show','-s','--format=%T',HEAD])
local_status=run(['git','-C',str(REPO),'status','--porcelain=v1'])
end=datetime.now(timezone.utc).isoformat(timespec='seconds')

# Compare all exact caller paths to the live-main diff. Changes to backend model/API references are recorded,
# while literal runtime translate callsites are checked separately for changes that would alter UI context.
caller_rows=readjl(INPUT/'caller-context.jsonl')
changed=set(compare['changedFiles'])
all_intersections={}
literal_intersections={}
for c in caller_rows:
    callrefs=c.get('callerRefs',[])
    all_hit=sorted({x.get('path') for x in callrefs if x.get('path') in changed})
    lit_hit=sorted({x.get('path') for x in callrefs if x.get('isRuntimeReference') and x.get('referenceKind')=='literal-translate-call' and x.get('path') in changed})
    if all_hit: all_intersections[c['sourceKey']]=all_hit
    if lit_hit: literal_intersections[c['sourceKey']]=lit_hit

need_files=[x for x in compare['changedFiles'] if x.startswith('src/NzbDrone.Core/Localization/Core/') and x.endswith('.json')]
need_files += [x for x in compare['changedFiles'] if x.startswith('frontend/')]
assert pr_view['state']=='OPEN' and pr_view['isDraft'] is True
assert pr_view['headRefOid']==pr_api['headSha']==refs[f'refs/heads/{BRANCH}']==refs['refs/pull/190/head']==HEAD
assert pr_api['baseSha']==pr_view['baseRefOid']
assert pr_view['headRefName']==pr_api['headRefName']==BRANCH
assert local_head==HEAD and local_tree==TREE and not local_status
assert not need_files, f'localization catalog/source or frontend caller drift detected: {need_files}'
assert not literal_intersections, f'literal runtime translation caller drift detected: {literal_intersections}'

att={
 'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'verificationWindowUTC':[start,end],
 'filteredPRFieldsOnly':True,'fullPullRequestBodyRetrieved':False,
 'pr':{'state':pr_view['state'],'draft':pr_view['isDraft'],'headRefName':pr_view['headRefName'],'headSha':pr_view['headRefOid'],'baseRefName':pr_view['baseRefName'],'baseSha':pr_view['baseRefOid'],'url':pr_view['url']},
 'apiFilteredFields':pr_api,
 'remoteRefs':refs,
 'sourceWorktree':{'path':str(REPO),'head':local_head,'tree':local_tree,'clean':True,'branch':run(['git','-C',str(REPO),'branch','--show-current'])}
}
drift={'apiBase':pr_api['baseSha'],'currentMain':main,'compareStatus':compare['status'],'aheadBy':compare['aheadBy'],'behindBy':compare['behindBy'],'totalCommits':compare['totalCommits'],'changedFiles':compare['changedFiles'],'coreLocalizationSourceOrCatalogChanges':False,'frontendCallerFilesChanged':False,'literalRuntimeTranslateCallsiteFilesChanged':literal_intersections,'callerPathIntersectionsBySourceKey':all_intersections,'assessment':'Live main is ahead of the pinned PR base. The compare includes backend/API files referenced by Book/BookCount/BookFileCount caller inventory, but no Core localization source/catalog files or frontend files; no literal runtime translate callsite changed. The reviewed UI label context and translation source remain pinned to the requested PR head.'}
writej('pre-apply-live-attestation.json',att)
writej('base-drift-comparison.json',drift)

cross_rows=readjl(CROSS/'cross-review-cells.jsonl')
changes=readjl(CROSS/'selected-changes.jsonl')
row=next(x for x in cross_rows if x['cellId']==CELL)
manifest_hash=sha((CROSS/'manifest.json').read_bytes())
sums_hash=sha((CROSS/'SHA256SUMS.txt').read_bytes())
root_adj={
 'recordType':'supplemental-root-adjudication','reviewWindow':'W250-W299-Core','cellId':CELL,
 'adjudicatedAtUTC':end,'adjudicator':'root-reviewer',
 'exactHead':HEAD,'exactTree':TREE,
 'crossPacketPath':str(CROSS),'crossPacketManifestSha256':manifest_hash,'crossPacketSHA256SUMSFileSha256':sums_hash,
 'sourceText':row['sourceText'],'sourceTextSha256':row['sourceTextSha256'],
 'currentTarget':row['currentTarget'],'currentTargetSha256':row['currentTargetSha256'],
 'crossSelectedTarget':row['recommendedTarget'],'crossSelectedTargetSha256':row['recommendedTargetSha256'],
 'crossReviewRowSha256':row_sha(row),
 'rootDisposition':'replace-cross-selected-target-before-apply',
 'rootReason':'The cross-selected Indonesian wording retained only the second source sentence and dropped the first clause: automatic updates are not directly supported through the Docker update mechanism.',
 'correctedTarget':ROOT_TARGET,'correctedTargetSha256':sha_text(ROOT_TARGET),
 'correctedTargetRationale':'Preserves both source clauses, keeps the {appName} placeholder exact, and corrects the earlier cross-review omission.',
 'sealedCrossPacketModified':False
}
writej('root-adjudication.json',root_adj)

cells=readjl(INPUT/'candidate-free-cells.jsonl')
fileguards={}
for r in cells:
 f=r['targetFile']
 g=fileguards.setdefault(f,{'sha256':r['targetFileSha256'],'gitBlob':r['targetFileGitBlob'],'cells':0})
 assert (g['sha256'],g['gitBlob'])==(r['targetFileSha256'],r['targetFileGitBlob'])
 g['cells']+=1
assert all(x['cells']==50 for x in fileguards.values()) and len(fileguards)==12

plan_changes=[]
for x in changes:
 target=ROOT_TARGET if x['cellId']==CELL else x['recommendedTarget']
 plan_changes.append({
  'cellId':x['cellId'],'sourceOrdinal':x['sourceOrdinal'],'sourceKey':x['sourceKey'],'locale':x['locale'],
  'targetFile':next(r['targetFile'] for r in cells if r['sourceKey']==x['sourceKey'] and r['locale']==x['locale']),
  'targetFileSha256':next(r['targetFileSha256'] for r in cells if r['sourceKey']==x['sourceKey'] and r['locale']==x['locale']),
  'targetFileGitBlob':next(r['targetFileGitBlob'] for r in cells if r['sourceKey']==x['sourceKey'] and r['locale']==x['locale']),
  'currentTarget':x['currentTarget'],'currentTargetSha256':x['currentTargetSha256'],
  'recommendedTarget':target,'recommendedTargetSha256':sha_text(target),
  'crossRecommendedTarget':x['recommendedTarget'],'crossRecommendedTargetSha256':x['recommendedTargetSha256'],
  'crossReviewRowSha256':row_sha(row) if x['cellId']==CELL else next(row_sha(z) for z in cross_rows if z['cellId']==x['cellId']),
  'selectedFrom':'root-corrected-cross-review' if x['cellId']==CELL else x['selectedFrom']
 })

plan={
 'repository':'snapetech-org/chaptarrng','pullRequest':190,'headRef':BRANCH,'baseRef':'main',
 'exactHead':HEAD,'exactTree':TREE,'apiBase':pr_api['baseSha'],'currentMain':main,
 'crossReviewManifestSha256':manifest_hash,'crossReviewSHA256SUMSFileSha256':sums_hash,
 'rootAdjudicationSha256':sha((OUT/'root-adjudication.json').read_bytes()),
 'method':'For each of 42 proposed cells, require exact pinned target-catalog file SHA-256 and Git blob plus exact current-target SHA-256 before replacement; verify each final target hash and all 600 readbacks. Preserve the other 558 current values byte-for-byte at the cell level.',
 'counts':{'reviewedCells':600,'applyChanges':42,'acceptCurrent':558,'callerlessCells':0},
 'fileGuards':fileguards,'changes':plan_changes
}
writej('apply-plan.json',plan)
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'main':main,'baseAhead':compare['aheadBy'],'changedLiteralCallers':len(literal_intersections),'backendCallerIntersections':{k:len(v) for k,v in all_intersections.items() if k in {'Book','BookCount','BookFileCount'}},'changes':len(plan_changes),'acceptedCurrent':558,'rootCorrectionSha256':sha_text(ROOT_TARGET),'rootAdjudicationPath':str(OUT/'root-adjudication.json')},sort_keys=True))
