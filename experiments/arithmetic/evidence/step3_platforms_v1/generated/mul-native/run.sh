#!/usr/bin/env bash
__vulrtlgen_run_main() (
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
mapfile -d '' RTL_FILES < <(find . -type f -name '*.sv' -not -path './obj_dir/*' -print0 | sort -z)
shopt -s nullglob
DRIVER_SOURCES=(./*.cpp)
shopt -u nullglob
if (( ${#RTL_FILES[@]} == 0 )); then
  echo 'No SystemVerilog files found in the output directory.' >&2
  exit 1
fi
if (( ${#DRIVER_SOURCES[@]} != 1 )); then
  echo "Expected exactly one top-level C++ test driver, found ${#DRIVER_SOURCES[@]}." >&2
  printf '  %s\n' "${DRIVER_SOURCES[@]}" >&2
  exit 1
fi
BUILD_LOG="$SCRIPT_DIR/verilator_build.log"
RUN_LOG="$SCRIPT_DIR/simulation.log"
DRIVER_SOURCE="${DRIVER_SOURCES[0]}"
echo "Building Verilator simulation; log: $BUILD_LOG"
if verilator --cc --exe --build --top-module MulProbe_sim_top --Mdir obj_dir -CFLAGS '-std=c++20' "${RTL_FILES[@]}" "$DRIVER_SOURCE" >"$BUILD_LOG" 2>&1; then
  :
else
  status=$?
  echo "Verilator build failed (exit $status); log: $BUILD_LOG" >&2
  cat "$BUILD_LOG" >&2
  exit "$status"
fi
echo "Running simulation; log: $RUN_LOG"
if "$SCRIPT_DIR/obj_dir/VMulProbe_sim_top" "$@" >"$RUN_LOG" 2>&1; then
  status=0
else
  status=$?
fi
cat "$RUN_LOG"
if (( status != 0 )); then
  echo "Simulation failed (exit $status); log: $RUN_LOG" >&2
fi
exit "$status"
)
__vulrtlgen_run_dispatch() {
  local status
  if __vulrtlgen_run_main "$@"; then status=0; else status=$?; fi
  unset -f __vulrtlgen_run_main __vulrtlgen_run_dispatch
  return "$status"
}
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  if __vulrtlgen_run_dispatch "$@"; then return 0; else return $?; fi
fi
__vulrtlgen_run_dispatch "$@"
exit $?
