"""Resolve each pickup by its scene component and pack original inventory sprites."""
import base64
import io
import json
from pathlib import Path
from PIL import Image
import UnityPy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TABS = ['consumables', 'tome', 'weapon', 'helm', 'armor', 'accessory', 'keyitem']

def read(path):
    return json.loads(path.read_bytes())

def build(records, game_data):
    art = read(ROOT/'qa/reward-icon-inventory.json')
    icons = {r['technical'].lower():r['technical'] for r in art['items']}
    props = {}
    for row in read(ROOT/'qa/map-battle-display-inventory.json'):
        data = row['data']
        item = data.get('mTemplate',{}).get('value',{}).get('mitemProperties',{}).get('value')
        if item:
            slot = item['mslot']
            props[data['technicalName'].lower()] = ('tome' if item['mconsumableDirect']==5 else 'consumables') if slot==1 else TABS[slot]
    sources = {}
    def register(k,x,y,data):
        reward = (data.get('treasureID','').lower(),int(data.get('valAmount') or 0))
        if any(reward):
            assert sources.setdefault((k,x,y),reward)==reward,(k,x,y)
    for k,x,y,chain in read(HERE/'event-sources.json')['chests']:
        for comp in chain[0][1]:
            if 'treasureID' in comp: register(k,x,y,comp)
    for k,x,y,_,data in read(HERE/'atlas-custom.json')['rewards']:
        register(k,x,y,data)
    collection = next(r for r in read(ROOT/'qa/controller-icon-source-inventory.json') if r['file']=='default_assets' and r['name']=='itemIcons')
    env = UnityPy.load(str(game_data/art['source_bundle']))
    obj = next(o for o in env.objects if o.path_id==collection['id'])
    refs = {s['name']:s['sprite']['m_PathID'] for s in obj.read_typetree()['sprites']}
    images = [obj.assets_file.objects[refs['inventory_'+k]].read().image.convert('RGBA') for k in TABS]
    index = {}
    entries = []
    # Story key items use explicit AddItem commands rather than collectible chest objects.
    # Record the actual scene trigger. A cutscene may travel elsewhere before the award.
    from collections import defaultdict
    nodes=read(HERE/'atlas-nodes.json')
    story=defaultdict(set)
    playable={room[0] for room in records}
    for k,x,y,node in read(HERE/'event-sources.json')['triggers']:
        if k not in playable: continue
        for op,cmd in nodes.get(node,[]):
            bits=cmd.lower().split()
            if op==3 and len(bits)>=2 and bits[0]=='additem' and props.get(bits[1])=='keyitem':
                story[k].add((x,y,bits[1]))
    localized={r['technical'].lower():r['zh'] for r in art['items']}
    def item_index(key):
        if key not in index:
            if key:
                im=Image.open(ROOT/'build/reward-icons'/(icons[key]+'.png')).convert('RGBA')
                category,sprite=props[key],len(images)
                images.append(im)
            else:
                category,sprite='money',-1
            index[key]=len(entries)
            entries.append([category,sprite])
        return index[key]
    for room in records:
        room.append([[x,y,localized[key],item_index(key),key] for x,y,key in sorted(story[room[0]])])
        for chest in room[5]:
            key,amount = sources[room[0],chest[0],chest[1]]
            if not key: assert chest[2]==f'{amount} 瓦尔'
            if len(chest)==3: chest.append(None)
            chest.append(item_index(key))
    cell = max(max(im.size) for im in images)
    sheet = Image.new('RGBA',(16*cell,((len(images)+15)//16)*cell))
    for i,im in enumerate(images):
        sheet.paste(im,((i%16)*cell+(cell-im.width)//2,(i//16)*cell+(cell-im.height)//2))
    buf = io.BytesIO()
    sheet.save(buf,'WEBP',lossless=True,method=6)
    print('Verified reward locations, distinct items, sheet bytes:',sum(len(r[5]) for r in records),len(entries)-1,len(buf.getvalue()))
    return [entries,TABS,cell,base64.b64encode(buf.getvalue()).decode('ascii')]
