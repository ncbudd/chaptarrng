#!/usr/bin/env python3
"""Create the cross-review part for caller-bound Chaptarr W475-W499 cells."""
from __future__ import annotations
import collections, datetime, hashlib, json, re, subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
TASK=OUT.parents[1]
CF=TASK/'candidate-free/input'; P=TASK/'primary-review'; B=TASK/'blind-review'
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned')
REPO_NAME='snapetech-org/chaptarrng'; PR=190; BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'; TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'; BASE_TREE='3c27ce1d128d1d74d3b46bf507e2f99f9c02f4d8'
START,END=475,499; HOLDS={481,482}
LOCS=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']

def sha(x):
 if isinstance(x,str): x=x.encode('utf-8')
 return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writejl(path,rows): path.write_text(''.join(canon(x)+'\n' for x in rows),encoding='utf-8')
def readjlraw(path):
 rows=[]; hashes=[]
 for line in path.read_bytes().splitlines(keepends=True):
  if line.strip(): rows.append(json.loads(line)); hashes.append(sha(line[:-1] if line.endswith(b'\n') else line))
 return rows,hashes
def jl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def packet_file_hashes(path): return {p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
def verify_sums(path):
 expected={}
 for line in (path/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1); expected[name]=digest
 actual=packet_file_hashes(path)
 if expected!=actual: raise RuntimeError('packet checksum mismatch: '+str(path))
 return actual
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def api(endpoint): return json.loads(subprocess.check_output(['gh','api',endpoint],text=True))
def capture(label):
 pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO_NAME,'--json','number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url'],text=True))
 headobj=api(f'repos/{REPO_NAME}/commits/{pr["headRefOid"]}')
 baseobj=api(f'repos/{REPO_NAME}/commits/{pr["baseRefOid"]}')
 mainobj=api(f'repos/{REPO_NAME}/commits/{api(f"repos/{REPO_NAME}/git/ref/heads/main")["object"]["sha"]}')
 refs_text=subprocess.check_output(['git','ls-remote',f'https://github.com/{REPO_NAME}.git',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'],text=True)
 refs={line.split('\t')[1]:line.split('\t')[0] for line in refs_text.splitlines() if line.strip()}
 local_head=git('rev-parse','HEAD'); local_tree=git('rev-parse','HEAD^{tree}'); clean=(git('status','--porcelain=v1')=='')
 head_tree=headobj['commit']['tree']['sha']; base_tree=baseobj['commit']['tree']['sha']; main_ref=refs.get('refs/heads/main'); main_tree=mainobj['commit']['tree']['sha']
 pin=(pr['state'],pr['isDraft'],pr['headRefName'],pr['headRefOid'],head_tree,pr['baseRefName'],pr['baseRefOid'],base_tree,refs.get(f'refs/heads/{BRANCH}'),refs.get(f'refs/pull/{PR}/head'),local_head,local_tree,clean)
 expect=('OPEN',True,BRANCH,HEAD,TREE,'main',BASE,BASE_TREE,HEAD,HEAD,HEAD,TREE,True)
 if pin!=expect: raise RuntimeError(f'PR/head/base/worktree changed at {label}: {pin!r}')
 snap={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'pr':pr,'headTree':head_tree,'baseTree':base_tree,'mainRef':main_ref,'mainTree':main_tree,'branchRef':refs.get(f'refs/heads/{BRANCH}'),'pullRef':refs.get(f'refs/pull/{PR}/head'),'localHead':local_head,'localTree':local_tree,'localClean':clean,'pinTuple':list(pin)}
 dump(OUT/f'{label}-attestation.json',snap); (OUT/f'{label}-remote-refs.txt').write_text(refs_text,encoding='utf-8')
 return snap
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])'); PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
def signatures(s): return {'placeholders':dict(sorted(collections.Counter(PH.findall(s)).items())),'inlineCode':INLINE.findall(s),'markup':MARKUP.findall(s),'numeric':dict(sorted(collections.Counter(NUM.findall(s)).items())),'protectedLiterals':sorted(set(PROTECTED.findall(s))|(BRANDS&set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))}

