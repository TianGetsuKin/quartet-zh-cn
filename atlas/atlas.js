'use strict';
const $=id=>document.getElementById(id),worldNames=['尼古拉','本','亚历珊德拉','科黛莉娅'],elements=['火','风','地','水'],worldTitle=i=>elements[i]+'之世界 · '+worldNames[i];
const make=(tag,cl,txt)=>{let n=document.createElement(tag);if(cl)n.className=cl;if(txt!==undefined)n.textContent=txt;return n};
const btn=(cl,txt,fn)=>{let b=make('button',cl,txt);b.onclick=fn;return b};
(async()=>{
const [rooms,worlds,images,worldRoom,sheetUrl,formations,itemArt]=window.quartetAtlasData;
const mapBytes=Uint8Array.from(atob(window.quartetAtlasTiles),c=>c.charCodeAt(0));
let terrain=$('terrain');
const worldImage=terrain,surface=$('surface'),small=matchMedia('(max-width:780px), (pointer:coarse) and (max-width:960px) and (max-height:520px)'),store='quartet.atlas.v1';
// Legacy file links may carry progress from the browser's per-file storage.
if(location.hash.startsWith('#from-old=')){
 try{
  const [anchor,previous]=JSON.parse(decodeURIComponent(location.hash.slice(10)));
  if(Array.isArray(previous)&&previous.every(id=>typeof id==='string')&&localStorage.getItem(store)===null)
   localStorage.setItem(store,JSON.stringify(previous));
  location.replace(typeof anchor==='string'&&anchor.startsWith('#p=')?anchor:'#');
 }catch{}
}
let marks=new Set,storageOK=true;try{marks=new Set(JSON.parse(localStorage.getItem(store)||'[]'))}catch{storageOK=false}
let w=0,room=-1,z=1,ox=0,oy=0,chosen=null,history=[],pins=[],dots=[],pending=false;
let arrival=null;
let cardSide=null;
let bounds=[0,0,184.5,193],cx=0,cy=0,mul=1,base=1;
const nameOf=i=>rooms[i][1]||rooms[i][0].split('/').pop();
const chapter=i=>{let m=/^chapter(\d+)/.exec(rooms[i][0]);return m?'第 '+m[1]+' 章':''};
const key=(kind,x,y,r,wi)=>kind==='chest'?'ch/'+rooms[r][0]+'/'+x+','+y:'loc/'+wi+'/'+x+','+y;
const cleanPanel=()=>{if(small.matches)$('panel').classList.add('closed');syncToggle()};
function syncToggle(){
 const open=!$('panel').classList.contains('closed');
 $('directory').setAttribute('aria-expanded',String(open));$('sheetShade').hidden=!small.matches||!open
}
function closeDirectory(){cleanPanel();$('directory').focus({preventScroll:true})}
$('panelClose').onclick=$('sheetShade').onclick=closeDirectory;
small.addEventListener('change',()=>{$('panel').classList.toggle('closed',small.matches);syncToggle();schedule()});
$('directory').onclick=()=>{$('panel').classList.toggle('closed');syncToggle();schedule()};cleanPanel();
$('help').onclick=()=>$('guide').showModal();$('dismiss').onclick=()=>$('guide').close();
const worldEmblems=[
 ['fire','M8 0h2v3h2v3h1V5h1v2h1v5h-1v2h-2v1H5v-1H3v-2H2V8h1V6h2v3h1V6h1V4h1z','M8 8h2v2h1v2h-1v2H7v-1H6v-2h1v-1h1z'],
 ['wind','M2 4h7V3h1V2h3v1h1v3h-1v1H3V6H1V4z M0 9h12V8h3v1h1v2h-2v1H4v-1H0z','M6 13h5v1h1v2H9v-1H6z'],
 ['earth','M1 12h1v-2h2V8h2V5h2V2h2v3h2v3h1v2h2v2h1v2H1z','M7 7h1V5h2v2h1v2H9V8H7z M2 15h13v1H2z'],
 ['water','M7 0h2v3h1v2h2v2h1v2h1v4h-1v1h-2v1H5v-1H3v-2H2V9h1V7h2V5h1V3h1z','M4 9h2v3h2v1H5v-1H4z']
];
function worldIcon(i){
 const [,shape,highlight]=worldEmblems[i];
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('class','element-emblem');svg.setAttribute('viewBox','0 0 16 16');svg.setAttribute('aria-hidden','true');
 for(const path of [shape,highlight]){
  const part=document.createElementNS(svg.namespaceURI,'path');part.setAttribute('d',path);svg.append(part)
 }
 return svg
}
for(const [i,[theme]] of worldEmblems.entries()){
 const b=btn('world-'+theme,'',()=>{go(i,-1,true);cleanPanel()});
 const label=make('span','',elements[i]+'之世界');label.append(make('small','',worldNames[i]));
 b.append(worldIcon(i),label);b.title=worldTitle(i);b.setAttribute('aria-label',b.title);$('worldbar').append(b)
}
const owner=Array(rooms.length).fill(-1),adj=rooms.map(()=>new Set),queue=[];
for(let i=0;i<rooms.length;i++)for(let e of rooms[i][4])if(!worldRoom.includes(i)&&!worldRoom.includes(e[2])){adj[i].add(e[2]);adj[e[2]].add(i)}
for(let wi=0;wi<4;wi++)for(let p of worlds[wi])for(let j of p[4])if(owner[j]<0){owner[j]=wi;queue.push(j)}
for(let i=0;i<rooms.length;i++){
 if(owner[i]>=0)continue;
 const direct=[...new Set(rooms[i][4].map(e=>worldRoom.indexOf(e[2])).filter(v=>v>=0))];
 const rootWorld={nikolai:0,ethosarchives:0,ben:1,bathosarchives:1,alex:2,pathosarchives:2,cordelia:3,logosarchives:3}[rooms[i][0].split('/')[0]];
 const known=direct.length===1?direct[0]:rootWorld;
 if(known!==undefined){owner[i]=known;queue.push(i)}
}
for(let n=0;n<queue.length;n++){let i=queue[n];for(let j of adj[i])if(owner[j]<0){owner[j]=owner[i];queue.push(j)}}
const [rewardTypes,tabKeys,iconCell,iconSheet]=itemArt;
const layerNames={loc:'世界地点',exit:'出口',boss:'首领与特殊遭遇',consumables:'消耗品',tome:'宝典',weapon:'武器',helm:'头部装备',armor:'身体装备',accessory:'饰品',keyitem:'关键物品',money:'瓦尔'};
const rewardLayers=[...tabKeys,'money'];
const hiddenLayers=new Set;
try{
 const saved=JSON.parse(localStorage.getItem('quartet.atlas.layers.v1')||'[]');
 if(Array.isArray(saved))for(const id of saved)if(Object.hasOwn(layerNames,id))hiddenLayers.add(id)
}catch{}
document.documentElement.style.setProperty('--item-sheet','url("'+iconSheet+'")');
function sprite(i){
 const node=make('span','item-sprite');
 node.setAttribute('aria-hidden','true');
 node.style.setProperty('--col',-(i%16));node.style.setProperty('--row',-Math.floor(i/16));
 return node
}
function pointIcon(p){
 if(p.sprite>=0)return sprite(p.sprite);
 if(p.layer==='money'){const coin=make('span','coin');coin.setAttribute('aria-hidden','true');return coin}
 return make('span','symbol',glyph(p))
}
const layerChecks=new Map,master=$('allRewards');
function syncLayers(){
 for(const [id,input] of layerChecks)input.checked=!hiddenLayers.has(id);
 const active=rewardLayers.filter(id=>!hiddenLayers.has(id)).length;
 master.indeterminate=active>0&&active<rewardLayers.length;master.checked=active===rewardLayers.length;
 $('layerButton').classList.toggle('filtered',hiddenLayers.size>0)
}
function setLayers(ids,visible){
 for(const id of ids)if(visible)hiddenLayers.delete(id);else hiddenLayers.add(id);
 try{localStorage.setItem('quartet.atlas.layers.v1',JSON.stringify([...hiddenLayers]))}catch{}
 syncLayers();if(chosen&&shown(chosen))detail();refresh()
}
for(const [id,label] of Object.entries(layerNames)){
 const row=make('label','layer-option'),box=make('input');box.type='checkbox';box.dataset.layer=id;
 box.onchange=()=>setLayers([id],box.checked);
 if(id==='exit')box.id='showExit';
 const idx=tabKeys.indexOf(id),icon=idx>=0?sprite(idx):make('span','layer-symbol',({loc:'◆',exit:'↗',boss:'⚔',money:'●'})[id]);
 row.append(box,icon,document.createTextNode(label));
 $(rewardLayers.includes(id)?'rewardLayers':'placeLayers').append(row);layerChecks.set(id,box)
}
master.onchange=()=>setLayers(rewardLayers,master.checked);
syncLayers();
$('layerButton').onclick=()=>$('layerDialog').showModal();
$('closeLayers').onclick=()=>$('layerDialog').close();

const bossName=g=>formations[g][0].map(([n,count])=>n+(count>1?' ×'+count:'')).join('、');
const bossPins=(i)=>rooms[i][6].map(([x,y,groups])=>({x,y,kind:'boss',groups,n:bossName(groups[0])}));
function guideCard(host,groups){
 const choices=[];
 for(const g of groups){
  for(const monster of formations[g][0])choices.push({g,monster});
 }
 const selector=make('select','fighter'),body=make('div','strategy');
 if(choices.length>1){
  selector.setAttribute('aria-label','选择敌人或战斗配置');
  choices.forEach(({g,monster:[n]},i)=>{
   let label=n;
   if(choices.some((c,j)=>j!==i&&c.monster[0]===n))label+=' · 配置 '+(groups.indexOf(g)+1);
   selector.append(new Option(label,String(i)));
  });host.append(selector)
 }
 function render(){
  body.replaceChildren();
  const {g,monster:[n,count,hp,weak,resist,immune,absorb,states,tactic,skills]}=choices[Number(selector.value)||0];
  const line=(title,content)=>{let row=make('div','guide-line');row.append(make('strong','',title),make('span','',content));body.append(row)};
  line('基础 HP',hp.toLocaleString('zh-CN')+(count>1?' / 每只':''));
  if(weak.length)line('弱点',weak.join('、'));
  if(resist.length)line('耐性',resist.join('、'));
  if(immune.length)line('免伤',immune.join('、'));
  if(absorb.length)line('吸收',absorb.join('、'));
  if(states.length)line('异常抗性 ≥100',states.join('、'));
  body.append(make('p','tip',formations[g][1]||tactic));
  if(skills.length){
   const more=make('details','moves');more.append(make('summary','','敌方招式'));
   for(const [name,description] of skills){const row=make('p');row.append(make('strong','',name+'　'),document.createTextNode(description));more.append(row)}
   body.append(more);more.ontoggle=schedule
  }
  body.append(make('small','muted','基础战斗配置；难度、剧情阶段和战斗中的状态会影响实际数值。'));schedule()
 }
 selector.onchange=render;host.append(body);render()
}
const bossIndex=$('bossIndex'),bossResults=$('bossResults'),bossQuery=$('bossQuery');
const storyRooms=new Map;
rooms.forEach((r,i)=>{for(const g of r[7]){if(!storyRooms.has(g))storyRooms.set(g,[]);storyRooms.get(g).push(i)}});
const locations=new Map(Object.keys(formations).map(g=>[g,[]]));
rooms.forEach((r,i)=>{for(const p of bossPins(i))for(const g of p.groups)locations.get(g).push([i,p])});
const totalHP=g=>formations[g][0].reduce((sum,[,n,hp])=>sum+n*hp,0);
const ranked=[...locations.keys()].sort((a,b)=>formations[a][2]-formations[b][2]||totalHP(a)-totalHP(b)||bossName(a).localeCompare(bossName(b),'zh-CN')||a.localeCompare(b));
let guideScope=null;
function areaGuides(body,roomsHere){
 const box=make('details','area-guides'),scope=new Set;
 for(const i of roomsHere)for(const g of [...rooms[i][7],...rooms[i][6].flatMap(row=>row[2])])scope.add(g);
 box.append(make('summary','','⚔ 相关首领与遭遇 · '+scope.size));
 for(const g of ranked)if(scope.has(g))box.append(btn('btn','Lv.'+formations[g][2]+'　'+bossName(g),()=>openGuide('',[g])));
 body.append(box)
}
$('sceneGuide').onclick=()=>openGuide('',rooms[room][7]);
function openGuide(query='',scope=null){guideScope=scope?new Set(scope):null;bossQuery.value=query;showIndex();bossIndex.showModal()}
function showIndex(){
 bossResults.replaceChildren();
 const q=bossQuery.value.trim().toLowerCase();
 let matches=0;
 for(const g of ranked){
  if(guideScope&&!guideScope.has(g))continue;
  const places=locations.get(g);
  const title=bossName(g),scenes=storyRooms.get(g)||[],names=[...new Set([...places.map(([i])=>nameOf(i)),...scenes.map(nameOf)])];
  if(![title,...names].join(' ').toLowerCase().includes(q))continue;
  const entry=make('details','boss-entry'),summary=make('summary','',title);
  summary.prepend(make('span','boss-level','Lv.'+formations[g][2]+'　'));summary.append(make('small','',formations[g][3]+' · 合计 '+totalHP(g).toLocaleString('zh-CN')+' HP · '+(names.join(' / ')||'剧情战斗')));entry.append(summary);
  entry.ontoggle=()=>{
   if(!entry.open||entry.children.length>1)return;
   const content=make('div','boss-content');entry.append(content);guideCard(content,[g]);
   for(const i of scenes)content.append(btn('btn','前往剧情场景 · '+nameOf(i),()=>{bossIndex.close();if(hiddenLayers.has('boss'))setLayers(['boss'],true);go(owner[i]>=0?owner[i]:w,i,true);cleanPanel()}));
   for(const [i,p] of places)content.append(btn('btn','定位 · '+nameOf(i),()=>{
    bossIndex.close();if(hiddenLayers.has('boss'))setLayers(['boss'],true);go(owner[i]>=0?owner[i]:w,i,true);select(dots.find(d=>d.kind==='boss'&&d.x===p.x&&d.y===p.y))
   }))
  };bossResults.append(entry);matches++
 }
 if(!matches)bossResults.append(make('p','muted','没有匹配的首领或地点。'))
}
$('openBoss').onclick=()=>openGuide();
$('closeBoss').onclick=()=>bossIndex.close();bossQuery.oninput=showIndex;

const chestAliases=new Map,choices=new Map;
rooms.forEach((r,i)=>r[5].forEach(([x,y,n,group])=>{
 const id=key('chest',x,y,i,0);
 if(group?.startsWith('shared/'))chestAliases.set(id,group);
 if(group?.startsWith('choice/')){if(!choices.has(group))choices.set(group,[]);choices.get(group).push(id)}
}));
for(const [old,group] of chestAliases)if(marks.has(old)){marks.delete(old);marks.add(group)}
function chestAt(wi,r,[x,y,n,group,reward]){const [layer,sprite]=rewardTypes[reward];const old=key('chest',x,y,r,wi);return {x,y,n,group,layer,sprite,kind:'chest',id:chestAliases.get(old)||old}}
function storyItems(r){return rooms[r][8].map(([x,y,n,reward,tech])=>({x,y,n,kind:'event',layer:'keyitem',sprite:rewardTypes[reward][1],id:'event/'+rooms[r][0]+'/'+x+','+y+'/'+tech}))}
function excluded(p){return p.group?.startsWith('choice/')&&!marks.has(p.id)&&choices.get(p.group).some(id=>marks.has(id))}
function allDots(wi,r){
 if(r<0)return worlds[wi].map(([x,y,n,en,targets,bossRooms])=>({x,y,n,en,targets,bossRooms,kind:'loc',id:key('loc',x,y,r,wi)}));
 return rooms[r][5].map(row=>chestAt(wi,r,row)).concat(storyItems(r),bossPins(r)).concat(rooms[r][4].map(([x,y,dest,landing])=>({x,y,landing,n:worldRoom.includes(dest)?worldTitle(worldRoom.indexOf(dest)):nameOf(dest),dest,kind:'exit'})))
}
const glyph=p=>excluded(p)?'—':marks.has(p.id)?'✓':({loc:'◆',chest:'▣',boss:'⚔',exit:'↗',landing:'◎',room:'▤'})[p.kind];
function areaBoss(p){return p.bossRooms?.length&&!hiddenLayers.has('boss')}
function shown(p){
 if(hiddenLayers.has(p.layer||p.kind)&&!areaBoss(p))return false;
 return p===arrival||!($('hide').checked&&(marks.has(p.id)||excluded(p)))
}
function snapshot(){return {w,room,z,ox,oy,chosen,arrival}}
const tileSheet=new Image();
tileSheet.src=sheetUrl;
await tileSheet.decode();
const roomCache=new Map;
function roomArt(r){
 if(roomCache.has(r))return roomCache.get(r);
 const [,,b,encoded]=rooms[r],can=document.createElement('canvas');
 const cell=tileSheet.naturalWidth/128,cols=b[2];can.width=cols*cell;can.height=b[3]*cell;
 const c=can.getContext('2d');c.fillStyle='#16272c';c.fillRect(0,0,can.width,can.height);
 let off=encoded[0];
 function read(){let v=0,k=0;for(;;){let b=mapBytes[off++];v|=(b&127)<<k;if(b<128)return v;k+=7}}
 const dict=Array.from({length:read()},read),lengths=Array.from({length:read()},read);
 const gaps=Uint32Array.from({length:lengths.reduce((a,b)=>a+b,0)},read);let j=0;
 for(const length of lengths){let pos=0;for(let i=0;i<length;i++){
  pos+=gaps[j++];const id=dict[read()];if(id){c.drawImage(tileSheet,(id%128)*cell,Math.floor(id/128)*cell,cell,cell,(pos%cols)*cell,Math.floor(pos/cols)*cell,cell,cell);pos++}
 }}
 roomCache.set(r,can);if(roomCache.size>3)roomCache.delete(roomCache.keys().next().value);return can
}
function go(wi,r,remember=false){
 if(worldRoom.includes(r)){wi=worldRoom.indexOf(r);r=-1}
 if(remember && (r!==room||wi!==w)){history.push(snapshot());if(history.length>80)history.shift()}
 w=wi;room=r;chosen=null;arrival=null;cardSide=null;z=1;ox=oy=0;$('search').value='';
 const isWorld=r<0;
 // On a tall phone start closer to the mainland. Fit always restores the full extent.
 if(isWorld&&small.matches&&surface.clientHeight>surface.clientWidth*1.45){
  z=Math.min(1.35,surface.clientHeight/surface.clientWidth/1.3)
 }
 bounds=isWorld?[0,0,[2952,2952,2944,2956][w]/16,[3088,3080,3088,3094][w]/16]:rooms[r][2];
 const nextTerrain=isWorld?worldImage:roomArt(r);
 if(isWorld&&worldImage.dataset.world!==String(w)){worldImage.src=images[w];worldImage.dataset.world=w}
 if(nextTerrain!==terrain){terrain.removeAttribute('id');nextTerrain.id='terrain';terrain.replaceWith(nextTerrain);terrain=nextTerrain}terrain.classList.toggle('indoor',!isWorld);
 terrain.alt=isWorld?worldTitle(w)+'地形图':nameOf(r)+'瓦片简图';const heading=$('mapname');
 heading.className=isWorld?'mapname world-heading world-'+worldEmblems[w][0]:'mapname';
 heading.textContent=isWorld?worldTitle(w):nameOf(r);
 if(isWorld)heading.prepend(worldIcon(w));
 [...$('worldbar').children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===w)));
 $('back').hidden=!history.length;$('panelTitle').textContent=isWorld?'地点目录':'场景点位';$('legendText').textContent=isWorld?'◆ 世界地点　⚔ 首领区域':'物品　⚔ 首领　↗ 出口';
 dots=allDots(w,r);$('detail').hidden=true;refresh()
}
$('back').onclick=()=>{let s=history.pop();if(!s)return;
 go(s.w,s.room);
 if(s.room<0){
  if(s.arrival){arrival=dots.find(p=>p.id&&p.id===s.arrival.id);if(!arrival&&s.arrival.kind==='landing'){arrival=s.arrival;dots.push(arrival)}}

 }
 z=s.z;ox=s.ox;oy=s.oy;if(s.chosen){chosen=dots.find(p=>p.x===s.chosen.x&&p.y===s.chosen.y&&p.kind===s.chosen.kind&&p.n===s.chosen.n)||null;if(chosen)detail()}refresh()};
