# Investigation: Hokkaido empty-texture fix versus Peanuts 0.1.7

## Device evidence

On Xiaomi 14T Pro / Immortalis G720 MC12, Pokémon Legends Z-A 2.0.2 using Peanuts 0.1.7 (719d4f7b6ffd) and Faux123 1.1.8 shows an all-white 3D battle scene while UI remains visible. It recurs at 0.5x and a second run consistent with 1x, and with and without the NANSCAN diagnostic. The ordinary run has zero graphics pipeline failures and no skipped draws waiting for async pipelines in the printed summaries. No demonstrated fix or cause follows from this alone.

## Exact other-project fix

Hokkaido commit c629c3ee7666e0c26c52b1982f04cd8a8a3749eb changes src/video_core/shader_environment.cpp in its Eden/Hokkaido engine. Its report describes an empty all-zero TIC descriptor for tonemapping being misidentified as 1D during runtime shader compilation; the actual texture subsequently is 2D. It also invalidates ambiguous historical cache records. Source: https://github.com/pavelgajdo/Hokkaido/commit/c629c3ee7666e0c26c52b1982f04cd8a8a3749eb . Hokkaido's release is not proof that this fix applies to Peanuts or that the hardware/game symptom has the same cause.

## Peanuts comparison

Peanuts 0.1.7 uses its dmsh_xlate / Ryujinx translator, not Hokkaido's shader_environment.cpp. In dm/gfx/tools/dmsh_xlate/Program.cs, QuerySamplerType first resolves explicit table entries or another instruction's inferred texture or image type. If none exists it already falls back to SamplerType.Texture2D. dm/third_party/ryujinx/src/Ryujinx.Graphics.Shader/Instructions/InstEmitTexture.cs uses QuerySamplerType for non-bindless texture-size queries and 2D/3D choice for bindless queries. Thus directly copying Hokkaido's patch is not applicable, and a missing type in the answer table already has a 2D default. This does not establish that every relevant shader or runtime binding is typed correctly: explicit answers, inferred answers, bindless usage, and actual texture bindings still require investigation.

Sources pinned to the actual host:
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/gfx/tools/dmsh_xlate/Program.cs
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/third_party/ryujinx/src/Ryujinx.Graphics.Shader/Instructions/InstEmitTexture.cs
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/gfx/vk_android/vka_tex.c

## Next technical work

Identify the game's tonemap shader and its texture-size queries and bindings using the existing shader reflection and logs, then test a narrowly scoped hypothesis with an appropriate reproducible shader/binding case. Use Faux123 unchanged. Do not force every 1D texture to 2D or invalidate user caches without understanding the type and cache semantics. Do not claim a gameplay fix before a matching device test.

## Game-specific evidence from available logs

The game's source documentation identifies deferred-lighting fragment shader ead6e2a32540b19a, with 31 bindings, including a stencil-dependent read, and identifies b29f08619f379a83 in the 32x32x32 color-grading LUT build. The former occurs in the Faux123 0.5x log in a mixed scaled/unscaled texture read; this does not identify it as the cause of the white fight. A matching fallback occurs in both ordinary Faux123 logs: fragment shader ed36f2f5bb1791b6, binding 273, expects a cube but receives a 2D texture and thus reads zeros. The game documentation independently describes a 2D placeholder for a cube slot on the Mac route; both host and documentation caution that the binding may be unused. This is a reproducible binding mismatch, not proof of the white screen's cause; do not force a 2D-to-cube reinterpretation.

The diagnostic ASTC test sampled a synthetic HDR-encoded block through an NVN 0x79 ASTC texture. The format corresponds to the LDR ASTC family in the host format table, so the observed NaN cannot by itself establish faulty HDR decoding or link it to the fight.

Correction: the documented overwritten texture-command case with a white screen concerns Luigi's Mansion 3, not Pokémon Z-A. It should not be represented as a confirmed Z-A bug.

Sources: https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/games/0100F43008C44000/README.md and https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/docs/reference/nvn-objects.md .

## Targeted capture, 2026-11-24

Faux123 1.1.8 with DM_VK_TEX_PEEK=ead6e2a32540b19a,ed36f2f5bb1791b6 and limit 5000. Screenshot shows white battle with HUD. The log contains 93 unique tex-peek rows (13 for ead6..., 80 for ed36...), frame numbers 1 through 2269, and 124 rt-peek rows. These are deduplicated by shader/binding/texture ID/view outcome (rt by image/range), not a frame-by-frame trace and not a pixel-content inspection. A missing later line does not mean no later draw.

On frame 1, all 13 recorded bindings of deferred-light shader ead6... have a made view. That does not verify the content, depth/stencil aspect or later battle frame. On frame 430, ed36... binding 273 gets two 2D placeholder IDs with no cube view; the replay explicitly reports a zero cube fallback. The same binding has valid cube views for other texture IDs at frame 430 and 2269. This demonstrates a mixed set of placeholder and actual cubes, not proof of the cause or whether a placeholder was sampled. The 32x32x32 render target appears at frame 1 but the text logs the 3D image's array layer count, not proof that 32 depth slices were or were not written. Avoid diagnosing a 3D-layer fault from that line alone.

No shader fix is confirmed. To identify the producer and values, collect a scoped frame capture/image dump and inspect intermediate targets and LUT contents, or isolate a reproducible unit-level fault. No ROM, save, keys or raw personal device log are published here.

## Source checks following the targeted capture

A white-veil failure from compiler FPCR was documented on Qualcomm, but the Peanuts version used in these runs contains host FPCR wrappers; the log reads an fp0-generation pipeline cache. That does not verify Faux123's compiler outputs, and an fp0 cache filename alone is not a measured runtime FPCR. No change proposed on this evidence.

The logged 32x32x32 target's image layers=1 is expected for a Vulkan 3D image: in this pinned Peanuts source the depth slices are distinct from array layers, and render passes use 2D/2D-array slice views. It does not prove the LUT's slices are correct or incorrect.

On ead6... the depth-stencil inputs have views, but the current tex-peek log does not include the chosen image aspect. The pinned source selects stencil aspect when the texture or its view requests it; that is implementation evidence, not proof that the game's runtime flags and driver values are correct. Diagnose this using an actual captured sample before changing it.

Diagnostic input snapshots without a PC: the available DM_VK_IMG_DUMP only triggers on the host's ctl screenshot command, not an ordinary phone screenshot, and writes binary files beside ctl.txt. The phone reports DM_CTL under Android/data, whose access varies with Android and file manager. No device access or user-tested phone-only method is available here; do not promise one.

Sources: https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/gfx/vk_android/vka_tex.c and https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/docs/reference/rendering.md .
