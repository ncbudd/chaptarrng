#!/usr/bin/env python3
"""Apply only root-accepted, hash-pinned ChaptarrNG W350-W399 values."""
import argparse, collections, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path
HEAD='dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0'
TREE='be10d71209076f753ef295038a9f3c3646a918a3'
PH=re.compile(r'\{[^{}]+\}')
MARKUP=re.compile(r'</?[^>]+>')
INLINE=re.compile(r'`[^`]*`')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
def sha(b): return hashlib.sha256(b).hexdigest()
def sth(s): return sha(s.encode('utf-8'))
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def fail(s): raise SystemExit('FAIL: '+s)
def main():
 p=argparse.ArgumentParser(); p.add_argument('--repo',type=Path,required=True); p.add_argument('--plan',type=Path,required=True); p.add_argument('--action-output',type=Path,required=True); a=p.parse_args()
 repo=a.repo.resolve(); plan=json.loads(a.plan.read_text(encoding='utf-8'))
 if plan['sourcePin']!={'head':HEAD,'tree':TREE}: fail('plan exact source pin mismatch')
 if git(repo,'rev-parse','HEAD')!=HEAD or git(repo,'rev-parse','HEAD^{tree}')!=TREE: fail('worktree is not exact PR head/tree')
 if git(repo,'status','--porcelain=v1'): fail('worktree is not clean')
 if len(plan['changes'])!=99 or plan['candidateCellCount']!=600: fail('wrong reviewed application dimensions')
 if plan['crossDecisionCounts']!={'accept-current':488,'recommend-revision':100,'hold-source-copy':12}: fail('cross decision counts mismatch')
 changes={}; by_path=collections.defaultdict(list)
 for c in plan['changes']:
  cid=c['cellId']
  if cid in changes: fail('duplicate change '+cid)
  if sth(c['finalTarget'])!=c['finalTargetSha256']: fail('selected target hash mismatch '+cid)
  if not c['targetFile'].startswith('src/NzbDrone.Core/Localization/Core/') or c['targetFile'].startswith('/'):
   fail('target outside locale catalog '+cid)
  if c['locale']=='en': fail('English fallback must not be edited by this window')
  if c['selectedTargetTokensVerified'] is not True: fail('reviewed selected-target token checks did not pass '+cid)
  if collections.Counter(PH.findall(c['sourceText']))!=collections.Counter(PH.findall(c['finalTarget'])): fail('placeholder mismatch '+cid)
  if collections.Counter(MARKUP.findall(c['sourceText']))!=collections.Counter(MARKUP.findall(c['finalTarget'])): fail('markup mismatch '+cid)
  if collections.Counter(INLINE.findall(c['sourceText']))!=collections.Counter(INLINE.findall(c['finalTarget'])): fail('inline-code mismatch '+cid)
  if collections.Counter(NUM.findall(c['sourceText']))!=collections.Counter(NUM.findall(c['finalTarget'])): fail('numeric-token mismatch '+cid)
  if not all(t in c['finalTarget'] for t in c['protectedLiterals']): fail('protected-literal mismatch '+cid)
  changes[cid]=c; by_path[c['targetFile']].append(c)
 if len(by_path)!=12: fail('expected all 12 direct locale catalogs')
 catalogs={}; before={}; original_keys={}
 for m in plan['catalogs']:
  path=repo/m['path']; raw=path.read_bytes()
  if sha(raw)!=m['preimageSha256']: fail('catalog preimage hash mismatch '+m['path'])
  data=json.loads(raw); keys=list(data)
  if len(keys)!=m['keyCount']: fail('catalog key count mismatch '+m['path'])
  keyhash=sha((json.dumps(keys,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
  if keyhash!=m['keyOrderSha256']: fail('catalog key-order hash mismatch '+m['path'])
  if raw!=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode(): fail('unexpected catalog serialization '+m['path'])
  catalogs[m['path']]=data; before[m['path']]=raw; original_keys[m['path']]=keys
 seen=set()
 for path,items in by_path.items():
  if path not in catalogs: fail('catalog absent from plan '+path)
  data=catalogs[path]
  for c in items:
   cid=c['cellId']; key=c['sourceKey']
   if cid in seen: fail('duplicate cell in path '+cid)
   seen.add(cid)
   if key not in data: fail('missing catalog key '+cid)
   current=data[key]
   if sth(current)!=c['currentTargetSha256'] or current!=c['currentTarget']: fail('current target hash/value mismatch '+cid)
   if current==c['finalTarget']: fail('selected edit is a no-op '+cid)
 if set(changes)!=seen: fail('plan application rows not all bound')
 expected_paths=set(by_path)
 for m in plan['catalogs']:
  path=m['path']; data=catalogs[path]
  for c in by_path.get(path,[]): data[c['sourceKey']]=c['finalTarget']
  if list(data)!=original_keys[path]: fail('catalog key order changed in memory '+path)
  if path not in expected_paths: continue
  output=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
  tmp=None
  try:
   with tempfile.NamedTemporaryFile(prefix='.w350-399-',suffix='.tmp',dir=(repo/path).parent,delete=False) as f:
    f.write(output); f.flush(); os.fsync(f.fileno()); tmp=f.name
   os.replace(tmp,repo/path)
  finally:
   if tmp and os.path.exists(tmp): os.unlink(tmp)
  if sha((repo/path).read_bytes())!=sha(output): fail('postimage write mismatch '+path)
 changed=set(git(repo,'diff','--name-only').splitlines())
 status_text=subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True)
 status={line[3:] for line in status_text.splitlines() if len(line)>=4}
 if changed!=expected_paths or status!=expected_paths: fail('working tree paths do not equal selected locale catalogs')
 action={'result':'PASS','sourcePin':{'head':HEAD,'tree':TREE},'cellCount':600,'selectedChanges':len(changes),'changedCatalogCount':len(expected_paths),'changedPaths':sorted(expected_paths),'rootDispositionCounts':{'accept-current':plan['crossDecisionCounts']['accept-current'],'recommend-revision-selected':plan['rootAcceptedChanges'],'recommend-revision-noop':plan['rootNoopRecommendations'],'hold-source-copy':plan['rootMaintainedSourceCopyHolds']},'catalogs':[],'hooks':{'preCommit':'not run; commit with hooks disabled because the task forbids scans','prePush':'not run; push with hooks disabled because the task forbids scans/tests'}}
 for m in plan['catalogs']:
  path=m['path']; raw=(repo/path).read_bytes(); data=json.loads(raw)
  action['catalogs'].append({'locale':m['locale'],'path':path,'preimageSha256':sha(before[path]),'postimageSha256':sha(raw),'keyCount':len(data),'keyOrderSha256':sha((json.dumps(list(data),ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()),'changedCellCount':len(by_path.get(path,[]))})
 a.action_output.parent.mkdir(parents=True,exist_ok=True); a.action_output.write_text(json.dumps(action,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'result':'PASS','selectedChanges':len(changes),'changedCatalogs':len(expected_paths),'changedPaths':sorted(expected_paths)},ensure_ascii=False))
if __name__=='__main__': main()
