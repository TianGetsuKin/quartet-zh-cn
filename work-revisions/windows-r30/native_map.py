from native_images import *
import sys,bisect,re,functools
from collections import defaultdict
sys.path.insert(0,str(HERE/'tools-deps'))
import capstone
from capstone.x86_const import X86_REG_RIP,X86_OP_MEM,X86_OP_IMM
dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);dis.detail=True
class Functions:
    def __init__(self,im):
        self.im=im
        addr,size=im.dir(3);ranges=struct.iter_unpack('<III',im.read(addr,size))
        self.ends={s:e for s,e,u in ranges}
        self.starts=sorted(self.ends)
    def owner(self,pos):
        i=bisect.bisect_right(self.starts,pos)-1
        return self.starts[i] if i>=0 and self.ends[self.starts[i]]>pos else None
    @functools.lru_cache(maxsize=8000)
    def signature(self,start):
        raw=self.im.read(start,self.ends[start]-start);masked=bytearray(raw)
        end=len(raw.rstrip(b'\xcc'))
        end-=(start+end)%4
        table=end
        while table>=4 and start<=u32(raw,table-4)<start+len(raw):
            table-=4
        if end-table>=8:
            for off in range(table,end,4):struct.pack_into('<I',masked,off,u32(raw,off)-start)
        else:table=len(raw)
        for ins in dis.disasm(raw[:table],start):
            at=ins.address-start
            for v in ins.operands:
                if v.type==X86_OP_MEM and v.mem.base==X86_REG_RIP:
                    masked[at+ins.disp_offset:at+ins.disp_offset+ins.disp_size]=bytes(ins.disp_size)
                elif v.type==X86_OP_IMM and (ins.group(capstone.CS_GRP_CALL) or ins.group(capstone.CS_GRP_JUMP)):
                    masked[at+ins.imm_offset:at+ins.imm_offset+ins.imm_size]=bytes(ins.imm_size)
                elif (v.type==X86_OP_MEM and ins.disp_size==4 and 0x4ce000<=v.mem.disp<0x4505000) or (v.type==X86_OP_IMM and 0x4ce000<=v.imm<0x4505000 and ins.imm_size==4):
                    off,l=(ins.disp_offset,ins.disp_size) if v.type==X86_OP_MEM else (ins.imm_offset,ins.imm_size)
                    masked[at+off:at+off+l]=bytes(l)
        return bytes(masked)
class Mapper:
    def __init__(self,a,c):
        self.a=Functions(a);self.c=Functions(c)
        self.cache={}
    def candidates(self,old):
        n=self.a.ends[old]-old
        lo,hi=[bisect.bisect_left(self.c.starts,old+d) for d in (-8192,8193)]
        return [s for s in self.c.starts[lo:hi] if self.c.ends[s]-s==n and self.a.signature(old)==self.c.signature(s)]
    def function(self,old):
        if old in self.cache:return self.cache[old]
        matches=self.candidates(old)
        if len(matches)>1:
            # Resolve duplicated implementations only when adjacent unique bodies agree on displacement.
            pos=bisect.bisect_left(self.a.starts,old);deltas=[]
            for step in (-1,1):
                for delta in range(1,6):
                    other=self.a.starts[pos+step*delta];choices=self.candidates(other)
                    if len(choices)==1:
                        deltas.append(choices[0]-other);break
            if len(deltas)==2 and deltas[0]==deltas[1]:matches=[p for p in matches if p==old+deltas[0]]
        self.cache[old]=matches[0] if len(matches)==1 else None
        return self.cache[old]
    def translate(self,addr):
        old=self.a.owner(addr)
        if old is None:
            j=bisect.bisect_right(self.a.starts,addr)
            if not (0<j<len(self.a.starts)):return None
            left,right=self.a.starts[j-1:j+1]
            if right-self.a.ends[left]>4096:return None
            l,r=self.function(left),self.function(right)
            if l is None or r is None or l-left!=r-right:return None
            src=self.a.ends[left];dst=src+l-left
            if src>=right:return None
            self.a.ends[src]=right;self.c.ends[dst]=r
            if self.a.signature(src)!=self.c.signature(dst):return None
            return addr+l-left
        n=self.function(old)
        return None if n is None else n+addr-old
if __name__=='__main__':
    a,b,c=images();m=Mapper(a,c);sites=json.loads((HERE/'native-sites.json').read_bytes())['il2cpp']
    r={}
    for x,y in sites:r[hex(x)]=m.translate(x)
    src=PREV/'work-revisions/equip-focus-r29-l15'
    for p in [src/'recent.c',src/'preview.h']:
        for x in re.findall(r'GAME_FUNCTION\((0x[0-9a-fA-F]+)',p.read_text('utf8')):
            r[x]=m.translate(int(x,16))
    (HERE/'native-address-audit.json').write_text(json.dumps(r,indent=2),'utf8')
    print(len(r),'addresses checked;',sum(v is None for v in r.values()),'unresolved')
    print([(k,hex(m.a.owner(int(k,16)) or 0)) for k,v in r.items() if v is None][:35])
