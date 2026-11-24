# E04 real-device crash analysis

## Observed test

Xiaomi 14T Pro, Mali-G720 Immortalis MC12, Android 16, Peanuts Native 0.1.7, Pokémon Legends Z-A. E04 was loaded and readiness returned PASS; it crashed during the first frame. Faux123 1.1.8 remains the user's only confirmed working baseline. No log or private paths are included here.

## Symbol and instruction evidence

The E04 build artifact contains the matching unstripped symbol table. The return address 0x1b2abb0 resolves to meta_gfx_end; the caller address 0x1b2b860 resolves to panvk_v12_CmdClearColorImage. AArch64 disassembly shows the call immediately before that return address obtains the saved descriptor count at save-context offset 1048, multiplies it by 32, and calls memcpy from save-context offset 16 to the push-set descriptor storage. The crash happened during that call: the log reports SEGV_ACCERR on a read from the no-access page at the end of the thread stack. These observations identify the copy path, not the original write that corrupted or exceeded its saved state.

E01 previously reported 33 descriptors with a save capacity of 32. This is consistent with a capacity problem in the same family of code, but E04's exact original count and overwrite have not been independently captured. The E02 candidate expands physical storage and guards copies, but no on-device E02 result has been verified. E04 did not include E02. Do not claim either candidate fixes the device crash or is equivalent to Faux123.

## Next gate

Faux123 v1.1.8's complete patch set is not available in this repository. A rebuild from the public tree cannot preserve that binary's behavior and must not be offered as an improved Faux123. Continue with the unchanged working binary for performance experiments. Candidate P01 (DM_VK_CHUNK_PASS=600) is a single reversible Peanuts setting, not a driver modification; compare matched scenes, temperature, visible correctness and repeated FPS/GPU frame-time windows against the default. It has not been measured yet.

For public-tree experimentation, first reproduce descriptor save/restore sizes and write paths with instrumentation and memory-safety tests, then use device tests before claiming a fix. Never truncate descriptors or claim that a readiness check establishes gameplay correctness.
