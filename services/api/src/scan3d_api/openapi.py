"""Write the OpenAPI schema: `python -m scan3d_api.openapi <out.json>`."""

import json
import sys
import tempfile
from pathlib import Path

from scan3d_api.app import create_app


def schema() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        return create_app(Path(tmp) / "openapi.sqlite").openapi()


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(json.dumps(schema(), indent=2) + "\n")
