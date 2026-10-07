// Minimal blob-economy policy — the clean-room control experiment.
// Doctrine: forage nearest seen pearl/bed, split len-2 child at len>=4 the
// moment it's legal, suicide in place when trapped inside the blob.
// No hunts, escorts, queen roles, sonar, portals, lookahead.
#pragma once
#include "common.hpp"
#include "nav.hpp"
#include "world.hpp"
#include <algorithm>
#include <vector>

namespace bc {

struct Choice {
    bool split = false;
    int dir = 0;
    int n = 0;
    int dest = -1;
    bool eat = false;
    double score = 0;
    std::string why;
    std::string sprint;
    bool terminal = false;
    double stepTerm = 0;
    int newL = 0;
    std::string path;
    bool midEat = false;
    int pathCost = 0;
};

class Policy {
  public:
    Policy(World& w, Params const& p, double, Out& out)
        : w_(w), p_(p), out_(out) {}

    int depthReached() const { return 0; }
    std::string dbg() const { return " blob"; }

    Choice decide() {
        Board const& b = w_.board;
        Choice c;

        // passable = in-bounds, not own body, not another dragon
        std::vector<int> blk(b.NC, 0);
        for (int x : w_.body) blk[x] = INF;
        for (int x : w_.ownExtra) blk[x] = INF;
        for (int i = 0; i < b.NC; i++)
            if (w_.occ[i] >= 0) blk[i] = INF;  // never ram anything

        auto freeAt = [&](int cell, int arr) {
            return cell >= 0 && blk[cell] <= arr;
        };

        // 1) Split the moment it's legal: len>=4, units under cap, child's head
        //    cell able to walk out.
        int L = w_.t.length;
        if (L >= 4 && w_.t.units < w_.init.unitLimit && w_.bodyKnown()) {
            int n = L / 2, keep = L - n;
            int chead = w_.body[keep];
            auto inSeg = [&](int cell, int lo, int hi) {
                for (int i = lo; i < hi; i++) if (w_.body[i] == cell) return true;
                return false;
            };
            bool roomy = false;
            for (int d = 0; d < 4; d++) {
                int nc = b.nb[chead * 4 + d];
                if (nc >= 0 && !inSeg(nc, 0, keep) && !inSeg(nc, keep, L)
                    && w_.occ[nc] < 0) roomy = true;
            }
            if (roomy) {
                // enemy adjacent: don't split under the knife
                bool danger = false;
                for (auto const& s : w_.others)
                    if (s.team != w_.init.team && b.cheb(s.head, w_.head) <= 1) danger = true;
                if (!danger) {
                    c.split = true; c.n = n; c.why = "split";
                    return c;
                }
            }
        }

        // 2) Adjacent pearl: eat it.
        for (int d = 0; d < 4; d++) {
            int ncell = b.nb[w_.head * 4 + d];
            if (freeAt(ncell, 1) && w_.seenPearl[ncell]) {
                c.dir = d; c.dest = ncell; c.eat = true; c.why = "eat";
                return c;
            }
        }

        // 3) BFS to nearest food (seen pearl or imminent bed), else nearest
        //    unseen cell.
        Nav nav;
        nav.bfs(b, w_.head, blk, 30);
        auto stepToward = [&](int tgt) -> int {
            int cur = tgt;
            while (nav.dist[cur] > 1) {
                int nxt = -1;
                for (int d = 0; d < 4; d++) {
                    int n = b.nb[cur * 4 + d];
                    if (n >= 0 && nav.dist[n] == nav.dist[cur] - 1) { nxt = n; break; }
                }
                if (nxt < 0) return -1;
                cur = nxt;
            }
            for (int d = 0; d < 4; d++)
                if (b.nb[w_.head * 4 + d] == cur) return d;
            return -1;
        };

        int best = -1, bestD = INF;
        for (int i = 0; i < b.NC; i++) {
            if (nav.dist[i] == INF) continue;
            bool food = w_.seenPearl[i] || (w_.next[i] >= 0 && w_.next[i] <= 4);
            if (food && nav.dist[i] < bestD) { best = i; bestD = nav.dist[i]; }
        }
        if (best >= 0) {
            int d = stepToward(best);
            if (d >= 0) { c.dir = d; c.dest = b.nb[w_.head * 4 + d]; c.why = "forage"; return c; }
        }

        // 4) Explore: nearest never-seen cell.
        best = -1; bestD = INF;
        for (int i = 0; i < b.NC; i++) {
            if (nav.dist[i] == INF || w_.seenRound[i] >= 0) continue;
            if (nav.dist[i] < bestD) { best = i; bestD = nav.dist[i]; }
        }
        if (best >= 0) {
            int d = stepToward(best);
            if (d >= 0) { c.dir = d; c.dest = b.nb[w_.head * 4 + d]; c.why = "explore"; return c; }
        }

        // 5) Idle: any legal step; if none, die-in-place (feed the blob).
        for (int d = 0; d < 4; d++)
            if (freeAt(b.nb[w_.head * 4 + d], 1)) {
                c.dir = d; c.dest = b.nb[w_.head * 4 + d]; c.why = "wander";
                return c;
            }
        // trapped: reverse into the neck — nva death drops our pearls here.
        c.dir = w_.t.dir ^ 2;
        c.dest = b.nb[w_.head * 4 + c.dir];
        c.why = "die";
        return c;
    }

  private:
    World& w_;
    Params const& p_;
    Out& out_;
};

}  // namespace bc
