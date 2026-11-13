#!/usr/bin/env python3
"""Exact 600-cell W450-W499 readback after the locale catalog commit."""
import argparse,collections,hashlib,json,subprocess
from pathlib import Path
BASE_HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
BASE_TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
def sha(b):return hashlib.sha256(b).hexdigest()
def sth(s):return sha(s.encode('utf-8'))
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def readjl(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def readjl_hash(path):return [(json.loads(x),sha(x.encode('utf-8'))) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def fail(msg):raise SystemExit('FAIL: '+msg)
def main():
 a=argparse.ArgumentParser();a.add_argument('--repo',type=Path,required=True);a.add_argument('--plan',type=Path,required=True);a.add_argument('--candidate-free',type=Path,required=True);a.add_argument('--readback',type=Path,required=True);a.add_argument('--summary',type=Path,required=True);args=a.parse_args()
 repo=args.repo.resolve();plan=json.loads(args.plan.read_text(encoding='utf-8'))
 head=git(repo,'rev-parse','HEAD').decode().strip();tree=git(repo,'rev-parse','HEAD^{tree}').decode().strip();parent=git(repo,'rev-parse','HEAD^').decode().strip()
 if parent!=BASE_HEAD:fail('product commit parent differs from exact review head')
 if git(repo,'rev-parse',f'{BASE_HEAD}^{{tree}}').decode().strip()!=BASE_TREE:fail('source pin/tree mismatch')
 if plan['sourcePin']!={'head':BASE_HEAD,'tree':BASE_TREE}:fail('plan source pin mismatch')
 diff=set(git(repo,'diff-tree','--no-commit-id','--name-only','-r','HEAD').decode().splitlines())
 changes={c['cellId']:c for c in plan['changes']}; expected_paths={c['catalogPath'] for c in plan['changes']}
 if len(changes)!=111 or diff!=expected_paths or len(expected_paths)!=12:fail('product commit paths/count differ from the 111-cell plan')
 if any(p.startswith('.github/workflows/') for p in diff):fail('workflow path changed')
 candidate_rows=readjl_hash(args.candidate_free/'candidate-free-cells.jsonl')
 candidates=[c for c,h in candidate_rows]
 by={(c['sourceKey'],c['locale']):(c,h) for c,h in candidate_rows}
 if len(by)!=600 or len(candidates)!=600:fail('candidate-free row coverage is not 600')
 plan_by={(c['sourceKey'],c['locale']):c for c in plan['changes']}
 if len(plan_by)!=111:fail('duplicate plan keys')
 catalog_base={};catalog_after={};catalog_info=[]
 for m in plan['catalogs']:
  path=m['path'];base_raw=git(repo,'show',f'{BASE_HEAD}:{path}');after_raw=(repo/path).read_bytes()
  if sha(base_raw)!=m['sha256']:fail('base catalog blob differs from candidate-free pin '+path)
  base=json.loads(base_raw);after=json.loads(after_raw)
  if len(base)!=m['keyCount'] or len(after)!=m['keyCount']:fail('catalog key count changed '+path)
  if list(base)!=list(after):fail('catalog order or key set changed '+path)
  orderhash=sha((json.dumps(list(after),ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
  if orderhash!=m['keyOrderSha256']:fail('catalog key order hash differs '+path)
  if after_raw!=(json.dumps(after,ensure_ascii=False,indent=2)+'\n').encode():fail('catalog JSON serialization differs '+path)
  target_keys={c['sourceKey'] for c in plan['changes'] if c['catalogPath']==path}
  for key in base:
   if key not in target_keys and base[key]!=after[key]:fail('non-target locale value changed '+path+'/'+key)
  catalog_base[path]=base;catalog_after[path]=after
  catalog_info.append({'locale':m['locale'],'path':path,'baseSha256':sha(base_raw),'postSha256':sha(after_raw),'keyCount':len(after),'keyOrderSha256':orderhash,'changedCellCount':len(target_keys)})
 # English is fallback and remains byte-identical.
 en=next(m for m in plan['catalogs'] if m['locale']=='en')
 if sha((repo/en['path']).read_bytes())!=en['sha256'] or git(repo,'show',f'HEAD:{en["path"]}')!=git(repo,'show',f'{BASE_HEAD}:{en["path"]}'):fail('English source catalog changed')
 hold_rows={r['candidateFreeRowSha256'] for r in readjl(args.plan.resolve().parent.parent/'cross-review-sealed/holds.jsonl')}
 readback=[];changed=0;retained=0;holds=0
 for (key,locale),(c,cell_hash) in sorted(by.items(),key=lambda kv:(kv[1][0]['sourceOrdinal'],kv[0][1])):
  cid=key+'::'+locale;selection=plan_by.get((key,locale));path=c['targetFile'];live=catalog_after[path][key]
  if selection:
   expected=selection['finalTarget'];expected_sha=selection['finalTargetSha256'];disp='accept-cross-recommendation'
   if live!=expected or sth(live)!=expected_sha:fail('selected target readback mismatch '+cid)
  elif cell_hash in hold_rows:
   expected_sha=c['currentTargetSha256'];disp='hold-hash-only';holds+=1
   if sth(live)!=expected_sha:fail('held target hash mismatch '+cid)
  else:
   expected_sha=c['currentTargetSha256'];disp='accept-current'
   if c.get('currentTarget') is not None and live!=c['currentTarget']:fail('retained current value changed '+cid)
   retained+=1
   if sth(live)!=expected_sha:fail('retained target hash mismatch '+cid)
  was_changed=bool(selection)
  changed+=was_changed
  readback.append({'sourceOrdinal':c['sourceOrdinal'],'locale':locale,'sourceKey':key,'sourceTextSha256':c['sourceTextSha256'],'callerContextSha256':c['callerContextSha256'],'beforeTargetSha256':c['currentTargetSha256'],'expectedAfterSha256':expected_sha,'observedAfterSha256':sth(live),'changed':was_changed,'rootDisposition':disp,'targetTextIncluded':False})
 if changed!=111 or retained!=441 or holds!=48:fail(f'cell disposition totals differ: changed={changed} retained={retained} holds={holds}')
 if len(set((r['sourceOrdinal'],r['locale']) for r in readback))!=600:fail('duplicate readback cell')
 status_lines=git(repo,'status','--porcelain=v1').decode().splitlines()
 status_paths={line[3:] for line in status_lines if len(line)>=4}
 evidence_root=args.plan.resolve().parent.parent.relative_to(repo).as_posix()
 if any(path!=evidence_root and not path.startswith(evidence_root+'/') for path in status_paths):fail('worktree has changes outside this evidence packet')
 args.readback.parent.mkdir(parents=True,exist_ok=True)
 payload=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in readback)
 args.readback.write_text(payload,encoding='utf-8')
 summary={'result':'PASS','productCommit':head,'productTree':tree,'parentHead':parent,'sourceTree':BASE_TREE,'sourceCellCount':600,'callerBoundCellCount':552,'callerlessHashOnlyHolds':48,'selectedChanges':111,'retainedCurrent':441,'changedCellCount':changed,'changedCatalogCount':12,'workflowChanges':0,'allNonTargetLocaleValuesPreserved':True,'catalogs':catalog_info,'readbackSha256':sha(args.readback.read_bytes()),'EnglishFallbackUnchanged':True,'nativeSpeakerApproval':False,'browserAcceptance':False}
 args.summary.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
