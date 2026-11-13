#!/usr/bin/env python3
"""Build an independent hold-only review packet at the exact live PR head."""
import hashlib, json, re, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/"input"
REVIEW=ROOT/"review"
SEED=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-reconsideration-20261103/live-input")
REPO=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w600-619-prep-20261103/repo")
EXPECTED_HEAD="15fde999b8b8dc29d44833845aba13e1a2ad0443"
EXPECTED_TREE="79f0882d1fa904ee967fb37ad1349dc6434c9537"
BRANCH="codex/chaptarrng-localization-complete-20261031"
REPOSITORY="snapetech-org/ChaptarrNG"
ACTIVE_HOLDS_PATH="docs/pr-evidence/pr190-localization-2026-11-03/review-gap-31/coverage-audit/active-holds.jsonl"
CALLER_STATUS_PATH="docs/pr-evidence/pr190-localization-2026-11-03/review-gap-31/candidate-free-packet/active-hold-caller-status.json"
LANGUAGE_PATHS={"ar":"src/NzbDrone.Core/Localization/Core/ar.json","de":"src/NzbDrone.Core/Localization/Core/de.json","es":"src/NzbDrone.Core/Localization/Core/es.json","fr":"src/NzbDrone.Core/Localization/Core/fr.json","hi":"src/NzbDrone.Core/Localization/Core/hi.json","id":"src/NzbDrone.Core/Localization/Core/id.json","ja":"src/NzbDrone.Core/Localization/Core/ja.json","ko":"src/NzbDrone.Core/Localization/Core/ko.json","pt-BR":"src/NzbDrone.Core/Localization/Core/pt_BR.json","vi":"src/NzbDrone.Core/Localization/Core/vi.json","zh-Hans":"src/NzbDrone.Core/Localization/Core/zh_CN.json","zh-Hant":"src/NzbDrone.Core/Localization/Core/zh_TW.json"}
LOCALES=list(LANGUAGE_PATHS)

def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def tokens(s):
    return {
        "placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),
        "markupTags":re.findall(r"<\/?[A-Za-z][^>]*>",s),
        "numericTokens":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),
        "protectedLiterals":[m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)]
    }

