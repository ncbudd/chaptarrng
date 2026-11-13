#!/usr/bin/env python3
"""Portable verifier for the ChaptarrNG PR #190 W450-W499 blind review."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']


def sha(data): return hashlib.sha256(data).hexdigest()
def die(msg): raise SystemExit('FAIL: '+msg)
def placeholders(s): return re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
def inline(s): return re.findall(r'`[^`]+`',s)
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
def numeric(s): return re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
def token_checks(source,target,literals):
    return {'placeholders':placeholders(source)==placeholders(target),
            'inlineCode':inline(source)==inline(target),
            'markupTags':markup(source)==markup(target),
            'numericTokens':numeric(source)==numeric(target),
            'protectedLiterals':all(target.count(x)>=source.count(x) for x in literals)}
def parse_jsonl(path):
    out=[]
    for raw in path.read_bytes().splitlines():
        if raw.strip(): out.append((raw,json.loads(raw)))
    return out
def sums(path):
    result={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,n=line.split(maxsplit=1); n=n.lstrip('*')
        if n in result: die(f'duplicate checksum path {n}')
        result[n]=h
    return result
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate-free',type=Path,help='candidate-free input dir; defaults to sibling packet input')
    ap.add_argument('--repo',type=Path,help='optional exact-head repository checkout')
    args=ap.parse_args()
    packet=Path(__file__).resolve().parent
    inp=(args.candidate_free or packet.parent/'candidate-free'/'input').resolve()
    manifest=json.loads((packet/'manifest.json').read_text(encoding='utf-8'))
    summary=json.loads((packet/'summary.json').read_text(encoding='utf-8'))
    cfmanifest=json.loads((inp/'candidate-free-manifest.json').read_text(encoding='utf-8'))
    if (manifest.get('exactHead'),manifest.get('exactTree'),manifest.get('apiBaseSha'))!=(HEAD,TREE,BASE): die('manifest pin mismatch')
    if (summary.get('exactHead'),summary.get('exactTree'),summary.get('apiBaseSha'))!=(HEAD,TREE,BASE): die('summary pin mismatch')
    if (cfmanifest.get('head'),cfmanifest.get('tree'),cfmanifest.get('apiBase'))!=(HEAD,TREE,BASE): die('candidate-free pin mismatch')
    if cfmanifest.get('candidateFreeOnly') is not True: die('input packet is not candidate-free')

    input_sums=sums(inp/'SHA256SUMS.txt')
    for name,h in input_sums.items():
        p=inp/name
        if not p.is_file() or sha(p.read_bytes())!=h: die(f'candidate-free checksum mismatch: {name}')
    if sha((inp/'candidate-free-manifest.json').read_bytes())!=manifest.get('candidateFreeManifestSha256'): die('candidate-free manifest hash mismatch')
    if sha((inp/'SHA256SUMS.txt').read_bytes())!=manifest.get('candidateFreeChecksumListSha256'): die('candidate-free checksum-list hash mismatch')

    rows=parse_jsonl(inp/'candidate-free-cells.jsonl')
    contexts={r['sourceKey']:r for _,r in parse_jsonl(inp/'caller-context.jsonl')}
    cf={f"{r['sourceKey']}::{r['locale']}":(raw,r) for raw,r in rows}
    expected={f"{r['sourceKey']}::{loc}" for _,r in rows for loc in [r['locale']]}
    if len(rows)!=600 or len(expected)!=600 or len(contexts)!=50: die('candidate-free scope mismatch')
    if {r['sourceOrdinal'] for _,r in rows}!=set(range(450,500)): die('source positions mismatch')
    if {r['locale'] for _,r in rows}!=set(LOCALES): die('locale set mismatch')

    ledger_rows=parse_jsonl(packet/'ledger.jsonl')
    proposals_rows=parse_jsonl(packet/'proposals.jsonl')
    holds_rows=parse_jsonl(packet/'holds.jsonl')
    ledger={r['cellId']:(raw,r) for raw,r in ledger_rows}
    ledger_by_posloc={(r['sourceOrdinal'],r['locale']):(raw,r) for raw,r in ledger_rows}
    proposals={r['cellId']:(raw,r) for raw,r in proposals_rows}
    holds=[r for _,r in holds_rows]
    if len(ledger)!=600 or len(ledger_rows)!=600 or len(ledger_by_posloc)!=600 or set(ledger_by_posloc)!={(r['sourceOrdinal'],r['locale']) for _,r in rows}: die('ledger scope mismatch')
    if len(proposals)!=69: die('proposal count mismatch')
    if len(holds)!=48: die('hold count mismatch')
    if any(f in r for r in holds for f in ('sourceKey','sourceText','currentTarget','recommendedTarget')): die('hash-only hold contains text')
    counts={}; confidence={}; current_alerts=0
    expected_proposals=set(); seen_holds=[]

    for cell_id,(raw_cell,cell) in cf.items():
        pos=cell['sourceOrdinal']; locale=cell['locale']; ctx=contexts[cell['sourceKey']]
        rec_raw,rec=ledger_by_posloc[(pos,locale)]
        if rec.get('exactHead')!=HEAD or rec.get('exactTree')!=TREE: die(f'exact pin mismatch: {cell_id}')
        if rec.get('candidateFreeRowSha256')!=sha(raw_cell): die(f'candidate-free row hash mismatch: {cell_id}')
        if rec.get('sourceTextSha256')!=cell['sourceTextSha256'] or sha(cell['sourceText'].encode())!=cell['sourceTextSha256']: die(f'source text hash mismatch: {cell_id}')
        if rec.get('currentTargetSha256')!=cell['currentTargetSha256'] or sha(cell['currentTarget'].encode())!=cell['currentTargetSha256']: die(f'current target hash mismatch: {cell_id}')
        if rec.get('callerContextSha256')!=cell['callerContextSha256'] or ctx.get('callerContextSha256')!=cell['callerContextSha256']: die(f'caller context pin mismatch: {cell_id}')
        decision=rec.get('decision')
        counts[decision]=counts.get(decision,0)+1

        if decision=='hold-hash-only':
            if ctx['callerReferenceCount']!=0: die(f'hold is not callerless: {cell_id}')
            if rec.get('cellId')!='sha256:'+sha(f"{HEAD}|{pos}|{locale}|{cell['sourceTextSha256']}|{cell['currentTargetSha256']}".encode()): die(f'hold id mismatch: {cell_id}')
            if rec.get('sourceKeySha256')!=sha(cell['sourceKey'].encode()) or rec.get('callerReferenceCount')!=0: die(f'hold binding mismatch: {cell_id}')
            if rec.get('locale')!=locale or rec.get('sourceOrdinal')!=pos: die(f'hold identity mismatch: {cell_id}')
            if rec.get('decision')!='hold-hash-only': die(f'hold decision mismatch: {cell_id}')
            seen_holds.append(rec)
            continue

        if rec.get('cellId')!=cell_id or rec.get('sourceOrdinal')!=pos or rec.get('locale')!=locale or rec.get('sourceKey')!=cell['sourceKey']: die(f'ledger identity mismatch: {cell_id}')
        if rec.get('sourceText')!=cell['sourceText'] or rec.get('currentTarget')!=cell['currentTarget']: die(f'ledger text binding mismatch: {cell_id}')
        if rec.get('sourceFileGitBlob')!=cell['sourceFileGitBlob'] or rec.get('targetFileGitBlob')!=cell['targetFileGitBlob']: die(f'catalog blob pin mismatch: {cell_id}')
        if rec.get('callerReferenceCount')!=ctx['callerReferenceCount'] or rec.get('callerPaths')!=sorted({c['path'] for c in ctx['callerRefs']}): die(f'caller summary mismatch: {cell_id}')
        if rec.get('sourceTokens')!={'placeholders':cell['sourcePlaceholders'],'inlineCode':cell['sourceInlineCode'],'markup':cell['sourceMarkup'],'numericTokens':cell['sourceNumericTokens'],'protectedLiterals':cell.get('protectedLiterals',[])}: die(f'source token signature mismatch: {cell_id}')
        current=token_checks(cell['sourceText'],cell['currentTarget'],cell.get('protectedLiterals',[]))
        if rec.get('currentTargetTokenChecks')!=current: die(f'current token audit mismatch: {cell_id}')
        if not all(current.values()): current_alerts+=1
        recommended=rec.get('recommendedTarget',cell['currentTarget'])
        checks=token_checks(cell['sourceText'],recommended,cell.get('protectedLiterals',[]))
        if rec.get('recommendedTargetTokenChecks')!=checks or not all(checks.values()): die(f'recommended token mismatch: {cell_id}')
        if decision=='accept-current':
            if 'recommendedTarget' in rec: die(f'accept-current row has proposal text: {cell_id}')
            if not all(current.values()): die(f'unresolved current token alert: {cell_id}')
        elif decision in ('correction','refinement'):
            expected_proposals.add(cell_id)
            if rec.get('recommendedTargetSha256')!=sha(recommended.encode()): die(f'recommended hash mismatch: {cell_id}')
            prop=proposals.get(cell_id,(None,None))[1]
            if prop is None: die(f'missing proposal: {cell_id}')
            for f in ('sourceOrdinal','sourceKey','locale','sourceTextSha256','currentTargetSha256','candidateFreeRowSha256','callerContextSha256','exactHead','exactTree','decision','recommendedTarget','recommendedTargetSha256'):
                if prop.get(f)!=rec.get(f): die(f'proposal binding mismatch {f}: {cell_id}')
        else: die(f'unexpected decision: {cell_id} {decision}')
        confidence[rec['confidence']]=confidence.get(rec['confidence'],0)+1

    if set(proposals)!=expected_proposals: die('proposal scope mismatch')
    if { (r['cellId'],r['sourceOrdinal'],r['locale'],r['candidateFreeRowSha256']) for r in holds }!={ (r['cellId'],r['sourceOrdinal'],r['locale'],r['candidateFreeRowSha256']) for r in seen_holds }: die('hash-only hold file/ledger mismatch')
    if counts!={'accept-current':483,'correction':27,'refinement':42,'hold-hash-only':48}: die(f'decision count mismatch: {counts}')
    if summary.get('decisionCounts')!=counts or summary.get('proposalCount')!=69 or summary.get('holdCount')!=48: die('summary decision counts mismatch')
    if summary.get('currentTargetTokenAlertCount')!=current_alerts or current_alerts!=2: die('current target alert summary mismatch')
    if summary.get('recommendedTargetTokenMismatches')!=0: die('recommended target token summary mismatch')
    if summary.get('localeDecisionCounts')!={l:{d:sum(1 for _,r in ledger_rows if r.get('locale')==l and r.get('decision')==d) for d in counts if any(r.get('locale')==l and r.get('decision')==d for _,r in ledger_rows)} for l in LOCALES}: die('per-locale summary mismatch')

    for name in ('attestation-entry.json','attestation-exit.json'):
        att=json.loads((packet/name).read_text(encoding='utf-8'))
        if (att.get('head'),att.get('tree'),att.get('apiBaseSha'))!=(HEAD,TREE,BASE): die(f'{name} pin mismatch')
        if att.get('state')!='OPEN' or att.get('draft') is not True: die(f'{name} PR state mismatch')
        refs=att.get('remoteRefs',{})
        if refs.get(f'refs/heads/{BRANCH}')!=HEAD or refs.get('refs/pull/190/head')!=HEAD: die(f'{name} branch/pull ref mismatch')
        if not refs.get('refs/heads/main'): die(f'{name} live main ref missing')

    out_sums=sums(packet/'SHA256SUMS.txt')
    if set(out_sums)!=(set(manifest['files'])|{'manifest.json'}): die('output checksum inventory mismatch')
    for name,h in out_sums.items():
        p=packet/name
        if not p.is_file() or sha(p.read_bytes())!=h: die(f'output checksum mismatch: {name}')

    repo_result='not-requested'
    if args.repo:
        repo=args.repo.resolve()
        if git(repo,'rev-parse','HEAD')!=HEAD or git(repo,'rev-parse','HEAD^{tree}')!=TREE: die('exact repository head/tree mismatch')
        blobs={cell['targetFileGitBlob'] for _,cell in rows}
        for blob in blobs:
            if git(repo,'cat-file','-t',blob)!='blob': die(f'missing target catalog blob {blob}')
        repo_result=f'PASS exact commit/tree and {len(blobs)} target catalog blobs'
    print('PASS: 600 cells (50 IDs × 12 locales), 69 proposals, 48 text-free hash-only holds, caller/source/catalog pins, recommended token checks, exact refs and checksums'+(f'; {repo_result}' if args.repo else ''))

if __name__=='__main__':
    try: main()
    except subprocess.CalledProcessError as e: die(e.output.decode(errors='replace').strip() or 'Git check failed')
