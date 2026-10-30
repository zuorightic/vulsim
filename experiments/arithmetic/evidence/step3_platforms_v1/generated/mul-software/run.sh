#!/usr/bin/env bash
__vulsimgen_run_main() (
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "Building Main"
g++ -std=c++20 -g -O2 main.cpp -I. -o 'Main'
exec './Main' "$@"
)
__vulsimgen_run_dispatch() {
  local status
  if __vulsimgen_run_main "$@"; then status=0; else status=$?; fi
  unset -f __vulsimgen_run_main __vulsimgen_run_dispatch
  return "$status"
}
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  if __vulsimgen_run_dispatch "$@"; then return 0; else return $?; fi
fi
__vulsimgen_run_dispatch "$@"
exit $?
