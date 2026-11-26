from native_refs import *
import subprocess,runpy,tempfile,shutil
def run(args,cwd):
    subprocess.run(args,cwd=cwd,check=True)
def helpers():
    a,b,c=images();refs=References(Mapper(a,c));src=PREV/'work-revisions/equip-focus-r29-l15'
    build=HERE/'windows-helpers';build.mkdir(exist_ok=True)
    mapping={}
    for n in ['recent.c','preview.h']:
        raw=(src/n).read_text('utf8')
        for addr in re.findall(r'GAME_(?:FUNCTION|METADATA)\((0x[0-9a-f]+)',raw):mapping[addr]=hex(refs.get(int(addr,16)))
    def relocate(raw):
        return re.sub(r'0x[0-9a-fA-F]+',lambda m:mapping.get(m[0],m[0]),raw)
    for n in ['recent.c','preview.h','test_route.c']:
        (build/n).write_text(relocate((src/n).read_text('utf8')).replace('Quartet build 25279268','Quartet build 26908524'),'utf8')
    stage=HERE/'stage'
    run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-static-libgcc','-shared','-s','-Wl,--no-insert-timestamp,--image-base,0x3bc460000','recent.c','-o',str(stage/'QuartetRecentItems.dll')],build)
    run(['gcc','-std=c11','-O2','-fno-strict-aliasing','test_route.c','-o','test_route.exe'],build)
    run([str(build/'test_route.exe')],build)
    r27=PREV/'work-revisions/speaker-review-r27/windows'
    scope=runpy.run_path(str(r27/'build.py'))
    receipt=json.loads((PREV/'work-revisions/equip-focus-r29-l15/r29.json').read_bytes())
    vr=json.loads((r27/'verification.json').read_bytes())
    with zipfile.ZipFile(receipt['archive']) as z:old=z.read('覆盖到游戏目录/QuartetZhLanguage.dll')
    pieces,lines=scope['unpack'](old,vr['catalog_sha256'])
    catalog=scope['tools']['BASE']['pack'](pieces,lines)
    assert hashlib.sha256(catalog).hexdigest()==vr['catalog_sha256']
    # Reuse the exact source-generation steps from the previous release. Recompile only with relocated native calls.
    code=(r27/'build.py').read_text('utf8')
    code=code[code.index('def compile_runtime'):code.index('def main')]
    needle="    main.write_text(code,'utf8')"
    assert code.count(needle)==1
    resize=refs.get(0x2a08ad0);mapping['0x2a08ad0']=hex(resize)
    code=code.replace(needle,"    assert code.count('r.base+0x2a08ad0') == 1\n    code = code.replace('r.base+0x2a08ad0','r.base+"+hex(resize)+"')\n"+needle)
    exec(code,scope)
    with tempfile.TemporaryDirectory(dir=build) as tmp:
        out=scope['compile_runtime'](Path(tmp),catalog)
    (stage/'QuartetZhLanguage.dll').write_bytes(out)
    (HERE/'helper-relocations.json').write_text(json.dumps(mapping,indent=2),'utf8')
if __name__=='__main__':helpers()
