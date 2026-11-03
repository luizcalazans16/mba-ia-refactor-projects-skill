"""Entry point: `python app.py`. Toda a montagem da aplicação está em src/app.py (create_app)."""
from src.app import create_app

app = create_app()

if __name__ == "__main__":
    settings = app.config["SETTINGS"]
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
