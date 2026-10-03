"""Paired-seed, both-sides A/B matches on kvmrun (judge-identical replays, ~10x
faster than `unswbc run --sandbox`).

  python3 tooling/kmatch.py run --cand abyss_v102 --base abyss_st \
      --maps small --seeds 4 --jobs 3 --tag v102_vs_st
  python3 tooling/kmatch.py summary results/v102_vs_st [results/other ...]

Every (map, seed) is played twice, cand as A and cand as B, with the same
seed, so map side and pearl schedule cancel within each pair. Replays go to
results/<tag>/replays/, one JSON line per game to results/<tag>/games.jsonl
(metrics from tooling/replay_metrics.py). Rerunning a tag skips games already
in games.jsonl, so an interrupted batch resumes.

Bot sources are copied to a content-addressed dir before building: unswbc's
wasm cache hashes only .cpp files, so header edits would otherwise be served
stale.

Environment (defaults in brackets):
  KVMRUN      kvmrun checkout                  [~/kvmrun]
  BC_PY       python with unswbc 1.2.7         [~/.venv-bc/bin/python]
  UNSWBC_PKG  site-packages holding unswbc     [BC_PY's venv]
  BC_MAPS     map dir                          [UNSWBC_PKG/unswbc/templates/maps, = upstream 1.2.7 maps]
  WABT_BIN, SIMDE_INC                          [~/bc-tools/... if present, else kvmrun's own search]
  BC_BOTCACHE staged bot copies                [~/.cache/bcbots]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import random
import os
import pathlib
import re
import shutil
import subprocess
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
WS = REPO / 'workspace'
HOME = pathlib.Path.home()
KVMRUN = pathlib.Path(os.environ.get('KVMRUN', HOME / 'kvmrun'))
BC_PY = os.environ.get('BC_PY', str(HOME / '.venv-bc' / 'bin' / 'python'))


def _site_packages():
    # the venv BC_PY belongs to: <venv>/lib/python3.*/site-packages
    venv = pathlib.Path(BC_PY).absolute().parent.parent  # no resolve(): venv python is a symlink
    hits = sorted(venv.glob('lib/python3*/site-packages'))
    return str(hits[0]) if hits else ''


os.environ.setdefault('UNSWBC_PKG', _site_packages())
for var, guess in (('WABT_BIN', HOME / 'bc-tools' / 'wabt' / 'bin'),
                   ('SIMDE_INC', HOME / 'bc-tools' / 'simde')):
    if var not in os.environ and guess.is_dir():
        os.environ[var] = str(guess)  # else kvmrun searches PATH / system include dirs
MAPS = pathlib.Path(os.environ.get('BC_MAPS', pathlib.Path(os.environ['UNSWBC_PKG']) / 'unswbc' / 'templates' / 'maps'))
BOTCACHE = pathlib.Path(os.environ.get('BC_BOTCACHE', pathlib.Path.home() / '.cache' / 'bcbots'))

# Small maps are where we lose by elimination (our-games report section 3), so
# presets weight them; `all` is every contest map the 1.2.7 toolkit ships.
SMALL = ['trophy', 'devil', 'dilemma', 'queen_of_spades', 'Colosseum', 'stripes',
         'tower_defense', 'weakhold', 'arena', 'default_small']
BIG = ['default', 'portals', 'autarky', 'stronghold', 'trauma', 'maze', 'schooltime',
       'slithery_fight', 'islands', 'big_empty', 'australia', 'unsw']
MID = ['default', 'portals', 'autarky', 'stronghold', 'trauma', 'maze']
PRESETS = {'small': SMALL, 'big': BIG, 'mid': MID, 'all': SMALL + BIG, 'std': SMALL + MID}
WIN_RE = re.compile(r'team (\S+) wins after (\d+) rounds|draw after (\d+) rounds')


def staged(bot):
    """Copy bot dir to BOTCACHE/<name>-<hash of every file>/ and return it."""
    src = pathlib.Path(bot)
    if not src.is_dir():
        src = WS / bot
    h = hashlib.sha256()
    files = sorted(p for p in src.rglob('*') if p.is_file() and not any(
        part.startswith('.') for part in p.relative_to(src).parts))
    for p in files:
        h.update(p.relative_to(src).as_posix().encode() + b'\0' + p.read_bytes())
    dst = BOTCACHE / f'{src.name}-{h.hexdigest()[:16]}'
    if not dst.is_dir():
        tmp = BOTCACHE / f'.tmp-{os.getpid()}-{threading.get_ident()}'
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(src, tmp, ignore=shutil.ignore_patterns('.*'))
        BOTCACHE.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(tmp, dst)
        except OSError:
            shutil.rmtree(tmp, ignore_errors=True)
    return dst


def build_runner(a_dir, b_dir):
    """Build (or fetch cached) kvmrun native runner for bots (A, B)."""
    code = ('import sys; sys.path.insert(0, %r); import kvmrun; '
            'b, _ = kvmrun.build("native", %r, %r); print("RUNNER", b)') % (
        str(KVMRUN), str(a_dir), str(b_dir))
    p = subprocess.run([BC_PY, '-c', code], capture_output=True, text=True)
    m = re.search(r'RUNNER (\S+)', p.stdout)
    if not m:
        sys.exit(f'build failed for {a_dir.name} vs {b_dir.name}:\n{p.stdout[-2000:]}\n{p.stderr[-4000:]}')
    return m.group(1)


def run(a):
    maps = PRESETS.get(a.maps, None) or a.maps.split(',')
    out = REPO / 'results' / a.tag
    (out / 'replays').mkdir(parents=True, exist_ok=True)
    games = out / 'games.jsonl'
    done = set()
    if games.exists():
        for line in games.read_text().splitlines():
            g = json.loads(line)
            done.add((g['map'], g['seed'], g['candSide']))
    cd, bd = staged(a.cand), staged(a.base)
    runners = {'A': build_runner(cd, bd), 'B': build_runner(bd, cd)}
    jobs = []
    for seed in range(a.seed_start, a.seed_start + a.seeds):
        for m in maps:
            for side in 'AB':
                if (m, seed, side) not in done:
                    jobs.append((m, seed, side))
    print(f'{len(jobs)} games to play ({len(done)} already done), {a.jobs} at a time', flush=True)
    lock = threading.Lock()
    sys.path.insert(0, str(HERE))
    import replay_metrics

    def one(job):
        m, seed, side = job
        na, nb = (a.cand, a.base) if side == 'A' else (a.base, a.cand)
        rp = out / 'replays' / f'{m}-s{seed}-{na}-{nb}.replay'
        t0 = time.time()
        p = subprocess.run([runners[side], str(MAPS / f'{m}.map'), '--name-a', na, '--name-b', nb,
                            '--seed', str(seed), '--replay', str(rp)],
                           capture_output=True, text=True)
        secs = time.time() - t0
        if p.returncode != 0 or not rp.exists():
            print(f'FAIL {m} s{seed} cand={side} rc={p.returncode}\n{p.stdout[-500:]}{p.stderr[-500:]}', flush=True)
            return
        met = replay_metrics.analyze(str(rp))
        other = 'B' if side == 'A' else 'A'
        rec = {'map': m, 'seed': seed, 'candSide': side, 'cand': a.cand, 'base': a.base,
               'secs': round(secs, 1), 'end': met['end'], 'rounds': met['rounds'],
               'winner': met['winner'], 'candWin': met[side]['win'], 'c': met[side], 'b': met[other]}
        if not a.keep_replays:
            rp.unlink(missing_ok=True)
        with lock:
            with open(games, 'a') as f:
                f.write(json.dumps(rec) + '\n')
            res = {1.0: 'W', 0.0: 'L'}.get(rec['candWin'], 'D')
            print(f'{m:>16} s{seed} cand={side} {res} r{met["rounds"]:<3} {met["end"]} '
                  f'len c{met[side]["longest"]}/b{met[other]["longest"]} {secs:.0f}s', flush=True)

    with cf.ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(one, jobs))
    summary([str(out)])


def wilson(w, n, z=1.96):
    if n == 0:
        return (0, 1)
    p = w / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def pair_ci(units, B=2000, z=1.96):
    """CI on the mean of per-pair scores (W=1, split=0.5, L=0; an unpaired game counts as its own unit).
    Games in a pair share a seed and map, so they are not independent; resampling pairs respects that.
    Percentile bootstrap with a fixed RNG so summaries are reproducible."""
    n = len(units)
    if n == 0:
        return (0, 1)
    if n == 1:
        return (0, 1)
    rng = random.Random(12345)
    ms = sorted(sum(rng.choice(units) for _ in range(n)) / n for _ in range(B))
    return (ms[int(0.025 * B)], ms[int(0.975 * B) - 1])


SIDE_LOCKED = {'queen_of_spades', 'devil', 'portals', 'schooltime', 'slithery_fight'}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float('nan')


def summary(dirs, out=sys.stdout):
    G = []
    for d in dirs:
        f = pathlib.Path(d) / 'games.jsonl'
        if f.exists():
            G += [json.loads(line) for line in f.read_text().splitlines()]
    if not G:
        print('no games', file=out)
        return
    cand, base = G[0]['cand'], G[0]['base']
    maps = sorted({g['map'] for g in G}, key=lambda m: (m not in SMALL, m))
    pr = lambda *x: print(*x, file=out)
    pr(f'## {cand} vs {base}: {len(G)} games')
    pr(f'{"map":>16} {"n":>4} {"score":>7} {"win%":>6} {"game CI":>13}  {"pairs W/S/L":>11}  {"pair CI":>13}')

    def line(name, gs):
        n = len(gs)
        w = sum(g['candWin'] for g in gs)
        lo, hi = wilson(w, n)
        pairs = {}
        for g in gs:
            pairs.setdefault((g['map'], g['seed']), []).append(g['candWin'])
        full = [v for v in pairs.values() if len(v) == 2]
        pw = sum(1 for v in full if sum(v) == 2)
        pl = sum(1 for v in full if sum(v) == 0)
        units = [sum(v) / len(v) for v in pairs.values()]
        plo, phi = pair_ci(units)
        pr(f'{name:>16} {n:>4} {w:>7.1f} {100 * w / n:>5.1f}% [{100 * lo:4.1f},{100 * hi:5.1f}]  '
           f'{pw:>3}/{len(full) - pw - pl:>3}/{pl:<3}  [{100 * plo:4.1f},{100 * phi:5.1f}]')
    for m in maps:
        line(m, [g for g in G if g['map'] == m])
    sm = [g for g in G if g['map'] in SMALL]
    bg = [g for g in G if g['map'] not in SMALL]
    if sm and bg:
        line('SMALL', sm)
        line('BIG', bg)
    line('ALL', G)
    un = [g for g in G if g['map'] not in SIDE_LOCKED]
    if 0 < len(un) < len(G):
        line('ALL-unlocked', un)
    pm = {}
    for g in G:
        pm.setdefault(g['map'], []).append(g['candWin'])
    pr(f'{"map-weighted":>16} {"":>4} {"":>7} {100 * mean([sum(v) / len(v) for v in pm.values()]):>5.1f}%  '
       f'(each map equal weight; ALL-unlocked drops {", ".join(sorted(SIDE_LOCKED))})')
    pr('\nper-game metrics, cand vs base (means):')
    r500 = [g for g in G if g['rounds'] >= 499]
    elim = [g for g in G if g['map'] in SMALL]
    rows = [
        ('alive at r499', r500, lambda s: s['alive499']),
        ('longest at end (r500 games)', r500, lambda s: s['longest']),
        ('queen len at end (r500 games)', r500, lambda s: s['queenEnd']),
        ('queen alive at end (r500)', r500, lambda s: int(s['queenEnd'] > 0)),
        ('pearls per dragon-turn', G, lambda s: s['ppt']),
        ('adjacent free pearl taken', G, lambda s: s.get('adjAte', 0) / max(1, s.get('adjN', 0))),
        ('  ... no enemy head <=3', G, lambda s: s.get('adjQuietAte', 0) / max(1, s.get('adjQuietN', 0))),
        ('queen non-ram deaths/game', G, lambda s: s['qNonRam']),
        ('queen dead (any) /game', G, lambda s: int(s['qDeadRound'] is not None)),
        ('deaths/game: wall+self+body', G, lambda s: s.get('d_hitWall', 0) + s.get('d_hitSelf', 0) + s.get('d_hitOtherBody', 0)),
        ('deaths/game: head-to-head', G, lambda s: s.get('d_hitHeadToHead', 0)),
        ('small maps: pearls eaten by r30', elim, lambda s: s.get('eaten30', 0)),
        ('all maps: pearls eaten by r30', G, lambda s: s.get('eaten30', 0)),
        ('small maps: pearls eaten by r60', elim, lambda s: s.get('eaten60', 0)),
        ('small maps: splits by r60', elim, lambda s: s.get('splits60', 0)),
        ('small maps: alive at r50', elim, lambda s: s['alive50']),
    ]
    for name, gs, f in rows:
        if name.startswith('small maps: pearls'):
            for b in '123':
                opp = [sum(g[k].get('slayOpp' + b, 0) for g in G) for k in 'cb']
                kil = [sum(g[k].get('slayKill' + b, 0) for g in G) for k in 'cb']
                pr(f'{"in-reach queen kill rate, dist " + b + ("+" if b == "3" else ""):>34}: '
                   f'{kil[0] / max(1, opp[0]):7.3f} vs {kil[1] / max(1, opp[1]):7.3f}  (opps {opp[0]} vs {opp[1]})')
            for k, lab in (('c', 'cand'), ('b', 'base')):
                o = 'b' if k == 'c' else 'c'
                first = [g for g in G if g[o]['qDeadRound'] is not None and
                         (g[k]['qDeadRound'] is None or g[k]['qDeadRound'] > g[o]['qDeadRound'])]
                kept = [g for g in first if g[k]['qDeadRound'] is None]
                pr(f'{"queen kept after theirs died (" + lab + ")":>34}: {len(kept) / max(1, len(first)):7.3f}'
                   f'  ({len(kept)}/{len(first)}; won {sum(g["candWin"] if k == "c" else 1 - g["candWin"] for g in first):.1f})')
        if gs:
            pr(f'{name:>34}: {mean([f(g["c"]) for g in gs]):7.3f} vs {mean([f(g["b"]) for g in gs]):7.3f}  (n={len(gs)})')
    pr(f'   r500 games: {len(r500)}, eliminations: {sum(1 for g in G if g["end"] == "teamEliminated")}, '
       f'mean secs/game {mean([g["secs"] for g in G]):.0f}')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--cand', required=True)
    r.add_argument('--base', default='abyss_st')
    r.add_argument('--maps', default='std')
    r.add_argument('--seeds', type=int, default=2)
    r.add_argument('--seed-start', type=int, default=1)
    r.add_argument('--jobs', type=int, default=1)
    r.add_argument('--tag', required=True)
    r.add_argument('--keep-replays', action='store_true')
    s = sub.add_parser('summary')
    s.add_argument('dirs', nargs='+')
    a = ap.parse_args()
    if a.cmd == 'run':
        run(a)
    else:
        summary(a.dirs)


if __name__ == '__main__':
    main()
