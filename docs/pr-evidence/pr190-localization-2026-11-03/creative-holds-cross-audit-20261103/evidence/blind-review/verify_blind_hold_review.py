#!/usr/bin/env python3
import collections, hashlib, json, pathlib

OUT=pathlib.Path(__file__).resolve().parent
INPUT=pathlib.Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-reconsideration-20261103/live-input')
HEAD='712d597e6f27f6485f7c287b70f6dc79003ca714'
TREE='275b19ba948bacd883d845ec970c154511be0e43'

def fail(msg): raise SystemExit('FAIL: '+msg)
def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(p): return sha(p.read_bytes())
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def checksums(folder):
    names=set()
    path=folder/'SHA256SUMS.txt'
    if not path.is_file():fail('missing checksum list '+str(path))
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        expected,name=line.split(None,1);name=name.lstrip('* ');f=folder/name
        if not f.is_file() or file_sha(f)!=expected:fail('checksum mismatch '+str(f))
        names.add(name)
    return names

def pins_from_input(contexts,targets):
    pins={}
    def add(kind,path,blob,digest,source_id=None,locale=None):
        k=(path,blob)
        row=pins.setdefault(k,{'pinType':kind,'path':path,'gitBlob':blob,'sha256':digest,'sourceIds':[],'locales':[]})
        if row['sha256']!=digest:fail('conflicting SHA for blob '+path)
        if source_id and source_id not in row['sourceIds']:row['sourceIds'].append(source_id)
        if locale and locale not in row['locales']:row['locales'].append(locale)
    for s in contexts:
        add('source-catalog',s['sourceFile'],s['sourceFileGitBlob'],s['sourceFileSha256'],s['sourceId'])
        for c in s['callerReferences']:add('caller-source',c['path'],c['gitBlob'],c['fileSha256'],s['sourceId'])
    for t in targets:add('target-catalog',t['targetFile'],t['targetFileGitBlob'],t['targetFileSha256'],t['sourceId'],t['locale'])
    return sorted(pins.values(),key=lambda x:(x['pinType'],x['path']))

