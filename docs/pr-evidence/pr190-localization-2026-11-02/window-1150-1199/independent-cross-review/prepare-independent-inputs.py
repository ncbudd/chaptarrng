import collections,datetime,hashlib,json,re,subprocess
from pathlib import Path
OUT=Path('.')
WORK=Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e'; TREE='d073e1373021bf715db37461a12654f7e993cdbf'; BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
SRC='src/NzbDrone.Core/Localization/Core/en.json'; QUEUE='docs/localization/source-followup-20261101.json.json';
QUEUE='docs/localization/source-followup-20261101.json'; REG='docs/localization/server-message-sources.json'; CALLER_INDEX='docs/localization/server-message-callers.json'
sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode('utf8')).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
def run(args):return subprocess.run(args,check=True,capture_output=True).stdout
def git(*args):return run(['git','-C',str(WORK),*args]).decode().strip()
def blob(path):return run(['git','-C',str(WORK),'show',f'{HEAD}:{path}'])
def file_pin(path,b=None):
 if b is None:b=blob(path)
 return {'path':path,'gitBlob':git('rev-parse',f'{HEAD}:{path}'),'sha256':sha(b),'bytes':len(b)}
def writej(path,obj): (OUT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
def writejl(path,rows):
 with open(OUT/path,'w',encoding='utf8') as f:
  for x in rows:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n')
# Exact remote and worktree pin before creating review data.
pr=json.loads(run(['gh','api','repos/snapetech-org/ChaptarrNG/pulls/190']))
branch=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/branches/{BRANCH}']))
commit=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/commits/{HEAD}']))
local={'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'branch':git('branch','--show-current'),'status':git('status','--porcelain')}
assert pr['state']=='open' and pr['draft'] is True and pr['head']['sha']==HEAD
assert branch['commit']['sha']==HEAD and commit['sha']==HEAD and commit['commit']['tree']['sha']==TREE
assert local=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},local
att={'checkedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pr':{'number':pr['number'],'state':pr['state'].upper(),'isDraft':pr['draft'],'head':pr['head']['sha'],'tree':TREE,'headRefName':BRANCH,'url':pr['html_url']},
 'officialRemoteBranch':branch['commit']['sha'],'officialRemoteTree':commit['commit']['tree']['sha'],'localWorktree':local}
writej('start-reattestation.json',att)
# Extract independent source/catalog/caller evidence strictly from the pinned Git object.
follow=json.loads(blob(QUEUE)); source=json.loads(blob(SRC)); reg=json.loads(blob(REG));
queue=follow['currentMissingIds']; assert len(queue)==1210 and sha(canon(queue))==follow['currentMissingIdsSha256']
ids=queue[1150:1200]; assert len(ids)==50 and len(set(ids))==50 and all(x.startswith('server.message.') for x in ids)
records={x['id']:x for x in reg['records']}; assert all(x in records for x in ids)
source_pin=file_pin(SRC); queue_pin=file_pin(QUEUE); reg_pin=file_pin(REG); caller_index_pin=file_pin(CALLER_INDEX)
# Load all target catalog blobs and bind ordered key sets.
catalogs={}; catpins={}
for loc,name in LOCALES.items():
 p=f'src/NzbDrone.Core/Localization/Core/{name}'; b=blob(p); catalogs[loc]=json.loads(b); catpins[loc]=file_pin(p,b)
assert all(set(catalogs[x])==set(source) for x in LOCALES)
assert len(source)==4165
ph=lambda s:collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
markup=lambda s: [] if re.fullmatch(r'<[^<>/]+>',s) else re.findall(r'</?[A-Za-z][^>]*>',s)
icu=lambda s: sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
source_rows=[]; caller_rows=[]; cells=[]; caller_files={}
for pos,sid in enumerate(ids,1150):
 rec=records[sid]; src=source[sid]; assert rec['source']==src
 assert rec['id']==sid
 direct=[]
 for ref in rec['callsites']:
  p=ref['file']; b=blob(p); lines=b.decode('utf8').splitlines(); line=ref['line']; rawline=lines[line-1]; line_text=rawline.strip(); assert line_text==ref['sourceLine']
  lh=sha(line_text); assert lh==ref['sourceLineSha256']
  fp=file_pin(p,b); caller_files[p]=fp
  direct.append({**ref,'lineText':line_text,'lineTextRaw':rawline,'lineSha256':lh,'fileSha256':fp['sha256'],'fileGitBlob':fp['gitBlob'],
   'contextBefore':lines[max(0,line-4):line-1],'contextAfter':lines[line:min(len(lines),line+3)],'registryPinExact':True,'registryLine':line,'registrySourceLineSha256':ref['sourceLineSha256']})
 assert direct
 cx=sha(canon(direct))
 srow={'sourceOrdinal':pos,'sourceId':sid,'source':src,'sourceIdSha256':sha(sid),'sourceTextSha256':sha(src),'sourceRegistryFingerprint':rec['sourceFingerprint'],
  'sourcePatterns':rec['patterns'],'sourceTemplates':rec['sourceTemplates'],'sourceRegistryParameters':rec['parameters'],'protectedLiterals':rec['protectedLiterals'],
  'sourcePlaceholders':dict(sorted(ph(src).items())),'sourceMarkup':markup(src),'sourceIcu':icu(src),'callerCount':len(direct),'callerContextSha256':cx}
 source_rows.append(srow)
 caller_rows.append({'sourceOrdinal':pos,'sourceId':sid,'callerContextSha256':cx,'callerReferenceStatus':'exact','callerReferences':direct})
 for loc,name in LOCALES.items():
  cur=catalogs[loc][sid]; targetpath=f'src/NzbDrone.Core/Localization/Core/{name}'
  cells.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':pos,'sourceId':sid,'source':src,'sourceIdSha256':sha(sid),'sourceTextSha256':sha(src),
   'locale':loc,'currentTarget':cur,'currentTargetSha256':sha(cur),'targetFile':targetpath,'targetFileGitBlob':catpins[loc]['gitBlob'],'targetFileSha256':catpins[loc]['sha256'],
   'sourceFile':SRC,'sourceFileGitBlob':source_pin['gitBlob'],'sourceFileSha256':source_pin['sha256'],
   'callerContextSha256':cx,'callerReferences':direct,'sourceRegistryFingerprint':rec['sourceFingerprint'],'sourceRegistryParameters':rec['parameters'],
   'protectedLiterals':rec['protectedLiterals'],'sourcePlaceholders':dict(sorted(ph(src).items())),'sourceMarkup':markup(src),'sourceIcu':icu(src)})
