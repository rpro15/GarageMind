from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from app.api.errors import ApiError
from app.data.car_tires_db import list_makes, list_models, lookup_tire_size
from app.db.database import Database
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


def _db() -> Database:
    return current_app.extensions["db"]


def _car_tires_db():
    return current_app.extensions["car_tires_db"]


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


@api_blueprint.post("/click")
def log_click():
    """Record an affiliate link click from the bot or Mini App."""
    if not request.is_json:
        raise ApiError(
            code="unsupported_media_type",
            message="Use application/json for this endpoint.",
            status_code=415,
        )

    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiError(
            code="invalid_json",
            message="Request body must contain valid JSON.",
            status_code=400,
        )

    product_name = str(payload.get("product_name") or "").strip()
    marketplace = str(payload.get("marketplace") or "").strip().lower()
    affiliate_url = str(payload.get("affiliate_url") or "").strip()

    if not product_name or not marketplace or not affiliate_url:
        raise ApiError(
            code="invalid_click_payload",
            message="product_name, marketplace, and affiliate_url are required.",
            status_code=400,
        )

    user_id = str(payload.get("user_id") or "").strip() or None
    _db().log_click(
        user_id=user_id,
        product_name=product_name,
        marketplace=marketplace,
        affiliate_url=affiliate_url,
    )
    return jsonify({"status": "ok"}), 200


@api_blueprint.get("/cars")
def list_cars():
    """Return available makes, and optionally models for a given make.

    ?make=Toyota  → list of models
    (no params)   → list of makes
    """
    conn = _car_tires_db()
    make = request.args.get("make", "").strip()

    if make:
        models = list_models(conn, make)
        return jsonify({"make": make, "models": models}), 200

    makes = list_makes(conn)
    return jsonify({"makes": makes}), 200


@api_blueprint.get("/cars/tire-size")
def car_tire_size():
    """Look up recommended tire size for a specific car.

    ?make=Toyota&model=Camry&year=2020
    """
    conn = _car_tires_db()
    make = request.args.get("make", "").strip()
    model = request.args.get("model", "").strip()
    try:
        year = int(request.args.get("year", 0))
    except (TypeError, ValueError):
        year = 0

    if not make or not model or not year:
        raise ApiError(
            code="missing_car_params",
            message="make, model, and year query parameters are required.",
            status_code=400,
        )

    spec = lookup_tire_size(conn, make, model, year)
    if spec is None:
        return jsonify({"found": False, "spec": None}), 200

    return jsonify({"found": True, "spec": spec}), 200
