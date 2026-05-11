"""
Patch GLM's platform.h to check HIP before CUDA.

PyTorch's ROCm hipification converts __CUDACC__ to __HIP__ in GLM headers.
Since GLM checks CUDA before HIP in the original code, the hipified version's
converted CUDA block shadows the native HIP detection, causing a build failure
("GLM requires CUDA 7.0 or higher") because CUDA_VERSION is not defined on HIP.

This patch:
1. Swaps the order so the native __HIP__ check comes first, ensuring
   that even after hipification the HIP compiler path is correctly selected.
2. Also swaps __HIP__ before __HIPCC__ since hipcc defines both.
"""

import os.path as osp

GLM_PLATFORM_H = osp.join(
    osp.dirname(__file__),
    "..",
    "gsplat",
    "cuda",
    "csrc",
    "third_party",
    "glm",
    "glm",
    "simd",
    "platform.h",
)


def apply_replacements(path: str) -> bool:
    with open(path, "r") as f:
        content = f.read()

    patched = False

    # Fix 1: Swap __HIP__ before __HIPCC__ (hipcc defines both; __HIP__ check must win)
    old_hipcc = (
        "// CUDA\n"
        "#elif defined(__HIPCC__)\n"
        "#\tif !defined(TORCH_HIP_VERSION) && !defined(GLM_FORCE_CUDA)\n"
        "#\t\tinclude <hip/hip_runtime.h>  "
        "// make sure version is defined since nvcc does not define it itself!\n"
        "#\tendif\n"
        "#\tif defined(__CUDACC_RTC__)\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA_RTC\n"
        "#\telif TORCH_HIP_VERSION >= 8000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA80\n"
        "#\telif TORCH_HIP_VERSION >= 7500\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA75\n"
        "#\telif TORCH_HIP_VERSION >= 7000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA70\n"
        "#\telif TORCH_HIP_VERSION < 7000\n"
        "#\t\terror \"GLM requires CUDA 7.0 or higher\"\n"
        "#\tendif\n"
        "\n"
        "// HIP\n"
        "#elif defined(__HIP__)\n"
        "#\tdefine GLM_COMPILER GLM_COMPILER_HIP"
    )

    new_hipcc = (
        "// HIP\n"
        "#elif defined(__HIP__)\n"
        "#\tdefine GLM_COMPILER GLM_COMPILER_HIP\n"
        "\n"
        "// CUDA\n"
        "#elif defined(__HIPCC__)\n"
        "#\tif !defined(TORCH_HIP_VERSION) && !defined(GLM_FORCE_CUDA)\n"
        "#\t\tinclude <hip/hip_runtime.h>  "
        "// make sure version is defined since nvcc does not define it itself!\n"
        "#\tendif\n"
        "#\tif defined(__CUDACC_RTC__)\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA_RTC\n"
        "#\telif TORCH_HIP_VERSION >= 8000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA80\n"
        "#\telif TORCH_HIP_VERSION >= 7500\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA75\n"
        "#\telif TORCH_HIP_VERSION >= 7000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA70\n"
        "#\telif TORCH_HIP_VERSION < 7000\n"
        "#\t\terror \"GLM requires CUDA 7.0 or higher\"\n"
        "#\tendif"
    )

    if old_hipcc in content:
        content = content.replace(old_hipcc, new_hipcc)
        print(f"Patched {path} — swapped __HIP__ before __HIPCC__")
        patched = True
    else:
        # Check if already patched (__HIP__ already before __HIPCC__)
        if "// HIP\n#elif defined(__HIP__)\n#\tdefine GLM_COMPILER GLM_COMPILER_HIP\n\n// CUDA\n#elif defined(__HIPCC__)" in content:
            print(f"{path} — __HIP__ already before __HIPCC__, skipping.")
        else:
            print(f"Warning: Could not find __HIPCC__/__HIP__ pattern in {path}")

    # Fix 2: Swap CUDA/HIP blocks (original fix — ensures __HIP__ wins over hipified __HIP__)
    old_cuda = (
        "// CUDA\n"
        "#elif defined(__CUDACC__)\n"
        "#\tif !defined(CUDA_VERSION) && !defined(GLM_FORCE_CUDA)\n"
        "#\t\tinclude <cuda.h>  "
        "// make sure version is defined since nvcc does not define it itself!\n"
        "#\tendif\n"
        "#\tif defined(__CUDACC_RTC__)\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA_RTC\n"
        "#\telif CUDA_VERSION >= 8000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA80\n"
        "#\telif CUDA_VERSION >= 7500\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA75\n"
        "#\telif CUDA_VERSION >= 7000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA70\n"
        "#\telif CUDA_VERSION < 7000\n"
        "#\t\terror \"GLM requires CUDA 7.0 or higher\"\n"
        "#\tendif\n"
        "\n"
        "// HIP\n"
        "#elif defined(__HIP__)\n"
        "#\tdefine GLM_COMPILER GLM_COMPILER_HIP"
    )

    new_cuda = (
        "// HIP\n"
        "#elif defined(__HIP__)\n"
        "#\tdefine GLM_COMPILER GLM_COMPILER_HIP\n"
        "\n"
        "// CUDA\n"
        "#elif defined(__CUDACC__)\n"
        "#\tif !defined(CUDA_VERSION) && !defined(GLM_FORCE_CUDA)\n"
        "#\t\tinclude <cuda.h>  "
        "// make sure version is defined since nvcc does not define it itself!\n"
        "#\tendif\n"
        "#\tif defined(__CUDACC_RTC__)\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA_RTC\n"
        "#\telif CUDA_VERSION >= 8000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA80\n"
        "#\telif CUDA_VERSION >= 7500\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA75\n"
        "#\telif CUDA_VERSION >= 7000\n"
        "#\t\tdefine GLM_COMPILER GLM_COMPILER_CUDA70\n"
        "#\telif CUDA_VERSION < 7000\n"
        "#\t\terror \"GLM requires CUDA 7.0 or higher\"\n"
        "#\tendif"
    )

    if old_cuda in content:
        content = content.replace(old_cuda, new_cuda)
        print(f"Patched {path} — swapped __HIP__ before __CUDACC__")
        patched = True
    else:
        if "// HIP\n#elif defined(__HIP__)\n#\tdefine GLM_COMPILER GLM_COMPILER_HIP\n\n// CUDA\n#elif defined(__CUDACC__)" in content:
            print(f"{path} — __HIP__ already before __CUDACC__, skipping.")
        else:
            print(f"Warning: Could not find CUDA/HIP pattern in {path}")

    if patched:
        with open(path, "w") as f:
            f.write(content)
        print(f"Patched {path} successfully")
    else:
        print(f"No changes needed for {path} (already patched or patterns not found)")
    # Always return success — if the file was already in the correct state, that's fine
    return True


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else GLM_PLATFORM_H
    apply_replacements(path)
    sys.exit(0)
