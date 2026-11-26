from native_refs import *
from collections import deque
from capstone.x86_const import X86_INS_LEA
def exceptions(im):
    start,size=im.dir(3)
    return set(struct.iter_unpack('<III',im.read(start,size)))
class Rebase:
    def __init__(self):
        self.a,self.b,self.c=images();self.m=Mapper(self.a,self.c);self.refs=References(self.m)
        self.out=bytearray(self.c.data);self.extra=min(v[1] for k,v in self.b.sections.items() if k not in self.a.sections)
        self.delta=len(self.c.data)-len(self.a.data)
        self.out.extend(self.b.data[len(self.a.data):])
        self.old_write={};self.queue=deque();self.seen=set();self.absolute_tables=set()
        self.instr=0
        a,b,c=self.a,self.b,self.c
        for im in (a,b,c):assert im.base==a.base
        oh=u32(self.out,60);tab=oh+24+u16(self.out,oh+20);section_count=len(a.sections)
        assert len(a.sections)==len(c.sections)
        for i,name in enumerate(b.sections):
            if name in a.sections:continue
            h=tab+i*40
            assert not any(self.out[h:h+40])
            self.out[h:h+40]=b.data[h:h+40]
            struct.pack_into('<I',self.out,h+20,u32(self.out,h+20)+self.delta)
        struct.pack_into('<H',self.out,oh+6,len(b.sections))
        for f in [4,8]:struct.pack_into('<I',self.out,c.opt+f,u32(c.data,c.opt+f)+u32(b.data,b.opt+f)-u32(a.data,a.opt+f))
        struct.pack_into('<I',self.out,c.opt+56,u32(b.data,b.opt+56));struct.pack_into('<I',self.out,c.opt+64,0)
        self.im=Image(self.out)
    def write(self,addr,data):
        i=self.im.off(addr)
        self.out[i:i+len(data)]=data
    def translate_instruction(self,ins,new,original):
        raw=bytearray(ins.bytes);dst=new+ins.size
        def fix(off,n,val,signed=True):
            raw[off:off+n]=int(val).to_bytes(n,'little',signed=signed)
        isbranch=ins.group(capstone.CS_GRP_CALL) or ins.group(capstone.CS_GRP_JUMP)
        for v in ins.operands:
            if v.type==X86_OP_IMM and isbranch:
                target=v.imm
                if target>=self.extra:self.queue.append(target)
                if ins.imm_size:
                    fix(ins.imm_offset,ins.imm_size,self.refs.get(target)-dst)
            elif v.type==X86_OP_MEM and v.mem.base==X86_REG_RIP:
                target=ins.address+ins.size+v.mem.disp
                if ins.id==X86_INS_LEA and target>=self.b.dir(1)[0] and ins.address>=self.b.dir(1)[0]:
                    self.queue.append(target)
                fix(ins.disp_offset,ins.disp_size,self.refs.get(target)-dst)
            elif v.type==X86_OP_MEM and ins.disp_size==4 and self.extra<=v.mem.disp<0x5000000:
                assert original
                self.absolute_tables.add(v.mem.disp)
            elif v.type==X86_OP_IMM and not original and 0x4ce000<=v.imm<self.extra:
                raise ValueError(('unreviewed injected absolute operand',hex(ins.address),ins.op_str))
        return raw
    def sites(self):
        a,b,c=self.a,self.b,self.c
        sites=json.loads((HERE/'native-sites.json').read_bytes())['il2cpp']
        by_owner=defaultdict(list)
        for x,y in sites:by_owner[self.m.a.owner(x) or x].append((x,y))
        for start,ranges in by_owner.items():
            last=max(y for x,y in ranges)
            data=b.read(start,last-start+15)
            covered=set()
            for ins in dis.disasm(data,start):
                if ins.address>=last:break
                hit=[(x,y) for x,y in ranges if x<ins.address+ins.size and y>ins.address]
                if not hit:continue
                addr=self.m.translate(ins.address);assert addr is not None,hex(ins.address)
                self.write(addr,self.translate_instruction(ins,addr,True))
                covered.update(range(ins.address,ins.address+ins.size))
            assert all(i in covered for x,y in ranges for i in range(x,y) if a.read(i,1)!=b.read(i,1)),hex(start)
    def payload(self):
        b=self.b
        extra_funcs=sorted(exceptions(b)-exceptions(self.a))
        assert not exceptions(self.a)-exceptions(b)
        for start,end,uw in extra_funcs:
            self.queue.append(start)
            assert self.extra<=start<end and uw>=self.extra
        for addr in self.absolute_tables:
            for i in range(9):
                target=u32(b.data,b.off(addr)+4*i)
                if i<8:
                    assert target<self.extra
                    self.write(addr+4*i,struct.pack('<I',self.refs.get(target)))
                else:self.queue.append(target)
        while self.queue:
            start=self.queue.popleft()
            if start in self.seen:continue
            assert self.extra<=start,hex(start)
            pos=start
            while pos not in self.seen:
                self.seen.add(pos);ins=next(dis.disasm(b.read(pos,15),pos),None)
                assert ins and ins.mnemonic not in ('int3','ud2','int'),hex(pos)
                self.write(pos,self.translate_instruction(ins,pos,False))
                self.instr+=1
                if ins.mnemonic in ('jmp','ret','retf'):break
                pos+=ins.size
        for begin,end,uw in extra_funcs:
            flags=b.read(uw,1)[0]>>3
            if flags&4:
                count=b.read(uw+2,1)[0];loc=uw+4+((count+1)&~1)*2
                s,e,u=struct.unpack('<III',b.read(loc,12));assert (s,e,u) in exceptions(self.a)
                ns=self.refs.get(s);ne,nu=next((j,k) for i,j,k in self.official_ex if i==ns)
                self.write(loc,struct.pack('<III',ns,ne,nu))
            else:assert flags==0,(hex(uw),flags)
        return extra_funcs
    def dirs(self,extra_funcs):
        a,b,c=self.a,self.b,self.c
        extra_dir,oldsize=b.dir(3);rows=sorted(self.official_ex|set(extra_funcs))
        raw=b''.join(struct.pack('<III',*i) for i in rows)
        assert len(raw)<=oldsize
        self.write(extra_dir,raw+bytes(oldsize-len(raw)))
        struct.pack_into('<II',self.out,c.opt+136,extra_dir,len(raw))
        loc,size=b.dir(1);oa,osize=a.dir(1);nc,nsize=c.dir(1)
        assert osize==nsize and b.read(loc,osize-20)==a.read(oa,osize-20)
        self.write(loc,c.read(nc,nsize-20))
        struct.pack_into('<II',self.out,c.opt+120,loc,size)
    def build(self):
        self.official_ex=exceptions(self.c)
        self.sites();extra=self.payload();self.dirs(extra)
        dest=HERE/'stage/GameAssembly.dll';dest.write_bytes(self.out)
        print('ported',self.instr,'injected instructions and',len(extra),'unwind ranges')
        return self
if __name__=='__main__':Rebase().build()
