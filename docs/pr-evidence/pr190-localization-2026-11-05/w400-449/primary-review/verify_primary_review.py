#!/usr/bin/env python3
"""Portable verifier for the W400–W449 ChaptarrNG Core primary review."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent; INPUT=HERE.parent/'candidate-free'/'input'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def readj(path):return json.loads(path.read_text())
def readjl(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def require(ok,msg):
 if not ok: raise SystemExit('FAIL: '+msg)
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def verify_repo(repo):
 att=readj(INPUT/'PR-attestation.json')
 require(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==att['headSha'],'exact PR head')
 require(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD^{tree}'],text=True).strip()==att['headTree'],'exact PR tree')
 require(subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).strip()=='','exact-head worktree clean')
def main():
 # Recheck the candidate-free input seal first.
 cf_sums={}
 for line in (INPUT/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);cf_sums[n]=h
 cf_actual={p.relative_to(INPUT).as_posix():sha(p.read_bytes()) for p in INPUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(cf_sums==cf_actual,'candidate-free input checksums')
 sums={}
 for line in (HERE/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);sums[n]=h
 actual={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(sums==actual,'primary-review SHA256SUMS')
 summary=readj(HERE/'primary-review-summary.json'); att=readj(INPUT/'PR-attestation.json')
 require(summary['exactHead']==att['headSha'] and summary['exactTree']==att['headTree'],'head/tree pins')
 require(summary['candidateFreeCellsSha256']==sha((INPUT/'candidate-free-cells.jsonl').read_bytes()),'candidate-free row seal')
 require(summary['candidateFreeManifestSha256']==sha((INPUT/'candidate-free-manifest.json').read_bytes()),'candidate-free manifest seal')
 require(summary['candidateFreeSumsSha256']==sha((INPUT/'SHA256SUMS.txt').read_bytes()),'candidate-free checksums seal')
 candidates=readjl(INPUT/'candidate-free-cells.jsonl'); contexts={r['sourceKey']:r for r in readjl(INPUT/'caller-context.jsonl')}
 rows=readjl(HERE/'primary-review-cells.jsonl'); proposals=readjl(HERE/'primary-review-proposals.jsonl'); holds=readjl(HERE/'primary-review-holds.jsonl')
 require(len(candidates)==len(rows)==600,'review row count')
 require([(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in rows]==[(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in candidates],'review identity/order')
 cf={(r['sourceKey'],r['locale']):r for r in candidates}; reviewed={(r['sourceKey'],r['locale']):r for r in rows}
 require(len(reviewed)==600,'review identity uniqueness')
 proposal_map={(r['sourceKey'],r['locale']):r for r in proposals}; hold_map={(r['sourceKey'],r['locale']):r for r in holds}
 for r in rows:
  ident=(r['sourceKey'],r['locale']); c=cf[ident]; ctx=contexts[r['sourceKey']]
  require(r['exactHead']==att['headSha'] and r['exactTree']==att['headTree'] and r['liveMainSha']==att['liveMainSha'],'review head '+r['cellId'])
  require(r['candidateFreeRowSha256']==sha(canon(c)),'candidate-free row hash '+r['cellId'])
  require(r['sourceTextSha256']==c['sourceTextSha256'] and r['currentTargetSha256']==c['currentTargetSha256'],'source/target hash '+r['cellId'])
  require(r['callerContextSha256']==c['callerContextSha256']==ctx['callerContextSha256'],'caller hash '+r['cellId'])
  require(r['literalCallCount']==c['literalCallCount'],'literal caller count '+r['cellId'])
  d=r['primaryDisposition']
  if d=='hold-hash-only':
   require(r['sourceKey']=='CatalogNumber' and ctx['literalCallCount']==0,'hash-only callerless key '+r['cellId'])
   require('sourceText' not in r and 'currentTarget' not in r,'hash-only hold contains no source/target text '+r['cellId'])
   require(r['recommendedTarget'] is None and r['recommendedTargetSha256'] is None and r['finalReviewedTarget'] is None and r['finalReviewedTargetSha256'] is None,'hash-only hold selected no text '+r['cellId'])
  elif d in ('accept-current','revise-current'):
   require(r['sourceText']==c['sourceText'] and r['currentTarget']==c['currentTarget'],'review text matches candidate-free '+r['cellId'])
   target=r['currentTarget'] if d=='accept-current' else r['recommendedTarget']
   require(isinstance(target,str) and r['finalReviewedTarget']==target and r['finalReviewedTargetSha256']==shat(target),'final target hash '+r['cellId'])
   if d=='accept-current': require(r['recommendedTarget'] is None,'accept row has no proposal '+r['cellId'])
   else: require(r['recommendedTargetSha256']==shat(target),'proposal target hash '+r['cellId'])
   source=r['sourceText']
   require(collections.Counter(PH.findall(source))==collections.Counter(PH.findall(target)),'placeholder parity '+r['cellId'])
   require(INLINE.findall(source)==INLINE.findall(target),'inline-code parity '+r['cellId'])
   require(MARKUP.findall(source)==MARKUP.findall(target),'markup parity '+r['cellId'])
   require(collections.Counter(NUM.findall(source))==collections.Counter(NUM.findall(target)),'numeric parity '+r['cellId'])
   require(all(t in target for t in protected(source)),'protected literal parity '+r['cellId'])
  else: raise SystemExit('FAIL: unknown disposition '+d)
 require(set(proposal_map)=={i for i,r in reviewed.items() if r['primaryDisposition']=='revise-current'},'proposal ledger linkage')
 require(set(hold_map)=={i for i,r in reviewed.items() if r['primaryDisposition']=='hold-hash-only'},'hold ledger linkage')
 for ident,p in proposal_map.items():
  r=reviewed[ident]; require(p['recommendedTarget']==r['recommendedTarget'] and p['recommendedTargetSha256']==r['recommendedTargetSha256'],'proposal row link '+r['cellId'])
 for ident,h in hold_map.items():
  r=reviewed[ident]; require(h['currentTargetSha256']==r['currentTargetSha256'] and h['sourceTextSha256']==r['sourceTextSha256'],'hold hash linkage '+r['cellId'])
  require('sourceText' not in h and 'currentTarget' not in h and not h['sourceTextIncluded'] and not h['currentTargetIncluded'],'hash-only hold ledger text boundary '+r['cellId'])
 counts=collections.Counter(r['primaryDisposition'] for r in rows)
 require(counts==collections.Counter({'accept-current':summary['counts']['accept-current'],'revise-current':summary['counts']['revise-current'],'hold-hash-only':summary['counts']['hold-hash-only']}),'summary disposition counts')
 require(counts==collections.Counter({'accept-current':513,'revise-current':75,'hold-hash-only':12}),'expected reviewed cell counts')
 ex=readj(HERE/'review-process-exposure.json')
 require(ex['reviewerRole']=='primary' and ex['currentWindowBlindOrCrossOutputsAccessed'] is False and ex['applicationPerformed'] is False and ex['nativeSpeakerReviewPerformed'] is False,'exposure / application record')
 require(summary['nativeSpeakerApproval'] is False and summary['currentWindowBlindOrCrossOutputsAccessed'] is False and summary['applicationPerformed'] is False,'summary scope')
 parser=argparse.ArgumentParser();parser.add_argument('--repo');args=parser.parse_args()
 if args.repo: verify_repo(Path(args.repo))
 print(json.dumps({'result':'PASS','head':summary['exactHead'],'tree':summary['exactTree'],'cells':600,'acceptCurrent':counts['accept-current'],'proposedRevisions':counts['revise-current'],'hashOnlyHolds':counts['hold-hash-only'],'proposalCount':len(proposals),'candidateFreeSeal':summary['candidateFreeSumsSha256'],'blindOrCrossOutputsAccessed':False,'applicationPerformed':False,'nativeSpeakerApproval':False},indent=2))
if __name__=='__main__':main()
