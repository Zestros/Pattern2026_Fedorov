"""Точка запуска REST API отчётности."""
from pathlib import Path

from Src.Api.application import create_app


if __name__ == "__main__":
    api = create_app(log_path=Path(__file__).resolve().with_name("operations.log"))
    api.run(host="0.0.0.0", port=8000)
else:
    api = create_app()
