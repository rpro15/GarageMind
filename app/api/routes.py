from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.errors import ApiError
from app.services.affiliate import ClickTrackingService
from app.services.part_recognition import PartRecognitionService
from app.services.recommendation import RecommendationRanker
from app.services.vin_decoder import VinDecoderService


api_blueprint = Blueprint("api", __name__, url_prefix="/api")

_VALID_CATEGORIES = {"tire", "wheel"}


def _part_service() -> PartRecognitionService:
    return current_app.extensions["services"]["part_recognition"]


def _vin_service() -> VinDecoderService:
    return current_app.extensions["services"]["vin_decoder"]


def _ranker() -> RecommendationRanker:
    return current_app.extensions["services"]["recommendation"]


def _click_tracker() -> ClickTrackingService:
    return current_app.extensions["services"]["click_tracking"]


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


@api_blueprint.get("/recommend")
def recommend():
    """Return ranked tire or wheel recommendations.

    Query parameters
    ----------------
    category : str
        Product category to filter by.  Must be ``tire`` or ``wheel``.
    n : int, optional
        Maximum number of results to return (1–10, default 4).
    """
    category = request.args.get("category", "").strip().lower()
    if not category:
        raise ApiError(
            code="missing_category",
            message="Query parameter 'category' is required (tire or wheel).",
            status_code=400,
        )
    if category not in _VALID_CATEGORIES:
        raise ApiError(
            code="invalid_category",
            message=f"Invalid category '{category}'. Allowed values: {sorted(_VALID_CATEGORIES)}.",
            status_code=400,
        )

    raw_n = request.args.get("n", "4")
    try:
        top_n = max(1, min(10, int(raw_n)))
    except ValueError:
        top_n = 4

    results = _ranker().recommend(category, top_n=top_n)
    return jsonify(
        {
            "category": category,
            "count": len(results),
            "recommendations": [r.to_dict() for r in results],
        }
    ), 200


@api_blueprint.post("/track-click")
def track_click():
    """Record a click on an affiliate recommendation.

    Request body (JSON)
    -------------------
    product_id : str  – required
    partner_id : str  – required
    session_id : str  – optional
    """
    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError(
            code="invalid_json",
            message="Request body must contain valid JSON.",
            status_code=400,
        )

    product_id = (payload.get("product_id") or "").strip()
    partner_id = (payload.get("partner_id") or "").strip()
    if not product_id or not partner_id:
        raise ApiError(
            code="missing_fields",
            message="Both 'product_id' and 'partner_id' are required.",
            status_code=400,
        )

    session_id = (payload.get("session_id") or "").strip() or None
    event = _click_tracker().record(product_id, partner_id, session_id)
    return jsonify({"status": "recorded", "event": event.to_dict()}), 201
