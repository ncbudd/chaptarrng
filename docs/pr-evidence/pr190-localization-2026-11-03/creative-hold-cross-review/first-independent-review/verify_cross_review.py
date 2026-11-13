#!/usr/bin/env python3
"""Portable exact-head verifier for this independent cross-review packet."""
import base64, concurrent.futures, hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source-packet'
REPO='snapetech-org/chaptarrng'
HEAD='15fde999b8b8dc29d44833845aba13e1a2ad0443'
TREE='79f0882d1fa904ee967fb37ad1349dc6434c9537'
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def require(ok,msg):
    if not ok: raise AssertionError(msg)
def sums(directory,name='SHA256SUMS.txt'):
    f=directory/name; rows=[]
    for line in f.read_text(encoding='utf-8').splitlines():
        parts=line.split(None,1); require(len(parts)==2,'malformed checksum row: '+str(f))
        rows.append((parts[1].lstrip('* '),parts[0]))
    listed={p for p,_ in rows}
    actual={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p!=f}
    require(len(rows)==len(listed) and listed==actual,'checksum manifest file set mismatch: '+str(directory))
    for p,h in rows: require(sha((directory/p).read_bytes())==h,'checksum mismatch: '+str(directory/p))
    return len(rows)
def tokens(s):
    return {'placeholders':re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s),'markupTags':re.findall(r'<\/?[A-Za-z][^>]*>',s),'numericTokens':re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])','') if False else re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s),'protectedLiterals':[m.group(0) for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s)]}
def gh(args):
    p=subprocess.run(args,text=True,capture_output=True)
    require(p.returncode==0,'command failed: '+' '.join(args)+'\n'+p.stderr.strip())
    return p.stdout
def fetch(pin):
    url='repos/{}/contents/{}?ref={}'.format(REPO,pin['path'],HEAD)
    obj=json.loads(gh(['gh','api',url])); data=base64.b64decode(obj['content'])
    # Match Git's object ID; the content is also pinned with SHA-256.
    blob=subprocess.check_output(['git','hash-object','--stdin'],input=data).decode().strip()
    require(len(data)==pin['byteCount'],'byte count mismatch: '+pin['path'])
    require(sha(data)==pin['sha256'],'file SHA-256 mismatch: '+pin['path'])
    require(blob==pin['gitBlob'],'git blob mismatch: '+pin['path'])
    return pin['path'],data
