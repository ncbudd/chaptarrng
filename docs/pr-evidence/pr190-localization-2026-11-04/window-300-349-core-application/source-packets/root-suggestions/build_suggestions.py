#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

BASE = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104/candidate-free/input')
OUT = Path(__file__).resolve().parent
HEAD = 'f0082d1b655c05b8d4019ede523dd695cd6d745a'
TREE = '4cf2322354e9cf9b12d59cf10d0d8661c68ab4af'
VALUES = {
(308,'ja'): 'バランス型',
(311,'de'): 'Streng: Erfordert ein sauberes Tag-Feld, in dem der Titel und der nahe gelegene aussagekräftige Text durch die Metadaten des Buches erklärt werden. Eine widersprüchliche Reihenposition macht dieses Feld ungültig. Pfad-Fallback ist deaktiviert.',
(315,'vi'): 'Thông tin chính xác về tác giả/người kể chuyện/loạt sách',
(315,'zh-Hant'): '準確的作者／旁白／系列資訊',
(321,'fr'): 'Mots supplémentaires sans rapport',
(326,'de'): 'Der Status der Slots für Torrents, die ihre Anforderungen noch nicht erfüllen, ist nicht verfügbar oder veraltet. Downloads von diesen MyAnonaMouse-Indexern sind daher blockiert, bis der Status aktualisiert wird: {0}',
(326,'es'): 'El estado de los cupos para torrents que aún no cumplen los requisitos no está disponible o está desactualizado, por lo que las descargas desde estos indexadores de MyAnonaMouse están bloqueadas hasta que se actualice: {0}',
(326,'fr'): 'L’état des emplacements pour les torrents qui ne remplissent pas encore les conditions est indisponible ou obsolète. Les téléchargements depuis ces indexeurs MyAnonaMouse sont donc bloqués jusqu’à la mise à jour de l’état : {0}',
(326,'ja'): '要件を満たしていないトレントのスロット状況を取得できないか、情報が古いため、状態が更新されるまでこれらのMyAnonaMouseインデクサーからのダウンロードはブロックされます: {0}',
(326,'pt-BR'): 'O status dos slots de torrents que ainda não atendem aos critérios está indisponível ou desatualizado, então os downloads desses indexadores MyAnonaMouse ficam bloqueados até a atualização do status: {0}',
(329,'zh-Hant'): '缺少權杖金鑰。',
(334,'ar'): 'كلمات إضافية مشوشة',
(334,'ja'): '雑然とした余分な語句',
(338,'ar'): 'جارٍ إنشاء المعاينة…',
(339,'ar'): 'تمت معالجتها',
(343,'ar'): 'العناصر المؤهلة للبحث',
(343,'de'): 'Für die Suche geeignete Elemente',
(343,'ja'): '検索可能な項目',
(348,'ar'): 'قيد المزامنة',
}

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

raw = (BASE/'candidate-free-cells.jsonl').read_bytes().splitlines()
rows = [json.loads(line) for line in raw if line.strip()]
raw_by_ident = {}
for line in raw:
    if not line.strip(): continue
    row = json.loads(line)
    raw_by_ident[(row['sourceOrdinal'], row['locale'])] = line
input_manifest = json.loads((BASE/'candidate-free-manifest.json').read_text())
by_ident = {(row['sourceOrdinal'],row['locale']): row for row in rows}
proposals=[]
for (ordinal,locale), target in sorted(VALUES.items()):
    row=by_ident[(ordinal,locale)]
    proposals.append({
      'batch':'W300-349-Core','exactHead':HEAD,'exactTree':TREE,
      'sourceOrdinal':ordinal,'sourceKey':row['sourceKey'],'cellId':f"{row['sourceKey']}::{locale}",'locale':locale,
      'sourceText':row['sourceText'],'sourceTextSha256':row['sourceTextSha256'],
      'currentTarget':row['currentTarget'],'currentTargetSha256':row['currentTargetSha256'],
      'proposedTarget':target,'proposedTargetSha256':sha(target.encode()),
      'candidateFreeRowSha256':sha(raw_by_ident[(ordinal,locale)]),
      'callerContextSha256':row['callerContextSha256'],'callerReferenceCount':row['callerReferenceCount'],
      'sourceFileGitBlob':row['sourceFileGitBlob'],'targetFileGitBlob':row['targetFileGitBlob'],
      'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True
    })
(OUT/'root-hold-proposals.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for p in proposals))
manifest={
 'artifact':'ChaptarrNG PR #190 W300-W349 root suggestions for direct-caller blind holds',
 'repository':'snapetech-org/chaptarrng','pullRequest':190,'window':'W300-W349-Core',
 'head':HEAD,'tree':TREE,'candidateFreeInputManifestSha256':sha((BASE/'candidate-free-manifest.json').read_bytes()),
 'candidateFreeChecksumListSha256':sha((BASE/'SHA256SUMS.txt').read_bytes()),
 'proposalCount':len(proposals),'cellIds':[p['cellId'] for p in proposals],
 'proposalsFileSha256':sha((OUT/'root-hold-proposals.jsonl').read_bytes()),
 'independence':'Root-generated suggestions from direct caller context; no primary-proposal target text was used to author these 19 suggestions. Cross-review receives only this file and candidate-free input, not other review outputs or the PR body.'
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'README.md').write_text(f'''# ChaptarrNG W300–W349 root suggestions for direct-caller blind holds\n\nThis separate task packet proposes wording for {len(proposals)} direct-caller-backed cells that the independent blind review held for semantic concern and that were not in the primary proposal set. It is pinned to `{HEAD}` / `{TREE}`. It contains exact source/current target text and hashes, the candidate-free row hash, caller-context hash and proposed target.\n\nA fresh cross-reviewer should verify all target wording against only `root-hold-proposals.jsonl` plus the candidate-free input at `{BASE}`. Do not use the primary, blind, or earlier cross-review outputs, nor read the PR body. Nothing is applied by this packet.\n''')
files=['root-hold-proposals.jsonl','manifest.json','README.md','build_suggestions.py']
(OUT/'SHA256SUMS.txt').write_text(''.join(f"{sha((OUT/name).read_bytes())}  {name}\n" for name in files))
print(json.dumps({'result':'SEALED-SUGGESTIONS','count':len(proposals),'manifestSha256':sha((OUT/'manifest.json').read_bytes()),'checksums':len(files)},sort_keys=True))
