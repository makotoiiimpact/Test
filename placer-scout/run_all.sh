#!/usr/bin/env bash
# Rebuild placer-scout outputs from the downloaded data in data/.
# Downloads (run once): src/fetch_vectors.py, src/prep_sources.py, src/dem.py, src/rain.py, src/storms.py, src/mrms.py,
#                       src/s2_select.py, src/s2_alteration.py
set -euo pipefail
cd "$(dirname "$0")"
python3 src/hydro.py                       # drainage network (both windows)
python3 src/score.py                       # score every wash cell
python3 src/history.py                     # old-report placer-history factor (re-scores)
rm -f data/lidar_rejected.csv
for i in 1 2 3 4 5 6; do                   # pick top 25, check traps with 1 m lidar, replace rejected spots
  python3 src/select_targets.py
  n=$(python3 src/lidar.py | grep LIDAR_REJECTED_THIS_ROUND | awk '{print $2}')
  echo "lidar round $i rejected $n"; [ "$n" = "0" ] && break
done
python3 src/s2_change.py                   # before/after storm hint
python3 src/finalize.py                    # final ranking
python3 src/build_map.py
python3 src/report.py > /dev/null
echo "done: out/targets.csv out/map.html out/REPORT.md"
