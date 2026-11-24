# E04 build validation — 2026-11-24

## Release

- Tag: `e04-build-45430044808-1`
- Asset: [PANVK-9300-PEANUTS-E04.adpkg.zip](https://github.com/chichoarq1212/panvk-9300-peanuts/releases/download/e04-build-45430044808-1/PANVK-9300-PEANUTS-E04.adpkg.zip)
- ZIP SHA-256: `1282b86dab1665924c66cca866bf96280b41b32c83d3527a9e484faa8b2e7247`
- Shared library SHA-256: `c54fea6cacc21c09951c5862d13d5c3412920307601d7d4847385540e062ae2e`
- Package size: 9,544,196 bytes
- CI run: [45430044808](https://github.com/chichoarq1212/panvk-9300-peanuts/actions/runs/45430044808), build and publish jobs successful.

## Checks completed

- The build's source-anchor tests and native AUTO32 policy harness passed.
- CI verified the sidecar SHA-256, ZIP integrity, `meta.json`, ELF64 little-endian, AArch64 machine (183), and the `libvulkan_panfrost.so` library name.
- The downloaded Actions artifact was independently checked: its SHA-256 matches the artifact digest; the nested driver ZIP passes `unzip -t`; the sidecar matches the ZIP hash.
- ELF header: ELF64, little-endian, shared object, AArch64.
- `meta.json`: `minApi=29`, `libraryName=libvulkan_panfrost.so`, package version `0.0.4`.
- Binary strings include `VK_KHR_map_memory2`, `VK_EXT_map_memory_placed`, `memoryMapPlaced`, `VK_KHR_swapchain`, `VK_KHR_timeline_semaphore`, and `VK_KHR_dynamic_rendering`.
- E04's dynamic exports and `DT_NEEDED` Android libraries were compared locally with the Faux123 v1.1.8 reference report from E03: the four ICD/HMI exports match exactly; no missing or extra exports; the needed Android libraries match.

## Scope and limits

E04 changes 32-bit float-result texel-buffer fetches to use NIR AUTO32 / `BI_REGISTER_FORMAT_AUTO` in the shared Bifrost/Valhall path. It does not carry the earlier E02 descriptor expansion or E03 FP16 rounding experiment.

This is a build/package/ELF validation, not a hardware validation. It has not been run on Xiaomi 14T Pro / Immortalis-G720 MC12, and it has not been tested in Peanuts Native. No crash fix, correct rendering, FPS gain, or complete equivalence to Faux123 v1.1.8 is claimed.

## Peanuts Native installation and runtime gate

Peanuts Native's GPU-driver guide accepts a driver ZIP with `meta.json`:
Settings → GPU driver → Install… → Pick a zip…

After import, select the installed PANVK E04 driver. Then run Settings → Readiness check. The important runtime requirements for Peanuts Native include Vulkan 1.3, `VK_KHR_swapchain`, `VK_KHR_map_memory2`, `VK_EXT_map_memory_placed`, `memoryMapPlaced`, timeline semaphores, dynamic rendering, and descriptor-indexing features. Proceed only if the readiness check reports the required rows as passing. If it reports a missing requirement or the game fails to render, switch back to the known working driver.

Peanuts Native references:
- https://github.com/igawa6/peanuts-native/blob/main/docs/guides/gpu-drivers.md
- https://github.com/igawa6/peanuts-native/blob/main/android/app/src/main/java/dev/nxnative/android/Readiness.java
- https://github.com/igawa6/peanuts-native/blob/main/android/app/src/main/java/dev/peanuts/ui/MaliDriver.java

Keep Faux123 v1.1.8 as the fallback. Do not flash a kernel, change vendor partitions, unlock the bootloader, or use root for this test.
