"""Capture preflight: flag photos worth retaking before expensive reconstruction.

Detects corrupt or undersized files, blur, bad exposure and near-duplicates. Image quality does
not prove geometric coverage, and the thresholds are heuristics to be tuned against real captures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

QC_VERSION = "preflight/1"

MIN_SIDE_PX = 1024
BLUR_VARIANCE_MIN = 60.0  # variance of the Laplacian on a 512 px grayscale copy
DARK_FRACTION_MAX = 0.35  # share of pixels below 16
BRIGHT_FRACTION_MAX = 0.35  # share of pixels above 240
DUPLICATE_HAMMING_MAX = 2  # of 64 difference-hash bits
MIN_PHOTOS = 20


@dataclass
class PhotoReport:
    name: str
    flags: list[str] = field(default_factory=list)
    width: int = 0
    height: int = 0
    sharpness: float = 0.0
    dhash: int = 0


@dataclass
class PreflightReport:
    qc_version: str
    photos: list[PhotoReport]
    warnings: list[str]

    @property
    def retake(self) -> list[str]:
        return [p.name for p in self.photos if p.flags]

    def to_dict(self) -> dict[str, object]:
        return asdict(self) | {"retake": self.retake}


def laplacian_variance(gray: np.ndarray) -> float:
    g = gray.astype(np.float64)
    lap = g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:] - 4 * g[1:-1, 1:-1]
    return float(lap.var())


def dhash(img: Image.Image) -> int:
    small = np.asarray(img.convert("L").resize((9, 8), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def check_photo(path: Path) -> PhotoReport:
    rep = PhotoReport(name=path.name)
    try:
        with Image.open(path) as im:
            im.load()
            rep.width, rep.height = im.size
            gray_img = im.convert("L")
            rep.dhash = dhash(im)
    except (UnidentifiedImageError, OSError, SyntaxError):
        rep.flags.append("corrupt")
        return rep
    if min(rep.width, rep.height) < MIN_SIDE_PX:
        rep.flags.append("undersized")
    gray_img.thumbnail((512, 512))
    gray = np.asarray(gray_img)
    rep.sharpness = laplacian_variance(gray)
    if rep.sharpness < BLUR_VARIANCE_MIN:
        rep.flags.append("blurry")
    if (gray < 16).mean() > DARK_FRACTION_MAX:
        rep.flags.append("underexposed")
    if (gray > 240).mean() > BRIGHT_FRACTION_MAX:
        rep.flags.append("overexposed")
    return rep


def run_preflight(paths: list[Path]) -> PreflightReport:
    photos = [check_photo(p) for p in sorted(paths)]
    seen: list[PhotoReport] = []
    # Sharpest first, so each near-duplicate group keeps its best photo.
    for photo in sorted(photos, key=lambda p: -p.sharpness):
        if "corrupt" in photo.flags:
            continue
        twin = next(
            (s for s in seen if (s.dhash ^ photo.dhash).bit_count() <= DUPLICATE_HAMMING_MAX), None
        )
        if twin:
            photo.flags.append(f"duplicate_of:{twin.name}")
        else:
            seen.append(photo)
    warnings = []
    usable = [p for p in photos if not p.flags]
    if len(usable) < MIN_PHOTOS:
        warnings.append(f"only {len(usable)} usable photos, aim for at least {MIN_PHOTOS}")
    return PreflightReport(QC_VERSION, photos, warnings)
