import attrs,copy,struct,difflib
from collections import Counter
def add_object(src,file):
    assert src.path_id not in file.objects
    st=copy.copy(src.serialized_type)
    def sig(t):return t.class_id,t.script_id,t.old_type_hash
    matches=[i for i,t in enumerate(file.types) if sig(t)==sig(st)]
    if matches:ti=matches[0];st=file.types[ti]
    else:
        if st.script_type_index>=0:
            script=copy.copy(src.assets_file.script_types[st.script_type_index])
            idx=script.local_serialized_file_index
            if idx>0:assert src.assets_file.externals[idx-1].path==file.externals[idx-1].path
            st.script_type_index=len(file.script_types);file.script_types.append(script)
        ti=len(file.types);file.types.append(st)
    file.objects[src.path_id]=attrs.evolve(src,assets_file=file,type_id=ti,serialized_type=st,data=src.get_raw_data())
def merge_bytes(base,patch,new):
    if len(base)!=len(new):
        # Only carry official changes through stretches untouched by localization.
        if max(map(len,(base,patch,new)))>8192:return None
        spans=difflib.SequenceMatcher(None,base,patch,autojunk=False).get_matching_blocks()
        edits=[]
        for op,start,end,ns,ne in difflib.SequenceMatcher(None,base,new,autojunk=False).get_opcodes():
            if op=='equal':continue
            fits=[b-a for a,b,size in spans if a<start and end<a+size]
            if len(fits)!=1:return None
            shift=fits[0];edits.append((start+shift,end+shift,new[ns:ne]))
        for start,end,data in reversed(edits):patch=patch[:start]+data+patch[end:]
        return patch
    left=0
    while left<min(len(base),len(patch)) and base[left]==patch[left]:left+=1
    right=0
    while right<min(len(base),len(patch))-left and base[-right-1]==patch[-right-1]:right+=1
    end=len(base)-right
    if base[left:end]!=new[left:end]:return None
    return new[:left]+patch[left:len(patch)-right]+new[end:]
def merge_yarn(a,b,c,schema):
    def split(obj):
        raw=obj.get_raw_data();prog=bytes(obj.read_typetree(nodes=schema)['compiledYarnProgram'])
        block=struct.pack('<I',len(prog))+prog+bytes(-len(prog)%4)
        assert raw.count(block)==1
        left,right=raw.split(block)
        return left,block,right
    al,ap,ar=split(a);bl,bp,br=split(b);cl,cp,cr=split(c)
    assert (al,ar)==(cl,cr)
    return bl+cp+br
