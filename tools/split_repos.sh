#!/usr/bin/env bash
# Split this repository into a public learner repo and a private instructor repo (committed files only).
#   tools/split_repos.sh <public_dir> <private_dir>
# Public copy: no answer keys, exam parameters, transfer generator or instructor pack. Private copy: everything committed.
set -euo pipefail
PUB=${1:?public dir}; PRIV=${2:?private dir}
SRC=$(cd "$(dirname "$0")/.." && pwd)
for d in "$PUB" "$PRIV"; do [ -e "$d" ] && { echo "$d exists — choose a new folder"; exit 1; }; done
mkdir -p "$PUB" "$PRIV"
git -C "$SRC" archive HEAD | tar -x -C "$PRIV"
git -C "$SRC" archive HEAD | tar -x -C "$PUB"
rm -rf "$PUB/instructor/pack" "$PUB/instructor/exam_config.py" "$PUB/instructor/transfer_gen.py"
rm -f "$PUB/tools/instructor_pack.py"
# safety net: fail if anything instructor-only leaked into the public copy
if grep -rIl --exclude=split_repos.sh -e "INSTRUCTOR ONLY" -e "EXAM_SEEDS" -e "transfer_gen import" "$PUB" | grep -v "datagen/generate.py"; then
  echo "^ instructor-only content found in $PUB — aborting"; exit 1
fi
for d in "$PUB" "$PRIV"; do (cd "$d" && git init -q -b main && git add -A && git commit -qm "Initial import" && echo "ready: $d"); done
