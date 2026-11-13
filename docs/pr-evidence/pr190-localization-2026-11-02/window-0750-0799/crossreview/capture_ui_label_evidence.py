import hashlib,json,pathlib,subprocess
repo=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0750-0799-a58de8c')
out=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-crossreview-20261102')
primary=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-primary-20261102')
manifest=json.load(open(primary/'input-manifest.json'))
sha=lambda b:hashlib.sha256(b).hexdigest()
def blob(b):
    # Match Git's object ID; the content is also pinned with SHA-256 above.
    return subprocess.check_output(['git','hash-object','--stdin'],input=b).decode().strip()
def pin(path,line_no):
    data=(repo/path).read_bytes(); lines=data.decode('utf-8').splitlines(); line=lines[line_no-1].strip()
    return {'path':path,'line':line_no,'lineText':line,'lineSha256':sha(line.encode()),'fileSha256':sha(data),'gitBlob':blob(data),'bytes':len(data),'contextBefore':[x.strip() for x in lines[max(0,line_no-4):line_no-1]],'contextAfter':[x.strip() for x in lines[line_no:min(len(lines),line_no+3)]]}
source=json.load(open(repo/manifest['sourceCatalog']['path']))
labels=[]
for locale,info in manifest['localeCatalogs'].items():
    cat=json.load(open(repo/info['path']))
    labels.append({'locale':locale,'catalogPath':info['path'],'catalogSha256':info['sha256'],'catalogBlob':info['blob'],'Bookshelf':cat['Bookshelf'],'AuthorEditor':cat['AuthorEditor']})
row=[json.loads(line) for line in open(primary/'source-slice.jsonl') if json.loads(line)['sourceOrdinal']==770][0]
evidence={
 'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'exactHead':manifest['head'],'exactTree':manifest['tree'],
 'message':{'sourceOrdinal':770,'sourceId':row['sourceId'],'source':row['source'],'sourceTextSha256':row['sourceTextSha256'],'sourceCallerRefs':[r for c in [json.loads(x) for x in open(primary/'caller-context.jsonl')] if c['sourceId']==row['sourceId'] for r in c['callerRefs']]},
 'englishLabelCatalog':{'path':manifest['sourceCatalog']['path'],'sha256':manifest['sourceCatalog']['sha256'],'blob':manifest['sourceCatalog']['blob'],'Bookshelf':source['Bookshelf'],'AuthorEditor':source['AuthorEditor']},
 'localeLabels':labels,
 'frontendUsesLabels':[
   {'key':'Bookshelf','purpose':'Bookshelf page sidebar title','pin':pin('frontend/src/Components/Page/Sidebar/PageSidebar.js',45)},
   {'key':'AuthorEditor','purpose':'Author Editor tab button label','pin':pin('frontend/src/Author/Index/AuthorIndex.js',497)}
 ],
 'finding':'The W770 API message names these two user-visible destinations. Both keys have exact locale-specific catalog values and the frontend reads those keys for the visible labels. The literal Bookshelf exception recorded in the primary packet therefore does not apply to this use; candidate targets should reuse these localized UI labels.'
}
(out/'ui-label-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'exactHead':evidence['exactHead'],'exactTree':evidence['exactTree'],'localeLabels':len(labels),'frontendPins':evidence['frontendUsesLabels'],'path':str(out/'ui-label-evidence.json')},ensure_ascii=False,indent=2))
