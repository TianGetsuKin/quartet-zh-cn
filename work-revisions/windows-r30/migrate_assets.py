from compare_depots import *
from zipfile import ZipFile
from collections import Counter, defaultdict
import UnityPy,sys,gc
from asset_merge import add_object,merge_bytes,merge_yarn
receipt=json.loads((PREV/'work-revisions/equip-focus-r29-l15/r29.json').read_bytes())
rows=json.loads((HERE/'windows-depot-diff.json').read_bytes())['patch_files']
def objmap(env):
    files={}
    for o in env.objects:
        f=o.assets_file.name
        files.setdefault(f,{})[o.path_id]=o
    return files
def matchfiles(a,b):
    if a.keys()==b.keys():return {k:k for k in a}
    if len(a)==len(b)==1:return {next(iter(a)):next(iter(b))}
    def key(k):return k.split('.sharedAssets')[-1] if '.sharedAssets' in k else k.split('_',1)[-1] if '_' in k else ('root' if k.startswith('CAB-') else k)
    ma={key(k):k for k in a};mb={key(k):k for k in b}
    if ma.keys()!=mb.keys() or len(ma)!=len(a):raise ValueError((list(a)[:6],list(b)[:6],len(a),len(b)))
    return {k:mb[key(k)] for k in a}
def audit(row,z):
    n,rel=row['old'],row['new']
    base=PREV/'backups/game-original'/n.partition('/')[2]
    if n.endswith('.resS') or row['state']=='same':
        dest=HERE/'stage'/rel;dest.parent.mkdir(exist_ok=True,parents=True)
        assert old[n]==new[rel]
        dest.write_bytes(z.read('覆盖到游戏目录/'+n));return {'unchanged_source':True}
    assert sha(base,'sha1')==old[n] and sha(GAME/rel,'sha1')==new[rel]
    a,b,c=[UnityPy.load(p) for p in (str(base),z.read('覆盖到游戏目录/'+n),str(GAME/rel))]
    ag,bg,cg=map(objmap,(a,b,c));bm=matchfiles(ag,bg);cm=matchfiles(ag,cg)
    modified=Counter();conflicts=[];added=[];dropped=[];ops=[]
    clones=[]
    for f,entries in ag.items():
        patch=bg[bm[f]];current=cg[cm[f]]
        by_raw=defaultdict(list);by_key=defaultdict(list)
        def resource_key(obj):
            if obj.type.name!='MonoBehaviour':return None
            raw=obj.get_raw_data()
            size=int.from_bytes(raw[28:32],'little')
            return (raw[16:28],raw[32:32+size]) if 0<size<2000 else None
        if n.endswith('/resources.assets'):
            for obj in current.values():
                by_raw[hashlib.sha256(obj.get_raw_data()).digest()].append(obj)
                by_key[resource_key(obj)].append(obj)
        def component_key(obj):
            if obj.type.name!='MonoBehaviour':return None
            head=obj.parse_monobehaviour_head()
            if not head.m_GameObject.path_id:return None
            go=obj.assets_file.objects[head.m_GameObject.path_id].read()
            graph=obj.assets_file.objects
            path=[]
            tr=graph[go.m_Component[0].component.path_id].read()
            while tr:
                path.append(graph[tr.m_GameObject.path_id].read().m_Name)
                tr=graph[tr.m_Father.path_id].read() if tr.m_Father.path_id else None
            return (tuple(path),head.m_Script.file_id,head.m_Script.path_id)
        if n.endswith('/sharedassets4.assets'):
            for obj in current.values():by_key[component_key(obj)].append(obj)
        for i in patch.keys()-entries.keys():
            added.append((f,i))
            if i in current:conflicts.append((f,i,'occupied new object ID'))
            else:clones.append((patch[i],next(iter(current.values())).assets_file))
        dropped.extend((f,i) for i in entries.keys()-patch.keys())
        for i,o in entries.items():
            if i not in patch:continue
            before=o.get_raw_data();after=patch[i].get_raw_data()
            if before==after:continue
            modified[o.type.name]+=1
            dest=current.get(i)
            if n.endswith('/resources.assets'):
                matches=by_raw.get(hashlib.sha256(before).digest(),[])
                if len(matches)!=1:matches=by_key.get(resource_key(o),[])
                dest=matches[0] if len(matches)==1 else None
            if n.endswith('/sharedassets4.assets'):
                matches=by_key.get(component_key(o),[])
                dest=matches[0] if len(matches)==1 else None
            if dest is None or dest.type!=o.type:
                conflicts.append((f,i,o.type.name));continue
            if dest.get_raw_data()!=before:
                if b'battle_liganti1' in before and b'BossCutscenes.yarn' in before:
                    schema=o.serialized_type.node
                    if not schema:
                        env=UnityPy.load(str(next(GAME.rglob('default_scenes_all*.bundle'))))
                        schema=next(o.serialized_type.node for o in env.objects if o.serialized_type.node and any(k.m_Name=='compiledYarnProgram' for k in o.serialized_type.node.m_Children))
                    after=merge_yarn(o,patch[i],dest,schema)
                else:
                    after=merge_bytes(before,after,dest.get_raw_data())
                    if after is None:conflicts.append((f,i,o.type.name));continue
            ops.append((dest,after))
    report=dict(modified=modified,conflicts=conflicts,added=added,dropped=dropped)
    if not conflicts and not dropped:
        for f in ag:
            owners=[next(iter(m.values())).assets_file for m in (ag[f],bg[bm[f]],cg[cm[f]])]
            old_ext,pat_ext,new_ext=([x.path for x in file.externals] for file in owners)
            if old_ext!=pat_ext or old_ext!=new_ext:
                return {**report,'external_table_review':f}
        for src,file in clones:add_object(src,file)
        for dest,data in ops:dest.set_raw_data(data)
        packed=n.endswith('.bundle')
        if packed:
            assert a.file.files.keys()==b.file.files.keys()==c.file.files.keys()
            for k,member in a.file.files.items():
                if hasattr(member,'objects'):continue
                translated=b.file.files[k]
                if member.bytes!=translated.bytes:
                    assert member.bytes==c.file.files[k].bytes
                    c.file.files[k]=translated
        path=HERE/'stage'/rel;path.parent.mkdir(exist_ok=True,parents=True);path.write_bytes(c.file.save(packer='lz4') if packed else c.file.save())
        output=UnityPy.load(str(path));verify=objmap(output)
        for f,entries in cg.items():
            entries=next(iter(entries.values())).assets_file.objects
            assert entries.keys()==verify[f].keys()
            assert all((o.data if o.data is not None else o.get_raw_data())==verify[f][i].get_raw_data() for i,o in entries.items())
        report['rebuilt']=True
    return report
if __name__=='__main__':
    with ZipFile(receipt['archive']) as z:
        results={}
        report_path=HERE/'asset-audit.json'
        if sys.argv[1:] and report_path.exists():results=json.loads(report_path.read_bytes())
        for row in rows:
            n=row['old']
            if sys.argv[1:] and not any(k in n for k in sys.argv[1:]):continue
            if '/il2cpp' in n or not n.startswith('Quartet_Data/'):continue
            try:r=audit(row,z)
            except Exception as exc:r={'error':repr(exc)}
            results[n]=r;gc.collect()
            print(n.split('/')[-1],{k:(len(v) if isinstance(v,list) else v) for k,v in r.items()},flush=True)
            (HERE/'asset-audit.json').write_text(json.dumps(results,indent=2),'utf8')
