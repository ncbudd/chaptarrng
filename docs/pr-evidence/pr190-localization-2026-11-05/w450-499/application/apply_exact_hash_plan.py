#!/usr/bin/env python3
"""Apply only root-adjudicated exact-hash ChaptarrNG W450-W499 values."""
import argparse,collections,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
PH=re.compile(r'\{[^{}]+\}')
MARKUP=re.compile(r'</?[^>]+>')
INLINE=re.compile(r'`[^`]*`')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
def sha(b):return hashlib.sha256(b).hexdigest()
def sth(s):return sha(s.encode('utf-8'))
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def fail(s):raise SystemExit('FAIL: '+s)
def main():
 a=argparse.ArgumentParser();a.add_argument('--repo',type=Path,required=True);a.add_argument('--plan',type=Path,required=True);a.add_argument('--action-output',type=Path,required=True);args=a.parse_args()
 repo=args.repo.resolve();plan=json.loads(args.plan.read_text(encoding='utf-8'))
 if plan['sourcePin']!={'head':HEAD,'tree':TREE}:fail('plan source pin mismatch')
 if git(repo,'rev-parse','HEAD')!=HEAD or git(repo,'rev-parse','HEAD^{tree}')!=TREE:fail('worktree is not exact source head/tree')
 if plan['candidateCellCount']!=600 or plan['callerBoundCellCount']!=552 or plan['hashOnlyHolds']!=48 or len(plan['changes'])!=111:fail('review dimensions mismatch')
 by_path=collections.defaultdict(list);seen=set()
 for c in plan['changes']:
  cid=c['cellId'];loc=c['locale'];key=c['sourceKey'];target=c['finalTarget']
  if cid in seen:fail('duplicate change '+cid)
  seen.add(cid)
  if loc=='en' or not c['catalogPath'].startswith('src/NzbDrone.Core/Localization/Core/') or c['catalogPath'].startswith('/'):fail('target outside direct locale catalogs '+cid)
  if sth(target)!=c['finalTargetSha256'] or target==c['expectedCurrentTarget']:fail('selected target hash/no-op mismatch '+cid)
  if c['tokenChecks']['placeholders'] is not True or c['tokenChecks']['markup'] is not True or c['tokenChecks']['inlineCode'] is not True or c['tokenChecks']['protectedLiterals'] is not True:fail('non-numeric token check failed '+cid)
  exc=c['manualLexicalizedNumericException']
  if exc:
   expected='8進数' if loc=='ja' else '8진수' if loc=='ko' else None
   if (c['sourceOrdinal'],loc) not in {(471,'ja'),(471,'ko')} or exc!=expected or exc not in target:fail('invalid lexicalized numeric exception '+cid)
  elif c['tokenChecks']['numeric'] is not True:fail('numeric token check failed '+cid)
  if collections.Counter(PH.findall(c['sourceText']))!=collections.Counter(PH.findall(target)):fail('placeholder mismatch '+cid)
  if collections.Counter(MARKUP.findall(c['sourceText']))!=collections.Counter(MARKUP.findall(target)):fail('markup mismatch '+cid)
  if collections.Counter(INLINE.findall(c['sourceText']))!=collections.Counter(INLINE.findall(target)):fail('inline-code mismatch '+cid)
  if not exc and collections.Counter(NUM.findall(c['sourceText']))!=collections.Counter(NUM.findall(target)):fail('numeric mismatch '+cid)
  by_path[c['catalogPath']].append(c)
 if len(by_path)!=12:fail('all 12 locale catalogs must be touched')
 catalog_data={};catalog_before={};catalog_key_order={};catalog_base={}
 for m in plan['catalogs']:
  path=m['path'];raw=(repo/path).read_bytes()
  data=json.loads(raw);keys=list(data)
  if len(keys)!=m['keyCount']:fail('catalog key count mismatch '+path)
  orderhash=sha((json.dumps(keys,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
  if orderhash!=m['keyOrderSha256']:fail('catalog order hash mismatch '+path)
  if raw!=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode():fail('catalog serialization mismatch '+path)
  base_raw=subprocess.check_output(['git','-C',str(repo),'show',f'HEAD:{path}'])
  if sha(base_raw)!=m['sha256']:fail('pinned catalog preimage hash mismatch '+path)
  base_data=json.loads(base_raw)
  if list(base_data)!=keys:fail('catalog structure differs from pinned HEAD '+path)
  catalog_data[path]=data;catalog_before[path]=base_raw;catalog_key_order[path]=keys;catalog_base[path]=base_data
 expected_paths=set(by_path)
 raw_status=subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).splitlines()
 status_paths={line[3:] for line in raw_status if len(line)>=4}
 if status_paths and not status_paths.issubset(expected_paths):fail('worktree contains unrelated changes: '+repr(sorted(status_paths-expected_paths)))
 for path,items in by_path.items():
  data=catalog_data[path]
  for c in items:
   key=c['sourceKey']
   if key not in data:fail('missing locale key '+c['cellId'])
   current=data[key]
   if current not in (c['expectedCurrentTarget'],c['finalTarget']):fail('current target mismatch '+c['cellId'])
   if sth(current) not in (c['expectedCurrentTargetSha256'],c['finalTargetSha256']):fail('current target hash mismatch '+c['cellId'])
   if current!=catalog_base[path][key] and current!=c['finalTarget']:fail('unexpected preexisting target change '+c['cellId'])
   data[key]=c['finalTarget']
  target_keys={c['sourceKey'] for c in items}
  for key in data:
   if key not in target_keys and data[key]!=catalog_base[path][key]:fail('non-target value changed before apply '+path+'/'+key)
  if list(data)!=catalog_key_order[path]:fail('key order changed '+path)
 for path,items in by_path.items():
  output=(json.dumps(catalog_data[path],ensure_ascii=False,indent=2)+'\n').encode()
  tmp=None
  try:
   with tempfile.NamedTemporaryFile(prefix='.w450-499-',suffix='.tmp',dir=(repo/path).parent,delete=False) as f:
    f.write(output);f.flush();os.fsync(f.fileno());tmp=f.name
   os.replace(tmp,repo/path)
  finally:
   if tmp and os.path.exists(tmp):os.unlink(tmp)
  if sha((repo/path).read_bytes())!=sha(output):fail('postimage write mismatch '+path)
 expected_paths=set(by_path)
 changed=set(git(repo,'diff','--name-only').splitlines())
 status_raw=subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).splitlines()
 status={line[3:] for line in status_raw if len(line)>=4}
 if changed!=expected_paths or status!=expected_paths:fail('working paths differ from exactly selected catalog files')
 if any(p.startswith('.github/workflows/') for p in changed):fail('workflow changed')
 result={'result':'PASS','sourcePin':plan['sourcePin'],'candidateCells':600,'callerBoundCells':552,'hashOnlyHolds':48,'selectedChanges':111,'changedCatalogCount':len(expected_paths),'changedPaths':sorted(expected_paths),'changedByLocale':plan['changedByLocale'],'catalogs':[],'hooks':{'preCommit':'not run because the local hook launches Semgrep outside private ephemeral JIT','prePush':'not run because the local hook launches a package test outside private ephemeral JIT'}}
 for m in plan['catalogs']:
  path=m['path'];raw=(repo/path).read_bytes();d=json.loads(raw)
  result['catalogs'].append({'locale':m['locale'],'path':path,'preimageSha256':sha(catalog_before[path]),'postimageSha256':sha(raw),'keyCount':len(d),'keyOrderSha256':sha((json.dumps(list(d),ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()),'changedCellCount':len(by_path.get(path,[]))})
 args.action_output.parent.mkdir(parents=True,exist_ok=True);args.action_output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'result':'PASS','selectedChanges':111,'changedCatalogs':len(expected_paths),'changedPaths':sorted(expected_paths)},ensure_ascii=False))
if __name__=='__main__':main()
