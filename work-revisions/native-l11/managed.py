"""Compile the native Mono assemblies using the archived l9 sources and the l10 hooks."""
from assets import S,OUT,HERE,ROOT,read
from pathlib import Path
import json, subprocess, zipfile
P=ROOT/'linux-native'
M=P/'input/build25279268/QuartetLinux_Data/Managed'
CS=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
def run(*args):subprocess.run([str(a) for a in args],check=True)
def compile_dll(name,refs,files,resources=()):
    run(CS,'/nologo','/noconfig','/nostdlib','/target:library','/optimize+','/out:'+str(OUT/name),
        *['/reference:'+str(r) for r in refs],*['/resource:'+str(r)+','+r.name for r in resources],*files)
def main():
    refdir=S/'ref';refdir.mkdir(exist_ok=True)
    game=refdir/'Assembly-CSharp.dll'
    run(CS,'/nologo','/optimize+','/out:'+str(S/'Patch.exe'),'/reference:'+str(S/'Mono.Cecil.dll'),HERE/'Patch.cs')
    run(S/'Patch.exe',S/'Assembly-CSharp.dll',game)
    src=S/'sources';src.mkdir(exist_ok=True)
    with zipfile.ZipFile(next((P/'release/delivery-l9-20261028').glob('*.zip'))) as z:
        for n in z.namelist():
            if n.startswith('增量构建/sources/') and Path(n).name.startswith('Quartet') and n.endswith('.cs'):
                (src/Path(n).name).write_bytes(z.read(n))
    path=src/'QuartetChinese.cs';code=path.read_text('utf-8-sig')
    def sub(old,new):
        nonlocal code
        assert code.count(old)==1,old
        code=code.replace(old,new)
    sub('string header=QuartetFullRules.Header(text,raw,chinese);','string header=LateLabels.Scoped(text,raw,chinese)??QuartetFullRules.Header(text,raw,chinese);')
    sub('bool known=result!=raw','result=LateLabels.Difficulty(result,chinese); bool known=header!=null||result!=raw')
    sub('QuartetFullRules.Speaker(source,line.TextID,chinese)','LateLabels.Speaker(source,line.TextID,chinese)')
    path.write_text(code,'utf-8-sig')
    path=src/'QuartetFullData.cs';code=path.read_text('utf-8-sig')
    import re
    match=re.search(r'\{[^{}]+,\"[^{}]*qzhreward_weapon_foilcards[^{}]*\"\}',code)
    assert match
    pair=match[0];value=pair.split(',',1)[1]
    code=code[:match.end()]+',{'+json.dumps('闪面纸牌')+','+value+code[match.end():]
    path.write_text(code,'utf-8-sig')
    titles=read(ROOT/'translations/dialogue-title-display.zh.json')
    unique={r['en'].lower():r['zh'] for r in titles['mappings']}
    cards={r['en']:r['zh'] for r in read(ROOT/'translations/oracle-card-display.zh.json').values() if r['en']!='????'}
    contexts={r['en']+'|'+r['line_id']:r['zh'] for r in titles['contextual_overrides']}
    def table(name,values):
        pairs=',\n'.join('{'+json.dumps(k)+','+json.dumps(v)+'}' for k,v in values.items())
        return 'static readonly Dictionary<string,string> '+name+'=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase){'+pairs+'};'
    amb=sorted({r['en'] for r in titles['contextual_overrides']})
    text='using System;using System.Collections.Generic;public static partial class LateLabels{\n'
    text+=table('names',unique)+table('cards',cards)+table('contexts',contexts)
    text+='static readonly HashSet<string> ambiguous=new HashSet<string>(StringComparer.OrdinalIgnoreCase){'+','.join(map(json.dumps,amb))+'};}'
    (src/'GeneratedNames.cs').write_text(text,'utf-8-sig')
    refs=[M/(r+'.dll') for r in ('mscorlib','System','System.Core','netstandard','UnityEngine.CoreModule','UnityEngine.UIModule',
          'UnityEngine.UI','Unity.TextMeshPro','UnityEngine.JSONSerializeModule','YarnSpinner.Unity','YarnSpinner','UniRx','ArticyRuntime')]
    refs.append(game)
    compile_dll('Quartet.Chinese.dll',refs,sorted(src.glob('*.cs'))+[HERE/'Labels.cs'],[OUT/'catalog.bin',S/'display.bin'])
    compile_dll('Quartet.RecentItems.dll',refs+[OUT/'Quartet.Chinese.dll'],[HERE/'RecentItems.cs'])
    run(S/'Patch.exe',game,OUT/'Assembly-CSharp.dll',OUT/'Quartet.RecentItems.dll')
if __name__=='__main__':main()
