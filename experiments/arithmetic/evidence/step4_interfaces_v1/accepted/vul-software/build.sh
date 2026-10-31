#!/bin/bash
echo "Building Main"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pushd "$SCRIPT_DIR"
g++ -std=c++20 -g -O2 main.cpp -I. -o Main
popd
