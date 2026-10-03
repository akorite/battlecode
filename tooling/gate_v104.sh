#!/usr/bin/env bash
# Gate for abyss_v104: self-death check on all 17 maps + win-rate spot-check.
# Usage: gate_v106.sh <runner> <phase>   phase=deaths|wins
set -u
RUNNER="$1"; PHASE="$2"
MAPDIR=/home/ubuntu/bc/workspace/maps
ENGMAPS=/home/ubuntu/bc/engine/maps
OUT=/home/ubuntu/bc/results/gate-v104
mkdir -p "$OUT"

maps17() {
  for m in "$MAPDIR"/*.map "$ENGMAPS/help.map" "$ENGMAPS/queen_of_spades_but_she_ages.map"; do basename "$m" .map; done
}
mapfile() {
  local n="$1"
  [ -f "$MAPDIR/$n.map" ] && echo "$MAPDIR/$n.map" || echo "$ENGMAPS/$n.map"
}

case "$PHASE" in
deaths)
  for n in $(maps17); do
    f=$(mapfile "$n")
    "$RUNNER" "$f" --name-a abyss_v104 --name-b abyss_cf --seed 1 --replay "$OUT/d-$n-a.replay" >/dev/null 2>&1 &
    "$RUNNER" "$f" --name-a abyss_cf --name-b abyss_v104 --seed 2 --replay "$OUT/d-$n-b.replay" >/dev/null 2>&1 &
    while [ "$(jobs -r | wc -l)" -ge 6 ]; do wait -n; done
  done
  wait
  ;;
wins)
  for opp in cf combat; do
    for n in $(maps17); do
      f=$(mapfile "$n")
      "$RUNNER" "$f" --name-a abyss_v104 --name-b "abyss_$opp" --seed 3 --replay "$OUT/w-$n-$opp-a.replay" >/dev/null 2>&1 &
      "$RUNNER" "$f" --name-a "abyss_$opp" --name-b abyss_v104 --seed 4 --replay "$OUT/w-$n-$opp-b.replay" >/dev/null 2>&1 &
      while [ "$(jobs -r | wc -l)" -ge 6 ]; do wait -n; done
    done
  done
  wait
  ;;
control)
  for s in 1 2 3; do
    "$RUNNER" "$MAPDIR/small.map" --name-a abyss_v104 --name-b starter --seed $s --replay "$OUT/ctl-s$s.replay" >/dev/null 2>&1 &
  done
  wait
  ;;
esac
echo "phase $PHASE done"