# Final target wording for all proposed cells in this source slice.
finals={
 (475,'pt-BR'):('Grupo do chown','blind','This is the group-name field for the Unix chown setting. A noun label is clearer than the current action phrasing.'),
 (475,'zh-Hans'):('chown 组','blind','This field supplies the group for the Unix chown operation. The current text says to change group permissions; retain the technical command, consistent with the other locale labels.'),
 (476,'hi'):('समूह का नाम या gid। दूरस्थ फ़ाइल सिस्टम के लिए gid का उपयोग करें।','consensus','The help asks for a group name or the literal Unix identifier gid. Correct the transliteration and preserve gid both times.'),
 (476,'zh-Hant'):('群組名稱或 gid。遠端檔案系統請使用 gid。','primary','The helper names the literal Unix identifier gid; removing spaces before Chinese punctuation improves the sentence without changing the identifier.'),
 (480,'ar'):('انقر لتغيير علامات المفهرس','blind','This interactive-import tooltip changes indexer flags. “علامات المفهرس” reads as UI indicators rather than physical flags.'),
 (480,'fr'):('Cliquez pour modifier les indicateurs de l’indexeur','blind','The tooltip changes indexer flags. “Indicateurs” is clearer UI wording than the literal “drapeaux”.'),
 (480,'hi'):('इंडेक्सर फ़्लैग बदलने के लिए क्लिक करें','blind','The tooltip changes software indexer flags. Keep the recognizable technical term instead of “सूचक झंडे”, which suggests physical flags.'),
 (480,'vi'):('Nhấn để thay đổi cờ của trình lập chỉ mục','primary','The tooltip changes indexer flags. “Trình lập chỉ mục” means indexer; “mục lục” means a table of contents.'),
 (483,'hi'):('डाउनलोड क्लाइंट की प्राथमिकता','primary','The Download Clients form labels the priority of the client application. “ग्राहक” means customer and changes the meaning.'),
 (485,'fr'):('Cloner la condition','blind','This is an icon tooltip action. Use an infinitive action instead of “Condition du clone”, which describes a condition belonging to a clone.'),
 (485,'hi'):('शर्त क्लोन करें','blind','This icon tooltip is an action. The verb phrase is clearer than the current noun stack.'),
 (485,'id'):('Klon kondisi','consensus','This icon tooltip is the action to clone a condition; Indonesian action-first word order is natural.'),
 (486,'hi'):('कस्टम फ़ॉर्मेट क्लोन करें','blind','This icon tooltip is an action. The verb phrase is clearer than the current noun stack.'),
 (486,'id'):('Klon format kustom','consensus','This is an icon tooltip action to clone a custom format; action-first Indonesian word order is clearer.'),
 (487,'ar'):('استنساخ المفهرس','blind','The action clones an indexer configuration. “الفهرس” means the index itself, not the indexer.'),
 (487,'hi'):('इंडेक्सर क्लोन करें','blind','This icon tooltip is an action; the imperative keeps the software term and avoids the current noun stack.'),
 (487,'id'):('Klon pengindeks','consensus','This is the action to clone an indexer; Indonesian action-first word order is clearer.'),
 (488,'hi'):('प्रोफ़ाइल क्लोन करें','blind','This icon tooltip is an action. Use an imperative verb phrase rather than the current noun stack.'),
 (488,'id'):('Klon profil','consensus','This is the action to clone a profile; Indonesian action-first word order is clearer.'),
 (489,'hi'):('बंद करें','consensus','This shared modal button uses the polite Hindi imperative; the current spelling is missing the nasal ending.'),
 (490,'hi'):('समेटें','blind','This toggles an expandable Quickstart section. “समेटें” is the concise action to collapse it; the current phrase suggests summarizing.'),
 (490,'id'):('Ciutkan','blind','This toggles the expanded Quickstart section. “Ciutkan” is a standard Indonesian UI verb for collapse.'),
 (490,'vi'):('Thu gọn','blind','This toggles the expanded Quickstart section; “Thu gọn” is the idiomatic Vietnamese UI action.'),
 (491,'ar'):('تجميع الكتب المتعددة','primary','The calendar option groups books with the same release date. Choose the proposal that directly describes grouping those books, not folding them.'),
 (491,'de'):('Mehrere Bücher gruppieren','primary','The calendar option groups same-day book releases. “Gruppieren” describes the behavior, unlike folding the books.'),
 (491,'es'):('Agrupar varios libros','primary','The calendar option groups same-day releases. “Agrupar” describes the behavior; “colapsar” can sound like shrinking the books.'),
 (491,'hi'):('कई पुस्तकों को समूहित करें','consensus','The calendar option groups books released on the same day; this is clearer than saying to summarize or fold them.'),
 (491,'id'):('Kelompokkan beberapa buku','consensus','The calendar option groups same-day book entries; “Kelompokkan” avoids the literal “fold”.'),
 (491,'ja'):('複数の書籍をまとめる','primary','The calendar option groups books released on the same day. “まとめる” expresses grouping rather than physically folding books.'),
 (491,'ko'):('여러 책 묶기','primary','The calendar option groups books released on the same day; “묶기” states grouping rather than folding.'),
 (491,'pt-BR'):('Agrupar vários livros','consensus','The calendar option groups same-day releases. “Agrupar” states that behavior directly.'),
 (491,'vi'):('Nhóm nhiều cuốn sách','primary','The calendar option groups same-day entries. “Nhóm” describes grouping rather than shrinking the books.'),
 (491,'zh-Hans'):('多本书籍分组显示','primary','The calendar option groups same-day entries. “分组显示” clearly describes the display behavior rather than folding or merging book contents.'),
 (491,'zh-Hant'):('多本書籍分組顯示','primary','The calendar option groups same-day entries. “分組顯示” clearly describes the display behavior rather than folding or merging book contents.'),
 (492,'ar'):('تجميع الكتب التي تصدر في اليوم نفسه','consensus','The help explains grouping calendar entries for books released on the same day; this retains the date condition and says grouping directly.'),
 (492,'de'):('Am selben Tag erscheinende Bücher gruppieren','primary','The help describes grouping books released on the same day. This preserves that condition and avoids literal folding.'),
 (492,'es'):('Agrupar varios libros publicados el mismo día','primary','The help describes same-day grouping; this preserves the date condition and avoids a literal “collapse” that could suggest shrinking.'),
 (492,'hi'):('एक ही दिन रिलीज़ होने वाली कई पुस्तकों को समूहित करें','consensus','The help describes grouping same-day calendar entries; this retains the date condition and avoids saying to summarize books.'),
 (492,'id'):('Kelompokkan beberapa buku yang terbit pada hari yang sama','primary','The help describes grouping books published on the same day. “Terbit” is natural for books and avoids the current ungrammatical literal phrasing.'),
 (492,'ja'):('同じ日に発売される複数の書籍をまとめる','primary','The help describes grouping books released on the same day. This keeps the explanation direct without adding an unnecessary display claim.'),
 (492,'ko'):('같은 날에 출시되는 여러 책을 묶어 표시합니다','blind','The help describes grouping same-day releases in the calendar; this explains that the entries are displayed together.'),
 (492,'pt-BR'):('Agrupar vários livros lançados no mesmo dia','consensus','The help describes same-day grouping; the wording preserves the release date and uses the natural action “agrupar”.'),
 (492,'vi'):('Nhóm các cuốn sách phát hành cùng ngày','primary','The help describes grouping books released the same day; this avoids the current wording that says the books shrink.'),
 (492,'zh-Hans'):('将同一天发行的多本书籍合并显示','primary','The help describes grouping same-day calendar entries into one display; it does not imply merging book contents.'),
 (492,'zh-Hant'):('將同一天發行的多本書籍合併顯示','primary','The help describes grouping same-day calendar entries into one display; it does not imply merging book contents.'),
 (493,'es'):('Reemplazo de dos puntos','primary','This is a naming-setting field label, so the noun phrase “reemplazo” fits better than the infinitive “reemplazar”.'),
 (493,'fr'):('Remplacement des deux-points','primary','This is a naming-setting field label; “Remplacement des deux-points” is the natural French noun phrase.'),
 (493,'hi'):('कोलन प्रतिस्थापन','primary','This is a naming-setting label for the colon replacement character; the Hindi noun phrase is clearer than the English loan “replacement”.'),
 (493,'pt-BR'):('Substituição dos dois-pontos','primary','This is a naming-setting label; “substituição” names the setting more naturally than the current “substituto para”.'),
 (495,'ar'):('معالجة التنزيلات المكتملة','blind','The download-client fieldset handles completed downloads as a category; use the plural described by the setting.'),
 (495,'de'):('Verarbeitung abgeschlossener Downloads','consensus','This fieldset describes processing completed downloads; the proposal is more idiomatic than the literal compound.'),
 (495,'es'):('Gestión de descargas completadas','consensus','This fieldset covers management of downloads after completion; “gestión” avoids the unintended sense of physical manipulation.'),
 (495,'fr'):('Gestion des téléchargements terminés','primary','This fieldset groups the settings for handling completed downloads. “Gestion” fits that management section better than a singular completed download.'),
 (495,'hi'):('पूर्ण हो चुके डाउनलोड का प्रबंधन','consensus','This fieldset manages downloads after they finish; the wording avoids the English loan “हैंडलिंग” and makes completion explicit.'),
 (495,'vi'):('Xử lý các lượt tải xuống đã hoàn tất','consensus','This fieldset handles downloads that have finished; the new word order makes “completed” modify the downloads.'),
 (495,'zh-Hans'):('已完成下载的处理','blind','This fieldset handles downloads that are complete, rather than a handling process that has itself completed.'),
 (495,'zh-Hant'):('已完成下載的處理','blind','This fieldset handles downloads that are complete, rather than a handling process that has itself completed.'),
 (496,'hi'):('घटक','consensus','The caller uses this as a software component column in the system event log; “घटक” is the technical term, while “अंग” means a body part.'),
 (498,'ar'):('الشروط','primary','The custom-format editor fieldset contains rule conditions. “الشروط” means conditions; “الظروف” means circumstances.'),
 (498,'hi'):('शर्तें','blind','This custom-format fieldset lists conditions; the current plural spelling is incorrect.'),
 (499,'pt-BR'):('Configurar a API do Hardcover','primary','This is the Hardcover setup modal title. Brazilian Portuguese uses “do” to express the API belonging to Hardcover.'),
}

