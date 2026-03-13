from __future__ import annotations

import re

from betteruv.core.models import ResolvePlan

_PACKAGE_NAME_SPLIT_RE = re.compile(r"[\s\[<>=!~]")
_VERSION_MM_RE = re.compile(r"(\d+)\.(\d+)")

_TORCH_FAMILY = {"torch", "torchvision", "torchaudio"}
_LATEST_TORCH_MINOR = "2.10"

# Compatibility mapping between the core PyTorch family distributions.
# Keyed by torch major.minor.
_TORCH_COMPAT: dict[str, dict[str, str]] = {
    "2.10": {"torchvision": "0.25.0", "torchaudio": "2.10.0"},
    "2.9": {"torchvision": "0.24.0", "torchaudio": "2.9.0"},
    "2.8": {"torchvision": "0.23.0", "torchaudio": "2.8.0"},
    "2.7": {"torchvision": "0.22.0", "torchaudio": "2.7.0"},
    "2.6": {"torchvision": "0.21.0", "torchaudio": "2.6.0"},
    "2.5": {"torchvision": "0.20.0", "torchaudio": "2.5.0"},
    "2.4": {"torchvision": "0.19.0", "torchaudio": "2.4.0"},
    "2.3": {"torchvision": "0.18.0", "torchaudio": "2.3.0"},
    "2.2": {"torchvision": "0.17.0", "torchaudio": "2.2.0"},
    "2.1": {"torchvision": "0.16.0", "torchaudio": "2.1.0"},
    "2.0": {"torchvision": "0.15.0", "torchaudio": "2.0.0"},
    "1.13": {"torchvision": "0.14.0", "torchaudio": "0.13.0"},
}

_REVERSE_TORCHVISION: dict[str, str] = {
    compat["torchvision"]: torch_minor for torch_minor, compat in _TORCH_COMPAT.items()
}


def _package_key(package: str) -> str:
    name = _PACKAGE_NAME_SPLIT_RE.split(package, maxsplit=1)[0]
    return name.strip().lower().replace("_", "-")


def _extract_major_minor(package: str) -> str | None:
    match = _VERSION_MM_RE.search(package)
    if not match:
        return None
    return f"{match.group(1)}.{match.group(2)}"


def _select_target_torch_minor(packages_by_key: dict[str, str]) -> str:
    torch_package = packages_by_key.get("torch")
    if torch_package:
        mm = _extract_major_minor(torch_package)
        if mm in _TORCH_COMPAT:
            return mm

    torchaudio_package = packages_by_key.get("torchaudio")
    if torchaudio_package:
        mm = _extract_major_minor(torchaudio_package)
        if mm in _TORCH_COMPAT:
            return mm

    torchvision_package = packages_by_key.get("torchvision")
    if torchvision_package:
        vision_mm = _extract_major_minor(torchvision_package)
        if vision_mm:
            for vision_version, torch_mm in _REVERSE_TORCHVISION.items():
                if vision_version.startswith(f"{vision_mm}."):
                    return torch_mm

    return _LATEST_TORCH_MINOR


def harmonize_torch_family(plan: ResolvePlan) -> ResolvePlan:
    packages_by_key: dict[str, str] = {}
    for package in plan.packages:
        key = _package_key(package)
        if key in _TORCH_FAMILY:
            packages_by_key[key] = package

    if len(packages_by_key) < 2:
        return plan

    target_torch_mm = _select_target_torch_minor(packages_by_key)
    compat = _TORCH_COMPAT.get(target_torch_mm)
    if compat is None:
        return plan

    replacements: dict[str, str] = {
        "torch": f"torch=={target_torch_mm}.0",
        "torchvision": f"torchvision=={compat['torchvision']}",
        "torchaudio": f"torchaudio=={compat['torchaudio']}",
    }

    updated_packages: list[str] = []
    for package in plan.packages:
        key = _package_key(package)
        updated_packages.append(replacements.get(key, package))

    updated_reasons = dict(plan.mapping_reasons)
    for key, original in packages_by_key.items():
        replacement = replacements[key]
        if original != replacement:
            updated_reasons.pop(original, None)
            updated_reasons[replacement] = (
                "Torch family compatibility alignment "
                f"(torch {target_torch_mm} / torchvision {compat['torchvision']} / "
                f"torchaudio {compat['torchaudio']})"
            )

    return ResolvePlan(
        packages=updated_packages,
        unresolved_imports=list(plan.unresolved_imports),
        mapping_reasons=updated_reasons,
    )
