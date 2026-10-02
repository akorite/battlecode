"""Minimal Cap'n Proto reader for the UNSW Battlecode .replay schema.

File format: gzip -> packed capnp -> single message with root struct Replay.
Schema (reconstructed from replay-viewer.vsix webview.js):

  Replay { formatVersion @0 :UInt32; union{ none@1:Void; seed@2:UInt64 }
           map @3 :Text; botA @4 :Text; botB @5 :Text;
           events @6 :List(Event); result @7 :GameResult; }   # dw=2,pc=5
  Event union (dw=1,pc=1): roundStart|turnStart|pearlCountdown|tileChange|
       dragonAction|engineLog|dragonLog|dragonIndicator|debugDraw|
       dragonUpdate|dragonSplit|dragonDeath|sonarPing
  Point {x,y:Int32}
  PlayerAction union (dw=1,pc=1): move:List(UInt16)|split:Int32@4|suicide
  EventDragonUpdate {id@0:Int32; facing@1:UInt16@4; head,tail:Point}
  EventDragonSplit {parentId,childId:Int32; team:UInt16@8; childFacing:UInt16@10;
                    parentBody,childBody:List(Point)}
  EventDragonDeath {id:Int32; reason:UInt16@4}
  EventSonarPing {senderId:Int32; direction:UInt16@4; union{noHit|hitId:Int32@12}@6;
                  value:UInt32@8; origin,end:Point; value64:UInt64@16; hitKind:UInt16@24}
  EventPearlCountdown/EventTileChange {tile:Point; countdown:Int32|hasPearl:Bool}
  EventDragonAction {id:Int32; action:PlayerAction; instructions:InstructionUsage; tle:Bool@32}
  Event*Log / Indicator {id:Int32; text:Text}
  EventDebugDraw {id:Int32; draw:DebugDraw}
  DebugDraw {shape:UInt16; from,to:Point; r,g,b:UInt8}
  GameResult {terminated:Bool@0; endReason:UInt16@2; union{noWinner|winner:UInt16@6}@4;
              teamA,teamB:TeamStanding}
  TeamStanding {dragonCount,longestDragon,totalLength:Int32}
"""
import gzip, struct
from dataclasses import dataclass

def depack(data: bytes) -> bytes:
    out = bytearray()
    i, n = 0, len(data)
    while i < n:
        tag = data[i]; i += 1
        if tag == 0:
            cnt = data[i]; i += 1
            out += b"\x00" * (8 + cnt * 8)
        elif tag == 0xFF:
            out += data[i:i + 8]; i += 8
            cnt = data[i]; i += 1
            nb = cnt * 8
            out += data[i:i + nb]; i += nb
        else:
            for b in range(8):
                if tag & (1 << b):
                    out.append(data[i]); i += 1
                else:
                    out.append(0)
    return bytes(out)

class Reader:
    def __init__(self, buf: bytes):
        self.buf = buf

    def u8(self, off): return self.buf[off]
    def u16(self, off): return struct.unpack_from('<H', self.buf, off)[0]
    def u32(self, off): return struct.unpack_from('<I', self.buf, off)[0]
    def i32(self, off): return struct.unpack_from('<i', self.buf, off)[0]
    def u64(self, off): return struct.unpack_from('<Q', self.buf, off)[0]

@dataclass
class Ptr:
    kind: int          # 0=struct 1=list 2=far
    seg: 'Seg'
    off: int           # byte offset of pointer
    raw: int

class Seg:
    def __init__(self, r: Reader, base: int):
        self.r = r; self.base = base

    def ptr(self, off):
        """Resolve pointer at absolute file offset off -> (kind, target_off, info)."""
        r = self.r
        p = r.u64(off)
        kind = p & 3
        if kind == 0:      # struct
            signed = p >> 2 & 0x3FFFFFFF
            if signed & 0x20000000: signed -= 0x40000000
            tgt = off + 8 + signed * 8
            dw = (p >> 32) & 0xFFFF; pc = (p >> 48) & 0xFFFF
            return ('struct', tgt, dw, pc)
        if kind == 1:      # list
            signed = p >> 2 & 0x3FFFFFFF
            if signed & 0x20000000: signed -= 0x40000000
            tgt = off + 8 + signed * 8
            esz = (p >> 32) & 7; cnt = (p >> 35) & 0x1FFFFFFF
            return ('list', tgt, esz, cnt)
        if kind == 2:      # far
            landing = (p >> 3) & 0x1FFFFFFF
            segid = (p >> 32) & 0xFFFFFFFF
            two = (p >> 2) & 1
            return ('far', landing * 8, two, segid)
        return ('capability', p >> 32, 0, 0)

