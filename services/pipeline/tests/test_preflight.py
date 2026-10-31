from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scan3d_pipeline.preflight import run_preflight


def textured(seed: int, size: int = 1200) -> Image.Image:
    rng = np.random.default_rng(seed)
    return Image.fromarray(rng.integers(0, 256, (size, size), dtype=np.uint8)).convert("RGB")


def test_flags_each_failure_mode(tmp_path: Path) -> None:
    textured(1).save(tmp_path / "good.jpg", quality=95)
    textured(1).filter(ImageFilter.GaussianBlur(12)).save(tmp_path / "blurry.jpg")
    Image.new("RGB", (1200, 1200), (0, 0, 0)).save(tmp_path / "dark.jpg")
    Image.new("RGB", (1200, 1200), (255, 255, 255)).save(tmp_path / "bright.jpg")
    textured(2, size=400).save(tmp_path / "small.jpg")
    (tmp_path / "broken.jpg").write_bytes(b"not an image")
    textured(1).save(tmp_path / "good_copy.jpg", quality=95)

    rep = run_preflight(list(tmp_path.iterdir()))
    flags = {p.name: p.flags for p in rep.photos}
    assert flags["good.jpg"] == []
    assert "blurry" in flags["blurry.jpg"]
    assert "underexposed" in flags["dark.jpg"]
    assert "overexposed" in flags["bright.jpg"]
    assert "undersized" in flags["small.jpg"]
    assert flags["broken.jpg"] == ["corrupt"]
    assert any(f.startswith("duplicate_of:good.jpg") for f in flags["good_copy.jpg"])
    assert "good.jpg" not in rep.retake
    assert rep.warnings  # far fewer than the minimum photo count
    assert rep.to_dict()["qc_version"] == "preflight/1"