if any((OUT/n).exists() for n in ['ledger.jsonl','proposals.jsonl','holds.jsonl','manifest.json']): raise RuntimeError('refusing to overwrite prior part output')
entry=capture('entry')
cf_dir_hashes=verify_sums(CF); p_dir_hashes=verify_sums(P); b_dir_hashes=verify_sums(B)
# Sealed input verifiers are run before consuming proposals.
results=[]
def run(name,cmd):
 p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode: raise RuntimeError(name+' verifier failed: '+p.stdout)
 results.append({'name':name,'command':cmd,'exitCode':p.returncode,'output':p.stdout.strip()})
run('candidate-free-exact',['python3',str(CF/'verify_candidate_free.py'),'--repo',str(REPO)])
run('primary-input-bound',['python3',str(P/'verify_primary.py'),'--input',str(CF)])
run('blind-exact',['python3',str(B/'verify_blind_review.py'),'--repo',str(REPO)])
cfrows,cfhashes=readjlraw(CF/'candidate-free-cells.jsonl')
prows=jl(P/'ledger.jsonl'); brows=jl(B/'ledger.jsonl')
pp={(x['sourceOrdinal'],x['locale']):x for x in jl(P/'proposals.jsonl')}
bp={(x['sourceOrdinal'],x['locale']):x for x in jl(B/'proposals.jsonl')}
pmap={(x['sourceOrdinal'],x['locale']):x for x in prows if 'sourceOrdinal' in x and START<=x['sourceOrdinal']<=END and x['sourceOrdinal'] not in HOLDS}; bmap={(x['sourceOrdinal'],x['locale']):x for x in brows if START<=x['sourceOrdinal']<=END}
# Text-free hold rows are paired only by candidate-free row digest.
pholds,phashes=readjlraw(P/'holds.jsonl'); bholds,bhashes=readjlraw(B/'holds.jsonl')
phold={x['candidateFreeRowSha256']:(x,h) for x,h in zip(pholds,phashes)}
bhold={x['candidateFreeRowSha256']:(x,h) for x,h in zip(bholds,bhashes)}
if not (len(cfrows)==len(cfhashes)==len(prows)==len(brows)==600): raise RuntimeError('expected 600 candidate/review rows')
if len(pmap)!=276 or len(bmap)!=300: raise RuntimeError('duplicate or missing reviewer cells')
if set(finals)!=set((k,loc) for k,loc in finals): raise RuntimeError('duplicate final decision map')
# Verify every final string is backed by one or both reviewer candidates and that chosen conflict resolutions are exact.
ledger=[]; holds=[]; proposals=[]; counts={}; agreement={}
for c,rowhash in zip(cfrows,cfhashes):
 pos=c['sourceOrdinal']; loc=c['locale']; key=(pos,loc)
 if pos<START or pos>END: continue
 b=bmap[key]
 caller_bound=bool(c['callerReferenceCount'])
 if not caller_bound:
  if pos not in HOLDS or key in pp or key in bp: raise RuntimeError('unexpected callerless/proposal cell '+str(key))
  if rowhash not in phold or rowhash not in bhold: raise RuntimeError('missing hash-only reviewer hold '+str(key))
  pr,prhash=phold[rowhash]; br,brhash=bhold[rowhash]
  forbidden={'sourceKey','sourceText','currentTarget','target','recommendedTarget','proposedTarget','translation'}
  if forbidden&set(pr) or forbidden&set(br): raise RuntimeError('input hold contains text '+str(key))
  if (pr['candidateFreeRowSha256']!=rowhash or br['candidateFreeRowSha256']!=rowhash or b['candidateFreeRowSha256']!=rowhash or b['currentTargetSha256']!=c['currentTargetSha256'] or b['callerContextSha256']!=c['callerContextSha256']): raise RuntimeError('hash-only hold binding mismatch '+str(key))
  if pr['exactHead']!=HEAD or pr['exactTree']!=TREE or br['exactHead']!=HEAD or br['exactTree']!=TREE or b['exactHead']!=HEAD or b['exactTree']!=TREE: raise RuntimeError('hash-only hold ref mismatch '+str(key))
  holds.append({'sourceOrdinal':pos,'locale':loc,'candidateFreeRowSha256':rowhash,'sourceKeySha256':sha(c['sourceKey']),'sourceTextSha256':c['sourceTextSha256'],'currentTargetSha256':c['currentTargetSha256'],'callerContextSha256':c['callerContextSha256'],'primaryHoldRowSha256':prhash,'blindHoldRowSha256':brhash,'primaryDecision':pr['decision'],'blindDecision':br['decision'],'reason':'No exact caller resolved; hash-only hold retained.','exactHead':HEAD,'exactTree':TREE})
  continue
 p=pmap[key]
 if c['sourceTextSha256']!=p.get('sourceTextSha256') or c['sourceTextSha256']!=b.get('sourceTextSha256'): raise RuntimeError('source hash mismatch '+str(key))
 if c['currentTargetSha256']!=p['currentTargetSha256'] or c['currentTargetSha256']!=b['currentTargetSha256']: raise RuntimeError('current hash mismatch '+str(key))
 if rowhash!=p.get('candidateFreeRowSha256') or rowhash!=b.get('candidateFreeRowSha256'): raise RuntimeError('candidate-free row hash mismatch '+str(key))
 if c['callerContextSha256']!=p['callerContextSha256'] or c['callerContextSha256']!=b['callerContextSha256']: raise RuntimeError('caller context mismatch '+str(key))
 if p['exactHead']!=HEAD or p['exactTree']!=TREE or b['exactHead']!=HEAD or b['exactTree']!=TREE: raise RuntimeError('review refs mismatch '+str(key))
 if pos in HOLDS: raise RuntimeError('unexpected caller-bound source ordinal marked held')
 final=finals.get(key)
 pprop=pp.get(key); bprop=bp.get(key)
 if final is None:
  if pprop or bprop: raise RuntimeError('unadjudicated proposal '+str(key))
  target=c['currentTarget']; decision='accept-current'
  activity={475:'the chown group field',476:'the Unix group-name or gid helper',477:'the chown permissions warning',478:'a generic clear action',479:'the edition change tooltip',480:'the indexer flags tooltip',483:'download-client priority',484:'a generic clone action',485:'a clone-condition action',486:'a clone-format action',487:'a clone-indexer action',488:'a clone-profile action',489:'a modal close action',490:'an expandable-section collapse action',491:'same-day calendar book grouping',492:'same-day calendar grouping help',493:'a naming setting label',494:'a generic column heading',495:'completed-download handling options',496:'a software component column',497:'concurrent conversions',498:'custom-format conditions',499:'the Hardcover API setup title'}[pos]
  rationale=f'The pinned caller uses this as {activity}; the current {loc} wording conveys the operation or label clearly, and both reviews retain it. Source tokens remain intact.'
 else:
  target,selection,detail=final
  if not (pprop or bprop): raise RuntimeError('unbacked cross proposal '+str(key))
  pt=pprop.get('proposedTarget') if pprop else None; bt=bprop.get('recommendedTarget') if bprop else None
  if selection=='consensus' and not (pt==bt==target): raise RuntimeError('consensus exact wording mismatch '+str(key))
  if selection=='primary' and pt!=target: raise RuntimeError('primary exact wording mismatch '+str(key))
  if selection=='blind' and bt!=target: raise RuntimeError('blind exact wording mismatch '+str(key))
  if selection not in {'consensus','primary','blind'}: raise RuntimeError('unknown selected source '+str(key))
  decision='accept-consensus-proposal' if selection=='consensus' else 'accept-primary-proposal' if selection=='primary' else 'accept-blind-proposal'
  rationale=detail
  if target==c['currentTarget']: raise RuntimeError('proposal did not change current target '+str(key))
 sig=signatures(c['sourceText']); ft=signatures(target)
 checks={'placeholders':sig['placeholders']==ft['placeholders'],'inlineCode':sig['inlineCode']==ft['inlineCode'],'markup':sig['markup']==ft['markup'],'numeric':sig['numeric']==ft['numeric'],'protectedLiterals':all(x in target for x in sig['protectedLiterals'])}
 if not all(checks.values()): raise RuntimeError(f'token mismatch {key}: {checks}')
 if c['callerReferenceCount']<=0: raise RuntimeError('missing caller on text row '+str(key))
 pproposal=None if pprop is None else {'decision':pprop['decision'],'target':pprop['proposedTarget'],'targetSha256':pprop['proposedTargetSha256'],'rationale':pprop['rationale']}
 bproposal=None if bprop is None else {'decision':bprop['decision'],'target':bprop['recommendedTarget'],'targetSha256':bprop['recommendedTargetSha256'],'rationale':bprop['rationale']}
 x={'sourceOrdinal':pos,'sourceKey':c['sourceKey'],'sourceKeySha256':sha(c['sourceKey']),'sourceText':c['sourceText'],'sourceTextSha256':c['sourceTextSha256'],'locale':loc,'exactHead':HEAD,'exactTree':TREE,'candidateFreeRowSha256':rowhash,'callerContextSha256':c['callerContextSha256'],'callerReferenceCount':c['callerReferenceCount'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],'primaryDecision':p['decision'],'blindDecision':b['decision'],'primaryProposal':pproposal,'blindProposal':bproposal,'crossDecision':decision,'recommendedTarget':target,'recommendedTargetSha256':sha(target),'finalTokenChecks':checks,'confidence':'moderate','rationale':rationale}
 ledger.append(x); counts[decision]=counts.get(decision,0)+1
 if target!=c['currentTarget']:
  proposals.append({'sourceOrdinal':pos,'sourceKey':c['sourceKey'],'sourceKeySha256':sha(c['sourceKey']),'sourceText':c['sourceText'],'sourceTextSha256':c['sourceTextSha256'],'locale':loc,'candidateFreeRowSha256':rowhash,'callerContextSha256':c['callerContextSha256'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],'recommendedTarget':target,'recommendedTargetSha256':sha(target),'crossDecision':decision,'primaryRecommendedTarget':pprop.get('proposedTarget') if pprop else None,'blindRecommendedTarget':bprop.get('recommendedTarget') if bprop else None,'rationale':rationale,'tokenChecks':checks,'exactHead':HEAD,'exactTree':TREE})
 if pprop or bprop:
  status='same-text' if pprop and bprop and pprop['proposedTarget']==bprop['recommendedTarget'] else 'different-text' if pprop and bprop else 'primary-only' if pprop else 'blind-only'
  agreement[status]=agreement.get(status,0)+1
