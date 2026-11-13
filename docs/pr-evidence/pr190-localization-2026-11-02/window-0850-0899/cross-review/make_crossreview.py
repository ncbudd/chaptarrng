from __future__ import annotations
import json,hashlib,pathlib,subprocess,re,collections,shutil
from datetime import datetime,timezone
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-crossreview-20261102')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
AUDIT=PRIMARY/'language-audit-addendum'
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def git(*a): return subprocess.check_output(['git','-C',str(WORK),*a])
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def readjl(path): return [json.loads(x) for x in path.read_text().splitlines()]
# The structural pass and live head query must have succeeded before authoring decisions.
struct=json.loads((OUT/'structural-summary.json').read_text())
assert struct['targetHashesVerified']==600 and struct['placeholderOrMarkupFailures']==0
assert struct['callerRefFailures']==0 and struct['genericPipelineFailures']==0 and struct['recommendedTargetNoOps']==0
assert struct['w884HoldCells']==12
# Verify primary+language audit packet checksums and exact pinned inputs.
primary_sha_manifest=sha((PRIMARY/'SHA256SUMS').read_bytes())
assert primary_sha_manifest=='c74bc2a0eda46571510b64e7560e925337447ad2da17d6f51946f631ed68c848'
assert subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=PRIMARY,text=True,capture_output=True).returncode==0
assert subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=AUDIT,text=True,capture_output=True).returncode==0
lang_manifest=json.loads((AUDIT/'manifest.json').read_text())
assert lang_manifest['head']==HEAD and lang_manifest['tree']==TREE and lang_manifest['rows']==91
assert lang_manifest['primaryReviewCellsSha256']==sha((PRIMARY/'review-cells.jsonl').read_bytes())
assert lang_manifest['candidateRows']==79 and lang_manifest['holdRows']==12 and lang_manifest['additionalProposals']==0
primary=[json.loads(x) for x in (PRIMARY/'review-cells.jsonl').read_text().splitlines()]
input_rows=[json.loads(x) for x in (PRIMARY/'input-cells.jsonl').read_text().splitlines()]
audit=readjl(AUDIT/'language-audit.jsonl')
assert len(primary)==len(input_rows)==600 and len(audit)==91
pmap={(x['sourceOrdinal'],x['locale']):x for x in primary}
imap={(x['sourceOrdinal'],x['locale']):x for x in input_rows}
amap={(x['sourceOrdinal'],x['locale']):x for x in audit}
assert len(pmap)==len(imap)==600 and len(amap)==91
# Independently reviewed additional proposals from accepted-current cells.
ADDITIONAL={
 (854,'ar'):('لا ينبغي تسمية عناصر الجودة الفردية.','The caller is QualityNameValidator for media-quality entries. The current word describes personal traits rather than individual quality items; this uses the media-quality term and preserves the prohibition.'),
 (854,'de'):('Einzelne Qualitätselemente dürfen nicht benannt werden.','The caller is QualityNameValidator for media-quality entries. The current term means general properties; this names individual quality items and keeps the prohibition.'),
 (854,'es'):('No se deben nombrar las calidades individuales.','The caller is QualityNameValidator for media-quality entries. In this UI context, calidades is the product term for media quality; this avoids the more general “cualidades”.'),
 (854,'hi'):('अलग-अलग गुणवत्ता स्तरों को नाम नहीं देना चाहिए।','The caller is QualityNameValidator for media-quality entries. This uses the media-quality term rather than a general personal-trait word.'),
 (854,'id'):('Kualitas individual tidak boleh diberi nama.','The caller is QualityNameValidator for media-quality entries. Sifat-sifat individu describes personal traits; this uses the Indonesian term for media quality.'),
 (854,'ja'):('個別の品質項目に名前を付けてはいけません。','The caller is QualityNameValidator for media-quality entries. The current term refers to general characteristics; this names the individual quality items directly.'),
 (854,'ko'):('개별 품질 항목에는 이름을 지정하면 안 됩니다.','The caller is QualityNameValidator for media-quality entries. The current term means personal aptitude/qualities rather than media quality; this uses the product quality term.'),
 (854,'vi'):('Không nên đặt tên cho từng mục chất lượng.','The caller is QualityNameValidator for media-quality entries. The current phrase suggests a personal quality; this says not to name each quality item.'),
 (854,'zh-Hans'):('不应为单个质量项命名。','The caller is QualityNameValidator for media-quality entries. The current phrase refers to personal character and ends with an incomplete “be called”; this names the quality item and completes the prohibition.'),
 (854,'zh-Hant'):('不應為個別品質項目命名。','The caller is QualityNameValidator for media-quality entries. The current phrase refers to personal character and ends with an incomplete “be called”; this names the quality item and completes the prohibition.'),
 (858,'ar'):('يجب توفير unmappedFiles.scope.','The API caller requires the unmappedFiles.scope field. The current Arabic places the field path before “must be provided”; this uses natural Arabic order and preserves the exact code path.'),
 (875,'pt-BR'):('O ID do tópico deve ser maior que 1 ou estar vazio.','The API field is Topic ID. This uses natural Brazilian Portuguese word order and preserves the valid empty value.'),
 (883,'zh-Hans'):('建议使用直接消息，或使用私人账号。','The caller warns users to enable Direct Messaging or use a private account. The current literal word order is awkward; this keeps both alternatives in a concise Chinese sentence.'),
 (883,'zh-Hant'):('建議使用直接訊息，或使用私人帳戶。','The caller warns users to enable Direct Messaging or use a private account. The current literal word order is awkward; this keeps both alternatives in a concise Traditional Chinese sentence.'),
}
assert len(ADDITIONAL)==14
# Check language audit verdicts against the exact primary rows, and cross-review the full 600-cell window.
rows=[]; crosscounts=collections.Counter(); audit_counts=collections.Counter(); audit_reconciled=[]; additions=[]; failures=[]; candidate_noops=[]
for key,p in pmap.items():
 ordinal,loc=key; c=imap[key]; sid=p['sourceId']; src=p['source']; target=p['currentTarget']
 assert p['exactHead']==HEAD and p['exactTree']==TREE and c['exactHead']==HEAD and c['exactTree']==TREE
 assert p['source']==c['source'] and p['sourceTextSha256']==c['sourceTextSha256'] and sha(src)==p['sourceTextSha256']
 assert p['currentTarget']==c['currentTarget'] and p['currentTargetSha256']==c['currentTargetSha256']==sha(target)
 assert p['callerContextSha256']==c['callerContextSha256']
 assert p['callerRefs']==next(x for x in readjl(PRIMARY/'caller-context.jsonl') if x['sourceId']==sid)['callerRefs']
 audit_row=amap.get(key); audit_pointer=None
 if audit_row:
  assert audit_row['sourceId']==sid and audit_row['source']==src and audit_row['sourceTextSha256']==p['sourceTextSha256']
  assert audit_row['currentTarget']==target and audit_row['currentTargetSha256']==p['currentTargetSha256']
  assert audit_row['callerContextSha256']==p['callerContextSha256'] and audit_row['callerRefs']==p['callerRefs']
  audit_pointer={'rowSha256':sha(jbytes(audit_row)),'fileSha256':sha((AUDIT/'language-audit.jsonl').read_bytes()),'verdict':audit_row['languageVerdict']}
  if audit_row['languageVerdict']=='accept-primary-correction':
   assert p['disposition']=='propose-correction' and audit_row['primaryDisposition']=='propose-correction'
   assert audit_row['languageFinalTarget']==p['finalTarget']==p['recommendedTarget']
   assert audit_row['languageFinalTargetSha256']==p['finalTargetSha256']==p['recommendedTargetSha256']==sha(p['finalTarget'])
   xdisp='accept-primary-correction'; final=p['finalTarget']; why='Accepted the exact primary correction after independent language-audit reconciliation.'
  elif audit_row['languageVerdict']=='accept-primary-refinement':
   assert p['disposition']=='propose-refinement' and audit_row['primaryDisposition']=='propose-refinement'
   assert audit_row['languageFinalTarget']==p['finalTarget']==p['recommendedTarget']
   assert audit_row['languageFinalTargetSha256']==p['finalTargetSha256']==p['recommendedTargetSha256']==sha(p['finalTarget'])
   xdisp='accept-primary-refinement'; final=p['finalTarget']; why='Accepted the exact primary refinement after independent language-audit reconciliation.'
  elif audit_row['languageVerdict']=='hold':
   assert p['disposition']=='hold' and ordinal==884 and p['finalTarget'] is None and audit_row['languageFinalTarget'] is None
   xdisp='retain-hold'; final=None; why=audit_row['reason']
  else: raise AssertionError((key,audit_row['languageVerdict']))
  audit_counts[audit_row['languageVerdict']]+=1
 elif key in ADDITIONAL:
  assert p['disposition']=='accept-current' and p['finalTarget']==target
  final,why=ADDITIONAL[key]
  assert final!=target
  xdisp='propose-additional-correction'
  assert placeholders(src)==placeholders(final) and markup(src)==markup(final)
  protected=p['protectedLiterals']
  assert all(lit in final for lit in protected),(key,protected,final)
  additions.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':p['sourceTextSha256'],
   'currentTarget':target,'currentTargetSha256':p['currentTargetSha256'],'recommendedTarget':final,'recommendedTargetSha256':sha(final),
   'rationale':why,'confidence':'moderate','callerContextSha256':p['callerContextSha256'],'callerRefs':p['callerRefs'],
   'placeholdersPreserved':True,'markupPreserved':True,'protectedLiterals':protected,'protectedLiteralsPreserved':True})
 else:
  assert p['disposition']=='accept-current' and p['finalTarget']==target and p['finalTargetSha256']==sha(target)
  xdisp='accept-current'; final=target; why='Current wording retained after independent source, caller, context, and integrity review.'
 if p['disposition'] in ('propose-correction','propose-refinement') and p['finalTarget']==target:
  candidate_noops.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc})
 # Structural checks are repeated for the cross-review target, including accepted current values.
 if final is not None:
  assert sha(final)==(sha(final) if xdisp=='propose-additional-correction' else p['finalTargetSha256'])
  assert placeholders(src)==placeholders(final) and markup(src)==markup(final)
 final_hash=sha(final) if final is not None else None
 row={
  'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':p['sourceTextSha256'],
  'sourceKeySha256':p['sourceKeySha256'],'sourceFile':p['sourceFile'],'sourceFileBlob':p['sourceFileBlob'],'sourceFileSha256':p['sourceFileSha256'],
  'currentTarget':target,'currentTargetSha256':p['currentTargetSha256'],'targetFile':p['targetFile'],'targetFileBlob':p['targetFileBlob'],'targetFileSha256':p['targetFileSha256'],
  'primaryDisposition':p['disposition'],'primaryTarget':p['finalTarget'],'primaryTargetSha256':p['finalTargetSha256'],
  'crossReviewDisposition':xdisp,'crossReviewFinalTarget':final,'crossReviewFinalTargetSha256':final_hash,'crossReviewRationale':why,'confidence':'moderate',
  'sourcePlaceholders':p['sourcePlaceholders'],'currentTargetPlaceholders':p['currentTargetPlaceholders'],'crossReviewFinalPlaceholders':placeholders(final) if final is not None else None,
  'sourceMarkup':p['sourceMarkup'],'currentTargetMarkup':p['currentTargetMarkup'],'crossReviewFinalMarkup':markup(final) if final is not None else None,
  'protectedLiterals':p['protectedLiterals'],'protectedLiteralsPreserved':(p['protectedLiteralsPreserved'] if xdisp!='propose-additional-correction' else True),
  'callerContextSha256':p['callerContextSha256'],'callerReferenceStatus':p['callerReferenceStatus'],'callerRefs':p['callerRefs'],
  'callerSourceMessageMismatch':p['callerSourceMessageMismatch'],'languageAudit':audit_pointer}
 rows.append(row); crosscounts[xdisp]+=1
