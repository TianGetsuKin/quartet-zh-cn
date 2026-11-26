from pathlib import Path
import hashlib,json,sys,UnityPy
from compare_depots import HERE,PREV,GAME
parser=(PREV/'tools/inspect_current_yarn_nodes.py').read_text('utf8')
exec(parser[parser.index('def varint'):parser.index('bundle=next')])
def read(folder):
    bundle=next(folder.glob('default_scenes_all*.bundle'))
    env=UnityPy.load(str(bundle))
    obj,=[o for o in env.objects if o.type.name=='MonoBehaviour' and o.serialized_type.node and any(n.m_Name=='compiledYarnProgram' for n in o.serialized_type.node.m_Children)]
    program=bytes(obj.read_typetree()['compiledYarnProgram'])
    nodes={}
    for f,w,v in fields(program):
        if f==2:
            key,node=fields(v)
            nodes[key[2].decode()]=node[2]
    return nodes
if __name__=='__main__':
    a,b=[read(folder/'StreamingAssets/aa/StandaloneWindows64') for folder in [PREV/'backups/game-original',GAME/'Quartet_Data']]
    changed=[n for n in a.keys()|b.keys() if a.get(n)!=b.get(n)]
    print('changed nodes',len(changed), sorted(changed)[:70])
    lines={}
    for name,node in [('old',a['battle_liganti1']),('new',b['battle_liganti1'])]:
        lines[name]=[printable(v).strip() for f,w,v in fields(node) if f==2]
        print(name,lines[name][:24])
    (HERE/'yarn-changes.json').write_text(json.dumps(dict(nodes=sorted(changed),liganti=lines),indent=2),'utf8')