if len(ledger)!=276 or len(holds)!=24 or len(proposals)!=61: raise RuntimeError(f'part counts mismatch {len(ledger)}/{len(holds)}/{len(proposals)}')
if len(finals)!=61: raise RuntimeError(f'final mapping expected 61, got {len(finals)}')
writejl(OUT/'ledger.jsonl',ledger); writejl(OUT/'holds.jsonl',holds); writejl(OUT/'proposals.jsonl',proposals)
exit_at=capture('exit')
if entry['pinTuple']!=exit_at['pinTuple']: raise RuntimeError('PR head/base/worktree changed during part review')
inputpins={}
for name,path,hashes in [('candidate-free',CF,cf_dir_hashes),('primary',P,p_dir_hashes),('blind',B,b_dir_hashes)]:
 inputpins[name]={'path':path.relative_to(TASK).as_posix(),'filesSha256':hashes,'checksumListSha256':sha((path/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((path/('candidate-free-manifest.json' if name=='candidate-free' else 'manifest.json')).read_bytes()),'fileCount':len(hashes)}
summary={'artifact':'ChaptarrNG PR #190 W475-W499 cross-review part','sourceOrdinalRange':[START,END],'cellCount':300,'callerBoundRows':len(ledger),'hashOnlyHolds':len(holds),'recommendations':len(proposals),'retainedCurrent':len(ledger)-len(proposals),'crossDecisionCounts':counts,'proposalAgreement':agreement,'inputProposalRows':{'primary':len([k for k in pp if START<=k[0]<=END and k[0] not in HOLDS]),'blind':len([k for k in bp if START<=k[0]<=END and k[0] not in HOLDS]),'uniqueCells':len(set(k for k in pp if START<=k[0]<=END)|set(k for k in bp if START<=k[0]<=END))},'tokenMismatches':0,'confidence':'moderate; no native-speaker signoff','entryExitHeadBaseStable':True,'mainAtEntry':entry['mainRef'],'mainAtExit':exit_at['mainRef'],'inputPacketMain':j(CF/'candidate-free-manifest.json')['liveMain'],'mainAdvancedSinceInputSeal':entry['mainRef']!=j(CF/'candidate-free-manifest.json')['liveMain'],'inputVerifierResults':results}
dump(OUT/'summary.json',summary)
manifest={'artifact':'ChaptarrNG PR #190 W475-W499 independent cross-review part','schemaVersion':1,'repository':REPO_NAME,'pullRequest':PR,'branch':BRANCH,'baseRef':'main','baseSha':BASE,'baseTree':BASE_TREE,'exactHead':HEAD,'exactTree':TREE,'sourceOrdinalRange':[START,END],'cellCount':300,'callerBoundRows':276,'hashOnlyHolds':24,'recommendationCount':61,'holdPolicy':'Callerless cells are confined to holds.jsonl with hashes/ordinal/locale only; no source or target text.','candidateFreeInputOnlyForCurrentText':True,'inputPackets':inputpins,'entryAttestation':'entry-attestation.json','exitAttestation':'exit-attestation.json','portableVerifier':'verify_part.py','exactWorktreeCommand':'python3 verify_part.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned','checksums':'SHA256SUMS.txt'}
dump(OUT/'manifest.json',manifest)
(OUT/'input-verifier-results.json').write_text(json.dumps({'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme='''# ChaptarrNG PR #190 W475–W499 cross-review part\n\nThis part covers source positions 475–499 (25 IDs × 12 locales = 300 cells) from the fresh W450–W499 candidate-free packet. It contains 276 caller-bound semantic decisions and 24 hash-only callerless holds. The held source keys and source/current target text are intentionally absent from the part output.\n\nPinned PR head/tree: `16c809b4787d70616a1a296ab0d90cf17923ba86` / `dbd8343a42476f4e830428cc59efb7f4830251d5`; base `025498c1a9deb999a4acd1eafc4c807a252e0c29`; branch `codex/chaptarrng-localization-complete-20261031`. Live `main` had advanced after candidate-free sealing; entry and exit snapshots record current `main` while the reviewed PR head/base and exact worktree remained stable.\n\nAll 61 primary/blind proposal cells in this half are adjudicated. Wording corrects Chown group semantics, technical `gid`, indexer flags, action labels, calendar grouping, colon replacement, completed-download settings, component terminology, and Hindi condition spelling. The octal help recommendations use written-language words instead of adding a numeric `8`. Token checks pass. Confidence is moderate; no native-speaker signoff was available.\n\nCallerless rows remain in `holds.jsonl` with hashes and position/locale metadata only.\n\nPortable verification:\n\n```sh\npython3 verify_part.py\n```\n\nExact pinned worktree verification:\n\n```sh\npython3 verify_part.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned\n```\n\nCandidate-free, primary input-bound, and blind exact worktree verifiers passed before adjudication. No repository or PR files were edited.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
checks=packet_file_hashes(OUT); (OUT/'SHA256SUMS.txt').write_text(''.join(f'{checks[n]}  {n}\n' for n in sorted(checks)),encoding='utf-8')
print(json.dumps({'output':str(OUT),'cells':300,'callerBound':len(ledger),'holds':len(holds),'recommendations':len(proposals),'decisions':counts,'inputVerifiers':[r['name']+':PASS' for r in results],'entryExitHeadBaseStable':True,'mainAtEntry':entry['mainRef'],'mainAtExit':exit_at['mainRef']},ensure_ascii=False,indent=2))
