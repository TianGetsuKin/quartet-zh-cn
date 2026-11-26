from compare_depots import HERE,PREV,GAME,old,new,sha
from pathlib import Path
import struct,json,zipfile,hashlib,itertools
from collections import Counter
def u32(data,i):return struct.unpack_from('<I',data,i)[0]
def u64(data,i):return struct.unpack_from('<Q',data,i)[0]
def u16(data,i):return struct.unpack_from('<H',data,i)[0]
class Image:
    def __init__(self,data):
        self.data=data
        hdr=u32(data,60);self.opt=hdr+24;table=self.opt+u16(data,hdr+20);self.base=u64(data,self.opt+24)
        self.sections={}
        for i in range(u16(data,hdr+6)):
            pos=table+i*40;s=data[pos:pos+8].rstrip(b'\0').decode();self.sections[s]=struct.unpack_from('<IIII',data,pos+8)
    def off(self,rva):
        if rva<1024:return rva
        for v,va,size,start in self.sections.values():
            if va<=rva<va+size:return start+rva-va
        raise ValueError(hex(rva))
    def read(self,rva,n):
        p=self.off(rva);return self.data[p:p+n]
    def dir(self,i):
        return struct.unpack_from('<II',self.data,self.opt+112+8*i)
def images():
    r=json.loads((PREV/'work-revisions/equip-focus-r29-l15/r29.json').read_bytes())
    with zipfile.ZipFile(r['archive']) as z:patched=z.read('覆盖到游戏目录/GameAssembly.dll')
    a=PREV.parent/'build-25279268-snapshot/GameAssembly.dll';c=GAME/'GameAssembly.dll'
    assert sha(a,'sha1')==old[a.name] and sha(c,'sha1')==new[c.name] and hashlib.sha256(patched).hexdigest()==r['files'][a.name]
    return tuple(map(Image,(a.read_bytes(),patched,c.read_bytes())))
def ranges(a,b,start):
    out=[]
    for p in range(0,len(a),4096):
        x,y=a[p:p+4096],b[p:p+4096]
        if x==y:continue
        for k,(l,r) in enumerate(zip(x,y)):
            if l==r:continue
            pos=start+p+k
            if out and out[-1][1]+4>=pos:out[-1][1]=pos+1
            else:out.append([pos,pos+1])
    return out
if __name__=='__main__':
    a,b,c=images()
    sites={}
    for s,(v,va,size,start) in a.sections.items():
        r=ranges(a.read(va,size),b.read(va,size),va)
        sites[s]=r
        print(s,len(r),[hex(x[0]) for x in r[:6]])
    print('directories',[(i,a.dir(i),b.dir(i),c.dir(i)) for i in range(16) if a.dir(i)!=b.dir(i)])
    (HERE/'native-sites.json').write_text(json.dumps(sites),'utf8')
