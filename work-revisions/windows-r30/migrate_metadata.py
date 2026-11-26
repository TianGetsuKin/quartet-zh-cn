from compare_depots import HERE,PREV,GAME,old,new,sha
from pathlib import Path
import sys, json,zipfile,hashlib,struct
sys.path.insert(0,str(PREV/'tools'))
import metadata_patch
def metadata():
    receipt=json.loads((PREV/'work-revisions/equip-focus-r29-l15/r29.json').read_bytes())
    path='Quartet_Data/il2cpp_data/Metadata/global-metadata.dat'
    a=PREV/'backups/game-original'/path.partition('/')[2]
    assert sha(a,'sha1')==old[path] and sha(GAME/path,'sha1')==new[path]
    with zipfile.ZipFile(receipt['archive']) as z:
        patch=z.read('覆盖到游戏目录/'+path)
    assert hashlib.sha256(patch).hexdigest()==receipt['files'][path]
    av,bv,cv=map(metadata_patch.literals,[a.read_bytes(),patch,(GAME/path).read_bytes()])
    assert av==cv and len(bv)>=len(av)
    old_data=a.read_bytes()
    table,size=struct.unpack_from('<II',old_data,8)
    assert old_data[24:table]==patch[24:table] and old_data[table+size:]==patch[table+size:len(old_data)]
    data=bytearray((GAME/path).read_bytes())
    for header in (8,16):
        offset,size=struct.unpack_from('<II',patch,header)
        data.extend(bytes(-len(data)%4))
        struct.pack_into('<II',data,header,len(data),size)
        data.extend(patch[offset:offset+size])
    assert metadata_patch.literals(data)==bv
    assert data[24:(GAME/path).stat().st_size]==(GAME/path).read_bytes()[24:]
    count=sum(x!=y for x,y in zip(av,bv))+len(bv)-len(av)
    dest=HERE/'stage'/path
    dest.parent.mkdir(exist_ok=True,parents=True)
    dest.write_bytes(data)
    return dict(changed_literals=count,sha256=sha(dest,'sha256'))
if __name__=='__main__':
    print(metadata())
