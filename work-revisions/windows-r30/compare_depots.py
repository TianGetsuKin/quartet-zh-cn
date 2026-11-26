from pathlib import Path
import json,struct,hashlib
HERE=Path(__file__).resolve().parent
PREV=HERE.parent/'rebased-25279268'
GAME=HERE.parent.parent/'Quartet'
def varint(data,pos):
    n=0
    for shift in range(0,70,7):
        b=data[pos];pos+=1;n|=(b&127)<<shift
        if b<128:return n,pos
    raise ValueError('varint')
def fields(data):
    p=0
    while p<len(data):
        tag,p=varint(data,p)
        v,p=varint(data,p)
        if tag%8==2:v,p=data[p:p+v],p+v
        else:assert tag%8==0,tag
        yield tag//8,v
def manifest(id):
    data=(Path('C:/Program Files (x86)/Steam/depotcache')/('1307962_'+id+'.manifest')).read_bytes()
    magic,size=struct.unpack_from('<II',data)
    assert magic==0x71f617d0
    result={}
    for tag,entry in fields(data[8:8+size]):
        f=dict(fields(entry))
        if 5 in f:result[f[1].decode().replace('\\','/')]=f[5].hex()
    return result
def sha(path,algo):
    if path.is_file():
        with path.open('rb') as f:return hashlib.file_digest(f,algo).hexdigest()
old=manifest('6808041564537862185')
new=manifest('8712119740688563894')
if __name__=='__main__':
    patch=json.loads((PREV/'work-revisions/equip-focus-r29-l15/r29.json').read_bytes())['files']
    delta=[n for n in sorted(set(old)|set(new)) if old.get(n)!=new.get(n)]
    items=[]
    for n in patch:
        alias=n
        if n in old and not n in new:
            matches=[k for k in new if k.rsplit('_',1)[0]==n.rsplit('_',1)[0]]
            if len(matches)==1:alias=matches[0]
        installed=sha(GAME/alias,'sha1')
        state='patch-added' if n not in old else 'same' if old[n]==new.get(alias) else 'changed'
        items.append(dict(old=n,new=alias,state=state,clean=installed==new.get(alias) and alias in new))
        print(state,items[-1]['clean'],alias.split('/')[-1])
    (HERE/'windows-depot-diff.json').write_text(json.dumps(dict(old_build=25279268,new_build=26908524,version='1.5.20261124',changed=delta,patch_files=items),indent=2),'utf8')
    print('official changes',len(delta))
