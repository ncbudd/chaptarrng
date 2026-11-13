#!/usr/bin/env python3
"""Verify the combined ChaptarrNG W450-W499 cross-review packet."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
R=Path(__file__).resolve().parent; TASK=R.parent
CF=TASK/'candidate-free/input'; P=TASK/'primary-review'; B=TASK/'blind-review'
PART_A=R/'part-450-474'; PART_B=R/'part-475-499'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'; TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'; BASE_TREE='3c27ce1d128d1d74d3b46bf507e2f99f9c02f4d8'
BRANCH='codex/chaptarrng-localization-complete-20261031'; START,END=450,499
LOCS=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
HELD={469,474,481,482}
FORBIDDEN={'sourceKey','sourceText','currentTarget','target','recommendedTarget','proposedTarget','translation','finalTarget','reviewedTarget'}
NUM_EXCEPTION={(471,'ja'):'8進数',(471,'ko'):'8진수'}
def sha(x):
 if isinstance(x,str): x=x.encode('utf-8')
 return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def require(ok,msg):
 if not ok: raise SystemExit('FAIL: '+msg)
def readjlraw(path):
 rows=[]; hashes=[]
 for line in path.read_bytes().splitlines(keepends=True):
  if line.strip(): rows.append(json.loads(line)); hashes.append(sha(line[:-1] if line.endswith(b'\n') else line))
 return rows,hashes
def jl(path): return readjlraw(path)[0]
def packet_sums(path):
 expected={}
 for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  if line.strip():
   h,n=line.split('  ',1); require(n not in expected,'duplicate checksum '+n); expected[n]=h
 actual={p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and p!=path/'SHA256SUMS.txt'}
 require(expected==actual,'checksum/file set '+str(path)); return expected
def signatures(s):
 ph=dict(sorted(collections.Counter(re.findall(r'\{[^{}]+\}',s)).items()))
 inline=re.findall(r'`([^`]+)`',s); markup=re.findall(r'<[^>]+>',s)
 nums=dict(sorted(collections.Counter(re.findall(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])',s)).items()))
 protected_re=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
 brands={'Chaptarr','ChaptarrNG','AudioBookShelf'}
 prot=sorted(set(protected_re.findall(s))|(brands&set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
 return {'placeholders':ph,'inlineCode':inline,'markup':markup,'numeric':nums,'protectedLiterals':prot}
def verify_part_inputs_and_parts(repo=None):
 cmd=["python3",str(PART_A/'verify_cross_review.py'),'--candidate-free',str(CF),'--primary',str(P),'--blind',str(B)]
 out=subprocess.check_output(cmd,text=True,cwd=PART_A)
 require('"result": "PASS"' in out,'W450-W474 portable part verifier')
 subprocess.check_call(['python3',str(PART_B/'verify_part.py')],cwd=PART_B)
 if repo:
  subprocess.check_call(['python3',str(PART_B/'verify_part.py'),'--repo',str(repo)],cwd=PART_B)
 return True
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path,help='optional exact pinned worktree readback'); args=ap.parse_args()
 outfiles=packet_sums(R); cfs=packet_sums(CF); ps=packet_sums(P); bs=packet_sums(B)
 part_a_sums=packet_sums(PART_A); part_b_sums=packet_sums(PART_B)
 m=j(R/'manifest.json'); sm=j(R/'summary.json')
 require(m['exactHead']==HEAD and m['exactTree']==TREE and m['baseSha']==BASE and m['baseTree']==BASE_TREE and m['branch']==BRANCH,'manifest refs')
 require(m['sourceOrdinalRange']==[START,END] and m['cellCount']==600 and m['callerBoundCells']==552 and m['hashOnlyHoldCells']==48,'manifest dimensions')
 for name,path,sums,manifest_name in [('candidate-free',CF,cfs,'candidate-free-manifest.json'),('primary',P,ps,'manifest.json'),('blind',B,bs,'manifest.json')]:
  pin=m['inputPackets'][name]
  require(pin['filesSha256']==sums and pin['checksumListSha256']==sha((path/'SHA256SUMS.txt').read_bytes()) and pin['manifestSha256']==sha((path/manifest_name).read_bytes()),'input pin '+name)
 for part,checks in [(PART_A,part_a_sums),(PART_B,part_b_sums)]:
  pin=m['crossReviewParts'][part.name]
  require(pin['sha256SumsFileSha256']==sha((part/'SHA256SUMS.txt').read_bytes()),'part checksum pin '+part.name)
  require(pin['manifestSha256']==sha((part/'manifest.json').read_bytes()) and pin['ledgerSha256']==sha((part/'ledger.jsonl').read_bytes()) and pin['holdSha256']==sha((part/'holds.jsonl').read_bytes()),'part content pin '+part.name)
 cm=j(CF/'candidate-free-manifest.json'); pm=j(P/'manifest.json'); bm=j(B/'manifest.json')
 require(cm['head']==HEAD and cm['tree']==TREE and cm['apiBase']==BASE and cm['apiBaseTree']==BASE_TREE,'candidate-free head/base')
 require(pm['exactHead']==HEAD and pm['exactTree']==TREE and bm['exactHead']==HEAD and bm['exactTree']==TREE,'primary/blind refs')
 # The part verifiers bind every part cell and its checksums; the exact mode additionally checks live catalog blobs below.
 verify_part_inputs_and_parts(args.repo)
 cfc,cfhash=readjlraw(CF/'candidate-free-cells.jsonl')
 cfmap={(x['sourceOrdinal'],x['locale']):(x,h) for x,h in zip(cfc,cfhash)}
 expected={(i,l) for i in range(START,END+1) for l in LOCS}
 require(len(cfmap)==600 and set(cfmap)==expected,'candidate-free 600-cell coverage')
 ledger=jl(R/'ledger.jsonl'); holds=jl(R/'holds.jsonl'); proposals=jl(R/'proposals.jsonl')
 lmap={(x['sourceOrdinal'],x['locale']):x for x in ledger}; hmap={(x['sourceOrdinal'],x['locale']):x for x in holds}; qmap={(x['sourceOrdinal'],x['locale']):x for x in proposals}
 require(len(lmap)==552 and len(hmap)==48 and not(set(lmap)&set(hmap)),'cross rows/holds size')
 require(set(lmap)|set(hmap)==expected,'cross coverage')
 require(len(qmap)==111 and len(proposals)==111,'proposal count')
 require(all(not(FORBIDDEN&set(x)) for x in holds),'hold text leak')
 primary_rows=jl(P/'ledger.jsonl'); primary_holds=jl(P/'holds.jsonl'); blind_rows=jl(B/'ledger.jsonl'); blind_holds=jl(B/'holds.jsonl')
 pmap={(x['sourceOrdinal'],x['locale']):x for x in primary_rows if 'sourceOrdinal' in x}
 bmap={(x['sourceOrdinal'],x['locale']):x for x in blind_rows}
 p_hold_map={x['candidateFreeRowSha256']:x for x in primary_holds}; b_hold_map={x['candidateFreeRowSha256']:x for x in blind_holds}
 pp={(x['sourceOrdinal'],x['locale']):x for x in jl(P/'proposals.jsonl')}
 bp={(x['sourceOrdinal'],x['locale']):x for x in jl(B/'proposals.jsonl')}
 require(len(pmap)==552 and len(bmap)==600 and len(p_hold_map)==len(b_hold_map)==48,'reviewer row dimensions')
 final_counts={}; hold_counts={}; numeric_exceptions=[]
 for key,(c,cfrowhash) in cfmap.items():
  pos,loc=key
  if pos in HELD:
   x=hmap.get(key); require(x is not None and not c['callerReferenceCount'],'callerless cell disposition '+str(key))
   ph=p_hold_map.get(cfrowhash); bh=b_hold_map.get(cfrowhash); br=bmap[key]
   require(ph is not None and bh is not None,'hash-only primary/blind holds '+str(key))
   require(ph['candidateFreeRowSha256']==bh['candidateFreeRowSha256']==br['candidateFreeRowSha256']==cfrowhash,'hold row hash '+str(key))
   require(ph['currentTargetSha256']==bh['currentTargetSha256']==br['currentTargetSha256']==c['currentTargetSha256'],'hold target hash '+str(key))
   require(ph['callerContextSha256']==bh['callerContextSha256']==br['callerContextSha256']==c['callerContextSha256'],'hold caller hash '+str(key))
   require(x['candidateFreeRowSha256']==cfrowhash and x['currentTargetSha256']==c['currentTargetSha256'] and x['callerContextSha256']==c['callerContextSha256'],'combined hold pin '+str(key))
   require(x['sourceTextSha256']==c['sourceTextSha256'] and x['exactHead']==HEAD and x['exactTree']==TREE and x['crossDecision']=='hold-hash-only','combined hash-only hold '+str(key))
   require(key not in pp and key not in bp and key not in qmap,'callerless proposal '+str(key))
   hold_counts[x['crossDecision']]=hold_counts.get(x['crossDecision'],0)+1
   continue
  x=lmap.get(key); require(x is not None and c['callerReferenceCount']>0,'caller-bound row missing '+str(key))
  p=pmap[key]; b=bmap[key]
  require(x['candidateFreeRowSha256']==p['candidateFreeRowSha256']==b['candidateFreeRowSha256']==cfrowhash,'candidate-free row pin '+str(key))
  require(x['sourceKey']==c['sourceKey'] and x['sourceKeySha256']==sha(c['sourceKey']),'source key pin '+str(key))
  require(x['sourceTextSha256']==c['sourceTextSha256']==p['sourceTextSha256']==b['sourceTextSha256'],'source text hash '+str(key))
  require(x['currentTarget']==c['currentTarget'] and x['currentTargetSha256']==c['currentTargetSha256']==p['currentTargetSha256']==b['currentTargetSha256'],'current target pin '+str(key))
  require(x['callerContextSha256']==c['callerContextSha256']==p['callerContextSha256']==b['callerContextSha256'],'caller context hash '+str(key))
  require(x['primaryDecision']==p['decision'] and x['blindDecision']==b['decision'],'review decision binding '+str(key))
  require(x['exactHead']==HEAD and x['exactTree']==TREE,'cross ref '+str(key))
  decision=x['crossDecision']; target=x['recommendedTarget']; require(x['recommendedTargetSha256']==sha(target),'final hash '+str(key))
  if decision=='accept-current': require(target==c['currentTarget'],'accept-current target '+str(key))
  if decision=='accept-primary-proposal': require(key in pp and pp[key].get('proposedTarget')==target,'primary proposal target '+str(key))
  if decision=='accept-blind-proposal': require(key in bp and bp[key].get('recommendedTarget')==target,'blind proposal target '+str(key))
  if decision=='accept-consensus-proposal': require(key in pp and key in bp and pp[key].get('proposedTarget')==bp[key].get('recommendedTarget')==target,'consensus proposal target '+str(key))
  source_sig=signatures(c['sourceText']); final_sig=signatures(target)
  checks={'placeholders':source_sig['placeholders']==final_sig['placeholders'],'inlineCode':source_sig['inlineCode']==final_sig['inlineCode'],'markup':source_sig['markup']==final_sig['markup'],'numeric':source_sig['numeric']==final_sig['numeric'],'protectedLiterals':all(v in target for v in source_sig['protectedLiterals'])}
  if key in NUM_EXCEPTION:
   require(NUM_EXCEPTION[key] in target and checks['numeric'] is False,'expected lexicalized octal exception '+str(key))
   numeric_exceptions.append({'sourceOrdinal':pos,'locale':loc,'target':NUM_EXCEPTION[key]})
  else: require(checks['numeric'],'unexpected numeric token delta '+str(key))
  recorded=x.get('tokenChecks',x.get('finalTokenChecks'))
  require(recorded==checks and all(v for k,v in checks.items() if k!='numeric') and (checks['numeric'] or key in NUM_EXCEPTION),'recorded final token checks '+str(key))
  if target!=c['currentTarget']:
   require(key in qmap,'changed row missing proposal '+str(key))
   q=qmap[key]
   require(q['sourceKey']==c['sourceKey'] and q['candidateFreeRowSha256']==cfrowhash and q['sourceTextSha256']==c['sourceTextSha256'],'proposal source pins '+str(key))
   require(q['currentTarget']==c['currentTarget'] and q['currentTargetSha256']==c['currentTargetSha256'] and q['recommendedTarget']==target and q['recommendedTargetSha256']==sha(target),'proposal target pins '+str(key))
  else: require(key not in qmap,'unchanged row in proposal output '+str(key))
  final_counts[decision]=final_counts.get(decision,0)+1
 require(set(qmap)=={k for k,x in lmap.items() if x['recommendedTarget']!=x['currentTarget']},'proposal/ledger alignment')
 require(final_counts==sm['crossDecisionCounts'] and hold_counts==sm['holdDecisionCounts'],'summary decision totals')
 require(len(numeric_exceptions)==2 and sorted((x['sourceOrdinal'],x['locale']) for x in numeric_exceptions)==sorted(NUM_EXCEPTION),'numeric exception set')
 require(sm['cellCount']==600 and sm['callerBoundCells']==552 and sm['hashOnlyHolds']==48 and sm['changedCellCount']==111 and sm['retainedCurrentCount']==441,'summary counts')
 manual=[{'sourceOrdinal':471,'locale':'ja','target':'8進数','reason':'standard Japanese lexicalized octal term, not a separate source value'},{'sourceOrdinal':471,'locale':'ko','target':'8진수','reason':'standard Korean lexicalized octal term, not a separate source value'}]
 require(sm['manualLexicalizedOctalExceptions']==manual,'manual numeric exception record')
 # Entry/exit record exact PR refs and allow independently advancing main.
 for phase in ['entry','exit']:
  at=j(R/f'{phase}-attestation.json'); refs={}
  for line in (R/f'{phase}-remote-refs.txt').read_text().splitlines():
   h,ref=line.split('\t'); refs[ref]=h
  pr=at['pr']
  require(pr['state']=='OPEN' and pr['isDraft'] is True and pr['headRefOid']==HEAD and pr['baseRefOid']==BASE and pr['headRefName']==BRANCH and pr['baseRefName']=='main','PR API '+phase)
  require(at['headTree']==TREE and at['baseTree']==BASE_TREE,'GitHub tree '+phase)
  require(at['branchRef']==HEAD and at['pullRef']==HEAD and at['localHead']==HEAD and at['localTree']==TREE and at['localClean'] is True,'PR/worktree refs '+phase)
  require(refs[f'refs/heads/{BRANCH}']==HEAD and refs['refs/pull/190/head']==HEAD and refs['refs/heads/main']==at['mainRef'],'remote ref snapshot '+phase)
 require(j(R/'entry-attestation.json')['pinTuple']==j(R/'exit-attestation.json')['pinTuple'],'PR/base/worktree entry/exit stability')
 require(sm['mainAtEntry']==j(R/'entry-attestation.json')['mainRef'] and sm['mainAtExit']==j(R/'exit-attestation.json')['mainRef'],'main snapshots')
 exact=False
 if args.repo:
  repo=args.repo.resolve()
  def git(*cmd): return subprocess.check_output(['git','-C',str(repo),*cmd],text=True).strip()
  require(git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and not git('status','--porcelain=v1'),'exact worktree head/tree/clean')
  catalogs={}; blobs={}
  for c in cfc:
   sf=c['sourceFile']; tf=c['targetFile']
   for f in [sf,tf]:
    if f not in catalogs:
     catalogs[f]=json.loads((repo/f).read_text(encoding='utf-8'))
     blobs[f]=git('rev-parse',f'HEAD:{f}')
   require(blobs[sf]==c['sourceFileGitBlob'] and blobs[tf]==c['targetFileGitBlob'],'catalog Git blob '+str((c['sourceOrdinal'],c['locale'])))
   require(catalogs[sf][c['sourceKey']]==c['sourceText'],'live English source '+str((c['sourceOrdinal'],c['locale'])))
   require(catalogs[tf][c['sourceKey']]==c['currentTarget'],'live target catalog '+str((c['sourceOrdinal'],c['locale'])))
  exact=True
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'base':BASE,'baseTree':BASE_TREE,'cells':600,'callerBound':552,'hashOnlyHolds':48,'changedCells':111,'retainedCurrent':441,'crossDecisionCounts':final_counts,'holdDecisionCounts':hold_counts,'primaryRowsBound':600,'blindRowsBound':600,'numericLexicalExceptions':numeric_exceptions,'checksummedFiles':len(outfiles),'exactWorktreeReadback':exact},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
