#pragma once

// ---------------------------------------------------------------------------
// Compile-time wave / wavefront-size abstraction for ROCm (HIP) + CUDA.
//
//  GSPLAT_WAVE_SIZE      – hardware wavefront/warp size for the current target
//  GSPLAT_TILE_PIXELS    – pixels in one 8×8 tile (always 64)
//  GSPLAT_WAVES_PER_TILE – how many waves are needed to cover one tile
//                          wave64 → 1,  wave32 → 2
//  GSPLAT_FULL_WARP_MASK – all-lanes-active mask for __shfl_*_sync calls
// ---------------------------------------------------------------------------

// On AMD/HIP the compiler predefines __AMDGCN_WAVEFRONT_SIZE to the actual
// hardware wavefront size (32 for RDNA, 64 for CDNA/GCN).
// On CUDA (NVIDIA) the warp is always 32 lanes.
#if defined(__HIP_PLATFORM_AMD__)
  #if defined(__AMDGCN_WAVEFRONT_SIZE)
    #define GSPLAT_WAVE_SIZE __AMDGCN_WAVEFRONT_SIZE
  #else
    // Fallback: AMD default (GCN / CDNA) when the compiler does not inject
    // the macro.  Override on the command line if needed.
    #define GSPLAT_WAVE_SIZE 64
  #endif
#else
  // CUDA / NVIDIA – warp size is always 32.
  #define GSPLAT_WAVE_SIZE 32
#endif

// Pixels per standard 8×8 tile.
#define GSPLAT_TILE_PIXELS 64

// Number of waves needed to cover one tile.
// wave64: 1 wave handles all 64 pixels (single-wave path).
// wave32: 2 waves handle 64 pixels (two-wave path, needs partial-sum combine).
#define GSPLAT_WAVES_PER_TILE \
    ((GSPLAT_TILE_PIXELS + GSPLAT_WAVE_SIZE - 1) / GSPLAT_WAVE_SIZE)

// Full-warp lane mask for __shfl_*_sync / __ballot_sync operations.
// On wave32 only the lower 32 bits are meaningful.
#if GSPLAT_WAVE_SIZE == 64
  #define GSPLAT_FULL_WARP_MASK 0xFFFFFFFFFFFFFFFFULL
#else
  #define GSPLAT_FULL_WARP_MASK 0xFFFFFFFFULL
#endif
