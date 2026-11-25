"""Render the original Unity tile layers into compact, reusable 16-pixel cells."""
from pathlib import Path
from functools import lru_cache
from collections import defaultdict, Counter
import math, struct, json, base64, io
import UnityPy
from PIL import Image
W=Path(__file__).resolve().parent
root=W.parents[1]
aa=Path('G:/SteamLibrary/steamapps/common/Quartet/Quartet_Data/StreamingAssets/aa/StandaloneWindows64')
def bundle(pattern):
 env=UnityPy.load(str(next(aa.glob(pattern))))
 return next(f for f in env.file.files.values() if hasattr(f,'objects'))
maps=bundle('maps_assets_all_*.bundle')
tiles=bundle('tilesets_assets_all_*.bundle')
roots=json.loads((root/'qa/map-display-name-source.json').read_text('utf8'))['entries']
by_root={r['game_object_id']:r for r in roots}
# Room addresses were already resolved from the catalogue; pair them by their GUID again.
catalog=(aa.parent/'catalog.bin').read_bytes()
def uint(p):return struct.unpack_from('<I',catalog,p)[0]
def address(g):
 p=catalog.find(g.encode())
 if p<0 or uint(p+32)>>30!=1:return None
 node=uint(p+32)&0x3fffffff;parts=[]
 while node!=0xffffffff:
  s,node=struct.unpack_from('<II',catalog,node);parts.append(catalog[s:s+uint(s-4)].decode())
 return '/'.join(reversed(parts))
keys={}
renderers={}
for o in maps.objects.values():
 if o.type.name=='AssetBundle':
  for guid,v in o.read().m_Container:
   if v.asset.path_id in by_root:keys[v.asset.path_id]=address(guid)
 if o.type.name=='TilemapRenderer':
  d=o.read_typetree()
  if d['m_Enabled']:renderers[d['m_GameObject']['m_PathID']]=(d['m_SortingLayer'],d['m_SortingOrder'])
@lru_cache(None)
def obj(i):return maps.objects[i].read_typetree()
@lru_cache(None)
def transform(tid):
 t=obj(tid);gid=t['m_GameObject']['m_PathID'];go=obj(gid)
 if gid in by_root:return gid,0,0,True
 parent=t['m_Father']['m_PathID']
 if not parent:return None,0,0,False
 r,x,y,active=transform(parent);p=t['m_LocalPosition']
 return r,x+p['x'],y+p['y'],active and go['m_IsActive']
files={0:maps,next(i+1 for i,f in enumerate(maps.externals) if tiles.name in f.path):tiles}
sprites={}
for fi,f in files.items():
 group=defaultdict(list)
 for o in f.objects.values():
  if o.type.name=='Sprite':
   s=o.read()
   if s.m_RD.texture.m_FileID==0:group[s.m_RD.texture.m_PathID].append((o.path_id,s))
 for tex,entries in group.items():
  if tex not in f.objects:continue
  im=f.objects[tex].read().image.convert('RGBA')
  for sid,s in entries:
   r=s.m_RD.textureRect
   if not (0<r.width<=2048 and 0<r.height<=2048):continue
   left=round(r.x);top=im.height-round(r.y+r.height)
   pic=im.crop((left,top,left+round(r.width),top+round(r.height)))
   factor=16/s.m_PixelsToUnits
   if factor!=1:pic=pic.resize((max(1,round(pic.width*factor)),max(1,round(pic.height*factor))),Image.Resampling.NEAREST)
   off=s.m_RD.textureRectOffset
   sprites[(fi,sid)]=(pic,(off.x-s.m_Pivot.x*s.m_Rect.width)*factor,(off.y+r.height-s.m_Pivot.y*s.m_Rect.height)*factor)
print('Sprite geometry loaded',len(sprites),flush=True)
tilepics=[];by_pixels={};opaque=[]
def intern(pic):
 k=pic.tobytes()
 if k not in by_pixels:
  by_pixels[k]=len(tilepics);tilepics.append(pic);opaque.append(pic.getextrema()[3][0]==255)
 return by_pixels[k]
