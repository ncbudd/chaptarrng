#!/usr/bin/env python3
import hashlib, json, subprocess
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent
INPUT=Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104/candidate-free/input')
EXPECTED_HEAD='f0082d1b655c05b8d4019ede523dd695cd6d745a'
EXPECTED_TREE='4cf2322354e9cf9b12d59cf10d0d8661c68ab4af'
CALLERLESS={'BookOnePlaceholder','BookTwoPlaceholder','ConflictsConsidered','SiblingTitlePlaceholder'}
def need(v,m):
    if not v: raise SystemExit('FAIL: '+m)
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
att=readj(P/'packet-attestation.json')
need((att['exactHead'],att['exactTree'])==(EXPECTED_HEAD,EXPECTED_TREE),'pinned head/tree')
need(att['sourceWorktreeClean'] is True and att['sourceWorktreeHead']==EXPECTED_HEAD and att['sourceWorktreeTree']==EXPECTED_TREE,'source worktree pin/status')
need(att['blindnessAttestation']['otherW300ReviewSuggestionsAccessed'] is False,'blindness attestation')
need(att['blindnessAttestation']['proposalTextIncluded'] is False and att['blindnessAttestation']['currentTargetTextCopiedIntoOutput'] is False,'text-free output attestation')
rows=readjl(P/'decisions.jsonl'); src=readjl(INPUT/'candidate-free-cells.jsonl')
need(len(rows)==len(src)==600,'row count')
need(len({(r['sourceKey'],r['locale']) for r in rows})==600,'unique cell identities')
need(sha((INPUT/'candidate-free-cells.jsonl').read_bytes())==att['inputAttestations']['candidateFreeCellsSha256'],'input cell file hash')
need([ (r['sourceKey'],r['locale']) for r in rows ]==[ (r['sourceKey'],r['locale']) for r in src ],'ordered cell identities')
for d,s in zip(rows,src):
    need(d['currentTargetSha256']==s['currentTargetSha256'] and d['sourceTextSha256']==s['sourceTextSha256'],'exact current hashes '+d['sourceKey']+'/'+d['locale'])
    need(d['callerContextSha256']==s['callerContextSha256'],'caller context pin '+d['sourceKey']+'/'+d['locale'])
    need(d['sourceTextIncluded'] is False and d['currentTargetTextIncluded'] is False and d['proposalIncluded'] is False,'text/proposal leak '+d['sourceKey']+'/'+d['locale'])
    need(d['decision'] in {'accept-current','hold'},'decision enum')
    ident={'sourceKey':d['sourceKey'],'locale':d['locale'],'sourceTextSha256':d['sourceTextSha256'],'currentTargetSha256':d['currentTargetSha256']}
    expect=sha((json.dumps(ident,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
    need(d['cellIdentitySha256']==expect,'cell identity hash '+d['sourceKey']+'/'+d['locale'])
    need((d['sourceKey'] in CALLERLESS)==(d['decision']=='hold' and d['findingType']=='callerless-hold'),'callerless hold '+d['sourceKey']+'/'+d['locale'])
need(all(sum(1 for d in rows if d['sourceKey']==k)==12 for k in CALLERLESS),'callerless cell coverage')
need(att['decisions']['callerlessHoldCells']==48,'callerless hold count')
counts=Counter(d['decision'] for d in rows)
need(counts['accept-current']==att['decisions']['acceptCurrent'],'accept-current total')
need(counts['hold']==att['decisions']['hold'],'hold total')
need(counts['accept-current']+counts['hold']==600,'decision totals')
need(sum(d['decision']=='hold' and d['sourceKey'] not in CALLERLESS for d in rows)==att['decisions']['semanticHoldCells'],'semantic hold total')
print(json.dumps({'result':'PASS','head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'cells':600,'callerlessHoldCells':48,'acceptCurrent':counts['accept-current'],'hold':counts['hold']},sort_keys=True))
