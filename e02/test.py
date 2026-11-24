import sys, unittest, tempfile, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_patch import FIXTURE

class E02Tests(unittest.TestCase):
    def test_storage_and_guard(self):
        old='   push_set->layout = set_layout;\n   push_set->desc_count = set_layout->desc_count;'
        files={
            'panvk_descriptor_set_layout.h':'#define MAX_PUSH_DESCS 32\n',
            'panvk_cmd_desc_state.h':'struct desc descs[MAX_PUSH_DESCS];',
            'panvk_cmd_meta.h':'struct desc desc_storage[MAX_PUSH_DESCS];\nstruct desc desc_storage[MAX_PUSH_DESCS];',
            'panvk_vX_cmd_desc_state.c':'push_desc_set_write(struct panvk_cmd_buffer *cmd,\n'+old+'\nCmdPushDescriptorSetWithTemplate2KHR\n'+old,
            'panvk_vX_cmd_meta.c':FIXTURE,
        }
        out=patch(files)
        self.assertEqual(out['panvk_cmd_meta.h'].count('[MAX_PUSH_DESC_STORAGE]'),2)
        self.assertIn('descs[MAX_PUSH_DESC_STORAGE]',out['panvk_cmd_desc_state.h'])
        self.assertEqual(out['panvk_vX_cmd_desc_state.c'].count('> MAX_PUSH_DESC_STORAGE'),2)
        self.assertIn('vk_command_buffer_set_error(&cmd->vk',out['panvk_vX_cmd_desc_state.c'])
        self.assertIn('vk_command_buffer_set_error(&cmdbuf->vk',out['panvk_vX_cmd_desc_state.c'])
        self.assertEqual(out['panvk_vX_cmd_meta.c'].count('abort();'),4)
        self.assertNotIn('PANVK9300_E01',out['panvk_vX_cmd_meta.c'])
        # Compile the actual transformed capacity macro with guarded copies.
        src=out['panvk_descriptor_set_layout.h']+r'''
#include <assert.h>
#include <string.h>
#include <stdint.h>
struct desc { unsigned char bytes[32]; };
struct backing { struct desc descs[MAX_PUSH_DESC_STORAGE]; uint64_t canary; };
struct saved { struct desc desc_storage[MAX_PUSH_DESC_STORAGE]; uint64_t canary; };
static int copy(struct backing *b, struct saved *s, unsigned n) {
    if (n > MAX_PUSH_DESC_STORAGE) return 0;
    memcpy(s->desc_storage,b->descs,n*sizeof(struct desc));
    memset(b->descs,0,n*sizeof(struct desc));
    memcpy(b->descs,s->desc_storage,n*sizeof(struct desc));
    return 1;
}
int main(void) {
    struct backing b={0}; struct saved s={0};
    b.canary=s.canary=0x123456789ULL;
    assert(MAX_PUSH_DESCS==32);
#if PAN_ARCH == 12
    assert(MAX_PUSH_DESC_STORAGE==161);
    b.descs[32].bytes[31]=0xAB;
    assert(copy(&b,&s,33));
    assert(b.descs[32].bytes[31]==0xAB);
    b.descs[160].bytes[31]=0xCD;
    assert(copy(&b,&s,161));
    assert(b.descs[160].bytes[31]==0xCD);
    assert(!copy(&b,&s,162));
#else
    assert(MAX_PUSH_DESC_STORAGE==32);
    assert(!copy(&b,&s,33));
#endif
    assert(b.canary==0x123456789ULL && s.canary==0x123456789ULL);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'test.c').write_text(src)
            for arch in (11,12):
                subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',f'-DPAN_ARCH={arch}',str(p/'test.c'),'-o',str(p/'test')],check=True)
                subprocess.run([str(p/'test')],check=True)

if __name__=='__main__': unittest.main()
