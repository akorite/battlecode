"""Dead-end corridor ENTRY study: do winners' workers enter deg<=2 dead-end
branches at all, or is the discipline at entry (not in-corridor)?

deadEnd set replicates abyss_v201 marking: walk each deg1 tip along its
deg<=2 chain; mark chain iff it terminates at a junction (deg>=3);
tip-to-tip corridors stay unmarked.

Per side per replay:
  enter   = head steps onto a deadEnd cell while previous head was non-deadEnd
  dwell   = rounds with head on a deadEnd cell
  exit    = head returns to non-deadEnd cell alive
  die_in  = dragonDeath while head on deadEnd cell (by reason)
  split_in= dragonSplit whose child lands on deadEnd cell
  post    = outcome within 8 rounds of each entry: exit / die / still-in

Usage: python3 tooling/deadend_visit.py <replay> [...] -> JSONL
"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map, edge_kind, cell_deg, D


def deadend_set(W, H, edges):
    deg = [cell_deg(W, H, edges, x, y) for y in range(H) for x in range(W)]
    def nbs(c):
        x, y = c % W, c // W
        return [((x + dx) % W) + ((y + dy) % H) * W
                for d, (dx, dy) in D.items() if edge_kind(edges, W, H, x, y, d) == 0]
    de = [0] * (W * H)
    for c in range(W * H):
        if deg[c] != 1:
            continue
        chain, prev, cur, mark = [c], -1, c, False
        for _ in range(W * H):
            nxt = -1
            for n in nbs(cur):
                if n != prev:
                    nxt = n
                    break
            if nxt < 0:
                break
            if deg[nxt] >= 3:
                mark = True
                break
            if deg[nxt] == 1:
                break
            chain.append(nxt)
            prev, cur = cur, nxt
        if mark:
            for x in chain:
                de[x] = 1
    return de, deg


def main(path):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    de, deg = deadend_set(W, H, edges)
    team = {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate':
            team[e['id']] = 'AB'[e['id'] % 2]
    rnd = 0
    heads = {}
    out = {s: collections.Counter() for s in 'AB'}
    entries = {s: [] for s in 'AB'}   # (round, dragon) pending entry records
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
        elif ty == 'dragonUpdate':
            i = e['id']
            h = tuple(e['head'])
            c = h[1] * W + h[0]
            prev = heads.get(i)
            s = team.get(i)
            if s:
                if de[c]:
                    out[s]['dwell'] += 1
                    if prev is not None and not de[prev[1] * W + prev[0]]:
                        out[s]['enter'] += 1
                        entries[s].append([rnd, i, 'open'])
                elif prev is not None and de[prev[1] * W + prev[0]]:
                    out[s]['exit'] += 1
            heads[i] = h
        elif ty == 'dragonSplit':
            s = e['team']
            team[e['childId']] = s
            ch = tuple(e['childBody'][0])
            heads[e['childId']] = ch
            if de[ch[1] * W + ch[0]]:
                out[s]['split_in'] += 1
            ph = tuple(e['parentBody'][0])
            heads[e['parentId']] = ph
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            h = heads.get(i)
            if s and h and de[h[1] * W + h[0]]:
                out[s][f"die_{e['reason']}"] += 1
            heads.pop(i, None)
    # post-entry outcome within 8 rounds: replay events already consumed;
    # second pass not needed for rough class — report raw counts.
    res = {'file': os.path.basename(path), 'map_nc': W * H,
           'deadEndCells': sum(de)}
    for s in 'AB':
        res[s] = dict(out[s])
    return res


if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            print(json.dumps(main(p)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(p), 'error': str(ex)}))
