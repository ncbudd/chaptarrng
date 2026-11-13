#!/usr/bin/env python3
import hashlib, json, shutil
from pathlib import Path

OUT = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-cross-review-20261103')
SRC = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-independent-review-20261103')
if not SRC.is_dir() or not OUT.is_dir():
    raise SystemExit('source packet or output directory is missing')
if (OUT / 'manifest.json').exists():
    raise SystemExit('refusing to overwrite an existing cross-review packet')
shutil.copytree(SRC, OUT / 'source-packet')
recs = [json.loads(line) for line in (SRC / 'review/independent-recommendations.jsonl').read_text(encoding='utf-8').splitlines() if line]
notes = {
('provider.option.o7285d46b982d','vi'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The caller is the CastilianSpanish enum option beside the distinct Spanish option. “Castilia” clearly names the regional variety in this Vietnamese label and keeps that distinction visible. This wording remains a draft pending qualified native review.'},
('ui.loading.newEbookSmell','ar'): {
 'disposition':'continue-hold','confidence':'low',
 'rationale':'The draft retains the smell-of-opening setup and delays the electronic-book reveal, which fits the rotating loading quip. I cannot confidently judge whether the post-ellipsis adjective reads as a natural Arabic comic afterthought; keep this cell held for an Arabic reviewer.',
 'holdReason':'Low confidence in the Arabic ellipsis/reveal phrasing; native review required.'},
('ui.loading.newEbookSmell','hi'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft delays ई-पुस्तक after “नई...” and keeps the playful smell claim as a standalone loading question. The setup and reveal fit the randomized message caller. Pending qualified native review.'},
('ui.loading.newEbookSmell','id'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft keeps the familiar aroma of opening a new book, then repeats buku in the delayed buku elektronik reveal. That repetition makes the intended ebook punchline legible in this short randomized loading message. Pending qualified native review.'},
('ui.loading.newEbookSmell','ja'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The ellipsis separates 新しい from 電子書籍, preserving the source reveal, while the rhetorical comparison keeps the impossible new-book scent joke. It reads as a standalone loading quip. Pending qualified native review.'},
('ui.loading.newEbookSmell','ko'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft preserves the pause between 새 and 전자책 and keeps the smell-of-opening claim as a conversational rhetorical question. This fits a rotating loading message. Pending qualified native review.'},
('ui.loading.newEbookSmell','vi'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft preserves the new-book aroma setup and delays sách điện tử until after the pause, so the ebook reveal remains clear in the standalone loading quip. Pending qualified native review.'},
('ui.loading.newEbookSmell','zh-Hans'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft holds 电子书 until after the pause and then closes with a conversational rhetorical question. The smell claim and delayed ebook reveal fit the randomized loading context. Pending qualified native review.'},
('ui.loading.newEbookSmell','zh-Hant'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft holds 電子書 until after the pause and then closes with a conversational rhetorical question. The smell claim and delayed ebook reveal fit the randomized loading context. Pending qualified native review.'},
('ui.loading.dodgeBooks','ar'): {
 'disposition':'continue-hold','confidence':'low',
 'rationale':'The draft turns the English -ing fragment into a first-person Arabic verb, which can work as a lively loading quip. I am not confident that this viewpoint and verb choice are idiomatic in context; keep it held for an Arabic reviewer.',
 'holdReason':'Low confidence in idiom and viewpoint for the Arabic verb; native review required.'},
('ui.loading.dodgeBooks','de'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The infinitive fragment describes moving around the book stacks and works as a concise standalone loading message. Adapting the English wordplay into the physical action preserves the caller-level meaning. Pending qualified native review.'},
('ui.loading.dodgeBooks','es'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The gerund directly expresses dodging the piles and suits a rotating loading-message fragment. Translating the action instead of the English spelling pun preserves the caller-level joke. Pending qualified native review.'},
('ui.loading.dodgeBooks','fr'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The en esquivant construction reads as an action fragment and retains the physical evasion of the randomized loading quip. The English spelling pun is sensibly adapted. Pending qualified native review.'},
('ui.loading.dodgeBooks','hi'): {
 'disposition':'continue-hold','confidence':'low',
 'rationale':'The draft conveys avoiding these book piles, and the participial construction could fit a loading-message fragment. I cannot confidently assess its aspect and idiomatic standalone use here; keep it held for a Hindi reviewer.',
 'holdReason':'Low confidence in aspect and standalone idiom; native review required.'},
('ui.loading.dodgeBooks','ja'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft conveys nimbly dodging the piles and ends in a natural action-fragment shape for a loading quip. It adapts the English pun while retaining the motion. Pending qualified native review.'},
('ui.loading.dodgeBooks','ko'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft describes actively weaving around the piles, which fits the standalone randomized loading message. It preserves motion and playful energy without forcing the English spelling pun. Pending qualified native review.'},
('ui.loading.dodgeBooks','pt-BR'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The gerund directly conveys dodging these piles and is suitable for a short loading-message fragment. The physical action is preserved while the English spelling pun is adapted. Pending qualified native review.'},
('ui.loading.dodgeBooks','vi'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The draft conveys slipping around the stacks and reads as a concise action fragment for a rotating loading message. It preserves the physical evasion rather than leaving the English pun unexplained. Pending qualified native review.'},
('ui.loading.dodgeBooks','zh-Hans'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The verb phrase plainly conveys dodging the heaps of books and works as a concise standalone loading quip. It retains the physical action; the English -ing wordplay is adapted. Pending qualified native review.'},
('ui.loading.dodgeBooks','zh-Hant'): {
 'disposition':'endorse-draft-pending-native-review','confidence':'moderate',
 'rationale':'The verb phrase plainly conveys dodging the heaps of books and works as a concise standalone loading quip. It retains the physical action; the English -ing wordplay is adapted. Pending qualified native review.'},
}
if len(recs) != 20 or set(notes) != {(r['sourceId'], r['locale']) for r in recs}:
    raise SystemExit('recommendation scope mismatch')
rows=[]
for r in recs:
    key=(r['sourceId'],r['locale']); n=notes[key]
    rows.append({
      'window':r['window'],'sourceId':r['sourceId'],'sourceIdSha256':r['sourceIdSha256'],
      'locale':r['locale'],'source':r['source'],'sourceSha256':r['sourceSha256'],
      'callerCount':r['callerCount'],'callerContextSha256':r['callerContextSha256'],
      'currentTargetSha256':r['currentTargetSha256'],
      'draftTarget':r['independentTargetRecommendation'],
      'draftTargetSha256':hashlib.sha256(r['independentTargetRecommendation'].encode()).hexdigest(),
      'freshProposalSha256':r['targetRecommendationSha256'],
      'crossDisposition':n['disposition'],'confidence':n['confidence'],
      'rationale':n['rationale'],'continuedHold':n['disposition']=='continue-hold',
      'holdReason':n.get('holdReason'),
      'nativeSpeakerSignoff':False,'applicationStatus':'not applied'
    })
(OUT/'cross-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
summary={
 'artifact':'Independent cross-review of caller-linked creative-hold drafts',
 'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'head':'15fde999b8b8dc29d44833845aba13e1a2ad0443',
 'tree':'79f0882d1fa904ee967fb37ad1349dc6434c9537',
 'window':'W1200-W1209','crossReviewedCells':20,
 'endorseDraftPendingNativeReview':17,'continuedHolds':3,
 'confidenceCounts':{'moderate':17,'low':3},
 'sourceCallerCatalogPinsRechecked':16,'targetPreimagesRechecked':20,
 'callerlessHoldsHashOnly':True,'callerlessHoldHashesReattested':24,
 'callerlessTargetTextsIncluded':False,'nativeSpeakerSignoff':False,
 'catalogApplication':'none','repositoryOrPullRequestEdits':'none',
 'buildsTestsScansCiBrowserWorkflowChanges':'none',
 'continuedHoldLocales':{'ui.loading.newEbookSmell':['ar'],'ui.loading.dodgeBooks':['ar','hi']},
 'requiredBeforeApplication':'Qualified native-language review remains required for every endorsed draft; the three continued holds need particular language review before reconsideration.'
}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest={
 'artifact':'ChaptarrNG PR #190 creative-hold independent cross-review',
 'head':summary['head'],'tree':summary['tree'],'repository':summary['repository'],'pullRequest':190,
 'sourcePacket':'source-packet','sourcePacketSha256SumsSha256':hashlib.sha256((OUT/'source-packet/SHA256SUMS.txt').read_bytes()).hexdigest(),
 'freshProposalSha256':hashlib.sha256((OUT/'source-packet/review/independent-recommendations.jsonl').read_bytes()).hexdigest(),
 'crossLedger':'cross-ledger.jsonl','crossLedgerRows':20,
 'callerlessHoldRows':24,'callerlessHoldRepresentation':'hash-only; no target strings',
 'catalogApplication':'none','nativeSpeakerSignoff':False
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('''# ChaptarrNG PR #190 creative-hold cross-review\n\nThis separate second-opinion packet reviews the 20 fresh caller-linked W1200–W1209 drafts from `source-packet/`. It is pinned to PR head `15fde999b8b8dc29d44833845aba13e1a2ad0443` and tree `79f0882d1fa904ee967fb37ad1349dc6434c9537`.\n\nThe cross-ledger endorses 17 drafts for qualified native-language review and keeps 3 low-confidence drafts on hold: Arabic `ui.loading.newEbookSmell`, Arabic `ui.loading.dodgeBooks`, and Hindi `ui.loading.dodgeBooks`. The recorded draft text is not applied. No native-speaker signoff is claimed; every endorsed draft still requires qualified native review before catalog application.\n\nThe caller context confirms that the two creative messages are selected as standalone randomized loading quips; the provider label is an enum option distinguishing Castilian Spanish from Spanish. The ledger records a separate rationale and confidence for every cell.\n\nThe 24 callerless holds are carried only as hashes in `source-packet/input/callerless-hold-hashes-only.jsonl`. No callerless target strings are included.\n\nRun `python3 verify_cross_review.py` from this directory. The verifier requires authenticated GitHub CLI access and checks the live PR, tree, all 16 pinned source/caller/catalog files, all 20 target preimages, the 24 callerless target hashes, token constraints, and this packet’s checksums.\n\nNo repository or PR content was edited, and no catalog changes, tests, builds, scans, CI, browser, or workflow actions were performed.\n''',encoding='utf-8')
print('built',len(rows),'rows at',OUT)
