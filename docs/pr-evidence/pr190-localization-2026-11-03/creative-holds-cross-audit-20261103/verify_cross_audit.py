#!/usr/bin/env python3
import collections, hashlib, json, pathlib, re, subprocess, sys
OUT=pathlib.Path(__file__).resolve().parent
HEAD='712d597e6f27f6485f7c287b70f6dc79003ca714'
TREE='275b19ba948bacd883d845ec970c154511be0e43'
REPO='snapetech-org/ChaptarrNG'
def fail(m): raise SystemExit('FAIL: '+m)
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def checksums(folder, expected_names=None):
    folder=pathlib.Path(folder); p=folder/'SHA256SUMS.txt'
    if not p.is_file(): fail('missing checksum file '+str(p))
    listed={}
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,name=line.split(None,1); name=name.lstrip('* '); f=folder/name
        if not f.is_file() or sha(f.read_bytes())!=digest: fail('checksum mismatch '+str(f))
        if name in listed: fail('duplicate checksum '+name)
        listed[name]=digest
    actual={x.relative_to(folder).as_posix() for x in folder.rglob('*') if x.is_file() and x!=p}
    if set(listed)!=actual: fail('checksum coverage mismatch '+str(folder))
    if expected_names is not None and set(listed)!=set(expected_names): fail('unexpected checksum file set '+str(folder))
    return listed
def tokens(s):
    return {'placeholders':sorted(re.findall(r'%(?:\d+\$)?[-+#0 ]*\d*(?:\.\d+)?[A-Za-z]|\{\{[^{}]+\}\}|\{[^{}]+\}|\$\{[^{}]+\}',s)), 'markupTags':sorted(re.findall(r'</?[A-Za-z][A-Za-z0-9:_-]*(?:\s+[^<>]*?)?/?>',s)), 'numericTokens':sorted(re.findall(r'\d+',s))}
def tokencheck(source,target,lits):
    a=tokens(source); b=tokens(target)
    return (a['placeholders']==b['placeholders'] and a['markupTags']==b['markupTags'] and a['numericTokens']==b['numericTokens'] and all(x in target for x in lits))
