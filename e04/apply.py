#!/usr/bin/env python3
"""E04: preserve 32-bit texel-buffer bits for float32 guest reads (AUTO32)."""
import argparse
import re
from pathlib import Path

TEXEL_RE = re.compile(
    r"(?m)^([ \t]*)nir_def \*val = nir_load_global_cvt_pan\(b, tex->def.num_components,\n"
    r"[ \t]*tex->def.bit_size, addr, cvt,\n"
    r"[ \t]*tex->dest_type\);"
)
LOAD_CVT_RE = re.compile(
    r"(?m)^([ \t]*)bi_instr \*I =\n"
    r"[ \t]*bi_ld_cvt_to\(b, dst, bi_extract\(b, addr, 0\), "
    r"bi_extract\(b, addr, 1\), icd,\n"
    r"[ \t]*bi_reg_fmt_for_nir\(nir_intrinsic_dest_type\(instr\)\),\n"
    r"[ \t]*instr->def\.num_components - 1\);"
)

def patch(tex, compiler):
    def texel_replacement(m):
        i = m.group(1)
        return (
            f"{i}nir_alu_type load_type =\n"
            f"{i}   (tex->dest_type == nir_type_float32 && tex->def.bit_size == 32)\n"
            f"{i}      ? 32 /* AUTO32: preserve integer texel-buffer payload bits */\n"
            f"{i}      : tex->dest_type;\n"
            f"{i}nir_def *val = nir_load_global_cvt_pan(b, tex->def.num_components,\n"
            f"{i}                                       tex->def.bit_size, addr, cvt,\n"
            f"{i}                                       load_type);"
        )

    def load_replacement(m):
        i = m.group(1)
        return (
            f"{i}nir_alu_type dest_type = nir_intrinsic_dest_type(instr);\n"
            f"{i}enum bi_register_format regfmt =\n"
            f"{i}   dest_type == 32 ? BI_REGISTER_FORMAT_AUTO : bi_reg_fmt_for_nir(dest_type);\n\n"
            f"{i}bi_instr *I =\n"
            f"{i}   bi_ld_cvt_to(b, dst, bi_extract(b, addr, 0), bi_extract(b, addr, 1), icd,\n"
            f"{i}                regfmt, instr->def.num_components - 1);"
        )

    tex, ntex = TEXEL_RE.subn(texel_replacement, tex)
    comp, ncomp = LOAD_CVT_RE.subn(load_replacement, compiler)
    if ntex != 2:
        raise ValueError(f"texel-buffer lowering: expected 2 anchors, found {ntex}")
    if ncomp != 1:
        raise ValueError(f"LD_CVT emitter: expected 1 anchor, found {ncomp}")
    return tex, comp

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mesa", type=Path)
    args = p.parse_args()
    tex_path = args.mesa / "src/panfrost/compiler/pan_nir_lower_tex.c"
    comp_path = args.mesa / "src/panfrost/compiler/bifrost/bifrost_compile.c"
    tex, comp = patch(tex_path.read_text(), comp_path.read_text())
    tex_path.write_text(tex)
    comp_path.write_text(comp)
    print("E04: Bifrost + Valhall float32 texelFetch uses AUTO32; other formats/types unchanged")

if __name__ == "__main__":
    main()
