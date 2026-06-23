from __future__ import annotations

from dataclasses import dataclass

from flask import Flask, current_app, g, jsonify
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge


@dataclass
class ApiError(Exception):
    code: str
    message: str
    status_code: int
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        error = {
            "code": self.code,
            "message": self.message,
            "request_id": getattr(g, "request_id", None),
        }
        if self.details:
            error["details"] = self.details
        return {"error": error}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(_: RequestEntityTooLarge):
        max_bytes = current_app.config.get("MAX_CONTENT_LENGTH")
        error = ApiError(
            code="image_too_large",
            message="Image payload exceeds the configured size limit.",
            status_code=413,
            details={"max_image_bytes": max_bytes},
        )
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        mapped_error = ApiError(
            code="http_error",
            message=error.description or "Request failed.",
            status_code=error.code or 500,
        )
        return jsonify(mapped_error.to_dict()), mapped_error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        current_app.logger.exception("Unhandled API error: %s", error)
        mapped_error = ApiError(
            code="internal_server_error",
            message="An unexpected error occurred.",
            status_code=500,
        )
        return jsonify(mapped_error.to_dict()), mapped_error.status_code
