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
        Policy policy(world, kParams, turnStart + BC_TURN_BUDGET);
        Choice c = policy.decide();
        if (c.split) {
            out.split(c.n);
            world.body.resize(std::max(2, world.t.length - c.n));
        } else if (!c.sprint.empty()) {
            out.moveSeq(c.sprint);  // sprint trade: we die with the target
        } else if (!c.path.empty()) {
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
        } else {
            out.move(c.dir);
            if (c.dest >= 0) world.advanceBody(c.dest, c.eat);
        }
        out.log("r" + std::to_string(turn.round) + " " + c.why +
                " depth=" + std::to_string(policy.depthReached()) +
                " ms=" + std::to_string(static_cast<int>((clockNow() - turnStart) * 1000)) +
                " L=" + std::to_string(turn.length) +
                " body=" + std::to_string(world.body.size()));
        out.flush();
    }
    return 0;
}
