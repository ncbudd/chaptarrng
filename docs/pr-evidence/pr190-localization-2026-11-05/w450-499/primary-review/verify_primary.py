#!/usr/bin/env python3
import argparse,collections,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parent;HEAD="16c809b4787d70616a1a296ab0d90cf17923ba86";TREE="dbd8343a42476f4e830428cc59efb7f4830251d5"
def sha(b):return hashlib.sha256(b).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',default=str(ROOT.parent/'candidate-free/input'));args=ap.parse_args()
 for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  h,n=line.split('  ',1);p=ROOT/n
  if not p.is_file() or sha(p.read_bytes())!=h:raise SystemExit('FAIL checksum '+n)
 L=jl(ROOT/'ledger.jsonl');P=jl(ROOT/'proposals.jsonl');H=jl(ROOT/'holds.jsonl')
 if (len(L),len(H))!=(600,48):raise SystemExit('FAIL record totals')
 if any(r.get('exactHead')!=HEAD or r.get('exactTree')!=TREE for r in L):raise SystemExit('FAIL exact pins')
 if len({r.get('cellId') or r.get('cellIdSha256') for r in L})!=600:raise SystemExit('FAIL duplicate cell identities')
 counts=collections.Counter(r['decision'] for r in L)
 if counts['hold-hash-only']!=48 or counts['accept-current']+counts['correction']+counts['refinement']!=552:raise SystemExit('FAIL decision counts')
 if {(r['cellId'],r['proposedTarget']) for r in P}!={(r['cellId'],r['proposedTarget']) for r in L if r['decision'] in ('correction','refinement')}:raise SystemExit('FAIL proposal set')
 for r in P:
  if sha(r['proposedTarget'].encode())!=r['proposedTargetSha256'] or r['currentTarget']==r['proposedTarget']:raise SystemExit('FAIL proposal digest/no-op')
  checks=r['proposedTargetIntegrityChecks']
  if not all(v for k,v in checks.items() if k!='numeric'):raise SystemExit('FAIL nonnumeric token check')
  if not checks.get('numeric') and not r.get('manualNumericAssessment'):raise SystemExit('FAIL unexplained numeric flag')
 forbidden={'sourceKey','sourceText','currentTarget','locale','sourceOrdinal'}
 for r in H:
  if r['decision']!='hold-hash-only' or forbidden.intersection(r):raise SystemExit('FAIL hold text/key leak')
  if any(k not in r for k in ('cellIdSha256','candidateFreeRowSha256','sourceTextSha256','currentTargetSha256')):raise SystemExit('FAIL incomplete hash hold')
 attestations=[json.loads((ROOT/name).read_text()) for name in ('exact-head-before.json','exact-head-after.json')]
 for a in attestations:
  if a.get('headRefOid')!=HEAD or a.get('apiCommitSha')!=HEAD or a.get('apiCommitTree')!=TREE or a.get('branchRefOid')!=HEAD or a.get('pullRefOid')!=HEAD or a.get('state')!='OPEN' or a.get('isDraft') is not True:raise SystemExit('FAIL exact-head attestation')
 if attestations[0].get('baseRefOid')!=attestations[1].get('baseRefOid'):raise SystemExit('FAIL PR base moved')
 d=pathlib.Path(args.input);cells=d/'candidate-free-cells.jsonl'
 if cells.is_file():
  lines=cells.read_bytes().splitlines();rows=[json.loads(x) for x in lines];by={sha((r['sourceKey']+'::'+r['locale']).encode()):(r,sha(line)) for line,r in zip(lines,rows)}
  if len(by)!=600:raise SystemExit('FAIL input cell count')
  for o in L:
   key=o.get('cellIdSha256') or sha(o['cellId'].encode());pair=by.get(key)
   if not pair or pair[1]!=o['candidateFreeRowSha256']:raise SystemExit('FAIL candidate row binding')
   r,_=pair
   ishold=o['decision']=='hold-hash-only'
   if ishold:
    if r['callerReferenceCount']!=0 or r['literalCallCount']!=0 or r['sourceTextSha256']!=o['sourceTextSha256'] or r['currentTargetSha256']!=o['currentTargetSha256']:raise SystemExit('FAIL callerless hold binding')
   elif r['callerReferenceCount']==0 and r['literalCallCount']==0 or o['sourceKey']!=r['sourceKey'] or o['locale']!=r['locale'] or o['sourceText']!=r['sourceText'] or o['sourceTextSha256']!=r['sourceTextSha256'] or o['currentTarget']!=r['currentTarget'] or o['currentTargetSha256']!=r['currentTargetSha256'] or o['callerContextSha256']!=r['callerContextSha256']:raise SystemExit('FAIL source/current/context binding')
  cp=d/'caller-context.jsonl';contexts={r['sourceKey']:r for r in jl(cp)}
  for o in L:
   if o['decision']=='hold-hash-only':continue
   c=contexts.get(o['sourceKey'])
   if not c or c['callerContextSha256']!=o['callerContextSha256']:raise SystemExit('FAIL caller-context hash')
  print('candidate-free rows and caller-context hashes PASS')
 else:print('candidate-free binding NOT CHECKED')
 print('primary packet PASS: 600 cells, '+str(len(P))+' proposals, 48 text-free hash-only holds')
if __name__=='__main__':main()
