# Alternative compatibility route: Galar v0.97

On 2026-11-24, the Galar Native v0.97 release notes describe a confirmed white-scene fix on POCO X6 Pro (G615 MC6, Arm r44p1): preserve small integer vertex attributes as the guest shader expects. This is a different game (Sword/Shield) and a different driver (stock Arm) from the G720 MC12 / Faux123 / Legends Z-A case. It is a hypothesis source, not a transferable proven fix.

Peanuts 0.1.7 source at 719d4f7b6ffd already has integer vertex input retyping in vka_draw.c:vin_format and vin_build. The 8/16-bit integer-to-float path uses USCALED/SSCALED for NVN formats 0x51..0x68, whereas raw integer-to-float inputs use a shader variant. Investigate those paths with a reduced vertex-fetch test before changing either. Do not indiscriminately reinterpret all attributes: numeric conversion and bit reinterpretation have different semantics.

Peanuts issue #20 is the official Mali compatibility tracker; contributor reports confirm Faux123 placed mapping works on several devices but visual correctness remains open. Faux123 Pixel7 issue #1 documents G720 MC7 test builds and a maintainer request for a bad-run log. The Faux123 private patch tree remains unavailable. No new binary or measured performance improvement is claimed.

References:
- https://github.com/simipoB/Galar-Native-Android/releases/tag/v0.97
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/gfx/vk_android/vka_draw.c#L826
- https://github.com/igawa6/peanuts-native/issues/20
- https://github.com/faux123/panvk-faux123-driver-pixel7/issues/1
