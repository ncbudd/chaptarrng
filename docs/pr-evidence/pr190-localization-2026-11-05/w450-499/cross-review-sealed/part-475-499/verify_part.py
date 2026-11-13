#!/usr/bin/env python3
"""Verify the sealed Chaptarr W475-W499 cross-review part."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
R=Path(__file__).resolve().parent; TASK=R.parents[1]
CF=TASK/'candidate-free/input'; P=TASK/'primary-review'; B=TASK/'blind-review'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'; TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'; BASE_TREE='3c27ce1d128d1d74d3b46bf507e2f99f9c02f4d8'
BRANCH='codex/chaptarrng-localization-complete-20261031'; START,END=475,499; HELD_POS={481,482}
LOCS=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
FORBIDDEN={'sourceKey','sourceText','currentTarget','target','recommendedTarget','proposedTarget','translation','finalTarget'}
def sha(x):
 if isinstance(x,str): x=x.encode('utf-8')
 return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def require(ok,msg):
 if not ok: raise SystemExit('FAIL: '+msg)
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def readjlraw(path):
 rows=[]; hs=[]
 for line in path.read_bytes().splitlines(keepends=True):
  if line.strip(): rows.append(json.loads(line)); hs.append(sha(line[:-1] if line.endswith(b'\n') else line))
 return rows,hs
def jl(path): return readjlraw(path)[0]
def packet_sums(path):
 expected={}
 for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  if line.strip():
   h,n=line.split('  ',1); require(n not in expected,'duplicate checksum '+n); expected[n]=h
 actual={p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(expected==actual,'checksum/file set '+str(path)); return expected
def signatures(s):
 ph=re.findall(r'\{[^{}]+\}',s); inline=re.findall(r'`([^`]+)`',s); markup=re.findall(r'<[^>]+>',s)
 num=collections.Counter(re.findall(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])',s))
 protected=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
 brands={'Chaptarr','ChaptarrNG','AudioBookShelf'}
 prot=sorted(set(protected.findall(s))|(brands&set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
 return {'placeholders':dict(sorted(collections.Counter(ph).items())),'inlineCode':inline,'markup':markup,'numeric':dict(sorted(num.items())),'protectedLiterals':prot}
def parse_refs(path):
 out={}
 for line in path.read_text().splitlines():
  h,ref=line.split('\t'); out[ref]=h
 return out
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path); args=ap.parse_args()
 outfiles=packet_sums(R); cf_sums=packet_sums(CF); p_sums=packet_sums(P); b_sums=packet_sums(B)
 m=j(R/'manifest.json'); sm=j(R/'summary.json')
 require(m['exactHead']==HEAD and m['exactTree']==TREE and m['baseSha']==BASE and m['baseTree']==BASE_TREE and m['branch']==BRANCH,'manifest pins')
 pins=m['inputPackets']
 for name,path,sums in [('candidate-free',CF,cf_sums),('primary',P,p_sums),('blind',B,b_sums)]:
  require(pins[name]['filesSha256']==sums and pins[name]['checksumListSha256']==sha((path/'SHA256SUMS.txt').read_bytes()),'input packet pin '+name)
  mp=path/('candidate-free-manifest.json' if name=='candidate-free' else 'manifest.json')
  require(pins[name]['manifestSha256']==sha(mp.read_bytes()),'input manifest pin '+name)
 cm=j(CF/'candidate-free-manifest.json'); pm=j(P/'manifest.json'); bm=j(B/'manifest.json')
 require(cm['head']==HEAD and cm['tree']==TREE and cm['apiBase']==BASE and cm['apiBaseTree']==BASE_TREE,'candidate-free refs')
 require(pm['exactHead']==HEAD and pm['exactTree']==TREE and bm['exactHead']==HEAD and bm['exactTree']==TREE,'reviewer refs')
 cfs,cfhash=readjlraw(CF/'candidate-free-cells.jsonl')
 p_all=jl(P/'ledger.jsonl'); b_all=jl(B/'ledger.jsonl'); pp=jl(P/'proposals.jsonl'); bp=jl(B/'proposals.jsonl')
 pheld=jl(P/'holds.jsonl'); bheld=jl(B/'holds.jsonl')
 psmap={x['candidateFreeRowSha256']:x for x in pheld}; bsmap={x['candidateFreeRowSha256']:x for x in bheld}
 pmap={(x['sourceOrdinal'],x['locale']):x for x in p_all if 'sourceOrdinal' in x}
 bmap={(x['sourceOrdinal'],x['locale']):x for x in b_all}
 ppmap={(x['sourceOrdinal'],x['locale']):x for x in pp}; bpmap={(x['sourceOrdinal'],x['locale']):x for x in bp}
 rows=jl(R/'ledger.jsonl'); rowhashes=[]
 holds,holdhashes=readjlraw(R/'holds.jsonl'); proposals=jl(R/'proposals.jsonl')
 require(len(cfs)==600 and len(p_all)==600 and len(b_all)==600,'full source/review inputs')
 expected={(pos,loc) for pos in range(START,END+1) for loc in LOCS}
 cand={(x['sourceOrdinal'],x['locale']): (x,h) for x,h in zip(cfs,cfhash)}
 sel={k:v for k,v in cand.items() if k[0]>=START and k[0]<=END}
 require(set(sel)==expected and len(sel)==300,'slice candidate-free coverage')
 ledger={(x['sourceOrdinal'],x['locale']):x for x in rows}; hmap={(x['sourceOrdinal'],x['locale']):x for x in holds}
 require(len(ledger)==276 and len(hmap)==24 and len(set(ledger)&set(hmap))==0,'part rows/holds dimensions')
 require(set(ledger)|set(hmap)==expected,'part covers all 300 cells')
 require(all(not (FORBIDDEN&set(x)) for x in holds),'hash-only hold text leak')
 # All reviewer proposal rows in this slice must be reconciled to a final proposal.
 psel={k:x for k,x in ppmap.items() if START<=k[0]<=END and k[0] not in HELD_POS}
 bsel={k:x for k,x in bpmap.items() if START<=k[0]<=END and k[0] not in HELD_POS}
 changed={(x['sourceOrdinal'],x['locale']):x for x in proposals}
 require(len(psel)==44 and len(bsel)==42 and len(set(psel)|set(bsel))==61,'input proposal coverage')
 require(len(changed)==61 and len(proposals)==61,'final proposal count')
 counts={}; token_mismatch=0
 for key,(c,h) in sel.items():
  pos,loc=key
  if key in hmap:
   x=hmap[key]; ph=psmap.get(h); bh=bsmap.get(h); blind=bmap[key]
   require(pos in HELD_POS and not c['callerReferenceCount'],'held caller mapping')
   require(ph is not None and bh is not None,'both reviewer hash-only holds '+str(key))
   require(ph['candidateFreeRowSha256']==bh['candidateFreeRowSha256']==blind['candidateFreeRowSha256']==h,'hold candidate row hash '+str(key))
   require(ph['currentTargetSha256']==bh['currentTargetSha256']==blind['currentTargetSha256']==c['currentTargetSha256'],'hold current target hash '+str(key))
   require(ph['callerContextSha256']==bh['callerContextSha256']==blind['callerContextSha256']==c['callerContextSha256'],'hold caller hash '+str(key))
   require(x['candidateFreeRowSha256']==h and x['currentTargetSha256']==c['currentTargetSha256'] and x['callerContextSha256']==c['callerContextSha256'],'cross hold pins '+str(key))
   require(x['sourceKeySha256']==sha(c['sourceKey']) and x['sourceTextSha256']==c['sourceTextSha256'],'cross hold source hashes '+str(key))
   require(x['exactHead']==HEAD and x['exactTree']==TREE and not (FORBIDDEN&set(x)),'cross hold text-free exact pin '+str(key))
   require(not (key in psel or key in bsel or key in changed),'proposal on hold '+str(key))
   continue
  require(key in ledger,'missing caller-bound row '+str(key))
  x=ledger[key]; p=pmap[key]; b=bmap[key]
  require(bool(c['callerReferenceCount']) and pos not in HELD_POS,'caller-bound selection '+str(key))
  require(x['candidateFreeRowSha256']==h and p['candidateFreeRowSha256']==b['candidateFreeRowSha256']==h,'candidate row binding '+str(key))
  require(x['sourceKey']==c['sourceKey'] and x['sourceKeySha256']==sha(c['sourceKey']),'source key binding '+str(key))
  require(x['sourceText']==c['sourceText'] and x['sourceTextSha256']==c['sourceTextSha256']==p['sourceTextSha256']==b['sourceTextSha256'],'source text binding '+str(key))
  require(x['currentTarget']==c['currentTarget'] and x['currentTargetSha256']==c['currentTargetSha256']==p['currentTargetSha256']==b['currentTargetSha256'],'current target binding '+str(key))
  require(x['callerContextSha256']==c['callerContextSha256']==p['callerContextSha256']==b['callerContextSha256'],'caller context binding '+str(key))
  require(x['primaryDecision']==p['decision'] and x['blindDecision']==b['decision'],'review decisions '+str(key))
  require(x['exactHead']==HEAD and x['exactTree']==TREE,'cross exact ref '+str(key))
  for origin,source,prop in [('primary',ppmap,p),('blind',bpmap,b)]:
   candidate=source.get(key); bound=x[origin+'Proposal']
   if candidate is None: require(bound is None,'unexpected attached '+origin+' proposal '+str(key))
   else:
    require(bound is not None,'missing attached '+origin+' proposal '+str(key))
    target=candidate.get('proposedTarget',candidate.get('recommendedTarget'))
    th=candidate.get('proposedTargetSha256',candidate.get('recommendedTargetSha256'))
    require(bound['target']==target and bound['targetSha256']==th,'attached proposal text/hash '+origin+str(key))
    require(candidate['candidateFreeRowSha256']==h and candidate['currentTargetSha256']==c['currentTargetSha256'] and candidate['callerContextSha256']==c['callerContextSha256'],'proposal pins '+origin+str(key))
  final=x['recommendedTarget']; require(x['recommendedTargetSha256']==sha(final),'final target hash '+str(key))
  sig=signatures(c['sourceText']); fs=signatures(final)
  checks={'placeholders':sig['placeholders']==fs['placeholders'],'inlineCode':sig['inlineCode']==fs['inlineCode'],'markup':sig['markup']==fs['markup'],'numeric':sig['numeric']==fs['numeric'],'protectedLiterals':all(t in final for t in sig['protectedLiterals'])}
  require(x['finalTokenChecks']==checks and all(checks.values()),'final token integrity '+str(key))
  if final!=c['currentTarget']:
   require(key in changed,'changed cell missing proposal '+str(key)); q=changed[key]
   require(q['recommendedTarget']==final and q['recommendedTargetSha256']==sha(final),'final proposal target '+str(key))
   require(q['candidateFreeRowSha256']==h and q['callerContextSha256']==c['callerContextSha256'],'final proposal pins '+str(key))
  else: require(key not in changed,'unchanged proposal '+str(key))
  counts[x['crossDecision']]=counts.get(x['crossDecision'],0)+1
 require(set(changed)=={k for k,x in ledger.items() if x['recommendedTarget']!=x['currentTarget']},'proposal/ledger set')
 require(len(proposals)==61 and len(rows)==276 and len(holds)==24,'final counts')
 require(sm['sourceOrdinalRange']==[START,END] and sm['cellCount']==300 and sm['callerBoundRows']==276 and sm['hashOnlyHolds']==24 and sm['recommendations']==61,'summary dimensions')
 require(sm['crossDecisionCounts']==counts and sm['tokenMismatches']==0,'summary results')
 # Entry/exit snapshots bind PR/base/head and record current main independently.
 at0=j(R/'entry-attestation.json'); at1=j(R/'exit-attestation.json')
 for at,phase in [(at0,'entry'),(at1,'exit')]:
  pr=at['pr']; refs=parse_refs(R/f'{phase}-remote-refs.txt')
  require(pr['state']=='OPEN' and pr['isDraft'] is True and pr['number']==190,'PR state '+phase)
  require(pr['headRefName']==BRANCH and pr['headRefOid']==HEAD and pr['baseRefName']=='main' and pr['baseRefOid']==BASE,'PR API refs '+phase)
  require(at['headTree']==TREE and at['baseTree']==BASE_TREE,'GitHub object tree '+phase)
  require(at['branchRef']==HEAD and at['pullRef']==HEAD and at['localHead']==HEAD and at['localTree']==TREE and at['localClean'] is True,'exact refs/worktree '+phase)
  require(refs[f'refs/heads/{BRANCH}']==HEAD and refs['refs/pull/190/head']==HEAD and refs['refs/heads/main']==at['mainRef'],'remote refs '+phase)
 require(at0['pinTuple']==at1['pinTuple'],'head/base stability')
 require(sm['mainAtEntry']==at0['mainRef'] and sm['mainAtExit']==at1['mainRef'],'main snapshot summary')
 require(sm['mainAdvancedSinceInputSeal']==(at0['mainRef']!=cm['liveMain']),'main drift marker')
 exact=False
 if args.repo:
  repo=args.repo.resolve()
  def git(*cmd): return subprocess.check_output(['git','-C',str(repo),*cmd],text=True).strip()
  require(git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and not git('status','--porcelain=v1'),'exact worktree state')
  for key,(c,h) in sel.items():
   if key in hmap: target_file=c['targetFile']; source_key=c['sourceKey']; target=c['currentTarget']
   else: target_file=c['targetFile']; source_key=c['sourceKey']; target=c['currentTarget']
   raw=(repo/target_file).read_text(encoding='utf-8'); catalog=json.loads(raw)
   require(git('rev-parse',f'HEAD:{target_file}')==c['targetFileGitBlob'],'target catalog blob '+str(key))
   require(catalog[source_key]==target,'exact catalog value '+str(key))
  exact=True
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'range':[START,END],'cells':300,'callerBound':276,'hashOnlyHolds':24,'recommendations':61,'retainedCurrent':215,'crossDecisionCounts':counts,'candidateFreeRowsBound':300,'primaryRowsBound':300,'blindRowsBound':300,'filesChecksummed':len(outfiles),'exactWorktreeReadback':exact},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
