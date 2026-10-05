// Every dragon runs its own copy of this program. Each turn: read what the dragon
// sees (io.hpp), update what it knows about the map (world.hpp), pick an action
// (policy.hpp) and write it out in a single write.
#include <cstring>

#include "io.hpp"
#include "policy.hpp"
#include "world.hpp"

int main() {
    using namespace bc;
    clockNow();  // start the meter: setup on the first turn counts against it
    std::setvbuf(stdout, nullptr, _IOFBF, 1 << 16);
    Reader in;
    Init init;
    if (!readInit(in, init)) return 0;

    World world;
    world.start(init);
    Out out;
    Turn turn;
    bool first = true;
    while (readTurn(in, turn)) {
        // The first turn's clock started with the process (setup counts); later ones on arrival.
        double turnStart = first ? 0.0 : clockNow();
        first = false;
        world.observe(turn, kParams);
        Policy policy(world, kParams, turnStart + BC_TURN_BUDGET, out);
        Choice c = policy.decide();
        if (c.split) {
            out.split(c.n);
            world.body.resize(std::max(2, world.t.length - c.n));
        } else if (!c.sprint.empty()) {
            out.moveSeq(c.sprint);  // sprint trade: we die with the target
        } else {
            // Safety net (scoped): the guard only runs in the opening and for the
            // champion. v106/v112 guarded every dragon at every round — the local
            // firing census shows ~300-1200 selfguard redirects per game, all on
            // non-queen dragons at rounds 320+, which silently blocked v104's
            // boxed-in feed deaths beside the champion (longest dragon at r499
            // fell 30.8 -> 13). Workers must be allowed to die for the feed after
            // the opening; the queen keeps her cover for the whole game.
            bool guardOn = (turn.round < 40) || (world.init.id == world.champId());
            // Safety net: never emit a first step that is provably fatal — across
            // a seen-kelp edge (nb < 0) or into our own tracked body — whatever
            // produced the choice (post-split geometry, trapped fallbacks, stale
            // path verification). Redirect to the first free exit when one exists;
            // otherwise the step was doomed anyway so nothing is lost.
            auto ownSeg = [&](int cell) {
                for (int x : world.body) if (x == cell) return true;
                for (int x : world.ownExtra) if (x == cell) return true;
                return false;
            };
            auto safeFirst = [&](int dir) -> int {
                int dest = dir >= 0 ? world.board.nb[world.head * 4 + dir] : -1;
                if (dest >= 0 && !ownSeg(dest)) return dir;
                for (int off : {0, 1, 3, 2}) {
                    int d = dir >= 0 ? (dir + off) & 3 : off;
                    int n = world.board.nb[world.head * 4 + d];
                    if (n >= 0 && !ownSeg(n) && world.occ[n] < 0) return d;
                }
                return -1;  // no free exit: keep the original (doomed) step
            };
            if (!c.path.empty()) {
                int d0 = dirFromChar(c.path[0]);
                int safe = guardOn ? safeFirst(d0) : d0;
                if (safe >= 0 && safe != d0) {
                    out.move(safe);  // path's first step was fatal: take the exit instead
                    out.log("wallguard " + std::to_string(turn.round));
                    int nxt = world.board.nb[world.head * 4 + safe];
                    if (nxt >= 0) world.advanceBody(nxt, c.midEat);
                } else {
                    out.moveSeq(c.path);  // free multi-step move along the planned path
                    int head = world.head;
                    int pay = c.pathCost;
                    for (size_t i = 0; i < c.path.size(); i++) {
                        int d = dirFromChar(c.path[i]);
                        if (d < 0) break;
                        int nxt = world.board.nb[head * 4 + d];
                        if (nxt < 0) break;  // should not happen; the path was verified
                        world.advanceBody(nxt, i == 0 ? c.midEat : c.eat);
                        if (i > 0 && pay-- > 0 && world.body.size() > 2) world.body.pop_back();
                        head = nxt;
                    }
                }
            } else {
                int safe = (guardOn && c.why != "scout") ? safeFirst(c.dir) : c.dir;
                if (safe >= 0 && safe != c.dir) {
                    out.log("selfguard " + std::to_string(turn.round));
                    c.dir = safe;
                }
                out.move(c.dir);
                int dest = world.board.nb[world.head * 4 + c.dir];
                if (dest >= 0) world.advanceBody(dest, c.eat);
            }
        }
        out.log("r" + std::to_string(turn.round) + " " + c.why +
                " depth=" + std::to_string(policy.depthReached()) +
                " ms=" + std::to_string(static_cast<int>((clockNow() - turnStart) * 1000)) +
                " L=" + std::to_string(turn.length) +
                " body=" + std::to_string(world.body.size())
#ifdef BC_DEBUG
                + policy.dbg()
#endif
                );
        out.flush();
    }
    return 0;
}
// v168
// v176
