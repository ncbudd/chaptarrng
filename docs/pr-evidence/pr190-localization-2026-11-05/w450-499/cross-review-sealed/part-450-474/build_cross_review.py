#!/usr/bin/env python3
"""Build the sealed W450-W474 cross-review part from the pinned three input packets."""
import collections, hashlib, json, re
from pathlib import Path

OUT=Path(__file__).resolve().parent
BASE=OUT.parents[1]
CF=BASE/'candidate-free'/'input'
PRIMARY=BASE/'primary-review'
BLIND=BASE/'blind-review'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
API_BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
HOLDS={469,474}
PH=re.compile(r'\{[^{}]+\}')
INLINE=re.compile(r'`([^`]+)`')
MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
# selector is current, primary, blind, consensus, or ('new', exact target)
OVERRIDES={
 (451,'hi'):('consensus','“कथावाचक” names an audiobook narrator directly; “सूत्रधार” can mean a host or emcee.','moderate'),
 (453,'hi'):('consensus','Use the same narrator term as the adjacent edition narrator field.','moderate'),
 (454,'hi'):('primary','The value identifies a full-cast production, not one complete artist.','high'),
 (454,'ko'):('primary','This is a full-cast edition label; the current phrase describes everyone reading aloud instead of the cast.','moderate'),
 (455,'es'):('blind','The catalog column denotes an abridged edition; this avoids “resumen,” which means a summary.','high'),
 (455,'fr'):('blind','“Version abrégée” identifies the shortened edition; “abréviation” means an abbreviation.','high'),
 (455,'id'):('consensus','“Versi ringkas” means a shortened version and fits this edition metadata field.','moderate'),
 (455,'ja'):('blind','“短縮版” means an abridged version; “縮刷” can suggest reduced-size printing.','high'),
 (455,'pt-BR'):('blind','The field describes an abridged edition, not a summary.','high'),
 (455,'vi'):('blind','“Bản rút gọn” names the shortened edition rather than the act of shortening.','moderate'),
 (455,'zh-Hant'):('consensus','“刪節” specifically denotes abridgement, unlike the current general term for reduction.','moderate'),
 (456,'es'):('consensus','“Abreviada” describes a shortened edition; “resumida” suggests summarized content.','high'),
 (456,'fr'):('consensus','“Abrégée” correctly describes the shortened edition; “résumé” means a summary.','high'),
 (456,'id'):('primary','“Dipersingkat” directly means shortened; “ringkas” can mean concise without stating that the edition was abridged.','moderate'),
 (456,'ja'):('consensus','“短縮版” is the clear label for an abridged edition.','high'),
 (456,'pt-BR'):('consensus','“Abreviada” directly describes an abridged edition rather than a summary.','high'),
 (456,'zh-Hant'):('consensus','“刪節版” directly describes an abridged edition.','moderate'),
 (457,'de'):('primary','“Ungekürzt” means unabridged; “ungeschnitten” is more commonly used for uncut film or media.','high'),
 (457,'fr'):('primary','The implied noun “édition” is feminine, so “intégrale” agrees and contrasts with “abrégée.”','high'),
 (457,'id'):('blind','“Versi utuh” clearly denotes the complete, unabridged version.','moderate'),
 (457,'ko'):('blind','“무축약판” means an edition without abridgement; “완역판” refers to a complete translation.','moderate'),
 (459,'ar'):('new','مختارة','The badge describes a selected edition; this feminine form agrees with the implied feminine “طبعة.”','moderate'),
 (459,'es'):('new','Seleccionada','The badge describes an edition (“edición,” feminine), so the adjective takes the feminine form.','high'),
 (459,'fr'):('primary','The implied “édition” is feminine, so the selected-status adjective must be feminine.','high'),
 (459,'pt-BR'):('primary','The implied “edição” is feminine, so the selected-status adjective must be feminine.','high'),
 (460,'es'):('primary','This is a status badge for an edition with a local file; the infinitive “tener” reads like an action.','moderate'),
 (460,'fr'):('consensus','“Fichier présent” reads as a concise file-present status, unlike the infinitive “posséder.”','moderate'),
 (462,'ar'):('new','مقارنة الرواة','The heading compares multiple audiobook narrators; use the plural term already used for the narrator field.','moderate'),
 (462,'hi'):('consensus','The genitive construction is natural Hindi for a comparison of narrators.','moderate'),
 (462,'zh-Hans'):('new','朗读者对比','Use the same audiobook narrator term as the edition table, rather than the term for a voice-over narrator.','moderate'),
 (462,'zh-Hant'):('new','朗讀者比較','Use the same audiobook narrator term as the edition table, rather than the term for a voice-over narrator.','moderate'),
 (463,'ar'):('new','أي أجزاء من هذه السلسلة يغطيها كل راوٍ، عبر جميع الطبعات المعروفة.','Use the same narrator term as the heading and clarify that the statement covers each individual narrator.','moderate'),
 (463,'hi'):('primary','This makes the narrator-to-volume relationship explicit and avoids the awkward literal borrowing “कवर करता है.”','moderate'),
 (463,'vi'):('primary','“Phụ trách” naturally describes which series volumes each narrator covers across editions.','moderate'),
 (463,'zh-Hans'):('new','显示在所有已知版本中，该系列每位朗读者分别负责朗读哪些卷。','Use the edition-table term “朗读者” and state which volumes each narrator reads.','moderate'),
 (463,'zh-Hant'):('new','顯示在所有已知版本中，此系列每位朗讀者分別負責朗讀哪些卷冊。','Use the edition-table term “朗讀者” and state which volumes each narrator reads.','moderate'),
 (464,'ar'):('new','تعذّر تحميل مقارنة الرواة.','Match the plural narrator term used in the section heading.','moderate'),
 (464,'hi'):('consensus','Use the natural genitive phrase for a comparison of narrators.','moderate'),
 (464,'zh-Hans'):('new','无法加载朗读者对比。','Use the same audiobook narrator term as the section heading and edition table.','moderate'),
 (464,'zh-Hant'):('new','無法載入朗讀者比較。','Use the same audiobook narrator term as the section heading and edition table.','moderate'),
 (465,'hi'):('primary','“खंड” is the natural Hindi term for book volumes in this series table.','moderate'),
 (466,'ar'):('new','أجزاء غير مغطاة','The count is for volumes outside this narrator’s coverage, not volumes missing from the catalog.','moderate'),
 (466,'hi'):('consensus','“छूटे हुए खंड” means volumes left uncovered by the selected narrator.','moderate'),
 (466,'id'):('new','Volume yang tidak tercakup','The matrix counts volumes outside a narrator’s coverage, not lost or missing catalog entries.','moderate'),
 (466,'ko'):('new','누락된 권','Use the native book-volume counter “권” consistently with the adjacent narrator coverage label.','moderate'),
 (467,'hi'):('primary','“खंड” is the natural Hindi term for book volumes in this series table.','moderate'),
 (467,'ko'):('new','파일이 있는 권','Use the native book-volume counter “권” consistently with the adjacent narrator coverage label.','moderate'),
 (470,'fr'):('primary','This is the French form label for a chmod value applied to folders; “chmod du dossier” has natural word order.','moderate'),
 (471,'ja'):('new','8進数で指定し、インポートや名前変更時にメディアのフォルダーとファイルに適用します（実行ビットを除く）。','The standard Japanese technical form is “8進数”; the 8 is lexicalized in “octal,” not a separate source value. This version also makes the import/rename relationship clearer.','moderate'),
 (471,'ko'):('new','8진수이며, 미디어 폴더와 파일을 가져오거나 이름을 변경할 때 적용됩니다(실행 비트 제외).','The conventional Korean technical notation is “8진수”; the 8 is lexicalized in “octal,” not a separate source value. This repairs spacing and clarifies the operation.','moderate'),
 (473,'zh-Hant'):('new','選擇預設…','“預設” is the usual Traditional Chinese term for a settings preset; preserve the source ellipsis.','moderate'),
}

