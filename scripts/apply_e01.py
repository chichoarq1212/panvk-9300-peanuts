#!/usr/bin/env python3
"""E01: diagnostic guard for meta descriptor copies on PAN_ARCH 12."""
import argparse
from pathlib import Path
import re

MARK = 'PANVK9300_E01'
TARGET = 'src/panfrost/vulkan/panvk_vX_cmd_meta.c'

def transform(s):
    if MARK in s:
        raise ValueError('E01 already applied')
    anchor = '#include "panvk_cmd_meta.h"'
    if s.count(anchor) != 1:
        raise ValueError('unexpected include anchor')
    s = s.replace(anchor, anchor + '\n#if PAN_ARCH == 12\n#include <stdio.h>\n#include <stdlib.h>\n#endif', 1)
    for mode, count, pattern in (
        ('save', 'push_set0->desc_count', r'memcpy\(save_ctx->push_set0\.desc_storage,\s*push_set0->descs\.host,\s*push_set0->desc_count\s*\*\s*PANVK_DESCRIPTOR_SIZE\);'),
        ('restore', 'save_ctx->push_set0.desc_count', r'memcpy\(push_set0->descs\.host,\s*save_ctx->push_set0\.desc_storage,\s*save_ctx->push_set0\.desc_count\s*\*\s*PANVK_DESCRIPTOR_SIZE\);'),
    ):
        if len(list(re.finditer(pattern, s))) != 2:
            raise ValueError(f'{mode}: expected 2 semantic anchors')
        def insert(m):
            log_count = "(push_set0 ? push_set0->desc_count : 0)" if mode == "save" else count
            return f'''/* {MARK}: reject invalid count rather than truncate. */
#if PAN_ARCH == 12
      if (!push_set0 || !push_set0->descs.host ||
          {count} > sizeof(save_ctx->push_set0.desc_storage) / PANVK_DESCRIPTOR_SIZE) {{
         fprintf(stderr, "{MARK} {mode} %s count=%u capacity=%zu\\n",
                 __func__, (unsigned)({log_count}),
                 sizeof(save_ctx->push_set0.desc_storage) / (size_t)PANVK_DESCRIPTOR_SIZE);
         fflush(stderr);
         abort();
      }}
#endif
      ''' + m.group(0)
        s = re.sub(pattern, insert, s)
    pattern = r'(panvk_per_arch\(CmdClearColorImage\)\([^{{]+\)\s*\{)'
    if len(re.findall(pattern, s)) != 1:
        raise ValueError('clear entrypoint anchor mismatch')
    s = re.sub(pattern, r'\1' + '''
#if PAN_ARCH == 12
   static unsigned e01_clear_calls;
   unsigned e01_call = __atomic_fetch_add(&e01_clear_calls, 1, __ATOMIC_RELAXED);
   if (e01_call < 32) {
      fprintf(stderr, "PANVK9300_E01 clear-color enter call=%u ranges=%u layout=%u\\\\n",
              e01_call, rangeCount, (unsigned)imageLayout);
      fflush(stderr);
   }
#endif
''', s, count=1)
    start = s.index('panvk_per_arch(CmdClearColorImage)')
    end = s.index('\n}', start)
    body = s[start:end]
    anchor = 'meta_gfx_end(cmdbuf, &save);'
    if body.count(anchor) != 1:
        raise ValueError('clear exit anchor mismatch')
    body = body.replace(anchor, anchor + '''
#if PAN_ARCH == 12
   if (e01_call < 32) {
      fprintf(stderr, "PANVK9300_E01 clear-color exit call=%u\\n", e01_call);
      fflush(stderr);
   }
#endif''')
    return s[:start] + body + s[end:]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('mesa', type=Path)
    args = p.parse_args()
    path = args.mesa / TARGET
    path.write_text(transform(path.read_text()))
    print('E01 applied: four guarded copies and clear trace')

if __name__ == '__main__':
    main()
