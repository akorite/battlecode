#!/usr/bin/env python3
"""Analyze queen_of_spades mutual-elimination kill geometry.
For each replay: list starter deaths, and for every hitHeadToHead death dump
both dragons' head traces over the last rounds plus the kill-cell geometry
(front-on vs flank approach, bodies adjacent to the kill cell).
Usage: qos_elim.py <replay_or_dir> [--window N]"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handoff', 'tooling'))
from collections import defaultdict
from parse_replay import parse

def team_of(did, splits):
    for s in splits:
        if s['childId'] == did:
            return s['team']
    return 'A' if did % 2 == 0 else 'B'   # starters alternate; queens = 0(A),1(B)

def analyze(path, window=45):
    r = parse(path)
    heads = defaultdict(dict)   # id -> round -> head tuple
    facing = defaultdict(dict)
    bodies = defaultdict(dict)  # id -> round -> [head..tail]
    deaths = []                 # (round, id, reason)
    splits = []
    actions = defaultdict(dict) # id -> round -> action dir/str
    rnd = -1
    for e in r['events']:
        t = e.get('type')
        if t == 'roundStart':
            rnd = e.get('round', rnd + 1)
        elif t == 'dragonUpdate':
            heads[e['id']][rnd] = tuple(e['head'])
            facing[e['id']][rnd] = e['facing']
            # approximate body segment = straight line head->tail
            h, tl = e['head'], e['tail']
            seg = [tuple(h)]
            x, y = h
            while (x, y) != tuple(tl):
                x += 1 if tl[0] > x else -1 if tl[0] < x else 0
                y += 1 if tl[1] > y else -1 if tl[1] < y else 0
                seg.append((x, y))
            bodies[e['id']][rnd] = seg
        elif t == 'dragonDeath':
            deaths.append((rnd, e['id'], e['reason']))
        elif t == 'dragonSplit':
            splits.append(e)
        elif t == 'dragonAction':
            actions[e['id']][rnd] = e.get('action', '?')

    starters = [d for d in range(4)]
    starter_deaths = [(rd, i, why) for rd, i, why in deaths if i in starters]
    early = [d for d in starter_deaths if d[0] <= window]
    tag = 'MUTUAL-ELIM' if len(early) >= 3 else ''
    print(f"\n== {os.path.basename(path)}  end={r['result']['endReason'] if r['result'] else '?'} "
          f"winner={r['result']['winner'] if r['result'] else '?'} rounds_seen={rnd} {tag}")
    for rd, i, why in deaths:
        mk = ' <== starter' if i in starters else ''
        if why == 'hitHeadToHead' or i in starters:
            print(f"  death r{rd} id{i} ({team_of(i,splits)}) {why}{mk}")
    # geometry for each starter h2h death <= window
    for rd, i, why in early:
        if why != 'hitHeadToHead':
            continue
        # find the other h2h death same round = the ram partner
        partner = next((j for rd2, j, w2 in deaths if rd2 == rd and w2 == 'hitHeadToHead' and j != i), None)
        cell = heads[i].get(rd) or heads[i].get(rd - 1)
        print(f"  -- r{rd} h2h: id{i} head@r{rd}={cell} facing={facing[i].get(rd-1,'?')}"
              f" last4={[(x, heads[i].get(x)) for x in range(rd-4, rd)]}")
        if partner is not None:
            print(f"     partner id{partner} ({team_of(partner,splits)}) "
                  f"last4={[(x, heads[partner].get(x)) for x in range(rd-4, rd)]} "
                  f"facing={facing[partner].get(rd-1,'?')}")
        # other dragons' heads within manhattan<=3 of kill cell at rd-1
        if cell:
            near = [(d, heads[d].get(rd - 1)) for d in heads
                    if d != i and heads[d].get(rd - 1) and
                    abs(heads[d][rd-1][0]-cell[0]) + abs(heads[d][rd-1][1]-cell[1]) <= 3]
            print(f"     heads<=3 of kill cell r{rd-1}: {near}")
            # bodies (escort walls) covering cells adjacent to the kill cell
            adj = [(cell[0]+dx, cell[1]+dy) for dx, dy in ((0,-1),(1,0),(0,1),(-1,0))]
            blockers = []
            for d in bodies:
                seg = bodies[d].get(rd - 1)
                if seg and d != i:
                    hit = [c for c in adj if c in seg]
                    if hit:
                        blockers.append((d, team_of(d, splits), hit, seg[0]))
            if blockers:
                print(f"     body walls adjacent: {blockers}")
    if not early and len(starter_deaths) >= 3:
        print(f"  starter deaths later than window: {starter_deaths}")

def main():
    target = sys.argv[1]
    window = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    files = sorted(glob.glob(os.path.join(target, 'replays', '*.replay'))) if os.path.isdir(target) else [target]
    for f in files:
        try:
            analyze(f, window)
        except Exception as ex:
            print(f"{f}: ERR {ex}")

if __name__ == '__main__':
    main()
