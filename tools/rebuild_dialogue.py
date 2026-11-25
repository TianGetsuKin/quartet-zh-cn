"""Refresh both dialogue tables in the existing font/UI build."""
import hashlib,json
import UnityPy
from asset_support import ROOT
from translation_catalog import load_catalog

out=ROOT/'build/pilot/Quartet_Data'
source={x['id']:x['en'] for x in map(json.loads,(ROOT/'translations/dialogue.source.jsonl').read_text(encoding='utf-8').splitlines())}
translated=load_catalog()['dialogue']
assert set(translated)<=set(source)
manifest_path=ROOT/'build/pilot/manifest.json'
manifest=json.loads(manifest_path.read_text())
bundle=next(out.glob('StreamingAssets/aa/StandaloneWindows64/*default_scenes*.bundle'))
env=UnityPy.load(str(bundle))
objects=[o for o in env.objects if o.type.name=='MonoBehaviour' and o.serialized_type.node and any(n.m_Name=='_stringTable' for n in o.serialized_type.node.m_Children)]
assert len(objects)==1
schema=objects[0].serialized_type.node
global_env=UnityPy.load(str(out/'globalgamemanagers.assets'))
global_object=global_env.file.objects[3126]
global_object.serialized_type.node=schema
for obj in [objects[0],global_object]:
    data=obj.read_typetree();table=data['_stringTable']
    assert len(table['keys'])==len(source) and set(table['keys'])==set(source)
    before=obj.get_raw_data()
    assert obj.save_typetree(data)==before,'Unsafe serialization roundtrip'
    table['values']=[translated.get(k,source[k]) for k in table['keys']]
    obj.save_typetree(data)
for path,asset_env in [(bundle,env),(out/'globalgamemanagers.assets',global_env)]:
    data=asset_env.file.save(packer='lz4') if path.suffix=='.bundle' else asset_env.file.save()
    path.write_bytes(data)
    record=next(x for x in manifest if x['file'].replace('\\','/')==path.relative_to(out).as_posix())
    record['patched_sha256']=hashlib.sha256(data).hexdigest()
    record['dialogue_entries']=len(translated)
manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Both dialogue tables updated:',len(translated))
