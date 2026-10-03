#pragma once

#include "board.hpp"

namespace bc {

// Time-aware search on the torus. blk[c] is the earliest move number at which the
// head may enter tile c (0/1 = free now, INF = never within the horizon). Own
// segment i of a body of length L frees after L - i moves, so it gets L - i + 1:
// the engine checks the destination before the tail moves ("tail included").
struct Scan {
    int cells = 0;
    bool cycle = false;      // a loop exists inside the scanned region
    bool exhausted = false;  // the whole region was scanned (not cut by limit)
};

struct Nav {
    std::vector<int> dist;
    std::vector<int> queue;
    std::vector<int> parent;

    // Distances from start (0 at start). Tiles never reached stay INF.
    void bfs(Board const& b, int start, std::vector<int> const& blk, int horizon) {
        dist.assign(b.NC, INF);
        queue.clear();
        dist[start] = 0;
        queue.push_back(start);
        for (size_t qi = 0; qi < queue.size(); qi++) {
            int c = queue[qi];
            int nd = dist[c] + 1;
            if (nd > horizon) continue;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[c * 4 + d];
                if (n < 0 || dist[n] != INF || blk[n] > nd) continue;
                dist[n] = nd;
                queue.push_back(n);
            }
        }
    }

    // How many tiles the head can reach, stopping once `limit` is hit.
    int flood(Board const& b, int start, std::vector<int> const& blk, int limit) {
        dist.assign(b.NC, INF);
        queue.clear();
        dist[start] = 0;
        queue.push_back(start);
        for (size_t qi = 0; qi < queue.size(); qi++) {
            if (static_cast<int>(queue.size()) >= limit) break;
            int c = queue[qi];
            int nd = dist[c] + 1;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[c * 4 + d];
                if (n < 0 || dist[n] != INF || blk[n] > nd) continue;
                dist[n] = nd;
                queue.push_back(n);
            }
        }
        return static_cast<int>(queue.size()) - 1;  // not counting the head's own tile
    }

    // Region reachable from `start` while `wall` cells stay walls forever
    // (wall[n] != 0 = blocked). Unlike flood() there is no time axis: this is
    // the room a dead end really has, because a cell our own body plugs never
    // frees while the head cannot advance. Stops at `limit` cells. `cycle`
    // fires when a reached cell is seen through a second path: a loop the
    // dragon can circle instead of dying at a leaf.
    Scan deadEnd(Board const& b, int start, std::vector<int> const& wall, int limit) {
        Scan s;
        dist.assign(b.NC, INF);
        parent.assign(b.NC, -1);
        queue.clear();
        dist[start] = 0;
        queue.push_back(start);
        size_t qi = 0;
        for (; qi < queue.size(); qi++) {
            int c = queue[qi];
            for (int d = 0; d < 4; d++) {
                int n = b.nb[c * 4 + d];
                if (n < 0 || wall[n] != 0) continue;
                if (dist[n] == INF) {
                    dist[n] = dist[c] + 1;
                    parent[n] = c;
                    queue.push_back(n);
                } else if (parent[c] != n) {
                    s.cycle = true;  // second path into a reached cell: a loop
                }
            }
            if (static_cast<int>(queue.size()) >= limit) break;
        }
        s.cells = static_cast<int>(queue.size());
        s.exhausted = qi == queue.size();
        return s;
    }
};

// blk for a body (head first, possibly only a known prefix) of true length L,
// on top of a base grid of other dragons.
inline void markBody(std::vector<int>& blk, std::vector<int> const& body, int L) {
    int n = std::min(static_cast<int>(body.size()), L);
    for (int i = 0; i < n; i++) blk[body[i]] = std::max(blk[body[i]], L - i + 1);
}

}  // namespace bc