let touchTarget=null,lastTap=null;
surface.addEventListener('pointerdown',e=>{
 touchTarget=null;
 if(e.pointerType!=='touch'||!e.target.closest('.pin')||e.target.closest('.caption'))return;
 // A phone can expand or retarget a tap onto the neighbouring button in a cluster.
 // Resolve a tap on a marker by the original contact; captions retain their named target.
 let nearest=11;
 for(const [point,b] of pins){const r=b.getBoundingClientRect(),d=Math.hypot(e.clientX-r.x-r.width/2,e.clientY-r.y-r.height/2);
  if(d<nearest){nearest=d;touchTarget=point}}
},true);
function refresh(){
 if(chosen&&!shown(chosen)){chosen=null;$('detail').hidden=true}
 let visibles=dots.filter(shown);pins=[];$('pins').replaceChildren();
 for(let p of visibles){
  let b=btn('pin '+p.kind+(p===arrival?' arrival':'')+(marks.has(p.id)?' done':'')+(p===chosen?' pick':''),'',e=>{
   if(e.pointerType==='touch'&&draggedTouch)return;
   const tapped=e.pointerType==='touch'?touchTarget||p:p;
   select(tapped,false,e);
   if(e.pointerType==='touch'){
    const now=performance.now();if(lastTap?.point===tapped&&now-lastTap.at<440){lastTap=null;enter(tapped)}else lastTap={point:tapped,at:now};
    touchTarget=null
   }
  });b.ondblclick=e=>{e.preventDefault();enter(p)};
  b.title=p.n;b.setAttribute('aria-label',p.n);let icon=make('i');const art=pointIcon(p);
  if(p.kind==='chest'||p.kind==='event'){b.classList.add('reward-pin');icon.append(art)}else icon.append(make('b','',glyph(p)));
  if(areaBoss(p)){b.classList.add('boss-area');b.append(make('span','boss-badge','⚔'));b.setAttribute('aria-label',p.n+' · 有首领')}
  if((p.kind==='chest'||p.kind==='event')&&(marks.has(p.id)||excluded(p)))b.append(make('span','mark-badge',glyph(p)));
  let label=make('span','caption',p.n);b.append(icon,label);$('pins').append(b);pins.push([p,b,label])
 }
 const sceneGuide=$('sceneGuide');sceneGuide.hidden=room<0||!rooms[room][7].length||hiddenLayers.has('boss');
 let track=dots.filter(p=>p.id),total=new Set(track.map(p=>p.group||p.id)).size;$('progress').textContent=(room<0?'已探索地点 ':'已标记物品 ')+track.filter(p=>marks.has(p.id)).length+' / '+total+(storageOK?'　·　本机记录':'　·　仅本次有效');
 list();draw()
}
function destinations(p){return p.kind==='exit'?[p.dest]:[...(p.targets||[])].sort((a,b)=>phase(a)-phase(b))}
function phase(i){return Number(/^chapter(\d+)/.exec(rooms[i][0])?.[1]||0)}
function focusArrival(info,source){
 arrival=Number.isInteger(info)?dots[info]:null;
 if(Array.isArray(info)){
  arrival={x:info[0],y:info[1],kind:'landing',n:source+' · 返回点'};dots.push(arrival)
 }
 if(!arrival)return;
 z=1.85;metrics();ox=(bounds[0]+bounds[2]/2-arrival.x)*mul;oy=(bounds[1]+bounds[3]/2-arrival.y)*mul;refresh()
}
function travel(p,j){
 chosen=p;
 const leaving=room>=0&&p.kind==='exit'&&worldRoom.includes(j),source=leaving?nameOf(room):'';
 go(w,j,true);if(leaving)focusArrival(p.landing,source)
}
function enter(p){if(!dots.includes(p))return;const [j]=destinations(p);if(j!==undefined)travel(p,j)}
function select(p,focus=true,event){chosen=p;cardSide=null;
 if(event?.target.closest('.caption')){let box=event.currentTarget.getBoundingClientRect();cardSide=event.clientY<box.top+box.height/2?'below':'above'}if(focus){z=Math.max(z,1.65);metrics();ox=(bounds[2]/2+bounds[0]-p.x)*mul;oy=(bounds[3]/2+bounds[1]-p.y)*mul}cleanPanel();detail();
 for(let [q,b] of pins)b.classList.toggle('pick',p===q);
 for(let row of $('list').children)row.classList.toggle('sel',row.point===p);
 draw()}
