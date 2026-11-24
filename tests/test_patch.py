import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from apply_e01 import transform

SAVE = '''      memcpy(save_ctx->push_set0.desc_storage, push_set0->descs.host,
             push_set0->desc_count * PANVK_DESCRIPTOR_SIZE);'''
RESTORE = '''      memcpy(push_set0->descs.host, save_ctx->push_set0.desc_storage,
             save_ctx->push_set0.desc_count * PANVK_DESCRIPTOR_SIZE);'''
FIXTURE = '#include "panvk_cmd_meta.h"\n' + '\n'.join([SAVE,RESTORE,SAVE,RESTORE]) + '''
panvk_per_arch(CmdClearColorImage)(VkCommandBuffer commandBuffer, VkImage image,
                                   VkImageLayout imageLayout,
                                   const VkClearColorValue *pColor,
                                   uint32_t rangeCount,
                                   const VkImageSubresourceRange *pRanges)
{
   meta_gfx_start(cmdbuf, &save);
   meta_gfx_end(cmdbuf, &save);
}
'''
class PatchTests(unittest.TestCase):
    def test_anchors_and_output(self):
        s=transform(FIXTURE)
        self.assertEqual(s.count('abort();'),4)
        self.assertEqual(s.count('clear-color enter'),1)
        self.assertEqual(s.count('clear-color exit'),1)
        self.assertIn('layout=%u\\n"',s)
        self.assertIn('capacity=%zu\\n"',s)
        self.assertIn('push_set0 ? push_set0->desc_count : 0',s)
        self.assertEqual(s.count('#if PAN_ARCH == 12'),7)
    def test_fail_closed(self):
        with self.assertRaises(ValueError): transform(FIXTURE.replace(SAVE,'',1))
        with self.assertRaises(ValueError): transform(transform(FIXTURE))
if __name__=='__main__': unittest.main()
