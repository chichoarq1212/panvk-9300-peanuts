"""Compile generated C in a minimal harness, not Mesa."""
import os, shutil, subprocess, tempfile, unittest
from pathlib import Path
from test_patch import SAVE, RESTORE, FIXTURE, transform

HEADER = r'''
#include <stdint.h>
#include <string.h>
#define PANVK_DESCRIPTOR_SIZE 32
#define panvk_per_arch(x) x
#define meta_gfx_start(a,b) ((void)0)
#define meta_gfx_end(a,b) ((void)0)
typedef void *VkCommandBuffer;
typedef void *VkImage;
typedef unsigned VkImageLayout;
typedef int VkClearColorValue;
typedef int VkImageSubresourceRange;
struct set { unsigned desc_count; struct { void *host; } descs; };
struct ctx { struct { unsigned char desc_storage[128]; unsigned desc_count; } push_set0; };
'''
class NativeGuardTests(unittest.TestCase):
    def test_compile_and_guard(self):
        cc = shutil.which(os.environ.get('CC','cc'))
        self.assertIsNotNone(cc)
        clear = FIXTURE[FIXTURE.index('panvk_per_arch(CmdClearColorImage)'):]
        source = '#include "panvk_cmd_meta.h"\n'
        for name, body in [('save1',SAVE),('restore1',RESTORE),('save2',SAVE),('restore2',RESTORE)]:
            source += f'void {name}(struct set *push_set0, struct ctx *save_ctx) {{\n{body}\n}}\n'
        source += 'void ' + clear
        source += r'''
int main(int argc, char **argv) {
    unsigned char bytes[128] = {42};
    struct set s = {4, {bytes}};
    struct ctx c = {0}; c.push_set0.desc_count = 4;
    if (argc > 1 && argv[1][0]=='s') s.desc_count=5;
    if (argc > 1 && argv[1][0]=='r') c.push_set0.desc_count=5;
    if (argc > 1 && argv[1][0]=='n') s.descs.host=0;
    save1(&s,&c); restore1(&s,&c);
    save2(&s,&c); restore2(&s,&c);
    CmdClearColorImage(0,0,0,0,1,0);
    return c.push_set0.desc_storage[0] != 42;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'panvk_cmd_meta.h').write_text(HEADER); (p/'guard.c').write_text(transform(source))
            for arch in (11,12):
                exe=p/f'guard{arch}'
                subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-parameter',f'-DPAN_ARCH={arch}',str(p/'guard.c'),'-o',str(exe)],check=True)
                ok=subprocess.run([str(exe)],capture_output=True,cwd=p)
                self.assertEqual(ok.returncode,0)
                if arch==12:
                    self.assertIn(b'clear-color enter',ok.stderr); self.assertIn(b'clear-color exit',ok.stderr)
                    for mode, marker in [('s',b'save'),('r',b'restore'),('n',b'save')]:
                        fail=subprocess.run([str(exe),mode],capture_output=True,cwd=p)
                        self.assertNotEqual(fail.returncode,0)
                        self.assertIn(b'PANVK9300_E01 '+marker,fail.stderr)
                else:
                    self.assertNotIn(b'PANVK9300_E01',ok.stderr)
if __name__=='__main__': unittest.main()
