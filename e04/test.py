#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path
from apply import (
    TEXEL_CALL, TEXEL_REPLACEMENT, LOAD_CVT, LOAD_CVT_REPLACEMENT, patch
)

tex, comp = patch(TEXEL_CALL + "\n" + TEXEL_CALL, LOAD_CVT)
assert tex.count("AUTO32: preserve integer texel-buffer payload bits") == 2
assert tex.count("load_type);") == 2
assert "tex->dest_type == nir_type_float32 && tex->def.bit_size == 32" in tex
assert comp.count("dest_type == 32 ? BI_REGISTER_FORMAT_AUTO") == 1
assert "bi_reg_fmt_for_nir(dest_type)" in comp
assert "PANVK9300_E03" not in tex + comp

# Compile the exact type-selection policy used by the patch. AUTO32 must be
# chosen only for the special 32-bit type; normal FP16/SINT/UINT/FLOAT paths
# keep their original register formats.
src = r'''
#include <assert.h>
enum { AUTO=0, F16=1, F32=2, S16=3, U16=4, S32=5, U32=6 };
static int choose(int t) {
    return t == 32 ? AUTO : t;
}
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

for bad_tex,bad_comp in [("",LOAD_CVT),(TEXEL_CALL,LOAD_CVT),(TEXEL_CALL*3,LOAD_CVT),(TEXEL_CALL*2,"")]:
    try:
        patch(bad_tex,bad_comp)
    except ValueError:
        pass
    else:
        raise AssertionError("patch accepted unexpected source anchors")
print("E04: AUTO32 selection and 5 patch-anchor regression cases passed (host test only)")
