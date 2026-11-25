const [rewardTypes,tabKeys,iconCell,iconSheet]=itemArt;
const layerNames={loc:'世界地点',exit:'出口',boss:'首领与特殊遭遇',consumables:'消耗品',tome:'宝典',weapon:'武器',helm:'头部装备',armor:'身体装备',accessory:'饰品',keyitem:'关键物品',money:'瓦尔'};
const rewardLayers=[...tabKeys,'money'];
const hiddenLayers=new Set;
try{
 const saved=JSON.parse(localStorage.getItem('quartet.atlas.layers.v1')||'[]');
 if(Array.isArray(saved))for(const id of saved)if(Object.hasOwn(layerNames,id))hiddenLayers.add(id)
}catch{}
document.documentElement.style.setProperty('--item-sheet','url("data:image/webp;base64,'+iconSheet+'")');
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
