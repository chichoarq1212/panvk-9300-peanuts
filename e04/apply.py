#!/usr/bin/env python3
"""E04: preserve 32-bit texel-buffer bits for float32 guest reads (AUTO32)."""
import argparse
import re
from pathlib import Path

TEXEL_CALL = """nir_def *val = nir_load_global_cvt_pan(b, tex->def.num_components,
                                           tex->def.bit_size, addr, cvt,
                                           tex->dest_type);"""
TEXEL_REPLACEMENT = """nir_alu_type load_type =
      (tex->dest_type == nir_type_float32 && tex->def.bit_size == 32)
         ? 32 /* AUTO32: preserve integer texel-buffer payload bits */
         : tex->dest_type;
   nir_def *val = nir_load_global_cvt_pan(b, tex->def.num_components,
                                          tex->def.bit_size, addr, cvt,
                                          load_type);"""

LOAD_CVT = """   bi_instr *I =
      bi_ld_cvt_to(b, dst, bi_extract(b, addr, 0), bi_extract(b, addr, 1), icd,
                   bi_reg_fmt_for_nir(nir_intrinsic_dest_type(instr)),
                   instr->def.num_components - 1);"""
LOAD_CVT_REPLACEMENT = """   nir_alu_type dest_type = nir_intrinsic_dest_type(instr);
   enum bi_register_format regfmt =
      dest_type == 32 ? BI_REGISTER_FORMAT_AUTO : bi_reg_fmt_for_nir(dest_type);

   bi_instr *I =
      bi_ld_cvt_to(b, dst, bi_extract(b, addr, 0), bi_extract(b, addr, 1), icd,
                   regfmt, instr->def.num_components - 1);"""

def once(s, old, new, n, label):
    count=s.count(old)
    if count != n:
        raise ValueError(f"{label}: expected {n} anchors, found {count}")
    return s.replace(old,new)

def patch(tex, compiler):
    # Both Bifrost and Valhall texel-buffer lowering paths must agree.
    tex=once(tex,TEXEL_CALL,TEXEL_REPLACEMENT,2,"texel-buffer lowering")
    # Only this load intrinsic accepts the AUTO32 pseudo-type. Other loads
    # continue to select their exact float/signed/unsigned register format.
    compiler=once(compiler,LOAD_CVT,LOAD_CVT_REPLACEMENT,1,"LD_CVT emitter")
    return tex,compiler

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mesa",type=Path)
    args=p.parse_args()
    tex_path=args.mesa/"src/panfrost/compiler/pan_nir_lower_tex.c"
    comp_path=args.mesa/"src/panfrost/compiler/bifrost/bifrost_compile.c"
    tex,comp=patch(tex_path.read_text(),comp_path.read_text())
    tex_path.write_text(tex)
    comp_path.write_text(comp)
    print("E04: Bifrost + Valhall float32 texelFetch uses AUTO32; other formats/types unchanged")

if __name__=="__main__":
    main()
