from base import *
import zipfile
# Keep the previous revision immutable and reuse the same checked Unity-object merge.
def core():
    script=(D.parent/'migrate_assets.py').read_text('utf8')
    functions=script[script.index('def objmap('):script.index("if __name__=='__main__':")]
    substitutions={
        "PREV/'backups/game-original'/n.partition('/')[2]":"PRISTINE/n",
        "GAME.rglob('default_scenes_all*.bundle')":"(GAME/'QuartetLinux_Data/StreamingAssets/aa/StandaloneLinux64').glob('default_scenes_all*.bundle')",
        'if not head.m_GameObject.path_id:return None':'if not head.m_GameObject.path_id:return (head.m_Name,head.m_Script.file_id,head.m_Script.path_id)',
    }
    for a,b in substitutions.items():
        assert functions.count(a)==1
        functions=functions.replace(a,b)
    import migrate_assets
    scope={**vars(migrate_assets), 'PRISTINE':PRISTINE, 'old':old, 'new':new,'HERE':D,'GAME':NEW}
    exec(functions,scope)
    return scope['audit']
if __name__=='__main__':
    audit=core()
    report={}
    assert sha(Path(l15['archive']),'sha256')==l15['archive_sha256']
    with zipfile.ZipFile(l15['archive']) as z:
        for n,digest in files.items():
            m=current_name(n)
            if n=='QuartetLinux_Data/Managed/Assembly-CSharp.dll':continue
            if n not in old or old[n]==new[m]:
                dest=STAGE/m;dest.parent.mkdir(exist_ok=True,parents=True)
                data=z.read('覆盖到游戏目录/'+n);assert hashlib.sha256(data).hexdigest()==digest
                dest.write_bytes(data);r={'carried':True}
            else:
                r=audit({'old':n,'new':m,'state':'changed'},z)
            report[m]=r
            (D/'assets-l16.json').write_text(json.dumps(report,indent=2),'utf8')
            print(m.split('/')[-1],r.get('rebuilt',r.get('carried')),str(r.get('conflicts',[]))[:300],flush=True)
