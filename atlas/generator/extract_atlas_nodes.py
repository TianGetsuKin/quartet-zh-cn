from pathlib import Path
import sys,json,UnityPy
w=Path(__file__).resolve().parent
sys.path.insert(0,str(w.parents[1]/'tools/offline_work'))
from native_yarn_reader import decode_nodes
folder=Path('G:/SteamLibrary/steamapps/common/Quartet/Quartet_Data/StreamingAssets/aa/StandaloneWindows64')
env=UnityPy.load(str(next(folder.glob('*default_scenes*.bundle'))))
o=next(o for o in env.objects if o.type.name=='MonoBehaviour' and o.serialized_type.node and any(k.m_Name=='compiledYarnProgram' for k in o.serialized_type.node.m_Children))
nodes=decode_nodes(bytes(o.read_typetree()['compiledYarnProgram']))
# Keep command strings, string operands, and node transfers, in execution order.
records={k:[[i['opcode'],s] for i in v['instructions'] for s in i['operands'] if isinstance(s,str) and not s.startswith('line:')] for k,v in nodes.items()}
(w/'atlas-nodes.json').write_text(json.dumps(records,ensure_ascii=False),'utf8')

