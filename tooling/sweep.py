"""Param sweep A/B: patch Params in a scratch copy of a bot, run a batch, score.

Usage:
  python3 tooling/sweep.py --base abyss --variant 'wSpace=1.2' \
      --maps slithery_fight,autarky --seeds 2 --tag wspace12

Creates workspace/sweep_<tag>/ as a copy of --base with the param literal
patched in common.hpp, runs match.py vs the base bot, and prints the W-L.
Multiple overrides comma-separated: --variant 'wSpace=1.2,wDanger=2.0'
"""
import argparse, os, re, shutil, subprocess, sys, json, glob

BC = '/home/ubuntu/battlecode'
WS = os.path.join(BC, 'workspace')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)          # bot dir to fork, e.g. abyss
    ap.add_argument('--against', default=None)        # opponent bot (default: base)
    ap.add_argument('--variant', required=True)       # 'param=val,param2=val2'
    ap.add_argument('--maps', default='slithery_fight,autarky,schooltime,trauma,queen_of_spades,trophy')
    ap.add_argument('--seeds', type=int, default=2)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--jobs', type=int, default=8)
    a = ap.parse_args()

    src = os.path.join(WS, a.base)
    dst = os.path.join(WS, 'sweep_' + a.tag)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    common = os.path.join(dst, 'common.hpp')
    text = open(common).read()
    for kv in a.variant.split(','):
        name, val = [x.strip() for x in kv.split('=', 1)]
        pat = re.compile(r'(\b' + re.escape(name) + r'\s*=\s*)[-0-9a-fxA-F\.]+')
        new, n = pat.subn(r'\g<1>' + val, text, count=1)
        if n != 1:
            sys.exit(f'param {name} not found in {common}')
        text = new
    open(common, 'w').write(text)

    # bust the wasm cache for a clean build
    subprocess.run(['touch', os.path.join(dst, 'main.cpp')])
    for f in glob.glob(os.path.expanduser(f'~/.cache/unswbc/wasmbots/sweep_{a.tag}-*.wasm')):
        os.unlink(f)

    against = a.against or a.base
    cmd = [sys.executable, os.path.join(BC, 'tooling/match.py'),
           '--bots', 'sweep_' + a.tag, against,
           '--maps', a.maps, '--seeds', str(a.seeds),
           '--tag', a.tag, '--jobs', str(a.jobs)]
    print('+', ' '.join(cmd))
    subprocess.run(cmd, cwd=BC)

if __name__ == '__main__':
    main()
