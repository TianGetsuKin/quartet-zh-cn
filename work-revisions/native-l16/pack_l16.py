from base import *
import zipfile,tempfile,shutil,os,UnityPy
def programs(base):
    env=UnityPy.load(str(next((base/'QuartetLinux_Data/StreamingAssets/aa/StandaloneLinux64').glob('default_scenes_all*.bundle'))))
    proj,=[o for o in env.objects if o.type.name=='MonoBehaviour' and o.serialized_type.node and any(c.m_Name=='compiledYarnProgram' for c in o.serialized_type.node.m_Children)]
    globe=UnityPy.load(str(base/'QuartetLinux_Data/globalgamemanagers.assets'))
    g,=[o for o in globe.objects if o.type.name=='MonoBehaviour' and o.parse_monobehaviour_head().m_Name==proj.parse_monobehaviour_head().m_Name and b'BossCutscenes.yarn' in o.get_raw_data() and b'battle_liganti1' in o.get_raw_data()]
    return [hashlib.sha256(bytes(o.read_typetree(nodes=proj.serialized_type.node)['compiledYarnProgram'])).hexdigest() for o in [proj,g]]
def clean(n):
    if (NEW/n).is_file():return NEW/n
    if (PRISTINE/n).is_file():return PRISTINE/n
    assert n.endswith('sharedassets7.assets.resS')
    return PREV/'work-revisions/native-l11/stage/sharedassets7.assets.resS'
def main():
    prog=programs(STAGE)
    assert prog==programs(NEW) and len(set(prog))==1
    assets=json.loads((D/'assets-l16.json').read_bytes())
    assert len(assets)==18 and all(v.get('rebuilt') or v.get('carried') for v in assets.values())
    il=json.loads((D/'managed-check.json').read_text('utf-8-sig'))
    assert il['old_replay_diff']==0 and il['official_vs_hooks_overlap']==0 and il['hook_runtime_verified']
    out=Path(l15['archive']).parent/'四重奏-1.5.20261124-原生Linux-l16-简体中文完整覆盖包.zip'
    tmp=out.with_suffix('.pending.zip')
    names={current_name(n) for n in files};assert len(names)==19 and names=={p.relative_to(STAGE).as_posix() for p in STAGE.rglob('*') if p.is_file()}
    hashes={n:sha(STAGE/n,'sha256') for n in sorted(names)}
    steam={n:new[n] for n in hashes if n in new};assert len(steam)==17
    for n,h in steam.items():assert sha(clean(n),'sha1')==h,n
    receipt=dict(game_version='1.5.20261124',steam_build=26908524,depot=1307964,revision='l16',steam_sha1=steam,files=hashes)
    with zipfile.ZipFile(l15['archive']) as z:license=z.read('OFL.txt')
    prefix='覆盖到游戏目录/'
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in hashes:z.write(STAGE/n,prefix+n)
        z.writestr('OFL.txt',license);z.write(D/'安装说明.txt','安装说明.txt')
        z.writestr('文件清单.json',json.dumps(receipt,indent=2,ensure_ascii=False).encode('utf8'))
    with tempfile.TemporaryDirectory(dir=D) as t,zipfile.ZipFile(tmp) as z:
        game=Path(t)/'game';backup=Path(t)/'backup'
        assert len(z.namelist())==len(hashes)+3 and z.testzip() is None
        for n in steam:
            for root in (game,backup):
                dest=root/n;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(clean(n),dest)
        for n,h in hashes.items():
            with z.open(prefix+n) as src,(game/n).open('wb') as dest:shutil.copyfileobj(src,dest)
            assert sha(game/n,'sha256')==h
        for n in hashes:
            if n in steam:shutil.copyfile(backup/n,game/n)
            else:(game/n).unlink()
        assert all(sha(game/n,'sha1')==h for n,h in steam.items())
        assert {p.relative_to(game).as_posix() for p in game.rglob('*') if p.is_file()}==set(steam)
    os.replace(tmp,out)
    receipt.update(archive=str(out),archive_sha256=sha(out,'sha256'),archive_bytes=out.stat().st_size,official_yarn_program_sha256=prog[0],file_install_restore=True,deck_ui_verified=False)
    (D/'release-l16.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False),'utf8')
    print(out,receipt['archive_sha256'])
if __name__=='__main__':main()