def main():
    outer=checksums(OUT)
    manifest=readj(OUT/'manifest.json')
    if (manifest.get('head'),manifest.get('tree'),manifest.get('repository'),manifest.get('pullRequest'))!=(HEAD,TREE,REPO,190): fail('manifest exact pin mismatch')
    manifest_paths={x['path'] for x in manifest['files']}
    actual={x.relative_to(OUT).as_posix() for x in OUT.rglob('*') if x.is_file() and x not in (OUT/'manifest.json',OUT/'SHA256SUMS.txt')}
    if manifest_paths!=actual: fail('manifest file set mismatch')
    for x in manifest['files']:
        f=OUT/x['path']
        if f.stat().st_size!=x['byteCount'] or sha(f.read_bytes())!=x['sha256']: fail('manifest output hash mismatch '+x['path'])
    ev=OUT/'evidence'; inp=ev/'live-input'; head=ev/'live-head'; pri=ev/'primary-review'; blind=ev/'blind-review'
    inhash=checksums(inp); prihash=checksums(pri); blhash=checksums(blind); headhash=checksums(head)
    im=readj(inp/'manifest.json'); att=readj(inp/'PR-attestation.json')
    if (im.get('head'),im.get('tree'),att.get('head'),att.get('tree'))!=(HEAD,TREE,HEAD,TREE): fail('input pin mismatch')
    if im.get('candidateFree') is not True or im.get('translationCandidatesIncluded') is not False or im.get('priorReviewVerdictsIncluded') is not False: fail('input is not candidate-free')
    contexts=readjl(inp/'source-and-caller-context.jsonl'); targets=readjl(inp/'current-target-cells.jsonl')
    p_rows=readjl(pri/'review-ledger.jsonl'); b_rows=readjl(blind/'blind-hold-ledger.jsonl'); ledger=readjl(OUT/'cross-audit-ledger.jsonl')
    src={x['sourceId']:x for x in contexts}; tmap={(x['sourceId'],x['locale']):x for x in targets}; pmap={(x['sourceId'],x['locale']):x for x in p_rows}; bmap={(x['sourceId'],x['locale']):x for x in b_rows}
    if len(src)!=3 or len(tmap)!=20 or set(tmap)!=set(pmap) or set(tmap)!=set(bmap) or len(ledger)!=20: fail('20-cell coverage mismatch')
    pin=readj(OUT/'live-pin-recheck.json'); live=readj(OUT/'live-pr-attestation.json')
    if pin.get('status')!='PASS' or pin.get('pinCount')!=16 or len(pin.get('pins',[]))!=16: fail('pin audit failed')
    if (live.get('head'),live.get('tree'),live.get('repository'),live.get('pullRequest'))!=(HEAD,TREE,REPO,190) or not live.get('worktreeClean'): fail('live re-attestation mismatch')
    pin_paths={x['path'] for x in pin['pins']}
    if len(pin_paths)!=16 or any(x.get('status')!='PASS' or x.get('actualGitBlob')!=x.get('gitBlob') or x.get('actualSha256')!=x.get('sha256') or not x.get('worktreeBytesMatch') for x in pin['pins']): fail('file blob pin mismatch')
    pin_manifest=readj(head/'live-file-pins.json')
    live_pin_rows={x['path']:x for x in pin_manifest.get('files',[])}
    if set(live_pin_rows)!=pin_paths: fail('captured live-head file set mismatch')
    live_pin_audit={x['path']:x for x in pin['pins']}
    catalog_cache={}
    for path, item in live_pin_rows.items():
        f=head/path
        if not f.is_file(): fail('missing captured pinned file '+path)
        raw=f.read_bytes()
        # Match Git's object ID; the content is also pinned with SHA-256.
        blob=subprocess.check_output(['git','hash-object','--stdin'],input=raw).decode().strip()
        audit=live_pin_audit[path]
        if len(raw)!=item.get('bytes') or sha(raw)!=item.get('sha256') or blob!=item.get('gitBlob') or audit.get('actualGitBlob')!=blob or audit.get('actualSha256')!=sha(raw): fail('captured raw blob mismatch '+path)
        if path.endswith('.json') and '/Localization/Core/' in path:
            catalog_cache[path]=json.loads(raw.decode('utf-8'))
    for source in contexts:
        if catalog_cache[source['sourceFile']].get(source['sourceId'])!=source['source'] or sha(source['source'].encode())!=source['sourceSha256']: fail('pinned source catalog value mismatch '+source['sourceId'])
        for ref in source['callerReferences']:
            lines=(head/ref['path']).read_text(encoding='utf-8').splitlines()
            for item in ref['contextLines']:
                if item['line']<1 or item['line']>len(lines) or lines[item['line']-1]!=item['text'] or sha(item['text'].encode())!=item['lineSha256']: fail('pinned caller line mismatch '+ref['path'])
    for target in targets:
        if catalog_cache[target['targetFile']].get(target['sourceId'])!=target['currentTarget'] or sha(target['currentTarget'].encode())!=target['currentTargetSha256']: fail('pinned target catalog value mismatch '+target['sourceId']+':'+target['locale'])
    if len(pin.get('sourceCatalogValues',[]))!=3 or len(pin.get('currentCellCatalogValues',[]))!=20 or pin.get('callerLineCount')!=16 or len(pin.get('callerLines',[]))!=16 or pin.get('callerLineOccurrenceCount')!=25: fail('source/target/caller pin count mismatch')
    if any(x.get('status')!='PASS' for x in pin['sourceCatalogValues']+pin['currentCellCatalogValues']): fail('catalog cell recheck failed')
    ex=readj(inp/'scope-exclusion-id-dodgeBooks.json')
    if ex.get('sourceId')!='ui.loading.dodgeBooks' or ex.get('locale')!='id' or ex.get('includedInReviewLedger') is not False or ex.get('targetChangedSinceSeed') is not True: fail('scope exclusion mismatch')
    if catalog_cache[ex['targetFile']].get(ex['sourceId'])!=ex['liveCurrentTarget'] or sha(ex['liveCurrentTarget'].encode())!=ex['liveCurrentTargetSha256']: fail('excluded live target mismatch')
    rows={(x['sourceId'],x['locale']):x for x in ledger}; disagreements=0
    for key,t in tmap.items():
        s=src[key[0]]; p=pmap[key]; b=bmap[key]; r=rows.get(key)
        if r is None: fail('missing resolution row '+str(key))
        if (r.get('head'),r.get('tree'),r.get('source'),r.get('sourceSha256'))!=(HEAD,TREE,s['source'],s['sourceSha256']): fail('ledger source pin mismatch '+str(key))
        if r.get('currentTarget')!=t['currentTarget'] or r.get('currentTargetSha256')!=t['currentTargetSha256'] or sha(t['currentTarget'].encode())!=t['currentTargetSha256']: fail('current target mismatch '+str(key))
        if r.get('callerReferences')!=s['callerReferences'] or r.get('callerContextSha256s')!=[c['contextSha256'] for c in s['callerReferences']]: fail('caller context mismatch '+str(key))
        if r.get('primarySuggestion',{}).get('target')!=p.get('proposedTarget') or r.get('primarySuggestion',{}).get('sha256')!=p.get('proposedTargetSha256'): fail('primary proposal mismatch '+str(key))
        if r.get('blindSuggestion',{}).get('target')!=b.get('proposedTarget') or r.get('blindSuggestion',{}).get('sha256')!=b.get('proposedTargetSha256'): fail('blind proposal mismatch '+str(key))
        if sha(p['proposedTarget'].encode())!=p['proposedTargetSha256'] or sha(b['proposedTarget'].encode())!=b['proposedTargetSha256']: fail('suggestion hash mismatch '+str(key))
        same=p['proposedTarget']==b['proposedTarget']
        if r.get('pairComparison',{}).get('sameTarget')!=same: fail('agreement record mismatch '+str(key))
        if not same: disagreements+=1
        lits=t.get('protectedLiterals',[])
        if not tokencheck(t['source'],p['proposedTarget'],lits) or not tokencheck(t['source'],b['proposedTarget'],lits): fail('token/literal check failed '+str(key))
        resolution=r.get('resolution',{})
        if resolution.get('disposition')!='hold-pending-qualified-native-speaker-review' or resolution.get('selectedTarget') is not None or resolution.get('selectedTargetSha256') is not None or resolution.get('nativeSpeakerApproval') is not False or resolution.get('nativeSpeakerReviewRequired') is not True: fail('row is not held '+str(key))
        if p.get('disposition')!='hold' or b.get('status')!='hold' or b.get('nativeSpeakerApproval') is not False: fail('source review not held '+str(key))
    if disagreements!=20: fail('expected 20 pairwise disagreements')
    summary=readj(OUT/'summary.json')
    expected={'cellCount':20,'sourceCount':3}
    if summary.get('scope',{}).get('cellCount')!=20 or summary.get('scope',{}).get('sourceCount')!=3: fail('summary scope mismatch')
    if summary.get('pairReconciliation',{}).get('targetDisagreementCount')!=20 or summary.get('pairReconciliation',{}).get('agreementCount')!=0 or summary.get('pairReconciliation',{}).get('winnerSelections')!=0: fail('summary pair count mismatch')
    if summary.get('resolutions',{}).get('holdCount')!=20 or summary.get('resolutions',{}).get('approvedTranslationCount')!=0 or summary.get('resolutions',{}).get('allRowsRemainOnHold') is not True: fail('summary hold count mismatch')
    print('PASS: 20 primary/blind cell pairs; all 20 distinct targets reconciled and retained as unapproved review input.')
    print('PASS: all 20 cells remain held; no selected or approved target; native-speaker review pending.')
    print('PASS: 16 exact-head file pins, 20 source/target catalog cells, 25 caller-line occurrences across 16 unique lines, 40 proposal token/literal checks.')
    print('PASS: evidence packet checksums, manifest, and sealed output checksums.')
if __name__=='__main__': main()
