from __future__ import annotations

import uvicorn

from src.api.app import create_app
from src.utils.logging import configure_root_logger


def main() -> None:
    configure_root_logger()
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