function detail(){
 let p=chosen,d=$('detail');if(!p){d.hidden=true;return}d.replaceChildren();d.hidden=false;
 const body=make('div','cardbody'),close=btn('x','×',()=>{chosen=null;d.hidden=true;refresh()});close.setAttribute('aria-label','关闭卡片');d.append(body,close);
 const kind={loc:'世界地点',chest:layerNames[p.layer]+' · 宝箱',event:'关键物品 · 剧情触发点',exit:'场景出口',landing:'世界返回点',boss:'首领战 · 触发位置'}[p.kind];
 body.append(make('div','where',kind+' · '+Math.floor(p.x)+', '+Math.floor(p.y)),make('h3','',p.n));
 const dest=destinations(p);
 const context=p.kind==='event'?'从此处触发剧情，随剧情进展获得。':p.kind==='boss'?nameOf(room):p.kind==='landing'?'刚离开场景时在世界地图上的位置。':p.kind==='chest'?nameOf(room):p.kind==='exit'?'双击前往此场景':dest.length>1?'双击进入'+(chapter(dest[0])||'初次到访的场景')+'，也可选择章节。':dest.length?'双击进入地点':'地形标记';
 if(!small.matches||!dest.length||p.kind==='boss'||p.kind==='chest')body.append(make('div','small',context));
 else if(dest.length>1)body.append(make('div','small','选择要进入的章节。'));
 if(p.sprite!==undefined)body.querySelector('h3').prepend(pointIcon(p));
 if(p.kind==='boss')guideCard(body,p.groups);
 if(areaBoss(p))areaGuides(body,p.bossRooms);
 if(p.group?.startsWith('shared/'))body.append(make('div','small','此宝箱与其他场景版本共用领取记录。'));
 if(p.group?.startsWith('choice/'))body.append(make('div','small',excluded(p)?'已选择另一只宝箱。':'二选一奖励，领取后另一只会消失。'));
 if(p.en&&p.en!==p.n)body.append(make('div','small',p.en));
 const a=make('div','actions');body.append(a);
 if(p.id)a.append(btn('',marks.has(p.id)?'✓ 取消标记':p.kind==='chest'?(excluded(p)?'改选这只宝箱':'标记为已领取'):p.kind==='event'?'标记为已获得':'标记为已探索',()=>{if(marks.has(p.id))marks.delete(p.id);else{if(p.group?.startsWith('choice/'))for(const id of choices.get(p.group))marks.delete(id);marks.add(p.id)}try{localStorage.setItem(store,JSON.stringify([...marks]))}catch{storageOK=false}
 if(!shown(p)){chosen=null;d.hidden=true}else detail();refresh()}));
 for(let j of dest)a.append(btn('primary',dest.length===1?'进入地点 →':(chapter(j)||nameOf(j))+' →',()=>travel(p,j)));
 const copy=btn('','复制点位链接',async()=>{
  const url=new URL(location.href);url.hash='p='+encodeURIComponent(JSON.stringify([w,room<0?'':rooms[room][0],p.kind,p.x,p.y,p.n]));
  try{await navigator.clipboard.writeText(url.href);copy.textContent='链接已复制'}catch{
   let input=body.querySelector('input');if(!input){input=make('input','search');input.readOnly=true;input.setAttribute('aria-label','点位链接');body.append(input)}
   input.value=url.href;input.select();copy.textContent='选中链接后复制';schedule()
  }
 });a.append(copy);
}
function list(){
 const q=$('search').value.trim().toLowerCase(),host=$('list');host.replaceChildren();let count=0;
 const add=(p,sub,fn)=>{count++;if(count>150)return;let b=btn('row'+(!q&&p===chosen?' sel':''),'',fn),t=make('span','text',p.n);if(sub)t.append(make('small','',sub));b.point=p;if(!q)b.ondblclick=()=>enter(p);const ic=make('span','ic '+p.kind+(marks.has(p.id)?' done':''));ic.append(pointIcon(p));b.append(ic,t,make('span','go','›'));host.append(b)};
 if(!q){for(let p of dots.filter(shown))add(p,p===arrival?'刚离开的地点':'',()=>select(p));if(room>=0&&!hiddenLayers.has('boss'))for(const g of rooms[room][7])add({kind:'boss',n:bossName(g)},'剧情战斗 · 查看攻略',()=>openGuide(bossName(g)))}
 else{
  for(let wi=0;wi<4;wi++)for(let p of allDots(wi,-1))if((p.n+' '+p.en).toLowerCase().includes(q)&&shown(p))add(p,worldTitle(wi),()=>{go(wi,-1,true);select(dots.find(t=>t.id===p.id))});
  for(let i=0;i<rooms.length;i++){if(worldRoom.includes(i))continue;let n=nameOf(i);
   let wi=owner[i]>=0?owner[i]:w,context=[chapter(i),n].filter(Boolean).join(' · ');
   if((n+' '+rooms[i][0]).toLowerCase().includes(q))add({n,kind:'room'},chapter(i)||'场景',()=>{go(wi,i,true);cleanPanel()});
   for(const p of bossPins(i))if(shown(p)&&(p.n+' 首领 boss').toLowerCase().includes(q))add(p,context,()=>{go(wi,i,true);select(dots.find(t=>t.kind==='boss'&&t.x===p.x&&t.y===p.y))});
   for(const p of storyItems(i))if(shown(p)&&p.n.includes(q))add(p,context,()=>{go(wi,i,true);select(dots.find(t=>t.id===p.id))});
   for(const row of rooms[i][5]){let p=chestAt(wi,i,row);if(p.n.toLowerCase().includes(q)&&shown(p))add(p,context,()=>{go(wi,i,true);select(dots.find(t=>t.id===p.id))})}
  }
 }
 $('count').textContent=count+(q?' 项结果':' 处');if(!count)host.append(make('div','none',q?'没有匹配的地点、宝箱或首领。':'当前筛选下没有点位。'));if(count>150)host.append(make('div','none','已列出前 150 项，可输入更具体的名称。'));
}
function metrics(){const sw=surface.clientWidth,sh=surface.clientHeight;cx=sw/2;cy=small.matches?sh/2:(sh+38)/2;base=Math.max(.05,Math.min((sw-(small.matches?14:32))/bounds[2],(sh-(small.matches?48:112))/bounds[3]));mul=base*z}
function placeCard(x,y){
 const d=$('detail'),sw=surface.clientWidth,sh=surface.clientHeight,pad=8;
 if(!chosen||(!small.matches&&(x<0||x>sw||y<0||y>sh))){d.hidden=true;return}
 d.hidden=false;
 if(small.matches){d.style.removeProperty('left');d.style.removeProperty('top');return}
 const above=y-20-pad,below=sh-y-20-pad;
 d.style.setProperty('--card-height',Math.max(52,Math.min(320,Math.max(above,below)-2))+'px');
 const wid=d.offsetWidth,h=d.offsetHeight,up=cardSide==='below'&&below>=h?false:cardSide==='above'&&above>=h?true:above>=h||above>=below;
 const left=Math.max(pad,Math.min(sw-pad-wid,x-wid/2));
 d.classList.toggle('above',up);d.classList.toggle('below',!up);
 d.style.left=left+'px';d.style.top=(up?y-20-h:y+20)+'px';d.style.setProperty('--tip',Math.max(14,Math.min(wid-14,x-left))+'px')
}
function draw(){pending=false;metrics();let width=bounds[2]*mul,height=bounds[3]*mul;ox=Math.max(-width/2,Math.min(width/2,ox));oy=Math.max(-height/2,Math.min(height/2,oy));let l=cx+ox-width/2,t=cy+oy-height/2;
 Object.assign(terrain.style,{width:width+'px',height:height+'px',left:l+'px',top:t+'px'});$('scale').textContent=Math.round(z*100)+'%';
 const half=pins.length?pins[0][1].offsetWidth/2:0;
 const stacked=new Set(pins.filter(([p])=>p.kind==='boss').map(([p])=>p.x+','+p.y));
 const shift=p=>p.kind==='event'&&stacked.has(p.x+','+p.y)?-22:0;
 let boxes=[];let items=pins.map(v=>[...v,shift(v[0])+l+(v[0].x-bounds[0])*mul,t+(v[0].y-bounds[1])*mul]);
 for(let [p,b,label,x,y] of items){b.style.left=x+'px';b.style.top=y+'px';label.hidden=true}
 if(chosen)placeCard(shift(chosen)+l+(chosen.x-bounds[0])*mul,t+(chosen.y-bounds[1])*mul);
 if(!$('labels').checked&&!arrival)return;
 for(let [p,b,label,x,y] of (arrival?[...items].sort((a,b)=>Number(b[0]===arrival)-Number(a[0]===arrival)):items)){
  if((!$('labels').checked&&p!==arrival)||x<0||y<40||x>surface.clientWidth||y>surface.clientHeight-30)continue;
  let ww=p.n.length*12+11;
  for(let [dx,dy] of [[12,-8],[-ww-12,-8],[5,-28],[-ww-4,11]]){
   let box=[x+dx,y+dy,x+dx+ww,y+dy+18];
   if(box[0]<1||box[2]>surface.clientWidth-1||box[1]<48||box[3]>surface.clientHeight-30)continue;
   if(boxes.some(o=>o[0]<box[2]+3&&o[2]+3>box[0]&&o[1]<box[3]+2&&o[3]+2>box[1])||items.some(v=>v[0]!==p&&v[3]>box[0]-6&&v[3]<box[2]+6&&v[4]>box[1]-6&&v[4]<box[3]+6))continue;
   label.hidden=false;label.style.left=(dx+half)+'px';label.style.top=(dy+half)+'px';boxes.push(box);break
  }
 }
}
function schedule(){if(!pending){pending=true;requestAnimationFrame(draw)}}
function zoom(f,x=cx,y=cy){let next=Math.max(.65,Math.min(12,z*f)),ratio=next/z;ox=(ox+cx-x)*ratio+x-cx;oy=(oy+cy-y)*ratio+y-cy;z=next;schedule()}
$('plus').onclick=()=>zoom(1.4);$('minus').onclick=()=>zoom(1/1.4);$('fit').onclick=()=>{ox=oy=0;z=1;schedule()};
$('search').oninput=list;for(let k of ['labels','hide'])$(k).onchange=refresh;
surface.onwheel=e=>{e.preventDefault();let r=surface.getBoundingClientRect();zoom(Math.exp(-Math.max(-140,Math.min(140,e.deltaY))*.0028),e.clientX-r.left,e.clientY-r.top)};
let fingers=new Map,gesture=null,firstTouch=null,draggedTouch=false;
const gestureData=()=>{let a=[...fingers.values()],b=a[1]||a[0];return {x:(a[0].x+b.x)/2,y:(a[0].y+b.y)/2,d:Math.hypot(a[0].x-b.x,a[0].y-b.y)}};
surface.onpointerdown=e=>{if(e.button!==0)return;const pin=e.target.closest('.pin');
 if(pin&&e.pointerType!=='touch')return;
 if(e.pointerType==='touch'){
  if(!fingers.size){draggedTouch=false;firstTouch=[e.clientX,e.clientY]}else draggedTouch=true
 }
 (pin||surface).setPointerCapture(e.pointerId);fingers.set(e.pointerId,{x:e.clientX,y:e.clientY});gesture=gestureData()};
