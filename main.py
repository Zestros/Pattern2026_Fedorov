"""Точка запуска REST API отчётности."""
from Src.Api.application import create_app


api = create_app()

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)
