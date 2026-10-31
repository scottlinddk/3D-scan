"""Write the OpenAPI schema: `python -m scan3d_api.openapi <out.json>`."""

import json
import sys
from pathlib import Path

from scan3d_api.app import app

if __name__ == "__main__":
    Path(sys.argv[1]).write_text(json.dumps(app.openapi(), indent=2) + "\n")
