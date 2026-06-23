from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.errors import ApiError
from app.services.click_tracker import ClickTrackingService
from app.services.part_recognition import PartRecognitionService
from app.services.recommendation import ALLOWED_CATEGORIES, RecommendationService
from app.services.vin_decoder import VinDecoderService


api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def _part_service() -> PartRecognitionService:
    return current_app.extensions["services"]["part_recognition"]


def _vin_service() -> VinDecoderService:
    return current_app.extensions["services"]["vin_decoder"]


def _recommendation_service() -> RecommendationService:
    return current_app.extensions["services"]["recommendation"]


def _click_tracker() -> ClickTrackingService:
    return current_app.extensions["services"]["click_tracker"]


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


@api_blueprint.get("/recommendations")
def get_recommendations():
    """Return ranked tire/wheel recommendations without requiring a VIN.

    Query parameters
    ----------------
    category : str, optional
        Filter by product category.  Accepted values: ``tires``, ``wheels``.
        Omit to receive recommendations across both categories.
    """
    category = request.args.get("category", "").strip() or None
    if category and category not in ALLOWED_CATEGORIES:
        raise ApiError(
            code="invalid_category",
            message="category must be 'tires' or 'wheels'.",
            status_code=400,
            details={"allowed_categories": sorted(ALLOWED_CATEGORIES)},
        )

    cards = _recommendation_service().recommend(category=category)
    return jsonify({"recommendations": [c.to_dict() for c in cards]}), 200


@api_blueprint.post("/clicks")
def record_click():
    """Record an outbound affiliate click event.

    Expected JSON body
    ------------------
    product_id   : str
    partner_id   : str
    affiliate_url: str
    """
    if not request.is_json:
        raise ApiError(
            code="invalid_content_type",
            message="Request body must be application/json.",
            status_code=415,
        )

    payload = request.get_json(silent=True) or {}
    product_id = (payload.get("product_id") or "").strip()
    partner_id = (payload.get("partner_id") or "").strip()
    affiliate_url = (payload.get("affiliate_url") or "").strip()

    if not product_id or not partner_id or not affiliate_url:
        raise ApiError(
            code="missing_click_fields",
            message="product_id, partner_id, and affiliate_url are required.",
            status_code=400,
        )

    event = _click_tracker().record(product_id, partner_id, affiliate_url)
    return jsonify({"recorded": True, "event": event.to_dict()}), 201
