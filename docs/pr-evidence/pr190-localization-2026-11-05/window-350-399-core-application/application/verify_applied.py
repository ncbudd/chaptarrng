#!/usr/bin/env python3
"""Read back the exact 600-cell W350 application at the pinned worktree."""
import argparse, collections, hashlib, json, subprocess
from pathlib import Path
HEAD='dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0'
TREE='be10d71209076f753ef295038a9f3c3646a918a3'
def sha(b): return hashlib.sha256(b).hexdigest()
def sth(s): return sha(s.encode('utf-8'))
def rawgit(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True)
def fail(m): raise SystemExit('FAIL: '+m)
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--candidate-free',type=Path,required=True);p.add_argument('--readback',type=Path,required=True);p.add_argument('--action-output',type=Path,required=True);a=p.parse_args()
 repo=a.repo.resolve(); plan=json.loads(a.plan.read_text(encoding='utf-8')); cand_dir=a.candidate_free.resolve()
 if rawgit(repo,'rev-parse','HEAD').strip()!=HEAD or rawgit(repo,'rev-parse','HEAD^{tree}').strip()!=TREE: fail('source HEAD/tree drift')
 if plan['sourcePin']!={'head':HEAD,'tree':TREE}: fail('plan source pin mismatch')
 candidates=readjl(cand_dir/'candidate-free-cells.jsonl'); by={(x['sourceOrdinal'],x['locale']):x for x in candidates}
 if len(by)!=600: fail('candidate-free row count')
 changes={x['cellId']:x for x in plan['changes']}
 if len(changes)!=99: fail('selected change count')
 paths=set()
 for m in plan['catalogs']:
  pth=m['path'];paths.add(pth);raw=(repo/pth).read_bytes();data=json.loads(raw)
  if len(data)!=m['keyCount']: fail('catalog key count '+pth)
  orderhash=sha((json.dumps(list(data),ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
  if orderhash!=m['keyOrderSha256']: fail('catalog order hash '+pth)
  if raw!=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode(): fail('catalog serialization '+pth)
  base=json.loads(subprocess.check_output(['git','-C',str(repo),'show',f'HEAD:{pth}']))
  if list(base)!=list(data) or set(base)!=set(data): fail('catalog key structure changed '+pth)
  expected_here={x['sourceKey']:x for x in plan['changes'] if x['targetFile']==pth}
  for key in base:
   if key in expected_here:
    if data[key]!=expected_here[key]['finalTarget']: fail('selected value readback mismatch '+pth+'/'+key)
   elif data[key]!=base[key]: fail('non-target catalog value changed '+pth+'/'+key)
 # Reconcile every W350 cell and create full readback.
 readback=[];changed=0
 for ident,c in by.items():
  cid=c['sourceKey']+'::'+c['locale'];final=changes.get(cid)
  expected=final['finalTarget'] if final else c['currentTarget']
  pth=repo/c['targetFile'];live=json.loads(pth.read_text(encoding='utf-8'))[c['sourceKey']]
  if live!=expected or sth(live)!=sth(expected): fail('600-cell readback mismatch '+cid)
  changed+=live!=c['currentTarget']
  readback.append({'sourceOrdinal':c['sourceOrdinal'],'locale':c['locale'],'sourceKey':c['sourceKey'],'sourceTextSha256':c['sourceTextSha256'],'callerContextSha256':c['callerContextSha256'],'beforeTargetSha256':c['currentTargetSha256'],'expectedAfterSha256':sth(expected),'observedAfterSha256':sth(live),'changed':live!=c['currentTarget'],'rootDisposition':final['rootDisposition'] if final else ('maintain-hold' if c['sourceKey']=='BookVisibilityToggleHelpText' else 'accept-current-or-noop')})
 if changed!=99: fail('changed cell count is not 99')
 diff=set(rawgit(repo,'diff','--name-only').splitlines())
 status_lines=subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).splitlines()
 status={line[3:] for line in status_lines if len(line)>=4}
 expected_paths={x['targetFile'] for x in plan['changes']}
 if diff!=expected_paths or status!=expected_paths: fail('working paths differ from exactly selected locale catalogs')
 if any(x.startswith('.github/workflows/') for x in diff): fail('workflow path changed')
 src_hash=sha(subprocess.check_output(['git','-C',str(repo),'show',f'HEAD:src/NzbDrone.Core/Localization/Core/en.json']))
 if src_hash!=json.loads((cand_dir/'catalog-pins.json').read_text())['en']['sha256']: fail('English source catalog changed')
 a.readback.parent.mkdir(parents=True,exist_ok=True)
 a.readback.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in sorted(readback,key=lambda x:(x['sourceOrdinal'],x['locale']))),encoding='utf-8')
 result={'result':'PASS','head':HEAD,'tree':TREE,'candidateCells':len(candidates),'selectedChanges':99,'observedChangedCells':changed,'changedCatalogCount':len(expected_paths),'changedPaths':sorted(expected_paths),'workflowChanges':0,'allNonTargetCatalogValuesPreserved':True,'EnglishSourceUnchanged':True,'rootDecisionCounts':{'accept-current':plan['crossDecisionCounts']['accept-current'],'recommend-revision-selected':plan['rootAcceptedChanges'],'recommend-revision-noop':plan['rootNoopRecommendations'],'hold-source-copy':plan['rootMaintainedSourceCopyHolds']},'readbackSha256':sha(a.readback.read_bytes())}
 a.action_output.parent.mkdir(parents=True,exist_ok=True);a.action_output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
