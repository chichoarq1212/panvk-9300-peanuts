import unittest
from check_p01 import extract, compare

def fixture(chunk=None, fps=10, gpu=100, draws=1000, extra=''):
    lines=['[dm] [vk] driver: panvk (panvk_faux123 v1.1.8 (Mesa test))','[nxlaunch] env DM_VK_PSO_ASYNC=2']
    if chunk is not None:lines.append(f'[nxlaunch] env DM_VK_CHUNK_PASS={chunk}')
    if extra:lines.append(extra)
    for f in (100,200,300):
        lines.append(f'[dm] [vk] pace up to frame {f} (5.0 s): interval other 100 %; {fps} fps; GPU busy p50/p90 {gpu}/120 ms; replay recording 20.0 ms a frame (its CPU 15.0), {draws} draws;')
    lines.append('[dm] [vk] replay up to frame 300: per frame 1000 draws, 100 render passes, 50 clears / copies (20 in a pass), 200 full barriers, 1 inline uniform updates, 1.0 submissions (9.0 parts);')
    return extract(lines,100,300)
class TestP01(unittest.TestCase):
    def test_accept(self):
        self.assertEqual(compare(fixture(),fixture(600,12,80))['fps_change_pct'],20)
    def test_replay(self):self.assertEqual(fixture()['replay']['parts'],9)
    def test_missing_profile(self):
        with self.assertRaises(ValueError):compare(fixture(),fixture())
    def test_other_setting(self):
        with self.assertRaises(ValueError):compare(fixture(),fixture(600,extra='[nxlaunch] env DM_RES=2'))
    def test_diagnostic(self):
        with self.assertRaises(ValueError):compare(fixture(),fixture(600,extra='[nxlaunch] env DM_VK_NANSCAN=1'))
    def test_workload(self):
        with self.assertRaises(ValueError):compare(fixture(),fixture(600,draws=1500))
if __name__=='__main__':unittest.main()
