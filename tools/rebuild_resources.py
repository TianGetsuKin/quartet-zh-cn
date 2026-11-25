import json,hashlib
from asset_support import ROOT,GAME,generator
from name_assets import build_name_asset
path=ROOT/'build/pilot/manifest.json';manifest=json.loads(path.read_text())
record=next(r for r in manifest if r['file']=='resources.assets')
assert hashlib.sha256((GAME/'resources.assets').read_bytes()).hexdigest()==record['original_sha256'],'Restore localization before rebuilding resources'
new=build_name_asset(generator());assert new['original_sha256']==record['original_sha256']
record.clear();record.update(new);path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Resource display asset rebuilt with unchanged unrelated objects.')
