from native_map import *
import numpy as np
class References:
    def __init__(self,mapper):
        self.m=mapper
        self.resolved={}
        self.arrays=[]
        self.seen={}
    def pair(self,ins,new):
        if ins.id!=new.id:return
        for x,y in zip(ins.operands,new.operands):
            if x.type==y.type==X86_OP_MEM and x.mem.base==y.mem.base==X86_REG_RIP:
                self.record(ins.address+ins.size+x.mem.disp,new.address+new.size+y.mem.disp)
            elif x.type==y.type==X86_OP_IMM and (ins.group(capstone.CS_GRP_CALL) or ins.group(capstone.CS_GRP_JUMP)):
                self.record(x.imm,y.imm)
    def record(self,x,y):
        if x in self.resolved and self.resolved[x]!=y:raise ValueError(('conflicting reference',hex(x),hex(y),hex(self.resolved[x])))
        self.resolved[x]=y
    def from_code(self,x):
        if x in self.resolved:return self.resolved[x]
        a=self.m.a;c=self.m.c
        for lo,hi in [(0x4ce000,0x730000),(0x730000,0x2ee0000),(0x1000,0x4cd000)]:
            for pos in range(lo,hi-8,0x100000):
                end=min(hi-8,pos+0x100000)
                block=a.im.read(pos,end-pos+8)
                for align in range(4):
                    seq=np.frombuffer(block,dtype='<i4',offset=align,count=(end-pos)//4)
                    dest=seq+np.arange(pos+align+4,end+align+4,4,dtype=np.int64)
                    for tail in (0,1,4):
                        for idx in np.nonzero(dest==x-tail)[0][:16]:
                            field=int(pos+align+idx*4)
                            start=a.owner(field)
                            if start is None:continue
                            new=self.m.function(start)
                            if new is None:continue
                            for ins in dis.disasm(a.im.read(start,a.ends[start]-start),start):
                                if ins.address>field:break
                                if not ((ins.address+ins.disp_offset==field and ins.disp_size==4) or
                                        (ins.address+ins.imm_offset==field and ins.imm_size==4)):continue
                                other=next(dis.disasm(c.im.read(new+ins.address-start,ins.size),new+ins.address-start),None)
                                if other:self.pair(ins,other)
                            if x in self.resolved:return self.resolved[x]
        raise ValueError(('no native reference',hex(x)))
    def get(self,x):
        if x==0 or x>=0x4505000:return x
        if x in self.resolved:return self.resolved[x]
        if x<0x2ee0000:
            result=self.m.translate(x)
            if result is not None:return result
        return self.from_code(x)
