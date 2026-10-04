#!/bin/bash
# Fire challenge batches, respecting the hourly game-start cap.
# Usage: batch_challenge.sh  — posts the queue below, one battle at a time,
# retrying after the 429 refill delay.
cd ~/bc
declare -a Q=("837 ranked" "919 ranked" "141 ranked" "742 ranked" "952 unranked" "507 unranked" "791 unranked" "501 unranked" "538 unranked" "31 unranked")
for item in "${Q[@]}"; do
  t=${item% *}; r=${item#* }
  flag=""; [ "$r" = "ranked" ] && flag="--ranked"
  out=$(python3 tooling/challenge.py post --team $t --n 1 $flag 2>&1 | tail -1)
  echo "$(date -u +%H:%M) team=$t $r -> $out"
  if echo "$out" | grep -q "429"; then
    echo "quota — sleeping 35min then retrying"
    sleep 2100
    out=$(python3 tooling/challenge.py post --team $t --n 1 $flag 2>&1 | tail -1)
    echo "$(date -u +%H:%M) retry team=$t $r -> $out"
  fi
  sleep 3
done
