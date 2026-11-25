from pathlib import Path
from PIL import Image
import json,io,re,base64,gzip,collections,math
import UnityPy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];OUT=ROOT/'release/活点地图/四重奏：四界图志.html'
def data(p):return json.loads((ROOT/p).read_text('utf-8-sig'))
def compact(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def enc(b):return base64.b64encode(b).decode()
rooms0=json.loads((W/'detailed-fixed.json').read_text('utf8'))
roots=['ethos','bathos','pathos','logos'];people=['尼古拉','本','亚历珊德拉','科黛莉娅']
ids=[49,58,56,53];D=Path('G:/SteamLibrary/steamapps/common/Quartet/Quartet_Data')
rooms={r['k'][4:]:r for r in rooms0 if 'b' in r and r['k'][4:].split('/')[0] not in ('bullshots','debugmaps','test','credits','fakechapterselect','decky training')}
ix={k:i for i,k in enumerate(sorted(rooms))}
worldids=[next(ix[k] for k in rooms if k.endswith('/'+world+'worldmap')) for world in roots]
rows=data('qa/overview-locations-full.json');sources={r['id']:r['data'] for r in rows}
missing=data('translations/overview-missing-labels.zh.json')
def clean(v):return re.sub('<[^>]*>','',v).replace('\n','').strip()
worlds=[[] for _ in roots]
for p in data('translations/overview-layout.json')['labels']:
 w=roots.index(p['world'].split('World')[0]);x,y=p['marker'];m=sources[p['id']].get('mapId',''); en=clean(p['en']);zh=clean(p['zh'])
 if not zh:en,zh=missing[m]
 if zh in ('赫尔瓦广场','赫尔瓦梯田'):zh=zh[:3]+'·'+zh[3:]
 k=m.lower();j=ix.get(k,-1)
 if k and j<0:print('Missing world destination',k)
 group=next((a for a in worlds[w] if a[2]==zh and math.hypot(a[0]-x,a[1]-y)<.5),None)
 if not group:
  group=[x,y,zh,en,[]];worlds[w].append(group)
 if j>=0 and j not in group[4]:group[4].append(j)
world_edge=1240
cache=W/f'world-images-{world_edge}-q79.json'
if not cache.exists():
 e=UnityPy.load(str(D/'sharedassets6.assets'));imgs=[]
 for sid in ids:
  s=e.file.objects[sid].read();full=Image.new('RGBA',(round(s.m_Rect.width),round(s.m_Rect.height)));off=s.m_RD.textureRectOffset
  im=s.image;full.paste(im,(round(off.x),round(full.height-off.y-s.m_RD.textureRect.height)))
  full.thumbnail((world_edge,world_edge),Image.Resampling.LANCZOS)
  ocean=Image.new('RGB',full.size,(20,44,53));ocean.paste(full,mask=full.getchannel('A'))
  buf=io.BytesIO();ocean.save(buf,'WEBP',quality=79,method=6)
  imgs.append(enc(buf.getvalue()))
 cache.write_text(compact(imgs),'utf8')
imgs=json.loads(cache.read_text('utf8'))
# Resolve exits against the correct world's reciprocal entrance. For story variants,
# an identical named spawn links to the same entrance. Otherwise retain the exact landing coordinates.
routes=json.loads((W/'world-exits.json').read_text('utf8'))
routes=[v for v in routes if v[0] in ix and v[3] in ix]
from collections import defaultdict
known=defaultdict(set)
def reciprocal(room,world,spawn):
 candidates=[i for i,pt in enumerate(worlds[world]) if ix[room] in pt[4]]
 if len(candidates)==1:return candidates[0]
 if candidates and spawn:return min(candidates,key=lambda i:math.dist(worlds[world][i][:2],spawn))
for room,x,y,dest,target,spawn in routes:
 wi=worldids.index(ix[dest]);match=reciprocal(room,wi,spawn)
 if match is not None:known[(dest,target)].add(match)
arrivals={}
for room,x,y,dest,target,spawn in routes:
 wi=worldids.index(ix[dest]);match=reciprocal(room,wi,spawn)
 if match is None and len(known[dest,target])==1:match=next(iter(known[dest,target]))
 arrival=match if match is not None else spawn
 assert arrival is not None,(room,dest,target)
 arrivals[(room,x,y,dest)]=arrival
from encounter_guides import build as build_guides
formations,boss_points,extra_rewards,chest_keys,story_battles=build_guides(rooms)
records=[]
for k in sorted(rooms):
 r=rooms[k]; e=[]; c=[]; b=r['b']
 for x,y,dest in r['e']:
  j=ix.get(dest)
  if j is None:continue
  entry=[x,y,j]
  if j in worldids:entry.append(arrivals[(k,x,y,dest)])
  if not any(q[2:]==entry[2:] and math.hypot(x-q[0],y-q[1])<1 for q in e):e.append(entry)
 for x,y,name in r['c']+extra_rewards.get(k,[]):
  entry=[x,y,name]
  if (k,x,y) in chest_keys:entry.append(chest_keys[k,x,y])
  if entry not in c:c.append(entry)
 records.append([k,r['n'],b,'' if ix[k] in worldids else r['i'],e,c,boss_points.get(k,[]),story_battles.get(k,[])])
for jj,name in enumerate(people):
 g=worlds[jj];print(name,len(g),'markers')
from tiles_codec import compress_room
blob=bytearray();unique={}
for r in records:
 if r[3] not in unique:
  compressed=compress_room(r[3])
  unique[r[3]]=[len(blob),len(compressed)]
  blob.extend(compressed)
 r[3]=unique[r[3]]
from item_layers import build as item_layers
from boss_routes import attach_boss_routes
attach_boss_routes(records,worlds,worldids)
item_art=item_layers(records,D)
payload=[records,worlds,imgs,worldids,(W/'tile-dict-fixed.txt').read_text('ascii'),formations,item_art]
html=(W/'atlas.html').read_text('utf8').replace('__LAYER_UI__',(W/'layer-ui.js').read_text('utf8')).replace('__BOSS_UI__',(W/'boss-ui.js').read_text('utf8')).replace('__DATA__',enc(gzip.compress(len(compact(payload).encode()).to_bytes(4,'little')+compact(payload).encode()+blob,compresslevel=9,mtime=0)))
OUT.write_text(html,'utf8')
OUT.with_name('Quartet-四界活点地图.html').write_bytes((W/'legacy-entry.html').read_bytes())
print(OUT,OUT.stat().st_size,len(records),sum(len(r[5]) for r in records),sum(len(r[4]) for r in records))
