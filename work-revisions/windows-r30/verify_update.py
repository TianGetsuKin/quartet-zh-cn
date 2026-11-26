"""Check the new native imports, Yarn programs and Windows loader independently of the build."""
from compare_depots import HERE, GAME
from native_images import Image
from pathlib import Path
import hashlib, json, os, struct, sys, ctypes
import UnityPy

def yarn(root):
    bundle = next((root/'Quartet_Data/StreamingAssets/aa/StandaloneWindows64').glob('default_scenes_all*.bundle'))
    scene = UnityPy.load(str(bundle))
    obj, = [o for o in scene.objects if o.type.name=='MonoBehaviour' and o.serialized_type.node and
            any(c.m_Name=='compiledYarnProgram' for c in o.serialized_type.node.m_Children)]
    schema = obj.serialized_type.node
    manager = UnityPy.load(str(root/'Quartet_Data/globalgamemanagers.assets'))
    shared, = [o for o in manager.objects if o.type.name=='MonoBehaviour' and
               o.parse_monobehaviour_head().m_Name==obj.parse_monobehaviour_head().m_Name and
               b'battle_liganti1' in o.get_raw_data() and b'BossCutscenes.yarn' in o.get_raw_data()]
    return [hashlib.sha256(bytes(o.read_typetree(nodes=schema)['compiledYarnProgram'])).hexdigest() for o in (obj,shared)]

def native(root):
    path=(root/'GameAssembly.dll').resolve()
    official,patched=[Image(p.read_bytes()) for p in [GAME/path.name,path]]
    def unwind(im):
        return set(struct.iter_unpack('<III',im.read(*im.dir(3))))
    orig=unwind(official); extra=unwind(patched)-orig
    assert orig <= unwind(patched) and len(extra)==35
    start,size=official.dir(1)
    assert official.read(start,size-20)==patched.read(patched.dir(1)[0],size-20)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.SetErrorMode(3)
    with os.add_dll_directory(str(GAME)):
        with os.add_dll_directory(str(root)):
            # Load helpers by absolute path before loading their importer.
            loaded=[ctypes.WinDLL(str(root/n),winmode=0x1100) for n in
                    ['QuartetRecentItems.dll','QuartetZhLanguage.dll','GameAssembly.dll']]
            for mod in loaded:
                buf=ctypes.create_unicode_buffer(32768)
                assert kernel.GetModuleFileNameW(ctypes.c_void_p(mod._handle),buf,len(buf))
                assert Path(buf.value).parent.samefile(root)
            assert all(getattr(loaded[-1],fn) for fn in ['il2cpp_init','il2cpp_domain_get','il2cpp_class_from_name'])
    return dict(official_unwind_entries=len(orig),additional_unwind_entries=len(extra),isolated_dll_load=True)

if __name__=='__main__':
    root = Path(sys.argv[1]).resolve() if sys.argv[1:] else HERE/'stage'
    digests=yarn(root)
    assert digests==yarn(GAME) and len(set(digests))==1
    assets=json.loads((HERE/'asset-audit.json').read_bytes())
    assert all(v.get('rebuilt') or v.get('unchanged_source') for v in assets.values())
    report=dict(yarn_scene_and_global_sha256=digests,asset_containers=len(assets),**native(root))
    print(json.dumps(report))
    (HERE/'verified-update.json').write_text(json.dumps(report,indent=2),'utf8')
