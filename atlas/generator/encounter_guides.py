"""Build map overlays from the map components, Yarn StartBattle calls, and Articy records."""
from pathlib import Path
from collections import defaultdict,Counter
import json
W=Path(__file__).resolve().parent
def load(path): return json.loads(path.read_bytes())
def build(rooms):
    root=W.parents[1]
    events=load(W/'event-sources.json')
    custom=load(W/'atlas-custom.json')
    nodes=load(W/'atlas-nodes.json')
    text={(v['technicalName'],v['path'][-1]):v['zh'] for v in load(root/'translations/resource-display.zh.json')}
    groups={}; monsters={}; refs={}
    for f in (root/'extracted/resources.assets').glob('*.json'):
        d=load(f)
        t=d.get('mTemplate',{}).get('value',{})
        if 'id' not in d:continue
        name=d.get('technicalName','')
        refs[d['id']]=name
        if 'mBattles' in t:groups[name.lower()]=(d.get('mDisplayName',''),t['mBattles']['value'])
        if 'mattackType' in t:monsters[d['id']]=(name,t['mattackType']['value'])
    attack={'earth':'地','fire':'火','water':'水','wind':'风','quintessence':'精粹','slash':'斩击','pierce':'穿刺','blunt':'打击'}
    states={'poison':'中毒','bleed':'流血','burn':'灼伤','blind':'失明','freeze':'冻结','silence':'沉默','sleep':'睡眠','stun':'眩晕','delay':'延迟'}
    formations={}; points=defaultdict(lambda:defaultdict(list)); catalog=set()
    def isboss(g):
        return g in groups and ('boss' in (g+' '+groups[g][0]).lower())
    # Named, optional encounters and story bosses without an explicit boss music argument.
    special_nodes = {'corsinBattle','keraunosBoss','kraptain_battle','dinosaur_whichBattle',
                     'duckDog_pass','duckDog_grasslands','duckDog_swamp','duckDog_dustwind'}
    random_nodes = {'kraptain_MaybeRandomEncounter':'kraptain_battle',
                    'dinosaur_MaybeRandomEncounter':'dinosaur_whichBattle'}
    random_groups=set()
    scene_battles=defaultdict(set)
    actions=defaultdict(list)
    for node,v in nodes.items():
        if any(s in node.lower() for s in ('demo','debug','test','reviewscenes')):continue
        for op,s in v:
            parts=s.lower().split()
            if op==3 and len(parts)>1 and parts[0]=='startbattle' and parts[1] in groups:
                g=parts[1]
                if g=='demoboss':continue
                if isboss(g) or node in special_nodes or any('boss' in a for a in parts[2:]):
                    actions[node].append(g);catalog.add(g)
    for k,x,y,g in events['encounters']:
        g=g.lower()
        if k in rooms and isboss(g):
            points[k][x,y].append(g);catalog.add(g)
    for k,x,y,node in events['triggers']:
        if k not in rooms:continue
        points_here=actions.get(node,[])
        if node in ('meetBrothersPal','meetBrothersSkil') and [6,'sparBrothers'] in nodes[node]:
            points_here=actions['sparBrothers']
        if points_here:points[k][x,y].extend(points_here)
        target=random_nodes.get(node)
        if target and [6,target] in nodes[node]:
            scene_battles[k].update(actions[target])
            random_groups.update(actions[target])
    # These battles start after a scripted change of scene and have no fixed field opponent.
    for node,v in nodes.items():
        if node not in actions or not node.endswith('Henge'):continue
        location=None
        for op,s in v:
            bits=s.lower().split()
            if op==3 and len(bits)>=2:
                if bits[0]=='levelchange':location=bits[1]
                if bits[0]=='startbattle' and location in rooms and bits[1] in actions[node]:
                    scene_battles[location].add(bits[1])
    # Only verified encounter triggers get coordinates. Script-only encounters stay in the index.
    tips={'battle_grasslandsboss':'两只蘑菇都弱火。用群体火系招式可以同时打中两只；留一人准备解毒，孢子炸弹会让全员中毒。',
          'battle_warehouseboss':'流氓、执行者和打手都弱风。有群体风系招式时可同时打三人；只能打单体时，优先对执行者或打手用风。',
          'battle_dreyfuss':'水系和斩击都能打中德雷福斯的弱点。队员没有水系法术时，可以改用斩击；火系会被他抵挡。'}
    for g in sorted(catalog):
        _,b=groups[g]; party=Counter(b['menemy'+str(i)]['objectRef'] for i in range(1,int(b['menemies'])+1))
        enemies=[]
        for mid,count in party.items():
            if not mid:continue
            tech,m=monsters[mid]
            n=text.get((tech,'mmonsterName'),m['mmonsterName'])
            resist=sorted(((m['m'+k+'Resist'],name) for k,name in attack.items()))
            weak=[name for v,name in resist if v< -25]; guard=[name for v,name in resist if 35<=v<100]
            immune=[name for v,name in resist if v==100]; absorb=[name for v,name in resist if v>100]
            st=[name for k,name in states.items() if m.get('m'+k+'Resist',0)>=100]
            skills=[]
            for i in range(1,13):
                sid=m.get('msignature'+str(i),{}).get('objectRef',0);skill=refs.get(sid)
                label=text.get((skill,'mabilityName'));desc=text.get((skill,'mflavorText'))
                if label and desc and '<' not in desc and (label,desc) not in skills:skills.append((label,desc))
            low=[name for v,name in resist if v==resist[0][0] and v<0]
            if low: tactic='优先用'+'、'.join(low)+'攻击。'
            elif m['mdefense']!=m['mmagicDefense']:
                tactic='没有明显的属性弱点。'+('魔防较低，可先试法术。' if m['mmagicDefense']<m['mdefense'] else '物防较低，可先试物理招式。')
            else:tactic='没有明显的属性弱点。优先用队伍擅长、对方能正常承受的招式。'
            enemies.append([n,count,int(m['mhp']),weak,guard,immune,absorb,st,tactic,skills[:4]])
        if enemies:
            level=max(int(monsters[mid][1]['mlevel']) for mid in party if mid)
            formations[g]=[enemies,tips.get(g,''),level,'区域遭遇' if g in random_groups else '首领战']
    pins={k:[[x,y,list(dict.fromkeys(gs))] for (x,y),gs in ps.items()] for k,ps in points.items()}
    rewards=defaultdict(list);aliases={};bykey=defaultdict(list)
    for k,x,y,name,p in custom['rewards']:
        if k not in rooms:continue
        item=p.get('treasureID') or '';val=int(p.get('valAmount') or 0)
        if not item and not val:continue
        label=text.get((item,'mitemName')) if item else str(val)+' 瓦尔'
        if not label:continue
        node=p.get('nodeId');exclusive=node in ('javelinChestOpen1','javelinChestOpen2')
        if node not in ('Chest_Open','javelinChestOpenMain') and not exclusive:continue
        if [x,y,label] not in rooms[k]['c']:rewards[k].append([x,y,label])
        if exclusive:aliases[k,x,y]='choice/javelin'
        else:
            # Treasure.GetYarnParameters calls LevelService.GetLevelIDForState, which reads delegateLevelID.
            level=custom['maps'].get(k,{}).get('delegateLevelID') or k
            bykey[level.lower(),name].append((k,x,y,label))
    for (level,name),rs in bykey.items():
        if len({k for k,x,y,n in rs})<2:continue
        assert len({n for k,x,y,n in rs})==1
        for k,x,y,_ in rs:aliases[k,x,y]='shared/'+level+'/'+name
    print('Boss formations / marker locations / shared chest keys:',len(formations),sum(map(len,pins.values())),len(set(aliases.values())))
    return formations,pins,rewards,aliases,{k:sorted(gs) for k,gs in scene_battles.items()}

