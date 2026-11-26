from compare_depots import HERE, PREV, GAME, new, sha
from pathlib import Path
import os, json, hashlib, tempfile, shutil, zipfile

def pack():
    previous=json.loads((PREV/'work-revisions/equip-focus-r29-l15/r29.json').read_bytes())
    out=Path(previous['archive']).parent/'四重奏-1.5.20261124-Windows-r30-简体中文完整覆盖包.zip'
    stage=HERE/'stage'
    files={p.relative_to(stage).as_posix():sha(p,'sha256') for p in sorted(stage.rglob('*')) if p.is_file()}
    rows=json.loads((HERE/'windows-depot-diff.json').read_bytes())['patch_files']
    assert len(files)==18 and set(files)=={row['new'] for row in rows}
    original={n:new[n] for n in files if n in new}
    assert set(files)-set(original)=={'QuartetRecentItems.dll','QuartetZhLanguage.dll'}
    docs={'使用说明.md':(HERE/'使用说明.md').read_bytes()}
    with zipfile.ZipFile(previous['archive']) as z:docs['OFL.txt']=z.read('OFL.txt')
    manifest=dict(game='Quartet',version='1.5.20261124',platform='Windows x64',steam_build=26908524,revision='r30',original_steam_sha1=original,files=files)
    docs['文件清单.json']=json.dumps(manifest,indent=2,ensure_ascii=False).encode('utf8')
    tmp=out.with_suffix('.pending.zip')
    prefix='覆盖到游戏目录/'
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in files:z.write(stage/n,prefix+n)
        for n,data in docs.items():z.writestr(n,data)
    with tempfile.TemporaryDirectory(dir=HERE) as temp:
        install=Path(temp)/'game'
        backup=Path(temp)/'backup'
        for n,h in original.items():
            assert sha(GAME/n,'sha1')==h
            for root in (install,backup):
                dest=root/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(GAME/n,dest)
        with zipfile.ZipFile(tmp) as z:
            assert len(z.namelist())==len(files)+len(docs)
            assert set(z.namelist())=={prefix+n for n in files}|docs.keys()
            for n in docs:assert docs[n]==z.read(n)
            for n,h in files.items():
                with z.open(prefix+n) as src,(install/n).open('wb') as dest:shutil.copyfileobj(src,dest)
                assert sha(install/n,'sha256')==h
        for n in files:
            if n in original:shutil.copyfile(backup/n,install/n)
            else:(install/n).unlink()
        assert all(sha(install/n,'sha1')==h for n,h in original.items())
        assert {p.relative_to(install).as_posix() for p in install.rglob('*') if p.is_file()}==set(original)
    os.replace(tmp,out)
    report={**manifest,'archive':str(out),'archive_sha256':sha(out,'sha256'),'archive_bytes':out.stat().st_size,'isolated_file_install_restore':True,'game_ui_verified':False,**json.loads((HERE/'verified-update.json').read_bytes())}
    (HERE/'release-r30.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),'utf8')
    print(out.name,report['archive_bytes'],report['archive_sha256'])
if __name__=='__main__':pack()
