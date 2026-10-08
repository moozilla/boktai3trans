#!/bin/sh
# Fetch and build the pinned third-party tools into build/tools/.
# System packages needed (Debian/Ubuntu):
#   apt install build-essential cmake binutils-arm-none-eabi libmgba-dev python3-numpy python3-pil
#   pip install capstone
set -e
cd "$(dirname "$0")/.."
mkdir -p build/tools
cd build/tools

fetch() { # name url commit
    if [ ! -d "$1" ]; then git clone -q "$2" "$1"; fi
    git -C "$1" fetch -q origin "$3" 2>/dev/null || true
    git -C "$1" checkout -q "$3"
}

# gbadisasm (pret lineage): recursive-descent disassembler emitting reassemblable GNU as
fetch gbadisasm https://github.com/jiangzhengwenjz/gbadisasm.git 940def2c91d678ee671716b8b44a2223c0ff2c62
git -C gbadisasm apply --check ../../tools/patches/gbadisasm-no-assert.patch 2>/dev/null && \
    git -C gbadisasm apply ../../tools/patches/gbadisasm-no-assert.patch
make -s -C gbadisasm

# agbcc: the GCC 2.95-based compiler used by agbcc-era GBA games (matching decomp)
fetch agbcc https://github.com/pret/agbcc.git da598c1d918402c42c0c0d7128ba14567f3175e9
[ -x agbcc/agbcc ] || (cd agbcc && ./build.sh)

# armips: for translation hacks (patch assembly)
fetch armips https://github.com/Kingcom/armips.git 62adab4ef30da765f5cf22a451eb08a59c54dc8b
git -C armips submodule update -q --init --recursive
[ -x armips/build/armips ] || (mkdir -p armips/build && cd armips/build && cmake -DCMAKE_BUILD_TYPE=Release .. >/dev/null && make -s)

# mGBA harness
make -s -C ../../tools/emu

echo "tools ready in build/tools"
