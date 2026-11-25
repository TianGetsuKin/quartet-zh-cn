from pathlib import Path
import json,collections,math
W=Path(__file__).resolve().parent
src=(W/'extract.py').read_text('utf8')
exec(src[:src.index("print('Sampling")]+src[src.index("cat=(A/"):src.index('tr={r')])
worldrooms={gid:k[4:].lower() for gid,k in roomkeys.items() if k.lower().endswith('worldmap') and '/bullshot' not in k.lower()}
warps=[];needed=set()
for o in f.objects.values():
 if o.type.name!='MonoBehaviour':continue
 keys=o.serialized_type.node.m_Children
 if len(keys)<5 or keys[4].m_Name!='mapId':continue
 d=o.read_typetree();dest=d.get('mapId','').lower()
 if dest not in worldrooms.values() or d.get('isDevEvent'):continue
 root,x,y=locate(getid(d['m_GameObject']))
 if root not in roomkeys:continue
 target=d['target'].lower();needed.add(target);warps.append([roomkeys[root][4:],round(x,2),round(-y,2),dest,target])
spawns={}
for o in f.objects.values():
 if o.type.name!='GameObject':continue
 name=o.peek_name()
 if not name or name.lower() not in needed:continue
 root,x,y=locate(o.path_id)
 if root in worldrooms:spawns[(worldrooms[root],name.lower())]=[round(x,2),round(-y,2)]
print('world exit and spawn counts',len(warps),len(spawns),'examples',list(spawns.items())[:6])
for row in warps:row.append(spawns.get(tuple(row[-2:])))
(W/'world-exits.json').write_text(json.dumps(warps,ensure_ascii=False),'utf8')
print('unresolved',[(r[0],r[4]) for r in warps if r[-1] is None][:25])
