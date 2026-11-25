from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,zipfile
here=Path(__file__).resolve().parent
revs=here.parent
sys.path.insert(0,str(revs/'native-l11'))
from managed import CS,M,compile_dll
def run(*args):
    subprocess.run(args,cwd=here,check=True)
def digest(data):
    return hashlib.sha256(data).hexdigest()
def package(old_dir,previous,revision,dll,binary,windows):
    old=json.loads((revs/old_dir/'verification.json').read_bytes())
    base=Path(old['archive'])
    target=base.with_name(base.name.replace('-'+previous+'-','-'+revision+'-'))
    assert target!=base and digest(base.read_bytes())==old['archive_sha256']
    prefix='覆盖到游戏目录/'
    baseline={(prefix+k if windows else k):v for k,v in old['files'].items()}
    payload=prefix+dll
    manifest={**baseline,payload:digest(binary.read_bytes())}
    assert baseline[payload]!=manifest[payload]
    with tempfile.TemporaryDirectory(dir=base.parent) as tmp:
        part=Path(tmp)/'candidate.zip'
        with zipfile.ZipFile(base) as src,zipfile.ZipFile(part,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
            names=src.namelist()
            for name in names:
                data=src.read(name)
                if name in baseline:
                    assert digest(data)==baseline[name]
                if name==payload:
                    data=binary.read_bytes()
                elif name=='文件清单.json':
                    index=json.loads(data)
                    assert index['revision']==previous
                    index.update(revision=revision,game_files={k[len(prefix):]:v for k,v in manifest.items()})
                    data=json.dumps(index,ensure_ascii=False,indent=2).encode()
                elif name=='SHA256.txt':
                    data=''.join(f'{h}  {n}\n' for n,h in sorted(manifest.items())).encode()
                elif name in ['使用说明.md','安装说明.txt']:
                    title='Windows' if windows else 'Steam Deck / 原生 Linux'
                    data=(f'《四重奏》1.5.20260912 · {title} 简体中文完整覆盖包 {revision}\n\n'
                        '从“最近获得”进入装备比较时，光标定位到该装备在游戏原有列表中的位置。可上下浏览同部位的其他装备。\n'
                        f'退出游戏后将“覆盖到游戏目录”内的文件复制到游戏目录并覆盖。回退可重新覆盖上一版 {previous} 完整包。\n\n以下是之前版本的说明与安装细节。\n\n').encode()+data
                out.writestr(name,data)
        with zipfile.ZipFile(part) as z:
            assert z.namelist()==names and z.testzip() is None
            actual={n:digest(z.read(n)) for n in names if n.startswith(prefix)}
            assert actual==manifest
            recorded=({prefix+k:v for k,v in json.loads(z.read('文件清单.json'))['game_files'].items()} if windows else
                      {n:h for h,n in (l.split('  ',1) for l in z.read('SHA256.txt').decode().splitlines())})
            assert recorded==actual
        os.replace(part,target)
    receipt=dict(revision=revision,archive=str(target),archive_sha256=digest(target.read_bytes()),files={k[len(prefix):] if windows else k:v for k,v in manifest.items()},offline_fixture=windows or fixture_passed,game_visual_verified=False)
    (here/(revision+'.json')).write_text(json.dumps(receipt,indent=2,ensure_ascii=False),'utf8')
    print(target,flush=True)
run('gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-static-libgcc','-shared','-s','-Wl,--no-insert-timestamp,--image-base,0x3bc460000','recent.c','-o','QuartetRecentItems.dll')
run('gcc','-std=c11','-O2','-fno-strict-aliasing','test_route.c','-o','test_route.exe')
run(here/'test_route.exe')
stage=here/'stage'
stage.mkdir(exist_ok=True)
for dll in ('Assembly-CSharp.dll','Quartet.Chinese.dll'):
    shutil.copyfile(revs/'native-shop-l14/stage'/dll,stage/dll)
refs=[M/(n+'.dll') for n in ('mscorlib','System','System.Core','netstandard','UnityEngine.CoreModule','UnityEngine.UIModule','UnityEngine.UI','Unity.TextMeshPro','UnityEngine.JSONSerializeModule','YarnSpinner.Unity','YarnSpinner','UniRx','ArticyRuntime')]
recent=stage/'Quartet.RecentItems.dll'
compile_dll(recent,refs+[stage/'Assembly-CSharp.dll',stage/'Quartet.Chinese.dll'],[here/'RecentItems.cs'])
fixture_passed=False
if '--skip-menu-fixture' not in sys.argv:
    run(CS,'/nologo','/codepage:65001','/out:'+str(stage/'MenuFixture.exe'),here/'MenuFixture.cs',here/'RecentItems.cs')
    run(stage/'MenuFixture.exe')
    fixture_passed=True
run(revs/'native-gear-l13/stage/Verify.exe',stage,M)
package('windows-gear-shop-r28','r28','r29','QuartetRecentItems.dll',here/'QuartetRecentItems.dll',True)
package('native-shop-l14','l14','l15','QuartetLinux_Data/Managed/Quartet.RecentItems.dll',recent,False)
