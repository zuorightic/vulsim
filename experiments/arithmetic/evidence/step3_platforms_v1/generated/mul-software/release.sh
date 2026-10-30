#!/bin/bash
echo "Building Main with O3 optimization"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pushd "$SCRIPT_DIR"
g++ -std=c++20 -O3 main.cpp -I. -o Main_O3
popd
