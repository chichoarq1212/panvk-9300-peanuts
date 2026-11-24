#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path
from apply import transform, ANCHOR

original = """      if (instr->op == nir_op_f2f16_rtz)
         I->round = BI_ROUND_RTZ;
""" + ANCHOR
patched = transform(original)
assert patched.count('E03 experimental implicit conversion') == 1
for invalid in ('', original + original, patched):
    try:
        transform(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('Unexpected input accepted')
source = """
#include <assert.h>
enum {nir_op_f2f16, nir_op_f2f16_rtz, nir_op_f2f16_rtne};
enum {BI_ROUND_NONE, BI_ROUND_RTZ};
struct N {struct {unsigned float_controls_execution_mode;} info;};
struct S {int arch; struct N *nir;};
struct B {struct S *shader;};
struct Ins {int op;};
struct I {int round;};
static int nir_is_rounding_mode_rtne(unsigned mode, unsigned bits) {return bits == 16 && mode == 1;}
static int run(int arch, int op, unsigned mode, int initial) {
 struct N n = {{mode}}; struct S s = {arch, &n}; struct B builder = {&s}, *b = &builder;
 struct Ins ins = {op}, *instr = &ins; struct I inst = {initial}, *I = &inst;
""" + patched + """
 return I->round;
}
int main(void) {
 assert(run(12, nir_op_f2f16, 0, BI_ROUND_NONE) == BI_ROUND_RTZ);
 assert(run(12, nir_op_f2f16, 1, BI_ROUND_NONE) == BI_ROUND_NONE);
 assert(run(12, nir_op_f2f16_rtne, 0, BI_ROUND_RTZ) == BI_ROUND_NONE);
 assert(run(12, nir_op_f2f16_rtz, 1, BI_ROUND_NONE) == BI_ROUND_RTZ);
 assert(run(11, nir_op_f2f16, 0, BI_ROUND_NONE) == BI_ROUND_NONE);
 assert(run(13, nir_op_f2f16, 0, BI_ROUND_NONE) == BI_ROUND_NONE);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / 'test.c'
    p.write_text(source)
    subprocess.run(['cc','-std=c11','-Wall','-Werror',str(p),'-o',str(p.with_suffix(''))],check=True)
    subprocess.run([str(p.with_suffix(''))],check=True)
print('E03: six rounding cases and three invalid-input cases passed (host stub, not GPU)')
