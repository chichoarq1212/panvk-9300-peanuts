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