def need(ok,msg):
 if not ok: raise SystemExit('REFUSED: '+msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def readj(p):return json.loads(p.read_text(encoding='utf-8'))
def jl(p):return [(line,json.loads(line)) for line in p.read_bytes().splitlines() if line.strip()]
def verify_sums(d):
 sums={}
 for line in (d/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  h,n=line.split('  ',1);sums[n]=h
 actual={p.relative_to(d).as_posix():sha(p.read_bytes()) for p in d.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 need(sums==actual,'input checksum mismatch: '+str(d))
 return sha((d/'SHA256SUMS.txt').read_bytes())
def check_token(source,target,protected):
 return {'placeholders':sorted(PH.findall(source))==sorted(PH.findall(target)),
         'inlineCode':INLINE.findall(source)==INLINE.findall(target),
         'markup':MARKUP.findall(source)==MARKUP.findall(target),
         'numeric':NUM.findall(source)==NUM.findall(target),
         'protectedLiterals':all(x in target for x in protected)}
def main():
 need({p.name for p in OUT.iterdir() if p.is_file()} <= {'entry-refs.json','input-reattestation.json','build_cross_review.py'},'unexpected file in output directory')
 cf_sums=verify_sums(CF); p_sums=verify_sums(PRIMARY); b_sums=verify_sums(BLIND)
 cfm=readj(CF/'candidate-free-manifest.json'); pm=readj(PRIMARY/'manifest.json'); bm=readj(BLIND/'manifest.json')
 need((cfm['head'],cfm['tree'],cfm['apiBase'])==(HEAD,TREE,API_BASE),'candidate-free exact pins')
 need((pm['exactHead'],pm['exactTree'])==(HEAD,TREE),'primary exact pins')
 need((bm['exactHead'],bm['exactTree'],bm['apiBaseSha'])==(HEAD,TREE,API_BASE),'blind exact pins')
 need((sha((CF/'candidate-free-manifest.json').read_bytes()),cf_sums,sha((PRIMARY/'manifest.json').read_bytes()),p_sums,sha((BLIND/'manifest.json').read_bytes()),b_sums)==(
  readj(OUT/'input-reattestation.json')['candidateFreeManifestSha256'],readj(OUT/'input-reattestation.json')['candidateFreeChecksumsSha256'],readj(OUT/'input-reattestation.json')['primaryManifestSha256'],readj(OUT/'input-reattestation.json')['primaryChecksumsSha256'],readj(OUT/'input-reattestation.json')['blindManifestSha256'],readj(OUT/'input-reattestation.json')['blindChecksumsSha256']),'input packet pins changed')
 need({p.name for p in OUT.iterdir() if p.is_file()} <= {'entry-refs.json','input-reattestation.json','build_cross_review.py'},'output changed during build')
 cfraw=jl(CF/'candidate-free-cells.jsonl'); cells=[r for _,r in cfraw]
 cfb={(r['sourceOrdinal'],r['locale']):(raw,r) for raw,r in cfraw}
 pledger=[r for _,r in jl(PRIMARY/'ledger.jsonl')]; pledger_by={r['candidateFreeRowSha256']:r for r in pledger}
 bledger=[r for _,r in jl(BLIND/'ledger.jsonl')]; bledger_by={r['candidateFreeRowSha256']:r for r in bledger}
 pprops={(r['sourceOrdinal'],r['locale']):r for _,r in jl(PRIMARY/'proposals.jsonl')}
 bprops={(r['sourceOrdinal'],r['locale']):r for _,r in jl(BLIND/'proposals.jsonl')}
 contexts={r['sourceKey']:r for _,r in jl(CF/'caller-context.jsonl')}
 need(len(cells)==600 and len(pledger_by)==600 and len(bledger_by)==600,'input row dimensions')
 ledger=[]; holds=[]; decision_counts=collections.Counter(); pc=collections.Counter(); bc=collections.Counter(); token_fail=collections.Counter(); manual_numeric=[]; proposal_source_counts=collections.Counter(); confidence_counts=collections.Counter()
 for ordinal in range(450,475):
  for locale in LOCALES:
   raw,c=cfb[(ordinal,locale)]; cfhash=sha(raw); p=pledger_by[cfhash]; b=bledger_by[cfhash]
   need(p['candidateFreeRowSha256']==b['candidateFreeRowSha256']==cfhash,'candidate row exact-byte pin')
   need((p['exactHead'],p['exactTree'],b['exactHead'],b['exactTree'])==(HEAD,TREE,HEAD,TREE),'review proposal PR pins')
   need((p['sourceTextSha256'],p['currentTargetSha256'],p['callerContextSha256'])==(c['sourceTextSha256'],c['currentTargetSha256'],c['callerContextSha256']),'primary input hash tuple')
   need((b['sourceTextSha256'],b['currentTargetSha256'],b['callerContextSha256'])==(c['sourceTextSha256'],c['currentTargetSha256'],c['callerContextSha256']),'blind input hash tuple')
   need(shat(c['sourceText'])==c['sourceTextSha256'] and shat(c['currentTarget'])==c['currentTargetSha256'],'candidate-free text hashes')
   ishold=ordinal in HOLDS
   need((p['decision']=='hold-hash-only')==(ishold) and (b['decision']=='hold-hash-only')==(ishold),'hold status/source ordinals')
   pc[p['decision']]+=1;bc[b['decision']]+=1
   if ishold:
    need(c['callerReferenceCount']==0,'hold has callers')
    need(all(key not in p for key in ('sourceKey','sourceText','currentTarget','locale','sourceOrdinal')),'primary hold ledger exposed identity/text')
    need(all(key not in b for key in ('sourceKey','sourceText','currentTarget','recommendedTarget')),'blind hold ledger exposed text')
    p_hold=next((r for _,r in jl(PRIMARY/'holds.jsonl') if r['candidateFreeRowSha256']==cfhash),None)
    b_hold=next((r for _,r in jl(BLIND/'holds.jsonl') if r.get('candidateFreeRowSha256')==cfhash),None)
    need(p_hold is not None and b_hold is not None,'hash-only hold rows missing')
    h={'sourceOrdinal':ordinal,'locale':locale,'cellIdSha256':shat(c['sourceKey']+'::'+locale),'sourceTextSha256':c['sourceTextSha256'],'currentTargetSha256':c['currentTargetSha256'],
       'candidateFreeRowSha256':cfhash,'callerContextSha256':c['callerContextSha256'],'sourceFileSha256':c['sourceFileSha256'],'sourceFileGitBlob':c['sourceFileGitBlob'],
       'targetFileSha256':c['targetFileSha256'],'targetFileGitBlob':c['targetFileGitBlob'],'callerReferenceCount':0,'literalCallCount':0,'primaryDecision':p['decision'],'blindDecision':b['decision'],
       'crossDecision':'hold-hash-only','exactHead':HEAD,'exactTree':TREE,'apiBaseSha':API_BASE,'confidence':'high','rationale':'No runtime or literal caller is attached to this source; retain the cell as a text-free hash-only hold.'}
    holds.append(h);decision_counts['hold-hash-only']+=1
    continue
   need(c['callerReferenceCount']>0,'non-hold is callerless')
   need(p['sourceKey']==b['sourceKey']==c['sourceKey'] and p['locale']==b['locale']==locale,'source key and locale binding')
   need(p['sourceText']==b['sourceText']==c['sourceText'] and p['currentTarget']==b['currentTarget']==c['currentTarget'],'source/current text binding')
   need(p['sourceFileGitBlob']==b['sourceFileGitBlob']==c['sourceFileGitBlob'] and p['targetFileGitBlob']==b['targetFileGitBlob']==c['targetFileGitBlob'],'catalog blob pins')
   ctx=contexts[c['sourceKey']];need(ctx['callerContextSha256']==c['callerContextSha256'],'caller context current hash')
   pprop=pprops.get((ordinal,locale));bprop=bprops.get((ordinal,locale))
   for name,prop in (('primary',pprop),('blind',bprop)):
    if prop:
     need(prop['candidateFreeRowSha256']==cfhash and prop['sourceTextSha256']==c['sourceTextSha256'] and prop['currentTargetSha256']==c['currentTargetSha256'],'proposal input hashes '+name)
     target=prop.get('proposedTarget') if name=='primary' else prop.get('recommendedTarget'); target_hash=prop.get('proposedTargetSha256') if name=='primary' else prop.get('recommendedTargetSha256')
     need(target is not None and shat(target)==target_hash,'proposal text hash '+name)
     proposal_source_counts[name]+=1
    else: target=None
   rule=OVERRIDES.get((ordinal,locale),('current','Current wording conveys the source accurately in its caller context; no change is needed.','moderate'))
   selector=rule[0]
   if selector=='current': recommended=c['currentTarget']; recommendation_source='current'; rationale=rule[1]; confidence=rule[2]
   elif selector in ('primary','blind','consensus'):
    need(pprop is not None or selector=='blind','selected primary proposal does not exist')
    need(bprop is not None or selector=='primary','selected blind proposal does not exist')
    pt=pprop['proposedTarget'] if pprop else None; bt=bprop['recommendedTarget'] if bprop else None
    if selector=='consensus': need(pt is not None and pt==bt,'reviewer proposals do not agree')
    if selector=='primary': recommended=pt; recommendation_source='primary'
    elif selector=='blind': recommended=bt; recommendation_source='blind'
    else: recommended=pt; recommendation_source='consensus'
    rationale=rule[1];confidence=rule[2]
   elif selector=='new':
    recommended=rule[1];rationale=rule[2];confidence=rule[3];recommendation_source='new'
   else: raise SystemExit('unknown override selector')
   if recommended==c['currentTarget']: cross='accept-current';recommendation_source='current'
   elif pprop and recommended==pprop.get('proposedTarget') and bprop and recommended==bprop.get('recommendedTarget'):cross='accept-consensus-proposal';recommendation_source='consensus'
   elif pprop and recommended==pprop.get('proposedTarget'):cross='accept-primary-proposal';recommendation_source='primary'
   elif bprop and recommended==bprop.get('recommendedTarget'):cross='accept-blind-proposal';recommendation_source='blind'
   else:cross='cross-adjustment';recommendation_source='new'
   checks=check_token(c['sourceText'],recommended,c.get('protectedLiterals',[]))
   for name,ok in checks.items():
    if not ok:token_fail[name]+=1
   manual=None
   if ordinal==471 and locale in ('ja','ko'):
    need('8進数' in recommended or '8진수' in recommended,'octal wording lost base-eight term')
    manual='The digit 8 is lexicalized in the standard target-language term for octal (8進数 / 8진수); it denotes the source word “Octal,” not an independent permission value.'
    manual_numeric.append({'sourceOrdinal':ordinal,'locale':locale})
   row={'sourceOrdinal':ordinal,'sourceKey':c['sourceKey'],'sourceKeySha256':shat(c['sourceKey']),'locale':locale,
        'sourceTextSha256':c['sourceTextSha256'],'candidateFreeRowSha256':cfhash,'callerContextSha256':c['callerContextSha256'],
        'callerReferenceCount':c['callerReferenceCount'],'literalCallCount':c['literalCallCount'],'indirectKeyReferenceCount':c['indirectKeyReferenceCount'],
        'relatedDynamicTranslationCallsiteCount':c['relatedDynamicTranslationCallsiteCount'],'sourceFile':c['sourceFile'],'sourceFileSha256':c['sourceFileSha256'],'sourceFileGitBlob':c['sourceFileGitBlob'],
        'targetFile':c['targetFile'],'targetFileSha256':c['targetFileSha256'],'targetFileGitBlob':c['targetFileGitBlob'],
        'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
        'primaryDecision':p['decision'],'blindDecision':b['decision'],'crossDecision':cross,'recommendedTarget':recommended,'recommendedTargetSha256':shat(recommended),
        'recommendationSource':recommendation_source,'confidence':confidence,'rationale':rationale,'tokenChecks':checks,
        'exactHead':HEAD,'exactTree':TREE,'apiBaseSha':API_BASE}
   if pprop:row['primaryProposal']={'target':pprop['proposedTarget'],'sha256':pprop['proposedTargetSha256'],'decision':pprop['decision']}
   if bprop:row['blindProposal']={'target':bprop['recommendedTarget'],'sha256':bprop['recommendedTargetSha256'],'decision':bprop['decision']}
   if manual:row['manualNumericAssessment']=manual
   ledger.append(row);decision_counts[cross]+=1;confidence_counts[confidence]+=1
 need(len(ledger)==276 and len(holds)==24,'complete review coverage')
 def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
 writejl('ledger.jsonl',ledger);writejl('holds.jsonl',holds)
 in_att=readj(OUT/'input-reattestation.json'); entry=readj(OUT/'entry-refs.json')
 summary={'artifact':'ChaptarrNG PR #190 W450-W474 cross-review part','result':'PASS','exactHead':HEAD,'exactTree':TREE,'apiBaseSha':API_BASE,
  'sourceOrdinalRange':[450,474],'sourceIdCount':25,'localeCount':12,'cellCount':300,'callerBackedCells':len(ledger),'hashOnlyHoldCells':len(holds),
  'hashOnlyHoldSourceOrdinals':[469,474],'crossDecisionCounts':dict(decision_counts),'confidenceCounts':dict(confidence_counts),
  'primaryDecisionCounts':in_att['primaryDecisions'],'blindDecisionCounts':in_att['blindDecisions'],'primaryProposalCellsInRange':proposal_source_counts.get('primary',0),
  'blindProposalCellsInRange':proposal_source_counts.get('blind',0),'candidateFreeRowsReattested':300,'primaryRowsReattested':300,'blindRowsReattested':300,
  'primaryBlindDecisionAgreement':in_att['decisionAgreementCells'],'primaryBlindDecisionDisagreement':in_att['decisionDisagreementCells'],
  'recommendedTokenCheckFailures':dict(token_fail),'manualOctalNumericAssessments':manual_numeric,'callerlessHoldTextIncluded':False,
  'candidateFreeVerifier':'PASS (portable and exact worktree)','primaryVerifier':'PASS (candidate-free bound)','blindVerifier':'PASS (exact worktree)',
  'liveMainAtCandidateFreeSeal':'317c5b431649a69a89e1c795f9490fd4df0b682b','liveMainAtEntry':entry['mainApiSha'],
  'PRHeadAndBaseUnchangedAtEntry':True,'noRepositoryOrPullRequestEdits':True,'testsBuildsScansOrCI':False,'browserOrDesktopUsed':False,
  'proposalOutputsRead':['candidate-free/input','primary-review','blind-review'],'staleOrOtherCrossOutputsRead':False}
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 readme='''# ChaptarrNG PR #190 cross-review: W450–W474

This part covers Core source ordinals 450–474 across all 12 locales: 300 cells total. The PR head/tree are `16c809b4787d70616a1a296ab0d90cf17923ba86` / `dbd8343a42476f4e830428cc59efb7f4830251d5`; the API base is `025498c1a9deb999a4acd1eafc4c807a252e0c29`. Live main had advanced from the candidate-free seal and is recorded at entry and exit; cross rows remain bound to the pinned PR head and base.

`ledger.jsonl` contains all 276 caller-backed cells with current targets, exact primary/blind proposal targets where present, the cross decision, recommended wording, rationale, caller/catalog pins, and token checks. `holds.jsonl` contains the remaining 24 cells at ordinals 469 and 474 as text-free hash-only holds. It includes no source keys or source, current-target, or proposal text for those holds.

The reviewer reverified the candidate-free input, primary and blind packet checksums and verifiers, then rebound all 300 selected candidate-free row hashes to both review ledgers. The two octal terms in Japanese and Korean use the conventional numeral-bearing technical notation `8進数` / `8진수`; the numeric heuristic is recorded as a lexicalized-token exception, not a permission-value change.

Run the portable verifier from this directory:

```sh
python3 verify_cross_review.py
```

It defaults to the sibling candidate-free, primary and blind input packets; optional `--candidate-free`, `--primary`, and `--blind` arguments can point to those packet directories elsewhere. The checksum list covers all part files except itself. No repository, catalog, workflow, or PR edits were made.
'''
 (OUT/'README.md').write_text(readme,encoding='utf-8')
 # Bind the source packets and the recorded entry snapshot into the part manifest.
 files=[]
 for p in sorted(OUT.iterdir()):
  if p.is_file() and p.name not in {'manifest.json','SHA256SUMS.txt'}:
   data=p.read_bytes();files.append({'path':p.name,'sha256':sha(data),'bytes':len(data)})
 manifest={'artifact':'ChaptarrNG PR #190 W450-W474 sealed cross-review part','schemaVersion':1,'repository':'snapetech-org/ChaptarrNG','pullRequest':190,
  'branch':'codex/chaptarrng-localization-complete-20261031','sourceOrdinalRange':[450,474],'sourceIds':25,'locales':LOCALES,'cells':300,
  'callerBackedCells':276,'hashOnlyHoldCells':24,'exactHead':HEAD,'exactTree':TREE,'apiBaseSha':API_BASE,'liveMainAtEntry':entry['mainApiSha'],
  'candidateFreeManifestSha256':in_att['candidateFreeManifestSha256'],'candidateFreeChecksumsSha256':in_att['candidateFreeChecksumsSha256'],
  'primaryManifestSha256':in_att['primaryManifestSha256'],'primaryChecksumsSha256':in_att['primaryChecksumsSha256'],
  'blindManifestSha256':in_att['blindManifestSha256'],'blindChecksumsSha256':in_att['blindChecksumsSha256'],
  'candidateFreeInput':'../../candidate-free/input','primaryInput':'../../primary-review','blindInput':'../../blind-review',
  'files':files,'holdTextIncluded':False,'proposalTargetsIncluded':True,'repositoryOrPREdited':False}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 sums=[]
 for p in sorted(OUT.iterdir()):
  if p.is_file() and p.name!='SHA256SUMS.txt':sums.append(f'{sha(p.read_bytes())}  {p.name}')
 (OUT/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
 print(json.dumps({'result':'PASS','output':str(OUT),'callerBacked':len(ledger),'hashOnlyHolds':len(holds),'crossDecisions':dict(decision_counts),'numericTokenChecks':dict(token_fail),'files':len(files),'checksums':len(sums)},indent=2))
if __name__=='__main__':main()
