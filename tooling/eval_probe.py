#!/usr/bin/env python3
"""Steering-3 eval for tune probes: elim-map early-game targets + open-map endgame
targets + rejection flags. Reads results/<tag>/games.jsonl + replays.

Targets (elim maps devil/dilemma/trophy/default): dragons/total-length at
r25=6.7/16.4, r50=10.3/25.5, r100=20/50 — report (winner - target) mean.
Open maps: longest@r499 > 33 and total@r499 >= 260.
Flags: cand queen death < r50 on Devil/Dilemma/Trophy/Default; any teamEliminat
game ending < r200.

Usage: $BC_PY tooling/eval_probe.py results/tune_x2b_cf [more dirs...]
"""
import collections, json, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'handoff/tooling'))
from parse_replay import parse
from replay_metrics import parse_map

ELIM = {'devil', 'dilemma', 'trophy', 'default'}
TARGETS = {25: (6.7, 16.4), 50: (10.3, 25.5), 100: (20.0, 50.0)}
MARKS = (25, 50, 100)


def per_round_stats(path):
    """Return {side: {round: (ndragons, total_len, longest)}} from a replay."""
    r = parse(path)
    ev = r['events']
    _, _, dr, _ = parse_map(r['map'])
    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    stats = {'A': {}, 'B': {}}
    rnd = 0
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            for s in 'AB':
                bs = [b for j, b in body.items() if team[j] == s]
                if bs:
                    stats[s][rnd] = (len(bs), sum(len(b) for b in bs),
                                     max(len(b) for b in bs))
                else:
                    stats[s][rnd] = (0, 0, 0)
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
        elif ty == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = e['team']
        elif ty == 'dragonDeath':
            body.pop(e['id'], None)
    return stats


def eval_tag(resdir):
    resdir = pathlib.Path(resdir)
    gj = resdir / 'games.jsonl'
    rows = []
    elim_pts = {m: {'d': [], 'l': []} for m in MARKS}
    open_longest, open_total = [], []
    flags_q50, flags_elim = [], []
    n = wins = 0
    for line in gj.read_text().splitlines():
        g = json.loads(line)
        n += 1
        wins += bool(g['candWin'])
        mp, sd, cs = g['map'], g['seed'], g['candSide']
        c = g['c']
        if g.get('end') == 'teamEliminat' and g.get('rounds', 999) < 200:
            flags_elim.append(f'{mp}s{sd}{cs} r{g["rounds"]}')
        if mp in ELIM and c.get('qDeadRound') and c['qDeadRound'] < 50:
            flags_q50.append(f'{mp}s{sd}{cs} r{c["qDeadRound"]}')
        if mp in ELIM:
            # replay-derived early marks; side letter for cand
            rp = resdir / 'replays'
            name = f'{mp}-s{sd}-' + (f'{g["cand"]}-{g["base"]}' if cs == 'A' else f'{g["base"]}-{g["cand"]}') + '.replay'
            rp_path = rp / name
            if rp_path.exists():
                st = per_round_stats(rp_path)[cs]
                for m in MARKS:
                    if m in st:
                        elim_pts[m]['d'].append(st[m][0])
                        elim_pts[m]['l'].append(st[m][1])
        else:
            open_longest.append(c['longest'])
            open_total.append(c['total'])
    parts = [f'{wins}-{n - wins} ({wins / max(1, n):.0%})']
    for m in MARKS:
        td, tl = TARGETS[m]
        if elim_pts[m]['d']:
            dd = sum(elim_pts[m]['d']) / len(elim_pts[m]['d']) - td
            dl = sum(elim_pts[m]['l']) / len(elim_pts[m]['l']) - tl
            parts.append(f'r{m} d{dd:+.1f} l{dl:+.1f}')
    if open_longest:
        parts.append(f'open longest {sum(open_longest) / len(open_longest):.1f}'
                     f'(>{33}: {sum(x > 33 for x in open_longest)}/{len(open_longest)})'
                     f' tot {sum(open_total) / len(open_total):.0f}'
                     f'(>=260: {sum(x >= 260 for x in open_total)}/{len(open_total)})')
    if flags_q50:
        parts.append(f'FLAG q<50: {";".join(flags_q50)}')
    if flags_elim:
        parts.append(f'FLAG elim<200: {";".join(flags_elim)}')
    return ' '.join(parts)


if __name__ == '__main__':
    for d in sys.argv[1:]:
        print(f'{os.path.basename(d):20s} {eval_tag(d)}')
