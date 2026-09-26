# Update: the true_camera_batch NaN was a caller bug, not a kernel bug

This branch's earlier commits ("Defensive: zero-init rasterize_to_pixels_3dgs_fwd
output buffers" / "Correct the at::zeros comment...") were investigating a NaN
corruption in splatograph's `render_true_camera_batch()` (packed=True,
multi-camera). That investigation is now closed: the actual root cause was a
splatograph-side caller bug, not a bug in this kernel, though it does expose a
real API inconsistency here worth noting for anyone else hitting it.

**Root cause**: splatograph passed a flat `[3]` `backgrounds` tensor into
`rasterization(..., packed=True)` for a C=4 camera batch.
`rasterize_to_pixels_3dgs_fwd_kernel`
(gsplat/cuda/csrc/RasterizeToPixels3DGSFwd.cu:26,55,181-182) indexes
`backgrounds` per camera image (`backgrounds += image_id * CDIM`, then
`T * backgrounds[k]` composited into every in-bounds pixel). For `image_id=0`
that's in-bounds on a 3-element tensor; for `image_id>=1` it's an
out-of-bounds read of whatever adjacent device memory the allocator has at
hand -- explaining the "only after allocator pressure, allocation-size-
dependent" symptom this branch's earlier commits were chasing with an
(ultimately ineffective) `at::zeros` patch on the kernel's *output* buffers.

**The real inconsistency worth flagging upstream**: `rasterize_to_pixels()`'s
own shape assert (gsplat/cuda/_wrapper.py:582
`image_dims = means2d.shape[:-2]`, :598) computes `image_dims` from packed
mode's `(nnz, 2)` `means2d`, which is empty -- so packed mode's own assert
*requires* a flat `(channels,)` background, contradicting what the kernel it
calls actually reads (which wants `[..., C, D]`, matching `rendering.py`'s own
docstring at line 186). A caller who satisfies the wrapper's assert by
flattening a per-camera background (exactly what splatograph did) gets
silently wrong/corrupted results for every camera beyond the first, with no
error. This branch's `at::zeros` patch does not address that and is not being
carried forward as a fix for anything; it is harmless (zero-init is not worse
than empty-init) but should not be read as a resolution.

splatograph's fix was on its own side: stop passing `backgrounds` into
`rasterization()` at all and composite the background in Python afterward
(`out = colors_without_bg + (1 - alpha) * bg`, exact for this blend). See
splatograph's `splatograph/mapping/renderer/true_camera_batch.py` module
docstring (branch `fix/true-batch-nan`) for the full bisection and the direct
A/B/C GPU confirmation (backgrounds=None / flat [3] / [C, 3]).
