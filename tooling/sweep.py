"""Param sweep: random search over common.hpp tunables, gated vs abyss_v376.

Each candidate: copy v376 -> regex-replace param literals -> kmatch seeds 1
(34 games, both seats, all maps). Fitness = win rate + decided-pair margin.
Survivors (>=53%) get logged for stage-B confirmation on fresh seeds.
"""
import subprocess, json, random, re, shutil, os, sys, time

BC = '/home/ubuntu/bc'
BASE = f'{BC}/workspace/abyss_v376'
PY = '/home/ubuntu/.venv-bc/bin/python'

# name: (lo, hi, is_int) — only tunables, no map gates
PARAMS = {
    'swarmSplitLen': (4, 6, 1), 'swarmBudLen': (6, 10, 1), 'swarmBudChild': (3, 5, 1),
    'growerKeepBase': (2, 6, 1), 'growerKeepEvery': (40, 100, 1), 'growerChild': (2, 3, 1),
    'splitRoom': (4, 12, 1), 'spaceFactor': (1.2, 3.0, 0), 'spaceMargin': (1, 5, 1),
    'budAlive': (20, 50, 1), 'wSpace': (0.3, 1.2, 0), 'wDanger': (0.8, 2.5, 0),
    'starveLocal': (1.5, 4.0, 0), 'growRound': (250, 350, 1), 'feedRound': (320, 450, 1),
    'queenBudUntil': (350, 500, 1), 'escortCount': (2, 5, 1), 'escortRing': (2, 4, 1),
    'coveredFavour': (0.0, 0.4, 0), 'exposedFavour': (0.2, 0.6, 0), 'tradeSlack': (0, 2, 1),
    'wQueenLeash': (0.4, 1.4, 0), 'queenLeashDist': (4, 8, 1), 'heardFoodDist': (14, 30, 1),
    'wHeardFood': (0.8, 2.0, 0), 'wFogPull': (3.0, 10.0, 0), 'wHunt': (0.8, 2.5, 0),
    'twoStep': (0, 1, 1), 'sprintTrades': (0, 1, 1), 'slayAlways': (0, 1, 1),
    'qRamAdj': (0, 1, 1), 'tradeMinUnits': (2, 8, 1), 'trapSeenOnly': (0, 1, 1),
    'openUntil': (0, 60, 1), 'openEnemyDist': (1, 3, 1), 'splitEnemyDist': (1, 2, 1),
    'wQueenRam': (10.0, 50.0, 0), 'wQueenAlly': (1.0, 8.0, 0), 'wQueenFog': (0.5, 4.0, 0),
    'champFeedDist': (1, 4, 1), 'escortRadius': (3, 8, 1), 'squadSize': (2, 5, 1),
    'leanMargin': (0.02, 0.08, 0), 'wPersist': (0.2, 1.0, 0), 'pullAfter': (30, 90, 1),
    'wPocket': (0.8, 2.5, 0), 'wBlind': (1.0, 3.0, 0), 'wBlindQuiet': (0.1, 0.6, 0),
    'gamma': (0.7, 0.9, 0), 'eatBonus': (0.7, 1.3, 0), 'exploreValue': (0.01, 0.08, 0),
    'sonarKeyed': (0, 1, 1),
}

def base_params():
    """Read current param values from v376."""
    out = {}
    src = open(f'{BASE}/common.hpp').read()
    for name in PARAMS:
        m = re.search(rf'\b{re.escape(name)} = ([^;]+);', src)
        if m:
            v = m.group(1).strip()
            out[name] = int(float(v)) if PARAMS[name][2] else float(v)
    return out

BASEP = base_params()

def sample(n_mut):
    p = dict(BASEP)
    keys = random.sample(list(PARAMS), n_mut)
    for k in keys:
        lo, hi, isint = PARAMS[k]
        p[k] = random.randint(int(lo), int(hi)) if isint else round(random.uniform(lo, hi), 3)
    return p

def build(dst, params):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(BASE, dst)
    path = f'{dst}/common.hpp'
    src = open(path).read()
    for name, val in params.items():
        src = re.sub(rf'\b{re.escape(name)} = [^;]+;', f'{name} = {val};', src, count=1)
    open(path, 'w').write(src)

def evaluate(tag, jobs):
    """Returns (wins, losses, games) or None on failure."""
    r = subprocess.run(
        [PY, f'{BC}/tooling/kmatch.py', 'run', '--cand', f'sweep_{tag}',
         '--base', 'abyss_v376', '--maps', 'all', '--seeds', '1',
         '--jobs', str(jobs), '--tag', f'sw{tag}'],
        cwd=BC, capture_output=True, text=True, timeout=3600)
    gj = f'{BC}/results/sw{tag}/games.jsonl'
    if not os.path.exists(gj):
        return None
    wins = losses = 0
    csplits = bsplits = 0
    for line in open(gj):
        g = json.loads(line)
        if g.get('candWin'):
            wins += 1
        else:
            losses += 1
        csplits += g['c'].get('splits', 0)
        bsplits += g['b'].get('splits', 0)
    return wins, losses, wins + losses, csplits, bsplits

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    n_evals = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    log = open(f'{BC}/devin/sweep_log.csv', 'a')
    for i in range(start, start + n_evals):
        random.seed(10000 + i)
        params = sample(random.randint(3, 6))
        tag = f'{i:04d}'
        dst = f'{BC}/workspace/sweep_{tag}'
        build(dst, params)
        try:
            res = evaluate(tag, jobs)
        except Exception as e:
            res = None
        if res is None:
            print(f'{tag} FAIL', flush=True)
            log.write(f'{tag},FAIL,{json.dumps(params)}\n'); log.flush()
            continue
        w, l, g, cs, bs = res
        wr = w / g if g else 0
        mark = ' ***' if wr >= 0.53 else ''
        print(f'{tag} {w}-{l} {wr:.3f} splits {cs}/{bs}{mark}', flush=True)
        log.write(f'{tag},{w}-{l},{wr:.3f},splits={cs}/{bs},{json.dumps(params)}\n'); log.flush()
        if wr < 0.45:  # clean losers to save disk
            shutil.rmtree(dst, ignore_errors=True)
    log.close()

if __name__ == '__main__':
    main()
