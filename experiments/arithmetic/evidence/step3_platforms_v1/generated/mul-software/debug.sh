#!/bin/bash
echo "Building Main for debug with sanitizers"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pushd "$SCRIPT_DIR"
g++ -std=c++20 -g -O1 -fsanitize=address,undefined,leak -fno-omit-frame-pointer -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow -Wnull-dereference -Wdouble-promotion -Wformat=2 -Wundef -Wuninitialized -Werror main.cpp -I. -o Main_debug
popd