class Msg:
    def __init__(self, packed: bytes):
        d = depack(packed)
        self.r = Reader(d)
        nsegs = self.r.u32(0) + 1
        self.seg_sizes = [self.r.u32(4 + 4 * i) for i in range(nsegs)]
        hdr = 4 + 4 * nsegs
        if nsegs % 2 == 0:
            hdr += 4
        self.seg_base = []
        off = hdr
        for s in self.seg_sizes:
            self.seg_base.append(off)
            off += s * 8
        self.seg = Seg(self.r, self.seg_base[0])

    def struct(self, off, dw, pc):
        return Struct(self, self.seg_base[0] + off, dw, pc)

    def root(self):
        kind, tgt, a, b = self.seg.ptr(self.seg_base[0])
        assert kind == 'struct'
        return Struct(self, tgt, a, b)

class Struct:
    def __init__(self, msg: Msg, off: int, dw: int, pc: int):
        self.m = msg; self.off = off; self.dw = dw; self.pc = pc

    # data section
    def bit(self, b): return (self.m.r.u8(self.off + b // 8) >> (b % 8)) & 1
    def u8(self, o): return self.m.r.u8(self.off + o)
    def u16(self, o): return self.m.r.u16(self.off + o)
    def u32(self, o): return self.m.r.u32(self.off + o)
    def i32(self, o): return self.m.r.i32(self.off + o)
    def u64(self, o): return self.m.r.u64(self.off + o)

    def poff(self, i): return self.off + self.dw * 8 + i * 8

    def is_null_ptr(self, i):
        return self.m.r.u64(self.poff(i)) == 0

    def get_struct(self, i, dw, pc):
        if self.is_null_ptr(i): return None
        kind, tgt, a, b = self.m.seg.ptr(self.poff(i))
        while kind == 'far':
            kind, tgt, a, b = self._far(tgt, a, b)
        assert kind == 'struct', kind
        return Struct(self.m, tgt, a, b)

    def _far(self, off_words8, two, segid):
        # only single-segment messages expected; support same-segment landing
        r = self.m.r
        landing = self.m.seg_base[segid] + off_words8 if segid < len(self.m.seg_base) else off_words8
        if two:
            kind, tgt, a, b = self.m.seg.ptr(landing)   # far ptr -> tag
            # landing is a far-far pointing to content pointer
            p = r.u64(landing)
            segid2 = (p >> 32) & 0xFFFFFFFF
            off2 = ((p >> 3) & 0x1FFFFFFF) * 8
            return self.m.seg.ptr(self.m.seg_base[segid2] + off2)
        else:
            return self.m.seg.ptr(landing)

    def get_list(self, i):
        if self.is_null_ptr(i): return []
        kind, tgt, esz, cnt = self.m.seg.ptr(self.poff(i))
        while kind == 'far':
            kind, tgt, esz, cnt = self._far(tgt, esz, cnt)
        assert kind == 'list'
        return List(self.m, tgt, esz, cnt)

    def get_text(self, i):
        if self.is_null_ptr(i): return ''
        kind, tgt, esz, cnt = self.m.seg.ptr(self.poff(i))
        while kind == 'far':
            kind, tgt, esz, cnt = self._far(tgt, esz, cnt)
        b = self.m.r.buf[tgt:tgt + cnt]
        return b.rstrip(b'\x00').decode('utf-8', 'replace')

class List:
    def __init__(self, msg, off, esz, cnt):
        self.m, self.off, self.esz, self.cnt = msg, off, esz, cnt
        if esz == 7:  # composite: tag word then elements
            tag = msg.r.u64(off)
            self.cnt = (tag >> 2) & 0x3FFFFFFF
            self.dw = (tag >> 32) & 0xFFFF
            self.pc = (tag >> 48) & 0xFFFF
            self.off = off + 8
            self.stride = (self.dw + self.pc) * 8

    def u16s(self):
        return [self.m.r.u16(self.off + 2 * i) for i in range(self.cnt)]

    def structs(self):
        for i in range(self.cnt):
            yield Struct(self.m, self.off + i * self.stride, self.dw, self.pc)

def load(path):
    data = open(path, 'rb').read()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    return Msg(data)
