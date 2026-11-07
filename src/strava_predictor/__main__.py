"""Start the app: python -m strava_predictor (serves on http://127.0.0.1:8000)."""

import uvicorn

from strava_predictor import config


def server_config() -> dict:
    """Bind to localhost only and keep logs to warnings, so no request data is written."""
    return {
        "host": config.HOST,
        "port": config.PORT,
        "log_level": "warning",
        "access_log": False,
    }


def main() -> None:  # pragma: no cover - starts a blocking server
    uvicorn.run("strava_predictor.web.app:create_app", factory=True, **server_config())


if __name__ == "__main__":  # pragma: no cover
    main()