RECOMMENDATIONS={
("provider.option.o7285d46b982d","vi"):("Tiếng Tây Ban Nha Castilia","moderate","This is the enum label for the CastilianSpanish provider option. Castilia gives Vietnamese readers the regional variety name and keeps the existing distinction from the separate Spanish option.","regional language label"),
("ui.loading.newEbookSmell","ar"):("لا شيء يضاهي رائحة فتح كتاب جديد... إلكتروني؟","low","This loading quip sets up the familiar new-book smell and reveals an electronic book after the pause. The ellipsis and question preserve that sensory joke in Arabic.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","hi"):("नई... ई-पुस्तक खोलने की खुशबू जैसी कोई और चीज़ नहीं?","moderate","This loading quip sets up the smell of a new book, then reveals ई-पुस्तक after the pause. The question keeps the playful, knowingly impossible claim.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","id"):("Tak ada yang menandingi aroma membuka buku baru... buku elektronik?","moderate","This loading quip keeps the familiar new-book aroma setup and delays buku elektronik until after the pause, preserving the joke that an ebook has no paper smell.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","ja"):("新しい…電子書籍を開くときの香りに勝るものはありませんよね？","moderate","This loading quip keeps the new-book aroma setup, delays 電子書籍 after the ellipsis, and ends with a rhetorical question.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","ko"):("새... 전자책을 펼칠 때 나는 냄새만큼 좋은 건 없죠?","moderate","This loading quip delays 전자책 until after the pause and keeps the rhetorical claim about the smell of opening a new book.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","vi"):("Không gì sánh bằng mùi thơm khi mở một cuốn sách mới... sách điện tử?","moderate","This loading quip preserves the new-book smell setup and reveals sách điện tử after the pause, keeping the rhetorical surprise.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","zh-Hans"):("打开一本新……电子书时的气味，真是无与伦比，对吧？","moderate","This loading quip delays 电子书 after the ellipsis and preserves the rhetorical new-book smell claim and its ebook punchline.","creative ellipsis and reveal"),
("ui.loading.newEbookSmell","zh-Hant"):("打開一本新……電子書時的氣味，真是無與倫比，對吧？","moderate","This loading quip delays 電子書 after the ellipsis and preserves the rhetorical new-book smell claim and its ebook punchline.","creative ellipsis and reveal"),
("ui.loading.dodgeBooks","ar"):("أراوغ أكوام الكتب هذه","low","The source is a playful loading-message fragment about dodging book piles. This uses an Arabic verb for maneuvering around them; the English Dodge-ing wordplay is adapted rather than left untranslated.","creative verb adaptation"),
("ui.loading.dodgeBooks","de"):("Diesen Bücherstapeln ausweichen","moderate","The source is a playful loading-message fragment about dodging book piles. This keeps the physical evasion in a natural German infinitive fragment instead of leaving Dodge-ing in English.","creative verb adaptation"),
("ui.loading.dodgeBooks","es"):("Esquivando estas pilas de libros","moderate","The source is a playful loading-message fragment about dodging book piles. Esquivando keeps the action and gerund-like fragment naturally in Spanish.","creative verb adaptation"),
("ui.loading.dodgeBooks","fr"):("En esquivant ces piles de livres","moderate","The source is a playful loading-message fragment about dodging book piles. En esquivant keeps the action and fragment naturally in French.","creative verb adaptation"),
("ui.loading.dodgeBooks","hi"):("किताबों के इन ढेरों से बचते हुए","low","The source is a playful loading-message fragment about dodging book piles. This renders the physical evasion in Hindi; the English Dodge-ing wordplay is adapted rather than left untranslated.","creative verb adaptation"),
("ui.loading.dodgeBooks","ja"):("本の山をひらりと避けながら","moderate","The source is a playful loading-message fragment about dodging book piles. ひらりと adds a light, nimble feel while 避けながら keeps the action.","creative verb adaptation"),
("ui.loading.dodgeBooks","ko"):("이 책 더미들을 요리조리 피해 가는 중","moderate","The source is a playful loading-message fragment about dodging book piles. 요리조리 conveys weaving around them and keeps the playful motion.","creative verb adaptation"),
("ui.loading.dodgeBooks","pt-BR"):("Desviando dessas pilhas de livros","moderate","The source is a playful loading-message fragment about dodging book piles. Desviando keeps the action and gerund-like fragment naturally in Brazilian Portuguese.","creative verb adaptation"),
("ui.loading.dodgeBooks","vi"):("Lách qua những chồng sách này","moderate","The source is a playful loading-message fragment about dodging book piles. Lách qua conveys weaving around the stacks in concise Vietnamese.","creative verb adaptation"),
("ui.loading.dodgeBooks","zh-Hans"):("躲开这些成堆的书","moderate","The source is a playful loading-message fragment about dodging book piles. 躲开 renders the physical action directly instead of retaining the untranslated English pun.","creative verb adaptation"),
("ui.loading.dodgeBooks","zh-Hant"):("閃避這些成堆的書","moderate","The source is a playful loading-message fragment about dodging book piles. 閃避 renders the physical action directly instead of retaining the untranslated English pun.","creative verb adaptation"),
}

