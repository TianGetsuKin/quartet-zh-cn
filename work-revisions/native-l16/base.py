from pathlib import Path
import hashlib,json,sys,struct
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parent))
from compare_depots import fields,sha,PREV
PRISTINE=PREV/'linux-native/input/build25279268'
NEW=D/'input'
STAGE=D/'stage'
def manifest(id):
    buf=(D/('1307964_'+id+'.manifest')).read_bytes()
    magic,length=struct.unpack_from('<II',buf)
    assert magic==0x71f617d0
    result={}
    for tag,entry in fields(buf[8:8+length]):
        row=dict(fields(entry))
        if 5 in row:result[row[1].decode().replace('\\','/')]=row[5].hex()
    return result
old=manifest('2670900619531972171')
new=manifest('2325920819324936782')
l15=json.loads((PREV/'work-revisions/equip-focus-r29-l15/l15.json').read_bytes())
files={k.split('/',1)[1]:v for k,v in l15['files'].items()}
def current_name(n):
    if n in new or n not in old:return n
    matches=[k for k in new if k.rsplit('_',1)[0]==n.rsplit('_',1)[0]]
    assert len(matches)==1,n
    return matches[0]
if __name__=='__main__':
    for n in files:
        m=current_name(n)
        print(n.split('/')[-1], 'added' if n not in old else 'same' if old[n]==new[m] else 'changed',m.split('/')[-1],(PRISTINE/n).is_file())
