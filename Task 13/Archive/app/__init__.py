from flask import Flask, send_from_directory

from app.config import Config
from app.routes.api import register_api_routes


def create_app():
    Config.ensure_directories()

    app = Flask(
        __name__,
        static_folder=str(Config.FRONTEND_DIR),
        static_url_path="",
    )
    app.config.from_object(Config)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    # Keep routing simple for a static single-page frontend.
    @app.get("/<path:path>")
    def static_proxy(path):
        target = Config.FRONTEND_DIR / path
        if target.exists() and target.is_file():
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    register_api_routes(app)
    return app