def main():
    manifest=readj(OUT/'manifest.json')
    if (manifest.get('head'),manifest.get('tree'))!=(HEAD,TREE):fail('output pin mismatch')
    outnames=checksums(OUT)
    expected_out={'README.md','pin-audit.json','blind-hold-ledger.jsonl','summary.json','manifest.json','verify_blind_hold_review.py'}
    if outnames!=expected_out:fail('output checksum coverage mismatch')
    innames=checksums(INPUT)
    if innames!=set(manifest['inputFiles']):fail('live-input file set mismatch')
    for name,digest in manifest['inputFiles'].items():
        if file_sha(INPUT/name)!=digest:fail('live-input hash mismatch '+name)
    im=readj(INPUT/'manifest.json'); att=readj(INPUT/'PR-attestation.json')
    if (im.get('head'),im.get('tree'),att.get('head'),att.get('tree'))!=(HEAD,TREE,HEAD,TREE):fail('live input head/tree mismatch')
    if not im.get('candidateFree') or im.get('translationCandidatesIncluded') or im.get('priorReviewVerdictsIncluded'):fail('input is not candidate-free')
    contexts=readjl(INPUT/'source-and-caller-context.jsonl'); targets=readjl(INPUT/'current-target-cells.jsonl')
    sources={s['sourceId']:s for s in contexts}; inputrows={(t['sourceId'],t['locale']):t for t in targets}
    rows={(r['sourceId'],r['locale']):r for r in readjl(OUT/'blind-hold-ledger.jsonl')}
    if len(sources)!=3 or len(inputrows)!=20 or len(rows)!=20 or set(rows)!=set(inputrows):fail('prompt coverage mismatch')
    expected_pins=pins_from_input(contexts,targets); audit=readj(OUT/'pin-audit.json')
    if audit.get('status')!='PASS' or audit.get('uniqueGitBlobPinCount')!=16 or audit.get('pins')!=expected_pins:fail('16-pin audit mismatch')
    if collections.Counter(x['pinType'] for x in expected_pins)!=collections.Counter({'source-catalog':1,'target-catalog':12,'caller-source':3}):fail('pin type count mismatch')
    exclusions=readj(INPUT/'scope-exclusion-id-dodgeBooks.json')
    if exclusions.get('sourceId')!='ui.loading.dodgeBooks' or exclusions.get('locale')!='id' or not exclusions.get('targetChangedSinceSeed') or exclusions.get('includedInReviewLedger') is not False:fail('scope exclusion record mismatch')
    for key,t in inputrows.items():
        r=rows[key];s=sources[key[0]]
        if (r.get('head'),r.get('tree'))!=(HEAD,TREE):fail('row pin mismatch '+str(key))
        for field in ('source','sourceSha256','sourceFile','sourceFileGitBlob','sourceFileSha256'):
            if r.get(field)!=t.get(field,s.get(field)):fail('source/catalog binding mismatch '+str(key)+' '+field)
        if r['source']!=s['source'] or r['sourceSha256']!=s['sourceSha256'] or r['callerReferences']!=s['callerReferences']:fail('caller context mismatch '+str(key))
        if r.get('callerContextSha256s')!=[x['contextSha256'] for x in s['callerReferences']]:fail('caller context hash mismatch '+str(key))
        if t['source']!=s['source'] or t['sourceSha256']!=s['sourceSha256']:fail('source row mismatch '+str(key))
        if not t.get('targetUnchangedSinceCandidateFreeInput') or t['currentTargetSha256']!=sha(t['currentTarget'].encode()):fail('target readback mismatch '+str(key))
        if r['currentTarget']!=t['currentTarget'] or r['currentTargetSha256']!=t['currentTargetSha256']:fail('current target mismatch '+str(key))
        if r['targetFile']!=t['targetFile'] or r['targetFileGitBlob']!=t['targetFileGitBlob'] or r['targetFileSha256']!=t['targetFileSha256']:fail('target catalog pin mismatch '+str(key))
        proposed=r.get('proposedTarget')
        if not proposed or r.get('proposedTargetSha256')!=sha(proposed.encode()):fail('proposal hash mismatch '+str(key))
        if r.get('status')!='hold' or not r.get('nativeSpeakerReviewRequired') or r.get('nativeSpeakerApproval') is not False:fail('hold status/approval mismatch '+str(key))
        if not r.get('holdRationale') or not r.get('proposalRationale'):fail('missing hold/proposal rationale '+str(key))
        if any(lit not in proposed for lit in t.get('protectedLiterals',[])):fail('protected literal missing '+str(key))
        if r['sourceId']=='ui.loading.dodgeBooks' and r['locale']=='id':fail('excluded Indonesian Dodge row included')
    if sum(1 for k in rows if k[0]=='provider.option.o7285d46b982d')!=1:fail('provider prompt count mismatch')
    group_counts=collections.Counter(r['promptGroup'] for r in rows.values())
    if group_counts!=collections.Counter({'provider-option':1,'ebook-smell':8,'dodge-books':11}):fail('prompt group counts mismatch')
    summary=readj(OUT/'summary.json')
    expected_summary={'promptCount':20,'sourceCount':3,'proposalCount':20,'holdCount':20,'blobPinCount':16,'allRowsHeld':True,'qualifiedNativeSpeakerReviewPending':True,'excludedIndonesianDodgeCellPresent':False}
    for k,v in expected_summary.items():
        if summary.get(k)!=v:fail('summary mismatch '+k)
    if summary.get('promptGroupCounts')!=dict(sorted(group_counts.items())):fail('summary prompt group count mismatch')
    for item in manifest['outputFiles']:
        f=OUT/item['path']
        if not f.is_file() or f.stat().st_size!=item['byteCount'] or file_sha(f)!=item['sha256']:fail('manifest output hash mismatch '+item['path'])
    print('PASS: 20 caller-linked prompts (1 provider label, 8 eBook smell, 11 Dodge books); all remain holds.')
    print('PASS: 16 source/caller/catalog blob pins; live-input row bindings, target hashes, and Dodge literals.')
    print('PASS: native-speaker approval not claimed; input and output checksums verified.')
if __name__=='__main__':main()
