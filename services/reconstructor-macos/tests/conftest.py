from pathlib import Path

import pytest
from scan3d_api.testing import Harness


@pytest.fixture
def h(tmp_path: Path) -> Harness:
    return Harness(tmp_path / "t.sqlite")
