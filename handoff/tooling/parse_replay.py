"""Parse a .replay file into structured events using the schema."""
import sys, json
from capnp_reader import load, Struct

TEAM = ['A', 'B']
DIR = ['N', 'E', 'S', 'W']
DEATH = ['hitWall', 'hitSelf', 'hitOtherBody', 'hitHeadToHead', 'noValidAction']
END_REASON = ['teamEliminated', 'roundLimit']
HIT_KIND = [None, 'empty', 'kelp', 'ally', 'allyHead', 'enemy', 'enemyHead']

EV_ROUND_START, EV_TURN_START, EV_PEARL_COUNTDOWN, EV_TILE_CHANGE, EV_DRAGON_ACTION, \
EV_ENGINE_LOG, EV_DRAGON_LOG, EV_DRAGON_INDICATOR, EV_DEBUG_DRAW, EV_DRAGON_UPDATE, \
EV_DRAGON_SPLIT, EV_DRAGON_DEATH, EV_SONAR_PING = range(13)

def point(s):
    return [s.i32(0), s.i32(4)] if s else None

def action(s: Struct):
    if s is None: return None
    w = s.u16(0)
    if w == 0:
        mv = s.get_list(0)
        steps = [DIR[v] for v in (mv.u16s() if mv else [])]
        return {'kind': 'move', 'steps': steps}
    if w == 1:
        return {'kind': 'split', 'childSegmentCount': s.i32(4)}
    if w == 2:
        return {'kind': 'suicide'}
    return {'kind': f'unknown{w}'}

def event(e: Struct, fmt_ver):
    w = e.u16(0)
    if w == EV_ROUND_START:
        s = e.get_struct(0, 1, 0); return {'type': 'roundStart', 'round': s.i32(0)}
    if w == EV_TURN_START:
        s = e.get_struct(0, 1, 0); return {'type': 'turnStart', 'id': s.i32(0)}
    if w == EV_PEARL_COUNTDOWN:
        s = e.get_struct(0, 1, 1); return {'type': 'pearlCountdown', 'tile': point(s.get_struct(0, 1, 0)), 'countdown': s.i32(0)}
    if w == EV_TILE_CHANGE:
        s = e.get_struct(0, 1, 1); return {'type': 'tileChange', 'tile': point(s.get_struct(0, 1, 0)), 'hasPearl': bool(s.bit(0))}
    if w == EV_DRAGON_ACTION:
        s = e.get_struct(0, 1, 2)
        d = {'type': 'dragonAction', 'id': s.i32(0)}
        a = s.get_struct(0, 1, 1)
        if a: d['action'] = action(a)
        ins = s.get_struct(1, 2, 0)
        if ins: d['instructions'] = {'count': ins.u64(0), 'exceeded': bool(ins.bit(64))}
        if s.bit(32): d['tle'] = True
        return d
    if w == EV_ENGINE_LOG:
        s = e.get_struct(0, 1, 1); return {'type': 'engineLog', 'id': s.i32(0), 'text': s.get_text(0)}
    if w == EV_DRAGON_LOG:
        s = e.get_struct(0, 1, 1); return {'type': 'dragonLog', 'id': s.i32(0), 'text': s.get_text(0)}
    if w == EV_DRAGON_INDICATOR:
        s = e.get_struct(0, 1, 1); return {'type': 'dragonIndicator', 'id': s.i32(0), 'text': s.get_text(0)}
    if w == EV_DEBUG_DRAW:
        s = e.get_struct(0, 1, 1)
        dr = s.get_struct(0, 1, 2)
        dd = None
        if dr:
            dd = {'shape': dr.u16(0), 'from': point(dr.get_struct(0, 1, 0)),
                  'to': point(dr.get_struct(1, 1, 0)),
                  'rgb': [dr.u8(2), dr.u8(3), dr.u8(4)]}
        return {'type': 'debugDraw', 'id': s.i32(0), 'draw': dd}
    if w == EV_DRAGON_UPDATE:
        s = e.get_struct(0, 1, 2)
        return {'type': 'dragonUpdate', 'id': s.i32(0), 'facing': DIR[s.u16(4)],
                'head': point(s.get_struct(0, 1, 0)), 'tail': point(s.get_struct(1, 1, 0))}
    if w == EV_DRAGON_SPLIT:
        s = e.get_struct(0, 2, 2)
        return {'type': 'dragonSplit', 'parentId': s.i32(0), 'childId': s.i32(4),
                'team': TEAM[s.u16(8)], 'childFacing': DIR[s.u16(10)],
                'parentBody': [point(p) for p in s.get_list(0).structs()] if not s.is_null_ptr(0) else [],
                'childBody': [point(p) for p in s.get_list(1).structs()] if not s.is_null_ptr(1) else []}
    if w == EV_DRAGON_DEATH:
        s = e.get_struct(0, 1, 0)
        return {'type': 'dragonDeath', 'id': s.i32(0), 'reason': DEATH[s.u16(4)]}
    if w == EV_SONAR_PING:
        s = e.get_struct(0, 4, 2)
        d = {'type': 'sonarPing', 'senderId': s.i32(0), 'direction': DIR[s.u16(4)],
             'origin': point(s.get_struct(0, 1, 0)), 'end': point(s.get_struct(1, 1, 0)),
             'hitKind': HIT_KIND[s.u16(24)]}
        if s.u16(6) == 1: d['hitId'] = s.i32(12)
        d['value'] = s.u64(16) if fmt_ver >= 2 else s.u32(8)
        return d
    return {'type': f'unknown{w}'}

def parse(path):
    m = load(path)
    r = m.root()
    fmt = r.u32(0)
    seed = r.u64(8) if r.u16(4) == 1 else None
    res_s = r.get_struct(4, 1, 2)
    result = None
    if res_s:
        result = {'terminated': bool(res_s.bit(0)), 'endReason': END_REASON[res_s.u16(2)],
                  'winner': TEAM[res_s.u16(6)] if res_s.u16(4) == 1 else None}
        for i, t in enumerate('AB'):
            ts = res_s.get_struct(i, 2, 0)
            if ts:
                result[f'team{t}'] = {'dragonCount': ts.i32(0), 'longestDragon': ts.i32(4), 'totalLength': ts.i32(8)}
    events = []
    ev = r.get_list(3)
    if ev:
        for e in ev.structs():
            events.append(event(e, fmt))
    return {
        'formatVersion': fmt, 'seed': seed,
        'map': r.get_text(0), 'botA': r.get_text(1), 'botB': r.get_text(2),
        'result': result, 'events': events,
    }

if __name__ == '__main__':
    p = parse(sys.argv[1])
    ev = p.pop('events')
    print(json.dumps(p, indent=1)[:3000])
    from collections import Counter
    print('events:', len(ev), Counter(e['type'] for e in ev))
    print('first events:', json.dumps(ev[:15]))
