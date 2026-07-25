"""Single-process Uvicorn entry point."""

import uvicorn

from .settings import Settings


def main() -> None:
    settings = Settings()
    uvicorn.run(
        "libero_remote.server.app:app",
        host=settings.host,
        port=settings.port,
        workers=1,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
