# Faux123 v1.1.8 / Peanuts 0.1.7 — G720 diagnostics

Keep the original Faux123 v1.1.8 binary. E01/E02 use a different patch series and are not drop-in equivalents. The Faux123 release identifies Mesa 5a07217f, zenithblue rc4 5b87b74 and 149 additional patches; the full corresponding patch set was not found in its public release repository. Do not represent a rebuilt Zenithblue binary as Faux123.

Pinned host: igawa6/peanuts-native@719d4f7b6ffd. Verified switches: docs/env_switches.tsv, dm/gfx/vk_android/vka_nanscan.c and vka_gprof.c.

## Reversible A/B tests
Use the original driver, unchanged game and resolution, same save and same scene. Append only ONE test's lines to Game settings > Extra environment; preserve existing lines. Restart the game. Remove the test lines afterward.
1. White scene: DM_VK_NANSCAN=1. Capture a short run including the first white frame, share log, then disable. It scans floating attachments and compute outputs, can greatly slow rendering and disables the command encoder; not for normal play. If it records invalid values, identify the earliest pass and shader pairs, not necessarily the original producer.
2. Performance: DM_VK_GPUPROF=120. Capture a short repeatable scene. GPU timestamps between barriers identify expensive passes/dispatches. The profiled frames are perturbed; do not benchmark FPS with this enabled.
3. Correctness A/B: DM_VK_CS_ASYNC=0. Prevents skipping compute dispatches for pipelines still being built while retaining graphics async. It can cause initial hitches. This is a hypothesis, not a fix.

No fake subgroup sizes, no disabling necessary texture reads, no root, no changes to kernel/vendor. No game assets or personal logs in this repository. No new driver binary is claimed.

Sources:
- https://github.com/faux123/panvk-faux123-driver-rp4pro/releases/tag/v1.1.8
- https://github.com/faux123/panvk-faux123-driver-pixel7/releases/tag/v1.1.7
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/docs/env_switches.tsv
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/gfx/vk_android/vka_nanscan.c
- https://github.com/igawa6/peanuts-native/blob/719d4f7b6ffd/dm/gfx/vk_android/vka_gprof.c
