# Faux123 v1.1.8 equivalence target

Reference: official unmodified package SHA256 1898e89be6256e67762876fe249e9017717f8643cc5fb6194cf11195fe6da6c8; library SHA256 499e3eae32a27340777cb890aac92468c2519d57223bfad93a2e2a8f71029728. Source release identifies Mesa 5a07217f, Zenithblue rc4 5b87b74, and 149 private patches. E03 uses the public Zenithblue tree, not the private Faux123 source.

Acceptance order:
1. ARM64 ELF and Peanuts package structure; reference ICD entry points retained.
2. Peanuts selftest passes, placed maps and real hardware capabilities unchanged.
3. Legends Z-A reaches gameplay without crash, corruption, or regression relative to reference; combat must be visually correct to claim improvement.
4. Matched ordinary gameplay A/B with the same scene, resolution, settings, and similar thermal state; no FPS claim from selftest.
5. No root, vendor or kernel changes, fake subgroup capabilities, or disabling synchronization.

E03 implements only a narrowly scoped implicit FP16 conversion experiment and E02 descriptor safeguards. Integer texel buffer bit preservation, Android loader presentation extension handling, and other private changes remain unverified. Do not blindly reinterpret all texture fetches: Vulkan typed access and guest Maxwell bit semantics differ. A reduced test is needed before implementing this path.

Static comparison is an early gate, not a substitute for hardware tests.

## Consolidated release policy (user requested no more intermediate releases)
E03 is an archived experimental build, not the final driver. Its automatic push trigger is disabled. Do not start E04 or publish a new intermediate candidate merely because it compiles. Consolidate compatibility changes in a development branch or source directory; only publish a final candidate when its static and runtime acceptance evidence is documented. Preserve the official Faux123 package as fallback. The private patch tree and access to physical hardware are unresolved blockers; exact equivalence cannot be certified without them or independently demonstrated behavior. No changes to Android vendor, kernel, root, or bootloader.