@lru_cache(None)
def parts(ref,m,tint):
 pic,u,v=sprites[ref];a,b,c,d,tx,ty=m
 # Source top-left in Unity units, expressed in pixels with screen Y down.
 x0=a*u+b*v+tx;y0=-c*u-d*v-ty
 aa,bb,cc,dd=a,-b,-c,d
 corners=[(x0+aa*x+bb*y,y0+cc*x+dd*y) for x,y in ((0,0),(pic.width,0),(0,pic.height),pic.size)]
 x=round(min(k[0] for k in corners));y=round(min(k[1] for k in corners))
 width=round(max(k[0] for k in corners))-x;height=round(max(k[1] for k in corners))-y
 det=aa*dd-bb*cc
 if not width or not height or abs(det)<1e-6:return []
 if (aa,bb,cc,dd)!=(1,0,0,1):
  dx=x-x0;dy=y-y0
  pic=pic.transform((width,height),Image.Transform.AFFINE,(dd/det,-bb/det,(dd*dx-bb*dy)/det,-cc/det,aa/det,(-cc*dx+aa*dy)/det),Image.Resampling.NEAREST)
 if tint!=(255,255,255,255):
  pic=pic.point([round(v*k/255) for k in tint for v in range(256)])
 out=[]
 for j in range(y//16,(y+pic.height-1)//16+1):
  for i in range(x//16,(x+pic.width-1)//16+1):
   px=i*16-x;py=j*16-y
   piece=pic.crop((px,py,px+16,py+16))
   if piece.getbbox():out.append((i,j,intern(piece)))
 return out
def rgba(col):
 if isinstance(col,dict) and 'rgba' in col:col=col['rgba']
 if isinstance(col,int):return tuple(col>>s&255 for s in (0,8,16,24))
 return tuple(col[k] for k in ('r','g','b','a'))
layers=defaultdict(list)
for o in maps.objects.values():
 if o.type.name!='Tilemap':continue
 raw=o.get_raw_data();gid=struct.unpack_from('<q',raw,4)[0]
 if gid not in renderers or not struct.unpack_from('<I',raw,16)[0]:continue
 go=obj(gid);rootid,gx,gy,active=transform(go['m_Component'][0]['component']['m_PathID'])
 if not active or not keys.get(rootid) or keys[rootid].lower().endswith('worldmap'):continue
 name=go['m_Name'].lower()
 if any(s in name for s in ('collision','trigger','blocker')):continue
 tree=o.read_typetree()
 # Full-screen fade and heat layers are animated by scripts. Their prefab
 # defaults obscure the environment when used as a static atlas frame.
 fades={'blackout','spellblackout','black','overdark','mid darkener','back darkener','zikarondarkness','heat layer','heat overlay','heatintensifier'}
 if len(tree['m_TileSpriteArray'])==1 and (name in fades or name in ('tile support','filler')):continue
 anchor=tree['m_TileAnchor'];gx+=anchor['x'];gy+=anchor['y']
 refs=[(p['m_Data']['m_FileID'],p['m_Data']['m_PathID']) for p in tree['m_TileSpriteArray']]
 mats=[]
 for entry in tree['m_TileMatrixArray']:
  t=entry['m_Data'];mats.append(tuple(t[k] for k in ('e00','e01','e10','e11'))+((t['e03']+gx)*16,(t['e13']+gy)*16))
 tint=rgba(tree['m_Color'])
 colors=[]
 for entry in tree['m_TileColorArray']:
  value=entry['m_Data'];factor=255 if isinstance(value,dict) and isinstance(value.get('r'),float) else 1
  colors.append(tuple(round(c*t*factor) for c,t in zip(rgba(value),tint)))
 pix=[]
 for pos,v in tree['m_Tiles']:
  ref=refs[v['m_TileSpriteIndex']]
  if ref not in sprites:continue
  for dx,dy,index in parts(ref,mats[v['m_TileMatrixIndex']],colors[v['m_TileColorIndex']]):
   pix.append((pos['x']+dx,-pos['y']+dy,index))
 if pix:layers[keys[rootid]].append((renderers[gid],pix))
print('Read layers',len(layers),'distinct tile fragments',len(tilepics),flush=True)
rooms=json.loads((W/'detailed.json').read_text('utf8'))
by_key={r['k']:r for r in rooms}
scenic={'map:chapter10/sky10','map:chapter11/peaktemple','map:chapter7/nibarospeakprologue','map:prologue/peakprologue'}
@lru_cache(None)
def basis(tid):
 t=obj(tid);gid=t['m_GameObject']['m_PathID']
 if gid in by_root:return (1.,0.,0.,1.,0.,0.)
 par=t['m_Father']['m_PathID']
 if not par:return (1.,0.,0.,1.,0.,0.)
 a,b,c,d,px,py=basis(par);q=t['m_LocalRotation'];sx=t['m_LocalScale']['x'];sy=t['m_LocalScale']['y'];p=t['m_LocalPosition']
 a1=(1-2*(q['y']**2+q['z']**2))*sx;b1=2*(q['x']*q['y']-q['w']*q['z'])*sy
 c1=2*(q['x']*q['y']+q['w']*q['z'])*sx;d1=(1-2*(q['x']**2+q['z']**2))*sy
 return a*a1+b*c1,a*b1+b*d1,c*a1+d*c1,c*b1+d*d1,px+a*p['x']+b*p['y'],py+c*p['x']+d*p['y']
for o in maps.objects.values():
 if o.type.name!='SpriteRenderer':continue
 d=o.read_typetree();sref=d['m_Sprite'];ref=(sref['m_FileID'],sref['m_PathID'])
 if not d['m_Enabled'] or ref not in sprites:continue
 go=obj(d['m_GameObject']['m_PathID']);tid=go['m_Component'][0]['component']['m_PathID']
 gid,x,y,active=transform(tid);k=keys.get(gid)
 if not active or not k or k.lower().endswith('worldmap') or k not in by_key or 'b' not in by_key[k]:continue
 # The sprite-painted rooms use separate scenery instead of terrain tiles.
 if k.lower() not in scenic or ref[0]!=0 or max(sprites[ref][0].size)<120:continue
 l,t,w,h=by_key[k]['b'];a,b,c,dd,x,y=basis(tid)
 if d.get('m_FlipX'):a,c=-a,-c
 if d.get('m_FlipY'):b,dd=-b,-dd
 ix,iy=math.floor(x),math.floor(y)
 mat=tuple(round(v,6) for v in (a,b,c,dd,(x-ix)*16,(y-iy)*16))
 tint=tuple(round(255*v) for v in rgba(d['m_Color']))
 pix=[(ix+dx,-iy+dy,i) for dx,dy,i in parts(ref,mat,tint) if l<=ix+dx<l+w and t<=-iy+dy<t+h]
 if pix:layers[k].append(((d['m_SortingLayer'],d['m_SortingOrder'],-y),pix))
used=set();grids={}
for room in rooms:
 if room['k'][4:].split('/')[0] in {'bullshots','debugmaps','test','credits','fakechapterselect','decky training'}:continue
 ll=layers.get(room['k'])
 if room['k'].lower().endswith('worldmap'):continue
 if not ll:
  room['i']='';continue
 points=[(x,y) for _,p in ll for x,y,_ in p]+[(p[0],p[1]) for p in room['c']+room['e']]
 l=math.floor(min(x for x,y in points))-1;t=math.floor(min(y for x,y in points))-1
 w=math.ceil(max(x for x,y in points))-l+2;h=math.ceil(max(y for x,y in points))-t+2
 grid=[()]*(w*h)
 for _,p in sorted(ll,key=lambda layer:layer[0]):
  for x,y,i in p:
   k=(y-t)*w+x-l;grid[k]=(i,) if opaque[i] else grid[k]+(i,)
 room['b']=[l,t,w,h];grids[room['k']]=grid;used.update(i for stack in grid for i in stack)
from array import array
assert len(used)<65535
lookup={v:i+1 for i,v in enumerate(sorted(used))}
sheet=Image.new('RGBA',(128*16,math.ceil((len(used)+1)/128)*16))
for v,i in lookup.items():sheet.paste(tilepics[v],(i%128*16,i//128*16))
for r in rooms:
 grid=grids.get(r['k'])
 if not grid:continue
 out=array('H')
 for layer in range(max(map(len,grid))):
  end=0
  for pos,stack in enumerate(grid):
   if len(stack)<=layer:continue
   skip=pos-end
   while skip>=65534:out.extend([65534,0]);skip-=65534
   out.extend([skip,lookup[stack[layer]]]);end=pos+1
  out.append(65535)
 r['i']=base64.b64encode(out.tobytes()).decode()
buf=io.BytesIO();sheet.save(buf,'WEBP',method=6,lossless=True)
(W/'tile-dict-fixed.txt').write_text(base64.b64encode(buf.getvalue()).decode(),'ascii')
(W/'detailed-fixed.json').write_text(json.dumps(rooms,ensure_ascii=False,separators=(',',':')),'utf8')
print('Wrote',len(used),'shared tile fragments',flush=True)
