from base import *
import shutil,subprocess,zipfile
REV=PREV/'work-revisions'
CSC=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
MAN='QuartetLinux_Data/Managed'
GAME_DLL='Assembly-CSharp.dll'
WORK=D/'managed-work'
def run(*args):subprocess.run(list(map(str,args)),check=True)
def main():
    WORK.mkdir(exist_ok=True)
    cecil=PREV/'linux-native/build/managed-tools/Mono.Cecil.dll'
    shutil.copyfile(cecil,WORK/'Mono.Cecil.dll')
    sources={'Pilot':PREV/'linux-native/tools/PatchManaged.cs','Recent':REV/'recent-items-20261119/PatchRecent.cs',
             'Equip':REV/'native-l11/Patch.cs','Slots':REV/'native-gear-l13/ExposeSlots.cs','Shop':REV/'native-shop-l14/ShopHooks.cs'}
    for k,src in sources.items():
        run(CSC,'/nologo','/optimize+','/reference:'+str(cecil),'/out:'+str(WORK/(k+'.exe')),src)
    l10=next((PREV/'linux-native/release/recent-items-l10').glob('*.zip'))
    with zipfile.ZipFile(l10) as z:(WORK/'l10-feature.dll').write_bytes(z.read('覆盖到游戏目录/'+MAN+'/Quartet.RecentItems.dll'))
    with zipfile.ZipFile(l15['archive']) as z:(WORK/'l15-reference.dll').write_bytes(z.read('覆盖到游戏目录/'+MAN+'/'+GAME_DLL))
    for key,base in [('old',PRISTINE),('new',NEW)]:
        w=WORK/key; w.mkdir(exist_ok=True)
        inp=w/'input';inp.mkdir(exist_ok=True)
        for name in ('Unity.TextMeshPro.dll','YarnSpinner.Unity.dll',GAME_DLL):
            p=base/MAN/name if name==GAME_DLL else PRISTINE/MAN/name
            assert sha(p,'sha1')==(old if key=='old' else new)[MAN+'/'+name]
            shutil.copy2(p,inp/name)
        shutil.copy2(STAGE/MAN/'Quartet.Chinese.dll',w/'Quartet.Chinese.dll')
        run(WORK/'Pilot.exe',inp,w,w/'hooks.txt')
        run(WORK/'Recent.exe',PRISTINE/MAN,w/GAME_DLL,WORK/'l10-feature.dll',w/'l10.dll')
        run(WORK/'Equip.exe',w/'l10.dll',w/'ref.dll')
        run(WORK/'Equip.exe',w/'ref.dll',w/'l11.dll',REV/'native-l11/stage/new/Quartet.RecentItems.dll')
        run(WORK/'Slots.exe',w/'l11.dll',w/'l13.dll')
        run(WORK/'Shop.exe',w/'l13.dll',STAGE/MAN/'Quartet.Chinese.dll',w/'final.dll')
if __name__=='__main__':main()
