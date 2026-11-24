#!/usr/bin/env python3
"""E03: experimental implicit FP32-to-FP16 RTZ on arch 12."""
import sys
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('e02_apply', Path(__file__).resolve().parents[1] / 'e02/apply.py')
e02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e02)
e02_patch = e02.patch
import re

ANCHOR = """      else if (instr->op == nir_op_f2f16_rtne)
         I->round = BI_ROUND_NONE; /* Nearest even */"""
EXTRA = """
      else if (b->shader->arch == 12 &&
               instr->op == nir_op_f2f16 &&
               !nir_is_rounding_mode_rtne(
                  b->shader->nir->info.float_controls_execution_mode, 16))
         I->round = BI_ROUND_RTZ; /* E03 experimental implicit conversion */"""

def transform(s):
    if s.count(ANCHOR) != 1 or EXTRA in s:
        raise ValueError('Unexpected FP16 conversion anchor')
    return s.replace(ANCHOR, ANCHOR + EXTRA)

def main():
    mesa = Path(sys.argv[1])
    root = mesa / 'src/panfrost/vulkan'
    names = ['panvk_descriptor_set_layout.h','panvk_cmd_desc_state.h','panvk_cmd_meta.h','panvk_vX_cmd_desc_state.c','panvk_vX_cmd_meta.c']
    for name, macro, value in [('panvk_image.h','PANVK_MAX_PLANES',3),('panvk_sampler.h','PANVK_MAX_DESCS_PER_SAMPLER',2)]:
        if not re.search(r'^#define\s+' + macro + r'\s+' + str(value) + r'\s*$', (root/name).read_text(), re.M):
            raise ValueError('Unexpected slot bound: ' + macro)
    out = e02_patch({name:(root/name).read_text() for name in names})
    compiler = mesa / 'src/panfrost/compiler/bifrost/bifrost_compile.c'
    changed = transform(compiler.read_text())
    for name, data in out.items():
        (root/name).write_text(data.replace('PANVK9300_E02','PANVK9300_E03'))
    compiler.write_text(changed)
    print('E03: arch12 implicit FP16 RTZ; explicit rounding preserved; E02 descriptor safeguards retained')

if __name__ == '__main__':
    main()