assert len(cells)==600
writejl('inputs/source-rows.jsonl',source_rows); writejl('inputs/caller-context.jsonl',caller_rows); writejl('inputs/source-cells.jsonl',cells)
selection={'exactHead':HEAD,'exactTree':TREE,'sourceQueue':queue_pin,'queueRecordedSha256':follow['currentMissingIdsSha256'],'queueCanonicalSha256':sha(canon(queue)),
 'window':'W1150-W1199','positions':list(range(1150,1200)),'sourceIds':ids,'sourceCount':50,'localeCount':12,'cellCount':600}
writej('inputs/source-selection.json',selection)
pins={'exactHead':HEAD,'exactTree':TREE,'englishCatalog':source_pin,'sourceQueue':queue_pin,'sourceRegistry':reg_pin,'callerIndex':caller_index_pin,
 'localeCount':12,'keyCount':4165,'keysetParityWithEnglish':True,'localeCatalogs':catpins,'callerFiles':sorted(caller_files.values(),key=lambda x:x['path'])}
writej('inputs/pinned-files.json',pins)
# Pin data separately to use when sealing and independent result comparison.
writej('inputs/selection-and-catalog-pins.json',{'selection':selection,'pins':pins})
print(json.dumps({'head':HEAD,'tree':TREE,'cells':len(cells),'sources':len(source_rows),'callers':sum(x['callerCount'] for x in source_rows),'callerFiles':len(caller_files),'currentProtectedMissing':sum(1 for x in cells for t in x['protectedLiterals'] if t not in x['currentTarget']),
 'inputPins':len(caller_files)+len(catpins)+4},ensure_ascii=False,indent=2))
