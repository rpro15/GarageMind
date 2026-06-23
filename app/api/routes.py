from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.errors import ApiError
from app.services.part_recognition import PartRecognitionService
from app.services.vin_decoder import VinDecoderService


api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def _part_service() -> PartRecognitionService:
    return current_app.extensions["services"]["part_recognition"]


def _vin_service() -> VinDecoderService:
    return current_app.extensions["services"]["vin_decoder"]


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

llm_client = DeepSeekClient()
catalog = MockPartnerCatalog()
recommendation_service = TireRecommendationService(llm_client, catalog)

@api_bp.route('/recommend_tires', methods=['POST'])
async def recommend_tires():
    """Эндпоинт для Mini App: принимает JSON с параметрами, возвращает рекомендации."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    
    required = ['brand', 'model', 'year', 'driving_style']
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing fields: {required}"}), 400
    
    try:
        tire_request = TireRequest(
            brand=data['brand'],
            model=data['model'],
            year=int(data['year']),
            driving_style=DrivingStyle(data['driving_style']),
            budget=int(data['budget']) if data.get('budget') else None,
            season=Season(data['season']) if data.get('season') else None
        )
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    
    try:
        result = await recommendation_service.get_recommendation(tire_request)
    except Exception as e:
        logger.exception("Recommendation failed")
        return jsonify({"error": "Internal server error"}), 500
    
    response = {
        "advice": result.advice,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "currency": p.currency,
                "image_url": p.image_url,
                "partner_link": p.partner_link,
                "source": p.source
            } for p in result.products
        ],
        "request": {
            "brand": result.request.brand,
            "model": result.request.model,
            "year": result.request.year,
            "driving_style": result.request.driving_style.value,
            "budget": result.request.budget,
            "season": result.request.season.value if result.request.season else None
        }
    }
    return jsonify(response), 200

@api_bp.route('/brands', methods=['GET'])
def get_brands():
    """Возвращает список популярных марок."""
    brands = [
        "Lada", "Kia", "Hyundai", "Toyota", "Volkswagen", 
        "Skoda", "Nissan", "Mitsubishi", "BMW", "Mercedes-Benz",
        "Audi", "Ford", "Renault", "Chevrolet", "Mazda"
    ]
    return jsonify(sorted(brands)), 200

@api_bp.route('/models', methods=['GET'])
def get_models():
    """Возвращает модели для выбранной марки (заглушка)."""
    brand = request.args.get('brand')
    if not brand:
        return jsonify({"error": "Missing brand parameter"}), 400
    mock_models = {
        "Toyota": ["Camry", "Corolla", "RAV4", "Land Cruiser", "Yaris"],
        "Kia": ["Rio", "Sportage", "Cerato", "Stinger", "Soul"],
        "Hyundai": ["Solaris", "Creta", "Tucson", "Elantra", "Santa Fe"],
        "Lada": ["Granta", "Vesta", "Niva", "Kalina", "Priora"],
        "Volkswagen": ["Polo", "Golf", "Passat", "Tiguan", "Jetta"],
    }
    models = mock_models.get(brand, [])
    return jsonify(models), 200