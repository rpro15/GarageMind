from __future__ import annotations

import logging
import uuid

from flask import Flask, g, request

from app.adapters.sqlite_catalog_repository import SqliteCatalogRepository
from app.adapters.stub_part_recognition import PART_CATALOG
from app.api.errors import register_error_handlers
from app.api.routes import api_blueprint
from app.config.settings import Settings
from app.ports.catalog_repository import CatalogRepository
from app.services.part_recognition import build_part_recognition_service
from app.services.vin_decoder import VinDecoderService


def configure_logging(level: str) -> None:
    resolved_level = getattr(logging, level, logging.INFO)
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def build_catalog_repository(settings: Settings) -> CatalogRepository:
    return SqliteCatalogRepository(settings.database_path)


def seed_catalog(repo: CatalogRepository) -> None:
    if repo.count() == 0:
        for item in PART_CATALOG:
            repo.add_part(item["part_name"], item["category"])


def create_app(settings: Settings | None = None) -> Flask:
    active_settings = settings or Settings.from_env()
    configure_logging(active_settings.log_level)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = active_settings.max_image_bytes

    catalog_repo = build_catalog_repository(active_settings)
    seed_catalog(catalog_repo)

    app.extensions["services"] = {
        "part_recognition": build_part_recognition_service(active_settings, app.logger),
        "vin_decoder": VinDecoderService(app.logger),
    }
    app.extensions["catalog_repo"] = catalog_repo

    @app.before_request
    def attach_request_id() -> None:
        g.request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex)

    @app.after_request
    def inject_request_id(response):
        response.headers["X-Request-Id"] = g.request_id
        return response

    register_error_handlers(app)
    app.register_blueprint(api_blueprint)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
