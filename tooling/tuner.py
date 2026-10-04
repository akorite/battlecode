#!/usr/bin/env python3
"""SPSA/coordinate-descent tuning lane driver (explore addendum).

For each (name, param=value) probe: copy the tune base to workspace/<tag>,
sed-patch the literal `name = val` in common.hpp, run kmatch vs a benchmark
bot on a fixed mapset, append a row to devin/tuning.md.

Usage:
  source ~/.bc-env
  $BC_PY tooling/tuner.py --plan plans/round1.txt --jobs 2

plan line:  <slug> <param>=<value> [maps=csv] [note...]
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, time

BC = pathlib.Path(__file__).resolve().parent.parent
WS = BC / 'workspace'
LOG = BC / 'devin' / 'tuning.md'
PY = os.environ.get('BC_PY', sys.executable)

MAPS = 'stronghold,trauma,schooltime,devil,trophy'   # S1-relevant big set + elim control
BASE = 'abyss_x_tune'
OPP = 'abyss_combat'


def make_variant(slug, pairs, base):
    dst = WS / slug
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(WS / base, dst)
    common = dst / 'common.hpp'
    text = common.read_text()
    # patch every assignment site: `PARAM = v` (struct default) and `p.PARAM = v`
    # (kParams lambda override) — a probe must set the ACTIVE site(s).
    # \b stops feedRound matching inside queenFeedRound / feedRoundBrawl.
    for param, val in pairs:
        pat = re.compile(r'(\b' + re.escape(param) + r'\s*=\s*)[-0-9a-fxA-F\.]+')
        text, n = pat.subn(r'\g<1>' + val, text)
        if n < 1:
            sys.exit(f'param {param} not found in {common}')
    common.write_text(text)
    (dst / 'main.cpp').touch()  # bust wasm cache
    for f in pathlib.Path.home().glob(f'.cache/unswbc/wasmbots/{slug}-*.wasm'):
        f.unlink()


def run_probe(slug, label, maps, jobs, seed_start, opp):
    tag = 'tune_' + slug
    res = BC / 'results' / tag
    shutil.rmtree(res, ignore_errors=True)
    cmd = [PY, str(BC / 'tooling/kmatch.py'), 'run',
           '--cand', slug, '--base', opp,
           '--maps', maps, '--seeds', '1', '--seed-start', str(seed_start),
           '--jobs', str(jobs), '--tag', tag, '--keep-replays']
    t0 = time.time()
    p = subprocess.run(cmd, cwd=BC, capture_output=True, text=True)
    mins = (time.time() - t0) / 60
    gj = res / 'games.jsonl'
    wins = losses = 0
    lens = []
    if gj.exists():
        for line in gj.read_text().splitlines():
            g = json.loads(line)
            w = g.get('candWin')
            if w is None:
                continue
            if w > 0:
                wins += 1
            else:
                losses += 1
            lens.append(g['c']['longest'] - g['b']['longest'])
    n = wins + losses
    score = wins / n if n else 0
    dlen = sum(lens) / len(lens) if lens else 0
    return wins, losses, score, dlen, mins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--base', default=BASE)
    ap.add_argument('--opp', default=OPP)
    ap.add_argument('--seed-start', type=int, default=7)
    a = ap.parse_args()

    LOG.parent.mkdir(exist_ok=True)
    for line in open(a.plan):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        slug, kv = parts[0], parts[1]
        pairs = [tuple(p.split('=', 1)) for p in kv.split(',')]
        maps = next((p[5:] for p in parts[2:] if p.startswith('maps=')), MAPS)
        note = ' '.join(p for p in parts[2:] if not p.startswith('maps='))
        make_variant(slug, pairs, a.base)
        wins, losses, score, dlen, mins = run_probe(slug, ','.join(k for k, _ in pairs), maps, a.jobs, a.seed_start, a.opp)
        row = (f'| {slug} | `{kv}` | {maps} | {wins}-{losses} '
               f'({score:.0%}) | dlen {dlen:+.1f} | {mins:.0f}m | {note} |\n')
        print(row, end='', flush=True)
        with open(LOG, 'a') as f:
            f.write(row)


if __name__ == '__main__':
    main()
