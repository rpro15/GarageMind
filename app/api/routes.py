from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.errors import ApiError
from app.services.part_recognition import PartRecognitionService
from app.services.recommendation import RecommendationService
from app.services.vin_decoder import VinDecoderService
from app.domain.models import RecommendRequest


api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def _part_service() -> PartRecognitionService:
    return current_app.extensions["services"]["part_recognition"]


def _vin_service() -> VinDecoderService:
    return current_app.extensions["services"]["vin_decoder"]


def _recommend_service() -> RecommendationService:
    return current_app.extensions["services"]["recommendation"]


@api_blueprint.post("/recognize-part")
def recognize_part():
    if request.mimetype and request.mimetype.startswith("multipart/form-data"):
        upload = request.files.get("image")
        if upload is None:
            raise ApiError(
                code="missing_image_payload",
                message="Multipart requests must include an 'image' file field.",
                status_code=400,
            )

        result = _part_service().recognize_upload(
            upload.read(),
            declared_mime_type=upload.mimetype,
            filename=upload.filename,
        )
        return jsonify(result.to_dict()), 200

    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ApiError(
                code="invalid_json",
                message="Request body must contain valid JSON.",
                status_code=400,
            )

        result = _part_service().recognize_base64(
            payload.get("image_base64"),
            declared_mime_type=payload.get("content_type"),
            filename=payload.get("filename"),
        )
        return jsonify(result.to_dict()), 200

    raise ApiError(
        code="unsupported_media_type",
        message="Use multipart/form-data or application/json for this endpoint.",
        status_code=415,
        details={"allowed_content_types": ["multipart/form-data", "application/json"]},
    )


@api_blueprint.route("/decode-vin", methods=["GET", "POST"])
def decode_vin():
    vin_value = request.args.get("vin", "")
    if request.method == "POST" and request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ApiError(
                code="invalid_json",
                message="Request body must contain valid JSON.",
                status_code=400,
            )
        vin_value = payload.get("vin", vin_value)

    if not vin_value:
        raise ApiError(
            code="missing_vin",
            message="VIN is required in the query string or JSON body.",
            status_code=400,
        )

    result = _vin_service().decode(vin_value)
    return jsonify(result.to_dict()), 200 if result.is_valid else 422


@api_blueprint.post("/recommend")
def recommend():
    if not request.is_json:
        raise ApiError(
            code="unsupported_media_type",
            message="Use application/json for this endpoint.",
            status_code=415,
            details={"allowed_content_types": ["application/json"]},
        )

    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiError(
            code="invalid_json",
            message="Request body must contain valid JSON.",
            status_code=400,
        )

    try:
        car_year = int(payload.get("car_year", 0))
    except (TypeError, ValueError):
        car_year = 0

    try:
        budget_rub = int(payload.get("budget_rub", 0))
    except (TypeError, ValueError):
        budget_rub = 0

    rec_request = RecommendRequest(
        car_make=str(payload.get("car_make") or "").strip(),
        car_model=str(payload.get("car_model") or "").strip(),
        car_year=car_year,
        category=str(payload.get("category") or "").strip().lower(),
        season=str(payload.get("season") or "").strip().lower(),
        driving_style=str(payload.get("driving_style") or "").strip().lower(),
        budget_rub=budget_rub,
    )

    result = _recommend_service().recommend(rec_request)
    return jsonify(result.to_dict()), 200