def run(cmd,cwd=None): return subprocess.check_output(cmd,cwd=cwd,text=True).strip()
def pr_snapshot():
    pr=json.loads(run(["gh","pr","view","190","--repo",REPOSITORY,"--json","state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url"]))
    raw=run(["git","-C",str(REPO),"ls-remote","origin",f"refs/heads/{BRANCH}","refs/pull/190/head"])
    refs={x.split("\t",1)[1]:x.split("\t",1)[0] for x in raw.splitlines()}
    head=run(["git","-C",str(REPO),"rev-parse","HEAD"]); tree=run(["git","-C",str(REPO),"rev-parse","HEAD^{tree}"])
    status=run(["git","-C",str(REPO),"status","--porcelain=v1"])
    assert head==EXPECTED_HEAD and tree==EXPECTED_TREE and not status
    assert pr["state"]=="OPEN" and pr["isDraft"] is True and pr["headRefName"]==BRANCH and pr["headRefOid"]==EXPECTED_HEAD
    assert refs=={f"refs/heads/{BRANCH}":EXPECTED_HEAD,"refs/pull/190/head":EXPECTED_HEAD}
    return {"observedAtUtc":datetime.now(timezone.utc).isoformat(),"repository":REPOSITORY,"pullRequest":190,"state":pr["state"],"draft":pr["isDraft"],"url":pr["url"],"branch":pr["headRefName"],"baseRef":pr["baseRefName"],"baseSha":pr["baseRefOid"],"head":head,"tree":tree,"branchRef":refs[f"refs/heads/{BRANCH}"],"pullRef":refs["refs/pull/190/head"],"checkoutClean":True}

def live_file_pin(path,kind):
    data=(REPO/path).read_bytes()
    blob=run(["git","-C",str(REPO),"rev-parse",f"HEAD:{path}"])
    return {"path":path,"kind":kind,"byteCount":len(data),"sha256":sha(data),"gitBlob":blob}

