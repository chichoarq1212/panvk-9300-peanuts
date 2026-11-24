#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path
from apply import patch

# Mirror the exact source formatting from Mesa 5a07217 and the v11 patch series.
tex_source = """\
    nir_def *val = nir_load_global_cvt_pan(b, tex->def.num_components,
                                           tex->def.bit_size, addr, cvt,
                                           tex->dest_type);
   nir_def *val = nir_load_global_cvt_pan(b, tex->def.num_components,
                                          tex->def.bit_size, addr, cvt,
                                          tex->dest_type);
"""
compiler_source = """\
    bi_instr *I =
       bi_ld_cvt_to(b, dst, bi_extract(b, addr, 0), bi_extract(b, addr, 1), icd,
                    bi_reg_fmt_for_nir(nir_intrinsic_dest_type(instr)),
                    instr->def.num_components - 1);
"""
tex, comp = patch(tex_source, compiler_source)
assert tex.count("AUTO32: preserve integer texel-buffer payload bits") == 2
assert tex.count("load_type);") == 2
assert "tex->dest_type == nir_type_float32 && tex->def.bit_size == 32" in tex
assert comp.count("dest_type == 32 ? BI_REGISTER_FORMAT_AUTO") == 1
assert "bi_reg_fmt_for_nir(dest_type)" in comp

# Compile the exact AUTO32 selection policy. Every regular format must remain
# untouched; only NIR's 32 pseudo-type maps to the hardware AUTO register mode.
src = r'''
#include <assert.h>
enum { AUTO=0, F16=1, F32=2, S16=3, U16=4, S32=5, U32=6 };
static int choose(int t) { return t == 32 ? AUTO : t; }
int main(void) {
    assert(choose(32)==AUTO);
    assert(choose(F16)==F16);
    assert(choose(F32)==F32);
    assert(choose(S16)==S16);
    assert(choose(U16)==U16);
    assert(choose(S32)==S32);
    assert(choose(U32)==U32);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/"auto32.c"
    p.write_text(src)
    subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror",str(p),"-o",str(p.with_suffix(""))],check=True)
    subprocess.run([str(p.with_suffix(""))],check=True)

for bad_tex,bad_comp in [("",compiler_source),(tex_source,""),(tex_source+"\\n"+tex_source,compiler_source)]:
    try:
        patch(bad_tex,bad_comp)
    except ValueError:
        pass
    else:
        raise AssertionError("patch accepted unexpected source anchors")
print("E04: AUTO32 selection and source-anchor regression tests passed (host tests only)")
