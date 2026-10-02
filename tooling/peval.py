"""A/B eval: run bceval win_probability over every replay in a results dir.

Usage: python3 peval.py <dir-or-replay> [<dir-or-replay> ...] [--bot NAME]
Normalizes to P(bot wins): if the named bot played side B, uses 1-P(A).
Pairs are already symmetric in match.py output (both sides per map+seed).
"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
import bceval_adapter as ba
_sc = ba._score()
win_probability, logit_parts = _sc.win_probability, _sc.logit_parts

KEYS = ["alive", "total", "longest", "eat", "deaths", "terr", "kills_h2h", "lost_len"]


def eval_replay(path, bot):
    game, rows = ba.replay_features(path, every=25)
    side = 1.0 if game["bot_a"] == bot else -1.0 if game["bot_b"] == bot else 0.0
    snaps = {}
    for r in rows:
        p = win_probability(r["round"], r["a"], r["b"])
        p = p if side >= 0 else 1.0 - p
        snaps[r["round"]] = {"p": p,
                             "d": {k: (r["a"][k] - r["b"][k]) * (1 if side >= 0 else -1)
                                   for k in KEYS}}
    return {"map": game["map"], "a": game["bot_a"], "b": game["bot_b"],
            "winner": game["winner"], "end": game["end"], "last": game["last_round"],
            "snaps": snaps, "bot": bot,
            "bot_won": (game["winner"] == "A") == (side > 0),
            "file": os.path.basename(path)}


def snap_at(r, rnd):
    if not r["snaps"]:
        return None
    best = min(r["snaps"], key=lambda k: abs(k - rnd))
    return r["snaps"][best]


def main():
    args = sys.argv[1:]
    bot = None
    if '--bot' in args:
        i = args.index('--bot')
        bot = args[i + 1]
        args = args[:i] + args[i + 2:]
    paths = []
    for d in args:
        paths += sorted(glob.glob(os.path.join(d, '*.replay')) if os.path.isdir(d) else [d])
    if not bot:
        # infer: the bot that appears in every replay
        names = set()
        for p in paths:
            names.update(os.path.basename(p).split('-')[2:4])
        bot = 'abyss' if 'abyss' in names else sorted(names)[0]
    results = []
    for p in paths:
        try:
            results.append(eval_replay(p, bot))
        except Exception as e:
            print(f'# {p}: {e}', file=sys.stderr)

    maps = sorted({r["map"] for r in results})
    print(f'{"map":>16} {"games":>5} {"W-L":>7} {"P125":>6} {"P250":>6} {"P375":>6} {"Pfin":>6}')
    all_p = {t: [] for t in (125, 250, 375, 999)}
    wl = [0, 0]
    for m in maps:
        rows = [r for r in results if r["map"] == m]
        w = sum(1 for r in rows if r["bot_won"])
        wl[0] += w
        wl[1] += len(rows) - w
        ps = {}
        for t in (125, 250, 375, 999):
            rnd = t
            vals = [snap_at(r, min(r["last"], rnd))["p"] for r in rows if snap_at(r, min(r["last"], rnd))]
            ps[t] = sum(vals) / len(vals) if vals else float('nan')
            all_p[t] += vals
        print(f'{m:>16} {len(rows):>5} {w}-{len(rows)-w:<3} {ps[125]:6.3f} {ps[250]:6.3f} {ps[375]:6.3f} {ps[999]:6.3f}')
    print(f'\n{bot}: {wl[0]}-{wl[1]} wins  meanP:', {t: round(sum(v) / max(1, len(v)), 3) for t, v in all_p.items()})
    # feature diffs at final snapshot
    fd = {k: 0.0 for k in KEYS}
    nf = 0
    for r in results:
        s = snap_at(r, r["last"])
        if s:
            for k in KEYS:
                fd[k] += s["d"][k]
            nf += 1
    print('final feature diffs (bot-other):', {k: round(v / max(1, nf), 1) for k, v in fd.items()})


if __name__ == '__main__':
    main()
