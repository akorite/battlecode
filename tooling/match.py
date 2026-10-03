"""Batch match runner: unswbc run across maps/seeds, parallel, with JSON summary.

Usage:
  python3 match.py --bots abyss abyss_base [--maps all|name,...] [--seeds 4]
                  [--tag run1] [--jobs 8] [--no-eval]

Writes replays to results/<tag>/replays/ and prints per-game + aggregate lines.
"""
import argparse, glob, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

BC = os.environ.get('BC_REPO', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WS = os.path.join(BC, 'workspace')
UNSWBC = os.environ.get('UNSWBC', os.path.expanduser('~/.local/bin/unswbc'))
ALL_MAPS = ['arena', 'autarky', 'big_empty', 'Colosseum', 'default', 'devil',
            'dilemma', 'portals', 'queen_of_spades', 'schooltime',
            'slithery_fight', 'stronghold', 'trauma', 'trophy', 'default_small']


def fresh_bots(bots):
    # unswbc hashes only .cpp contents for the wasm cache; header edits would be
    # served stale unless the cached artifact is removed first. Clear once per
    # batch: doing it inside run_one races parallel builds.
    for bot in bots:
        for f in glob.glob(os.path.expanduser(f'~/.cache/unswbc/wasmbots/{bot}-*.wasm')):
            os.unlink(f)
        cpp = os.path.join(WS, bot, 'main.cpp')
        if os.path.exists(cpp):
            os.utime(cpp)


def run_one(args):
    mapname, side, seed, bots, outdir = args
    bots2 = bots if side == 0 else bots[::-1]
    out = os.path.join(outdir, f'{mapname}-s{seed}-{"-".join(bots2)}.replay')
    cmd = [UNSWBC, 'run', f'maps/{mapname}.map',
           *bots2, '--sandbox', '--seed', str(seed), '-o', out]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=900)
    tail = p.stdout.strip().split('\n')
    return dict(map=mapname, side=side, seed=seed, bots=bots2, replay=out,
                rc=p.returncode, secs=round(time.time() - t0, 1),
                tail=tail[-6:], errtail=p.stderr.strip().split('\n')[-4:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bots', nargs=2, required=True)
    ap.add_argument('--maps', default='all')
    ap.add_argument('--seeds', type=int, default=1)
    ap.add_argument('--seed-start', type=int, default=0)
    ap.add_argument('--both-sides', action='store_true', default=True)
    ap.add_argument('--one-side', dest='both_sides', action='store_false')
    ap.add_argument('--tag', default='run')
    ap.add_argument('--jobs', type=int, default=8)
    a = ap.parse_args()

    maps = ALL_MAPS if a.maps == 'all' else a.maps.split(',')
    fresh_bots(a.bots)
    outdir = os.path.join(BC, 'results', a.tag)
    os.makedirs(os.path.join(outdir, 'replays'), exist_ok=True)
    jobs = []
    for m in maps:
        for seed in range(a.seed_start, a.seed_start + a.seeds):
            sides = (0, 1) if a.both_sides else (0,)
            for side in sides:
                jobs.append((m, side, seed, a.bots, outdir + '/replays'))
    res = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for r in ex.map(run_one, jobs):
            res.append(r)
            wins = [x for x in r['tail'] if 'wins' in x]
            print(f"{r['map']:>16} seed{r['seed']} {'vs'.join(r['bots']):>22} "
                  f"rc={r['rc']} {r['secs']:>5}s  {wins[0] if wins else r['tail'][-1] if r['tail'] else ''}",
                  flush=True)
    json.dump(res, open(os.path.join(outdir, 'runs.json'), 'w'), indent=1)
    fails = [r for r in res if r['rc'] != 0]
    if fails:
        print(f'\n{len(fails)} failed runs:')
        for f in fails[:5]:
            print(f['map'], f['errtail'])


if __name__ == '__main__':
    main()