if failures: raise AssertionError(failures[:10])
assert not candidate_noops,candidate_noops
assert audit_counts=={'accept-primary-correction':69,'accept-primary-refinement':10,'hold':12},audit_counts
assert len(additions)==14 and len(rows)==600
assert crosscounts=={'accept-current':495,'propose-additional-correction':14,'accept-primary-correction':69,'accept-primary-refinement':10,'retain-hold':12},crosscounts
assert all(r['sourceOrdinal']==884 for r in rows if r['crossReviewDisposition']=='retain-hold')
(OUT/'cross-review-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
(OUT/'additional-corrections.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in additions))
# Include audit evidence, not just references, to make the packet self-contained.
copy=OUT/'language-audit-addendum'; copy.mkdir(exist_ok=True)
for name in ('README.md','SHA256SUMS','build_language_audit.py','language-audit.jsonl','manifest.json'):
 shutil.copy2(AUDIT/name,copy/name)
summary={'schemaVersion':1,'title':'ChaptarrNG PR #190 W850-W899 independent cross-review','repository':'snapetech-org/ChaptarrNG','pullRequest':190,'exactHead':HEAD,'exactTree':TREE,
 'scope':{'sourceOrdinals':[850,899],'sourceIds':50,'locales':LOCALES,'cells':600},'crossReviewDispositionCounts':dict(crosscounts),
 'primaryProposalsAudited':79,'primaryCorrectionsAccepted':69,'primaryRefinementsAccepted':10,'additionalCorrections':len(additions),'holdsRetained':12,
 'additionalCorrectionCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'recommendedTargetSha256':x['recommendedTargetSha256']} for x in additions],
 'w884HeldAcrossAllLocales':True,'w884SourceCallerMismatch':'English catalog omits backslash (\\) while the pinned qBittorrent caller forbids it; all 12 remain held.',
 'structuralReadback':'structural-caller-reattestation.jsonl','callerRefsVerified':74,'genericPipelineRefsVerified':76,'structuralFailures':0,
 'languageAuditInput':{'path':str(AUDIT),'manifestSha256':sha((AUDIT/'manifest.json').read_bytes()),'languageAuditRowsSha256':sha((AUDIT/'language-audit.jsonl').read_bytes()),'acceptedCorrections':69,'acceptedRefinements':10,'holds':12},
 'primaryPacket':str(PRIMARY),'primaryChecksumManifestSha256':sha((PRIMARY/'SHA256SUMS').read_bytes()),'primaryReviewCellsSha256':sha((PRIMARY/'review-cells.jsonl').read_bytes()),
 'nativeSpeakerApproval':False,'browserReview':False,'testsBuildCiRun':False,'repositoryModified':False,'confidence':'moderate'}
(OUT/'cross-review-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'crossReviewCounts':dict(crosscounts),'additionalCorrections':len(additions),'additionalCells':[f"{x['sourceOrdinal']}:{x['locale']}" for x in additions],'languageAuditCounts':dict(audit_counts)},ensure_ascii=False,indent=2))