def main():
    outer_count=sums(ROOT); src_root_count=sums(SRC); input_count=sums(SRC/'input'); review_count=sums(SRC/'review')
    manifest=readj(ROOT/'manifest.json')
    require(manifest['head']==HEAD and manifest['tree']==TREE,'cross manifest ref mismatch')
    require(manifest['sourcePacketSha256SumsSha256']==sha((SRC/'SHA256SUMS.txt').read_bytes()),'source packet checksum anchor mismatch')
    require(manifest['freshProposalSha256']==sha((SRC/'review/independent-recommendations.jsonl').read_bytes()),'fresh proposal anchor mismatch')
    pin_doc=readj(SRC/'input/file-pins.json')
    require(pin_doc['head']==HEAD and pin_doc['tree']==TREE,'source pin ref mismatch')
    pins=pin_doc['pins']; require(len(pins)==16,'expected 16 source/caller/catalog pins')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: fetched=list(pool.map(fetch,pins))
    files=dict(fetched); require(len(files)==16,'duplicate pinned path')
    pr=json.loads(gh(['gh','pr','view','190','--repo',REPO,'--json','number,state,isDraft,headRefOid,headRefName,baseRefName,url']))
    require(pr['number']==190 and pr['state']=='OPEN' and pr['isDraft'] is True,'PR state/draft mismatch')
    require(pr['headRefOid']==HEAD,'live PR head moved')
    commit=json.loads(gh(['gh','api','repos/{}/git/commits/{}'.format(REPO,HEAD)]))
    require(commit['tree']['sha']==TREE,'live commit tree moved')
    catalog_paths={p['path'] for p in pins if p['kind'] in {'source-catalog','locale-catalog'}}
    locale_file={'zh-Hans':'zh_CN','zh-Hant':'zh_TW','pt-BR':'pt_BR'}
    catalogs={}
    for p in catalog_paths: catalogs[p.rsplit('/',1)[-1][:-5]]=json.loads(files[p].decode('utf-8'))
    source_catalog=catalogs['en']
    contexts=readjl(SRC/'input/source-caller-context.jsonl'); cells=readjl(SRC/'input/creative-current-cells.jsonl')
    proposals=readjl(SRC/'review/independent-recommendations.jsonl'); ledger=readjl(ROOT/'cross-ledger.jsonl')
    require(len(contexts)==3 and len(cells)==20 and len(proposals)==20 and len(ledger)==20,'review scope count mismatch')
    by_context={x['sourceId']:x for x in contexts}; by_cell={(x['sourceId'],x['locale']):x for x in cells}
    by_proposal={(x['sourceId'],x['locale']):x for x in proposals}; by_ledger={(x['sourceId'],x['locale']):x for x in ledger}
    require(len(by_cell)==len(by_proposal)==len(by_ledger)==20,'duplicate or missing creative cell')
    caller_refs=0
    for ctx in contexts:
        require(ctx['sourceId'] in source_catalog and source_catalog[ctx['sourceId']]==ctx['source'],'source text differs at head')
        require(ctx['sourceSha256']==sha_text(ctx['source']),'source text hash mismatch')
        require(ctx['callerCount']==len(ctx['callerReferences']) and ctx['callerCount']>0,'caller count mismatch')
        for cref in ctx['callerReferences']:
            caller_refs+=1; data=files[cref['path']]
            require(sha(data)==cref['fileSha256'],'caller file hash mismatch')
            lines=data.decode('utf-8').splitlines()
            for item in cref['contextLines']:
                ix=item['line']-1
                require(0<=ix<len(lines),'caller context line out of range')
                require(lines[ix]==item['text'],'caller context line text mismatch')
                require(sha_text(lines[ix])==item['lineSha256'],'caller context line hash mismatch')
    require(caller_refs==5,'expected five caller references')
    for cell in cells:
        cat_name=locale_file.get(cell['locale'],cell['locale']); path='src/NzbDrone.Core/Localization/Core/{}.json'.format(cat_name)
        require(path in files,'target catalog missing from source pins')
        actual=catalogs[cat_name].get(cell['sourceId'])
        require(actual==cell['currentTarget'],'target preimage text mismatch at head')
        require(sha_text(actual)==cell['currentTargetSha256'],'target preimage hash mismatch')
        pin=next(p for p in pins if p['path']==path)
        require(pin['sha256']==cell['targetFileSha256'] and pin['gitBlob']==cell['targetFileGitBlob'],'target catalog file pin mismatch')
        require(cell['source']==source_catalog[cell['sourceId']] and cell['sourceSha256']==sha_text(cell['source']),'cell source mismatch')
        require(cell['currentTargetTokens']==tokens(actual) and cell['sourceTokens']==tokens(cell['source']),'input token inventory mismatch')
    for key,row in by_ledger.items():
        require(key in by_cell and key in by_proposal,'ledger row not in source packet')
        cell=by_cell[key]; proposal=by_proposal[key]; ctx=by_context[row['sourceId']]
        require(row['window']=='W1200-W1209','window mismatch')
        require(row['source']==cell['source']==proposal['source'] and row['sourceSha256']==cell['sourceSha256']==proposal['sourceSha256'],'source text/hash mismatch')
        require(row['currentTargetSha256']==cell['currentTargetSha256']==proposal['currentTargetSha256'],'preimage hash mismatch')
        require(row['callerCount']==ctx['callerCount']==proposal['callerCount'],'caller count mismatch')
        require(row['callerContextSha256']==ctx['callerContextSha256']==proposal['callerContextSha256'],'caller context hash mismatch')
        require(row['draftTarget']==proposal['independentTargetRecommendation'],'cross review changed the reviewed draft')
        require(row['draftTargetSha256']==sha_text(row['draftTarget'])==proposal['targetRecommendationSha256'],'draft target hash mismatch')
        require(tokens(row['draftTarget'])==tokens(row['source']),'placeholder/markup/numeric/protected-token mismatch')
        require(row['crossDisposition'] in {'endorse-draft-pending-native-review','continue-hold'},'invalid cross disposition')
        require(row['confidence'] in {'moderate','low'},'unexpected cross confidence')
        require(row['continuedHold'] is (row['crossDisposition']=='continue-hold'),'continued-hold flag mismatch')
        require(row['nativeSpeakerSignoff'] is False and row['applicationStatus']=='not applied','signoff/application status mismatch')
        require(bool(row['rationale']),'missing cross rationale')
        if row['continuedHold']: require(bool(row['holdReason']),'continued hold needs a reason')
    require(sum(r['crossDisposition']=='endorse-draft-pending-native-review' for r in ledger)==17,'endorsed draft count mismatch')
    require(sum(r['continuedHold'] for r in ledger)==3,'continued hold count mismatch')
    require(sum(r['confidence']=='moderate' for r in ledger)==17 and sum(r['confidence']=='low' for r in ledger)==3,'confidence count mismatch')
    # Callerless inventory is intentionally hashed only; never print its source IDs or target strings.
    exclusions=readjl(SRC/'input/callerless-hold-hashes-only.jsonl')
    allowed={'sourceOrdinal','sourceIdSha256','locale','sourceTextSha256','recordedTargetSha256','liveTargetSha256','sourceTextHashSameAtHead','targetHashSameAtHead','evidenceSha256'}
    require(len(exclusions)==24,'callerless hash-only count mismatch')
    require(all(set(x)==allowed for x in exclusions),'callerless row contains extra fields')
    source_keys={sha_text(k):k for k in source_catalog}
    require(len(source_keys)==len(source_catalog),'unexpected duplicate source key digest')
    for x in exclusions:
        require(x['sourceTextHashSameAtHead'] is True and x['targetHashSameAtHead'] is True,'callerless match flag false')
        for h in ('sourceIdSha256','sourceTextSha256','recordedTargetSha256','liveTargetSha256','evidenceSha256'):
            require(isinstance(x[h],str) and re.fullmatch(r'[0-9a-f]{64}',x[h]) is not None,'invalid callerless hash')
        source_id=source_keys.get(x['sourceIdSha256']); require(source_id is not None,'callerless source key hash absent at head')
        require(sha_text(source_catalog[source_id])==x['sourceTextSha256'],'callerless source hash mismatch')
        cat_name=locale_file.get(x['locale'],x['locale'])
        require(cat_name in catalogs and source_id in catalogs[cat_name],'callerless target key absent at head')
        target_hash=sha_text(catalogs[cat_name][source_id])
        require(target_hash==x['recordedTargetSha256']==x['liveTargetSha256'],'callerless target hash mismatch')
    summary=readj(ROOT/'summary.json')
    require(summary['crossReviewedCells']==20 and summary['sourceCallerCatalogPinsRechecked']==16 and summary['targetPreimagesRechecked']==20,'summary count mismatch')
    require(summary['callerlessHoldsHashOnly'] is True and summary['callerlessHoldHashesReattested']==24 and summary['callerlessTargetTextsIncluded'] is False,'hash-only summary mismatch')
    require(summary['nativeSpeakerSignoff'] is False and summary['catalogApplication']=='none','summary signoff/application mismatch')
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'livePr':'OPEN/DRAFT','sourceCallerCatalogPins':len(pins),'sourceRecords':len(contexts),'callerReferences':caller_refs,'targetPreimages':len(cells),'crossReviewedCells':len(ledger),'endorsedDraftsPendingNativeReview':17,'continuedHolds':3,'callerlessHashOnlyCellsReattested':len(exclusions),'nativeSpeakerSignoff':False,'catalogApplication':'none','outerChecksumEntries':outer_count,'sourcePacketChecksumEntries':src_root_count,'sourceInputChecksumEntries':input_count,'sourceReviewChecksumEntries':review_count},ensure_ascii=False,indent=2))
if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('FAIL:',str(exc),file=sys.stderr); raise SystemExit(1)
