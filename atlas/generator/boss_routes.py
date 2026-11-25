from collections import defaultdict, deque

def attach_boss_routes(records, worlds, world_rooms):
    """Index encounters under the closest reachable world entrances by room transitions."""
    entrances = {(wi,pi):point[4] for wi,world in enumerate(worlds) for pi,point in enumerate(world)}
    gates = set(world_rooms).union(*(set(ids) for ids in entrances.values()))
    targets = {i for i,r in enumerate(records) if r[6] or r[7]}
    nearest = defaultdict(list)
    for gate, starts in entrances.items():
        dist = dict.fromkeys(starts,0)
        queue = deque(starts)
        while queue:
            room = queue.popleft()
            if room in targets: nearest[room].append((dist[room], gate))
            for _,_,dest,*_ in records[room][4]:
                if dest not in gates and dest not in dist:
                    dist[dest] = dist[room]+1
                    queue.append(dest)
    areas = defaultdict(list)
    for room,paths in nearest.items():
        shortest = min(d for d,_ in paths)
        for d,gate in paths:
            if d==shortest: areas[gate].append(room)
    # Scripted scene changes can bypass an exit. Associate a named area only
    # when the full zone name identifies one world marker unambiguously.
    zone_gates=defaultdict(set)
    for gate,indices in entrances.items():
        wi,pi=gate
        zone_gates[worlds[wi][pi][2]].add(gate)
        for i in indices:
            name=records[i][1].split(' - ')[0]
            if name:zone_gates[name].add(gate)
    matched=0
    for i in targets-nearest.keys():
        zone=records[i][1].split(' - ')[0]
        if zone and '?' not in zone and len(zone_gates[zone])==1:
            gate,=zone_gates[zone]
            areas[gate].append(i)
            matched+=1
    print('Additional boss rooms with an unambiguous area name:',matched)
    for wi,world in enumerate(worlds):
        for pi,point in enumerate(world): point.append(sorted(areas[wi,pi]))
    print('Boss rooms reachable from world entrances:',len(nearest),'of',len(targets))
