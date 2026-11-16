#!/usr/bin/env bash
# One command to regenerate data, prove every planted anomaly, regression-check every recipe and build the site.
#   ./build.sh            full pipeline
#   ./build.sh --serve    full pipeline, then preview at http://127.0.0.1:8000
#   ./build.sh --quick    skip data regeneration (uses existing data/)
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
step() { printf '\n\033[1;34m▶ %s\033[0m\n' "$*"; }
QUICK=0; SERVE=0
for arg in "$@"; do case $arg in --quick) QUICK=1;; --serve) SERVE=1;; esac; done

if [ $QUICK -eq 0 ]; then
  EXTRA=""
  [ -f instructor/exam_config.py ] && EXTRA="$EXTRA --exam"
  [ -f instructor/transfer_gen.py ] && EXTRA="$EXTRA --transfer"
  step "1/6 Generate datasets (retail, finance${EXTRA:+, instructor:$EXTRA})"
  $PY -m datagen.generate --with-truth $EXTRA
  $PY -m datagen.docs
fi
step "2/6 Tests (anomaly proofs + cross-platform hashes)"
$PY -m pytest -q
step "3/6 Anomaly register (every planted issue within band)"
$PY -m validator.register
step "4/6 Recipe regression checks"
fails=0
for b in toolkit/baselines/*.metrics.json; do
  c=$(basename "$b" .metrics.json)
  if $PY -m toolkit.run "toolkit/configs/$c.yaml" --check-baseline >/dev/null 2>&1; then echo "  ok   $c"; else echo "  FAIL $c"; fails=$((fails+1)); fi
done
[ $fails -eq 0 ] || { echo "$fails recipe(s) failed their baseline"; exit 1; }
step "5/6 Render lessons, quizzes and exercises from data"
$PY -m tools.build_site
step "6/6 Strict site build"
OUT=${SITE_DIR:-site}
mkdocs build --strict -q -d "$OUT"
echo -e "\n\033[1;32m✔ All checks passed. Site in $OUT/\033[0m"
[ $SERVE -eq 1 ] && mkdocs serve
exit 0
