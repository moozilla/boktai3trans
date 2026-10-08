#!/usr/bin/env python3
"""Decompilation progress: functions/bytes in src/*.c vs all code.

  progress.py            human-readable summary
  progress.py --json F   objdiff-style report (schema-ish v2) for decomp.dev
"""
import json
import re
import sys

from romlib import ROOT
from split import c_functions
import glob
import os


def main():
    code = open(os.path.join(ROOT, "build", "asm", "code_sym.s")).read()
    funcs = [(n, int(a, 16)) for n, a in re.findall(r"^(\w+): @ 0x([0-9A-F]{8})", code, re.M)]
    funcs.sort(key=lambda x: x[1])
    code_end = 0x0824DAFA
    sizes = {}
    for (n, a), nxt in zip(funcs, funcs[1:] + [(None, code_end)]):
        sizes[n] = nxt[1] - a
    done = set()
    for p in glob.glob(os.path.join(ROOT, "src", "**", "*.c"), recursive=True):
        done |= set(c_functions(p, with_asm=False))
    total_b = sum(sizes.values())
    done_b = sum(sizes.get(n, 0) for n in done)
    print(f"functions: {len(done)}/{len(funcs)} ({100 * len(done) / len(funcs):.2f}%)")
    print(f"code bytes: {done_b}/{total_b} ({100 * done_b / total_b:.3f}%)")
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        rep = {"measures": {
            "total_code": str(total_b), "matched_code": str(done_b),
            "matched_code_percent": 100 * done_b / total_b,
            "total_functions": len(funcs), "matched_functions": len(done),
            "matched_functions_percent": 100 * len(done) / len(funcs),
            "complete_code": str(done_b), "complete_code_percent": 100 * done_b / total_b,
        }, "units": []}
        json.dump(rep, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