surface.onpointermove=e=>{if(!fingers.has(e.pointerId))return;if(e.pointerType==='touch'&&firstTouch&&Math.hypot(e.clientX-firstTouch[0],e.clientY-firstTouch[1])>7){draggedTouch=true;lastTap=null}fingers.set(e.pointerId,{x:e.clientX,y:e.clientY});let g=gestureData(),r=surface.getBoundingClientRect();if(gesture.d&&g.d)zoom(g.d/gesture.d,gesture.x-r.left,gesture.y-r.top);ox+=g.x-gesture.x;oy+=g.y-gesture.y;gesture=g;schedule()};
surface.onpointerup=surface.onpointercancel=e=>{fingers.delete(e.pointerId);gesture=fingers.size?gestureData():null};
document.onkeydown=e=>{if(e.target.matches('input,textarea,select')||$('guide').open||$('bossIndex').open)return;
 if(e.key==='Escape'){if(small.matches&&!$('panel').classList.contains('closed')){closeDirectory();return}if(chosen){chosen=null;$('detail').hidden=true;refresh()}else if(history.length)$('back').click();return}
 if(e.key==='+'||e.key==='=')zoom(1.35);else if(e.key==='-')zoom(1/1.35);else if(e.key.startsWith('Arrow')){e.preventDefault();ox+=(e.key==='ArrowLeft'?45:e.key==='ArrowRight'?-45:0);oy+=(e.key==='ArrowUp'?45:e.key==='ArrowDown'?-45:0);schedule()}
};
function followLink(){
 if(!location.hash.startsWith('#p='))return;
 try{const [wi,k,kind,x,y,n]=JSON.parse(decodeURIComponent(location.hash.slice(3)));
  if(!Number.isInteger(wi)||wi<0||wi>3)return;
  const r=k?rooms.findIndex(row=>row[0]===k):-1;if(k&&r<0)return;
  go(wi,r,true);
  if(r<0&&kind==='landing'){
   const matched=rooms.find(v=>v[1]+' · 返回点'===n&&v[4].some(e=>e[2]===worldRoom[wi]&&Array.isArray(e[3])&&e[3][0]===x&&e[3][1]===y));
   if(matched)focusArrival([x,y],matched[1])
  }
  const p=dots.find(q=>q.kind===kind&&q.x===x&&q.y===y&&q.n===n);if(p){if(hiddenLayers.has(p.layer||p.kind))setLayers([p.layer||p.kind],true);select(p)}
 }catch{}
}
let startTap=null;
surface.addEventListener('pointerdown',e=>{startTap=(!e.target.closest('.pin')&&e.isPrimary&&fingers.size===1)?[e.clientX,e.clientY]:null});
surface.addEventListener('pointerup',e=>{if(startTap&&chosen&&Math.hypot(e.clientX-startTap[0],e.clientY-startTap[1])<4){chosen=null;$('detail').hidden=true;refresh()}startTap=null});
new ResizeObserver(schedule).observe(surface);go(0,-1);followLink();addEventListener('hashchange',followLink)
})().catch(err=>{$('progress').textContent='地图读取失败，请使用较新版本的 Edge、Chrome、Firefox 或 Safari。';console.error(err)});
