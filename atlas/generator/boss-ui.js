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
