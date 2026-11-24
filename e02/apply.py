#!/usr/bin/env python3
"""E02: distinguish API push-descriptor count from internal slot capacity."""
import argparse
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_e01 import transform as guard_meta

def once(s, old, new, n=1):
    if s.count(old) != n:
        raise ValueError(f'Expected {n} anchors: {old!r}; got {s.count(old)}')
    return s.replace(old, new)

def patch(files):
    layout = files['panvk_descriptor_set_layout.h']
    m = re.search(r'^#define MAX_PUSH_DESCS\s+32\s*$', layout, re.M)
    if not m or 'MAX_PUSH_DESC_STORAGE' in layout:
        raise ValueError('Unexpected API limit')
    # Keep the public Vulkan limit at 32. A combined image sampler may
    # occupy up to 3 texture and 2 sampler slots, plus one internal slot.
    layout = layout[:m.end()] + '\n#if PAN_ARCH == 12\n#define MAX_PUSH_DESC_STORAGE (MAX_PUSH_DESCS * 5 + 1)\n#else\n#define MAX_PUSH_DESC_STORAGE MAX_PUSH_DESCS\n#endif\n' + layout[m.end():]
    files['panvk_descriptor_set_layout.h'] = layout
    files['panvk_cmd_desc_state.h'] = once(files['panvk_cmd_desc_state.h'],
        'descs[MAX_PUSH_DESCS]', 'descs[MAX_PUSH_DESC_STORAGE]')
    files['panvk_cmd_meta.h'] = once(files['panvk_cmd_meta.h'],
        'desc_storage[MAX_PUSH_DESCS]', 'desc_storage[MAX_PUSH_DESC_STORAGE]', 2)
    # Reject oversized layouts before either descriptor writer touches storage.
    s = files['panvk_vX_cmd_desc_state.c']
    old = '   push_set->layout = set_layout;\n   push_set->desc_count = set_layout->desc_count;'
    guard = '''#if PAN_ARCH == 12
   if (set_layout->desc_count > MAX_PUSH_DESC_STORAGE) {
      vk_command_buffer_set_error(&cmdbuf->vk, VK_ERROR_UNKNOWN);
      return;
   }
#endif
'''
    # The first writer names its command buffer cmd, the template writer cmdbuf.
    if s.count(old) != 2:
        raise ValueError('Unexpected descriptor write anchors')
    a,b,c = s.split(old)
    if 'push_desc_set_write(struct panvk_cmd_buffer *cmd,' not in a or 'CmdPushDescriptorSetWithTemplate2KHR' not in b:
        raise ValueError('Unexpected descriptor write context')
    files['panvk_vX_cmd_desc_state.c'] = a + guard.replace('&cmdbuf->vk','&cmd->vk') + old + b + guard + old + c
    files['panvk_vX_cmd_meta.c'] = guard_meta(files['panvk_vX_cmd_meta.c']).replace('PANVK9300_E01','PANVK9300_E02')
    return files

def main():
    p = argparse.ArgumentParser()
    p.add_argument('mesa', type=Path)
    args = p.parse_args()
    root = args.mesa / 'src/panfrost/vulkan'
    names = ['panvk_descriptor_set_layout.h','panvk_cmd_desc_state.h','panvk_cmd_meta.h','panvk_vX_cmd_desc_state.c','panvk_vX_cmd_meta.c']
    # Confirm the physical slot assumptions against the actual patched tree.
    for name, macro, value in [('panvk_image.h','PANVK_MAX_PLANES',3),('panvk_sampler.h','PANVK_MAX_DESCS_PER_SAMPLER',2)]:
        if not re.search(r'^#define\s+' + macro + r'\s+' + str(value) + r'\s*$', (root/name).read_text(), re.M):
            raise ValueError('Unexpected slot bound: ' + macro)
    out = patch({name:(root/name).read_text() for name in names})
    for name, data in out.items():
        (root/name).write_text(data)
    print('E02: 32 API descriptors, 161 physical slots on arch 12; both backing and save storage enlarged; pre-write and copy guards retained')

if __name__ == '__main__':
    main()
