import hashlib,json,subprocess
from pathlib import Path
root=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w600-619-prep-20261103/repo")
p=Path(__file__).parent
m=json.loads((p/"manifest.json").read_text()); d=json.loads((p/"input.json").read_text())
assert hashlib.sha256((p/"input.json").read_bytes()).hexdigest()==m["inputSha256"]
assert subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()==m["exactHead"]
assert subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD^{tree}"],text=True).strip()==m["exactTree"]
assert d["exactHead"]==m["exactHead"] and d["exactTree"]==m["exactTree"]
for pin in [d["sourceRegistryPin"],*d["catalogPins"]]:
 raw=subprocess.check_output(["git","-C",str(root),"show",f"HEAD:{pin['path']}"])
 assert hashlib.sha256(raw).hexdigest()==pin["fileSha256"]
 assert subprocess.check_output(["git","-C",str(root),"rev-parse",f"HEAD:{pin['path']}"],text=True).strip()==pin["gitBlob"]
for c in d["callerReferences"]:
 raw=subprocess.check_output(["git","-C",str(root),"show",f"HEAD:{c['path']}"],text=True)
 assert hashlib.sha256(raw.encode()).hexdigest()==c["fileSha256"]
 assert subprocess.check_output(["git","-C",str(root),"rev-parse",f"HEAD:{c['path']}"],text=True).strip()==c["gitBlob"]
 line=raw.splitlines()[c["line"]-1]
 assert line.strip()==c["lineText"] and hashlib.sha256(line.strip().encode()).hexdigest()==c["lineSha256"]
for c in d["targetCells"]:
 raw=subprocess.check_output(["git","-C",str(root),"show",f"HEAD:{c['catalogPath']}"])
 value=json.loads(raw)[d["sourceId"]]
 assert value==c["target"] and hashlib.sha256(value.encode()).hexdigest()==c["targetSha256"]
print("PASS",len(d["targetCells"]),"cells",len(d["callerReferences"]),"caller pins",d["sourceId"])