def build():
    INPUT.mkdir(parents=True,exist_ok=True); REVIEW.mkdir(parents=True,exist_ok=True)
    before=pr_snapshot()
    seed_ctx=readjl(SEED/"source-and-caller-context.jsonl")
    seed_cells=readjl(SEED/"current-target-cells.jsonl")
    assert len(seed_ctx)==3 and len(seed_cells)==20
    source_path=seed_ctx[0]["sourceFile"]
    assert all(r["sourceFile"]==source_path for r in seed_ctx)
    source_data=(REPO/source_path).read_bytes()
    source_catalog=json.loads(source_data)
    contexts=[]; refs_by_path={}
    for item in seed_ctx:
        source_id=item["sourceId"]; source=source_catalog[source_id]
        assert source==item["source"] and sha_text(source)==item["sourceSha256"]
        callers=[]
        for old in item["callerReferences"]:
            path=old["path"]; fpin=live_file_pin(path,"production-caller")
            assert fpin["sha256"]==old["fileSha256"] and fpin["gitBlob"]==old["gitBlob"]
            lines=(REPO/path).read_text(encoding="utf-8").splitlines()
            line_rows=[]
            for old_line in old["contextLines"]:
                text=lines[old_line["line"]-1]
                assert text==old_line["text"] and sha_text(text)==old_line["lineSha256"]
                line_rows.append({"line":old_line["line"],"text":text,"lineSha256":sha_text(text)})
            refs_by_path[path]=fpin
            caller={"path":path,"fileSha256":fpin["sha256"],"gitBlob":fpin["gitBlob"],"startLine":old["startLine"],"endLine":old["endLine"],"contextLines":line_rows}
            caller["freshContextSha256"]=sha_text(canon(caller))
            callers.append(caller)
        contexts.append({"sourceId":source_id,"source":source,"sourceSha256":sha_text(source),"sourceFile":source_path,"sourceFileSha256":sha(source_data),"sourceFileGitBlob":run(["git","-C",str(REPO),"rev-parse",f"HEAD:{source_path}"]),"callerCount":len(callers),"callerReferences":callers,"callerContextSha256":sha_text(canon(callers))})
    assert all(x["callerCount"]>0 for x in contexts)
    current_cells=[]; catalog_files={}
    for seed in seed_cells:
        locale=seed["locale"]; source_id=seed["sourceId"]; target_path=LANGUAGE_PATHS[locale]
        if target_path not in catalog_files:
            data=(REPO/target_path).read_bytes(); catalog_files[target_path]=json.loads(data)
        target=catalog_files[target_path].get(source_id)
        assert isinstance(target,str)
        target_hash=sha_text(target)
        assert target_hash==seed["currentTargetSha256"],(source_id,locale)
        pin=live_file_pin(target_path,"locale-catalog")
        current_cells.append({"sourceId":source_id,"source":source_catalog[source_id],"sourceSha256":sha_text(source_catalog[source_id]),"locale":locale,"targetFile":target_path,"targetFileSha256":pin["sha256"],"targetFileGitBlob":pin["gitBlob"],"currentTarget":target,"currentTargetSha256":target_hash,"targetUnchangedFromCandidateFreeSeed":True,"sourceTokens":tokens(source_catalog[source_id]),"currentTargetTokens":tokens(target)})
    assert len(current_cells)==20 and len({(x["sourceId"],x["locale"]) for x in current_cells})==20
    source_pin=live_file_pin(source_path,"source-catalog")
    filepins={source_path:source_pin,**refs_by_path}
    for locale,path in LANGUAGE_PATHS.items():
        filepins[path]=live_file_pin(path,"locale-catalog")
    assert len(filepins)==16
    # Callerless holds are explicitly excluded and represented only by hashes.
    active_path=REPO/ACTIVE_HOLDS_PATH; status_path=REPO/CALLER_STATUS_PATH
    active_rows=readjl(active_path); status=readj(status_path)
    callerless_ordinals=set(status["summary"]["groupsWithoutExactUserFacingCaller"])
    assert len(callerless_ordinals)==2
    callerless_ids={g["sourceId"] for g in status["groups"] if g["sourceOrdinal"] in callerless_ordinals and not g["exactUserFacingCallerFound"]}
    assert len(callerless_ids)==2
    all_catalogs={locale:catalog_files.get(path) or json.loads((REPO/path).read_text(encoding="utf-8")) for locale,path in LANGUAGE_PATHS.items()}
    exclusions=[]
    for row in active_rows:
        if row["sourceOrdinal"] not in callerless_ordinals: continue
        src=source_catalog[row["sourceId"]]
        assert row["sourceId"] in callerless_ids and sha_text(src)==row["sourceTextSha256"]
        target=all_catalogs[row["locale"]][row["sourceId"]]
        live_target_hash=sha_text(target)
        exclusions.append({"sourceOrdinal":row["sourceOrdinal"],"sourceIdSha256":sha_text(row["sourceId"]),"locale":row["locale"],"sourceTextSha256":sha_text(src),"recordedTargetSha256":row["currentTargetSha256"],"liveTargetSha256":live_target_hash,"sourceTextHashSameAtHead":True,"targetHashSameAtHead":live_target_hash==row["currentTargetSha256"],"evidenceSha256":row["evidenceSha256"]})
    exclusions.sort(key=lambda x:(x["sourceOrdinal"],x["locale"]))
    assert len(exclusions)==24 and len({(x["sourceOrdinal"],x["locale"]) for x in exclusions})==24
    assert all(set(x)=={"sourceOrdinal","sourceIdSha256","locale","sourceTextSha256","recordedTargetSha256","liveTargetSha256","sourceTextHashSameAtHead","targetHashSameAtHead","evidenceSha256"} for x in exclusions)
    # Re-attest candidate-free hash-only evidence blobs at this exact head.
    evidence_pins=[live_file_pin(ACTIVE_HOLDS_PATH,"hash-only-hold-inventory"),live_file_pin(CALLER_STATUS_PATH,"hash-only-caller-status")]
    (INPUT/"source-caller-context.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in contexts),encoding="utf-8")
    (INPUT/"creative-current-cells.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in current_cells),encoding="utf-8")
    (INPUT/"callerless-hold-hashes-only.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in exclusions),encoding="utf-8")
    (INPUT/"file-pins.json").write_text(json.dumps({"head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"sourceCatalogCallerCatalogPinCount":len(filepins),"pins":sorted(filepins.values(),key=lambda x:x["path"]),"hashOnlyExclusionEvidencePins":evidence_pins},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (INPUT/"PR-attestation.json").write_text(json.dumps(before,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    seed_files={name:sha((SEED/name).read_bytes()) for name in ("manifest.json","source-and-caller-context.jsonl","current-target-cells.jsonl","SHA256SUMS.txt")}
    seedm=readj(SEED/"manifest.json")
    assert seedm["candidateFree"] and not seedm["translationCandidatesIncluded"] and not seedm["priorReviewVerdictsIncluded"]
    im={"artifact":"Fresh ChaptarrNG PR #190 W1200-W1209 caller-linked creative hold source/caller input","repository":REPOSITORY,"pullRequest":190,"head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"window":"W1200-W1209","creativeSourceCount":3,"creativeCellCount":20,"callerlessHoldExcludedCount":24,"callerlessHoldContentIncluded":False,"callerlessHoldHashOnly":True,"callerlessHoldCellsUnchangedAtHead":sum(x["targetHashSameAtHead"] for x in exclusions),"sourceCallerCatalogPinCount":len(filepins),"callerFileCount":len(refs_by_path),"callerReferenceCount":sum(x["callerCount"] for x in contexts),"seedCandidateFree":True,"seedHadTranslationCandidates":False,"seedHadPriorReviewVerdicts":False,"seedFileHashes":seed_files,"evidencePins":evidence_pins}
    (INPUT/"manifest.json").write_text(json.dumps(im,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (INPUT/"README.md").write_text("# Fresh ChaptarrNG PR #190 W1200-W1209 hold-only input\n\nRebuilt from the candidate-free source/caller seed and exact live PR head "+EXPECTED_HEAD+" / "+EXPECTED_TREE+". It contains 3 caller-linked creative source contexts and 20 current catalog cells, all re-read from the live checkout. The candidate-free seed contains no translation candidates or prior verdicts.\n\nThe 24 callerless holds are excluded from translation review. Their inventory is hash-only: source IDs are represented by hashes, and no source strings, target strings, or recommendations are included. Source and target digests are reattested at the live head.\n\nThe 16 source, caller, and locale catalog file pins match the exact head. The PR and refs were OPEN/DRAFT and equal to the pinned head at packet creation.\n",encoding="utf-8")
    write_sums(INPUT,INPUT/"SHA256SUMS.txt")
    recs=[]
    caller_by_id={x["sourceId"]:x for x in contexts}
    for cell in current_cells:
        key=(cell["sourceId"],cell["locale"])
        assert key in RECOMMENDATIONS
        target,confidence,rationale,kind=RECOMMENDATIONS[key]
        src_tokens=tokens(cell["source"])
        target_tokens=tokens(target)
        assert all(src_tokens[k]==target_tokens[k] for k in src_tokens),key
        ctx=caller_by_id[cell["sourceId"]]
        recs.append({"window":"W1200-W1209","sourceId":cell["sourceId"],"sourceIdSha256":sha_text(cell["sourceId"]),"source":cell["source"],"sourceSha256":cell["sourceSha256"],"locale":cell["locale"],"callerCount":ctx["callerCount"],"callerContextSha256":ctx["callerContextSha256"],"currentTarget":cell["currentTarget"],"currentTargetSha256":cell["currentTargetSha256"],"independentTargetRecommendation":target,"targetRecommendationSha256":sha_text(target),"decision":"recommend-target","rationale":rationale,"rationaleKind":kind,"confidence":confidence,"confidenceRationale":"Confidence reflects translation judgment only; these creative targets have not received native-speaker signoff.","sourceTokenChecks":src_tokens,"recommendedTargetTokenChecks":target_tokens,"placeholderMarkupNumericProtectedChecksPass":True,"nativeSpeakerSignoff":False,"applicationStatus":"not applied"})
    assert len(recs)==20
    (REVIEW/"independent-recommendations.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in recs),encoding="utf-8")
    after=pr_snapshot()
    assert before["head"]==after["head"] and before["tree"]==after["tree"] and before["branchRef"]==after["branchRef"] and before["pullRef"]==after["pullRef"]
    # Recheck all 16 file pins after ledger construction.
    after_pins=[live_file_pin(path,x["kind"]) for path,x in filepins.items()]
    assert all(x["sha256"]==filepins[x["path"]]["sha256"] and x["gitBlob"]==filepins[x["path"]]["gitBlob"] for x in after_pins)
    (REVIEW/"live-pr-and-pin-after.json").write_text(json.dumps({"afterLedger":after,"sourceCallerCatalogPinCount":len(after_pins),"pins":sorted(after_pins,key=lambda x:x["path"]),"creativeTargetCount":20,"creativeTargetsReattested":True,"callerlessHoldHashCount":len(exclusions),"callerlessHoldTargetsHashOnly":True},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cc=Counter(x["confidence"] for x in recs)
    hold_summary={"artifact":"Independent review of caller-linked creative holds","repository":REPOSITORY,"pullRequest":190,"head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"window":"W1200-W1209","creativeSourceCount":3,"creativeCellCount":20,"decisionCounts":{"recommend-target":20,"continued-hold":0},"recommendationsBySource":dict(Counter(x["sourceId"] for x in recs)),"confidenceCounts":dict(cc),"callerBackedSourceCount":len(contexts),"callerReferenceCount":sum(x["callerCount"] for x in contexts),"callerFileCount":len(refs_by_path),"sourceCallerCatalogPins":len(filepins),"callerlessHoldsExcluded":24,"callerlessHoldsHashOnly":True,"callerlessHashCellsReattested":len(exclusions),"callerlessHashesUnchangedAtHead":sum(x["targetHashSameAtHead"] for x in exclusions),"callerlessTargetTextsIncluded":False,"selectedTargetTokenFailures":0,"nativeSpeakerSignoff":False,"nextRequiredReview":"A qualified native-language reviewer should review these creative recommendations before any catalog application; no target has been applied.","noRepoOrPrEdits":True,"noTestsBuildsScansCi":True}
    (REVIEW/"summary.json").write_text(json.dumps(hold_summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (REVIEW/"README.md").write_text("# Independent ChaptarrNG creative-hold review\n\nThis ledger gives fresh recommendations for all 20 caller-linked creative cells. It was prepared from the exact English source strings and caller contexts, with live catalog values recorded only as the current baseline. The 24 callerless holds remain out of scope and appear only as hashes in the input packet.\n\nRecommendations are not applied. Confidence is recorded per cell. No native-speaker signoff is claimed; a qualified native-language review is the next required review before any catalog change.\n",encoding="utf-8")
    write_verifier(REVIEW/"verify_review.py")
    rfiles=sorted(x for x in REVIEW.iterdir() if x.is_file() and x.name not in {"manifest.json","SHA256SUMS.txt"})
    rm={"artifact":"Independent ChaptarrNG PR #190 creative hold recommendations","head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"window":"W1200-W1209","recommendationCount":20,"hashOnlyCallerlessHoldCount":24,"recommendationCounts":dict(Counter(x["decision"] for x in recs)),"fileHashes":{x.name:{"sha256":sha(x.read_bytes()),"byteCount":x.stat().st_size} for x in rfiles}}
    (REVIEW/"manifest.json").write_text(json.dumps(rm,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); write_sums(REVIEW,REVIEW/"SHA256SUMS.txt")
    (ROOT/"README.md").write_text("# ChaptarrNG PR #190 W1200-W1209 creative hold review\n\nFresh exact-head review packet for 20 caller-linked creative hold cells. The 24 callerless holds are out of scope and are reattested hash-only. No earlier primary/blind target proposals were used as starting values.\n\nExact live OPEN/DRAFT head/tree: "+EXPECTED_HEAD+" / "+EXPECTED_TREE+". Recommendations are not applied. No tests, builds, scans, CI, browser, or workflow changes were made. See review/README.md for the next required review.\n",encoding="utf-8")
    root_files=sorted(x for x in ROOT.rglob("*") if x.is_file() and x.name not in {"manifest.json","SHA256SUMS.txt"})
    rootm={"artifact":"Fresh ChaptarrNG PR #190 W1200-W1209 independent creative hold review evidence","repository":REPOSITORY,"pullRequest":190,"stateAtSeal":after["state"],"draftAtSeal":after["draft"],"head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"branch":BRANCH,"window":"W1200-W1209","creativeSourceCount":3,"creativeCellCount":20,"recommendationCounts":dict(Counter(x["decision"] for x in recs)),"confidenceCounts":dict(cc),"callerlessHoldsOutOfScope":24,"callerlessHoldHashesOnly":True,"callerlessHashCount":len(exclusions),"callerlessHashesUnchangedAtHead":sum(x["targetHashSameAtHead"] for x in exclusions),"sourceCallerCatalogPinCount":len(filepins),"callerFiles":len(refs_by_path),"callerReferences":sum(x["callerCount"] for x in contexts),"nativeSpeakerSignoff":False,"nextRequiredReview":"Qualified native-language review of the 20 creative recommendations before any application.","repositoryOrPrModified":False,"testsBuildsScansCiRun":False,"fileHashes":{str(x.relative_to(ROOT)):{"sha256":sha(x.read_bytes()),"byteCount":x.stat().st_size} for x in root_files}}
    (ROOT/"manifest.json").write_text(json.dumps(rootm,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); write_sums(ROOT,ROOT/"SHA256SUMS.txt")
    print(json.dumps({"result":"BUILT","head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"creativeCells":len(recs),"callerlessHashCells":len(exclusions),"callerlessHashesUnchanged":sum(x["targetHashSameAtHead"] for x in exclusions),"sourceCallerCatalogPins":len(filepins),"callerReferences":sum(x["callerCount"] for x in contexts),"recommendationCount":len(recs),"confidenceCounts":dict(cc),"bytes":sum(x.stat().st_size for x in ROOT.rglob("*") if x.is_file())},ensure_ascii=False,indent=2))

def write_sums(directory,output):
    output.write_text("".join(f"{sha(p.read_bytes())}  {p.relative_to(directory).as_posix()}\n" for p in sorted(x for x in directory.rglob("*") if x.is_file() and x!=output)),encoding="utf-8")

def write_verifier(path):
    path.write_text(r'''#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; INPUT=ROOT/"input"; REVIEW=ROOT/"review"
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def sums(d,n):
 f=d/n; rows=[line.split(None,1) for line in f.read_text().splitlines()]
 entries=[(x[1].lstrip("* "),x[0]) for x in rows]
 actual={p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file() and p!=f}
 assert len(entries)==len({p for p,_ in entries}) and {p for p,_ in entries}==actual
 for p,h in entries: assert sha((d/p).read_bytes())==h,p
 return len(entries)
def tokens(s):
 return {"placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),"markupTags":re.findall(r"<\/?[A-Za-z][^>]*>",s),"numericTokens":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),"protectedLiterals":[m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)]}
root=readj(ROOT/"manifest.json"); review=readj(REVIEW/"manifest.json"); summary=readj(REVIEW/"summary.json")
assert root["head"]==review["head"]=="15fde999b8b8dc29d44833845aba13e1a2ad0443" and root["tree"]==review["tree"]=="79f0882d1fa904ee967fb37ad1349dc6434c9537"
assert root["creativeCellCount"]==review["recommendationCount"]==summary["creativeCellCount"]==20
assert root["callerlessHoldsOutOfScope"]==root["callerlessHashCount"]==summary["callerlessHoldsExcluded"]==24
root_n=sums(ROOT,"SHA256SUMS.txt"); review_n=sums(REVIEW,"SHA256SUMS.txt"); input_n=sums(INPUT,"SHA256SUMS.txt")
contexts=readjl(INPUT/"source-caller-context.jsonl"); cells=readjl(INPUT/"creative-current-cells.jsonl"); recs=readjl(REVIEW/"independent-recommendations.jsonl"); exclusions=readjl(INPUT/"callerless-hold-hashes-only.jsonl")
assert len(contexts)==3 and len(cells)==len(recs)==20 and len(exclusions)==24
byctx={x["sourceId"]:x for x in contexts}; bycell={(x["sourceId"],x["locale"]):x for x in cells}
assert len(bycell)==20
for x in contexts:
 assert x["sourceSha256"]==sha_text(x["source"]) and x["callerCount"]==len(x["callerReferences"])>0
 for c in x["callerReferences"]:
  assert c["freshContextSha256"] and all(q["lineSha256"]==sha_text(q["text"]) for q in c["contextLines"])
for c in cells:
 assert c["currentTargetSha256"]==sha_text(c["currentTarget"])
 assert c["sourceTokens"]==tokens(c["source"]) and c["currentTargetTokens"]==tokens(c["currentTarget"])
 assert c["targetUnchangedFromCandidateFreeSeed"] is True
for r in recs:
 key=(r["sourceId"],r["locale"]); c=bycell[key]; x=byctx[r["sourceId"]]
 assert r["source"]==c["source"] and r["sourceSha256"]==c["sourceSha256"]==sha_text(r["source"])
 assert r["currentTarget"]==c["currentTarget"] and r["currentTargetSha256"]==c["currentTargetSha256"]
 assert r["targetRecommendationSha256"]==sha_text(r["independentTargetRecommendation"])
 assert r["decision"]=="recommend-target" and r["confidence"] in {"high","moderate","low","unknown"}
 assert r["callerCount"]==x["callerCount"] and r["nativeSpeakerSignoff"] is False and r["applicationStatus"]=="not applied"
 assert r["sourceTokenChecks"]==tokens(r["source"]) and r["recommendedTargetTokenChecks"]==tokens(r["independentTargetRecommendation"])
 for k in r["sourceTokenChecks"]: assert r["sourceTokenChecks"][k]==r["recommendedTargetTokenChecks"][k]
assert len({(x["sourceOrdinal"],x["locale"]) for x in exclusions})==24
for x in exclusions:
 assert set(x)=={"sourceOrdinal","sourceIdSha256","locale","sourceTextSha256","recordedTargetSha256","liveTargetSha256","sourceTextHashSameAtHead","targetHashSameAtHead","evidenceSha256"}
 assert x["sourceTextHashSameAtHead"] is True and all(len(x[k])==64 for k in ["sourceIdSha256","sourceTextSha256","recordedTargetSha256","liveTargetSha256","evidenceSha256"])
pin=readj(INPUT/"file-pins.json"); live=readj(REVIEW/"live-pr-and-pin-after.json")
assert len(pin["pins"])==16 and pin["head"]=="15fde999b8b8dc29d44833845aba13e1a2ad0443" and pin["tree"]=="79f0882d1fa904ee967fb37ad1349dc6434c9537"
assert live["afterLedger"]["head"]==live["afterLedger"]["branchRef"]==live["afterLedger"]["pullRef"]==root["head"]
assert live["afterLedger"]["state"]=="OPEN" and live["afterLedger"]["draft"] is True and live["creativeTargetsReattested"] is True
assert live["callerlessHoldHashCount"]==24 and live["callerlessHoldTargetsHashOnly"] is True
print(json.dumps({"result":"PASS","head":root["head"],"tree":root["tree"],"recommendations":len(recs),"callerlessHashOnlyCells":len(exclusions),"callerlessHashMatchesAtHead":sum(x["targetHashSameAtHead"] for x in exclusions),"sourceCallerCatalogPins":len(pin["pins"]),"rootChecksumEntries":root_n,"reviewChecksumEntries":review_n,"inputChecksumEntries":input_n,"nativeSpeakerSignoff":False},ensure_ascii=False,indent=2))
''',encoding="utf-8")

if __name__=="__main__": build()

