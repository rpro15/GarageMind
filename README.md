# GarageMind

GarageMind is a partner-aware tire and wheel recommendation engine with a Flask HTTP API.  The primary flow lets a user request ranked product recommendations **without a VIN**.  Affiliate links are embedded in every recommendation so partner-driven revenue can be tracked from the first click.

VIN decoding and photo-based part recognition remain available as secondary, opt-in capabilities for users who want richer context.

## Product flow

```
User → GET /api/recommend?category=tire
     ← ranked product cards with affiliate URLs

User clicks a card → POST /api/track-click
                   ← click event recorded for attribution
```

## Referral monetization

Partners in the registry are assigned an `affiliate_weight` (0–1).  Partners who have a signed affiliate agreement receive a higher weight, which lifts their products in the ranking formula:

```
score = match_score   × 0.40
      + price_score   × 0.20
      + delivery_score× 0.10
      + rating_score  × 0.10
      + affiliate_weight × 0.20
```

Each recommendation card includes an `affiliate_url` built from the partner's URL template.  Click events are recorded via `/api/track-click` and carry a `session_id` for attribution.

## Stack

- Python 3.11
- Flask 3.1
- Standard-library `unittest`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

The API starts on `http://127.0.0.1:8000`.

## Test locally

```bash
python -m unittest discover -s tests -v
```

## Configuration

Environment variables are loaded directly from the process environment.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MAX_IMAGE_BYTES` | `5242880` | Maximum accepted image payload size |
| `ALLOWED_IMAGE_MIME_TYPES` | `image/jpeg,image/png,image/webp,image/gif,image/bmp` | Allowed upload types |
| `PART_RECOGNITION_PROVIDER` | `stub` | Provider toggle; unknown values fall back to stub |
| `LOG_LEVEL` | `INFO` | Application log level |

## Project structure

```text
app/
  api/
    errors.py
    routes.py
  adapters/
    stub_part_recognition.py
  config/
    settings.py
  domain/
    catalog.py          ← Partner, Product, Recommendation, ClickEvent models
    models.py
  ports/
    part_recognition.py
  services/
    affiliate.py        ← AffiliateLinkBuilder, ClickTrackingService
    part_recognition.py
    recommendation.py   ← PartnerRegistry, ProductCatalog, RecommendationRanker
    vin_decoder.py
  main.py
tests/
  test_api.py
  test_recommendations.py
  test_vin_decoder.py
```

## API

### `GET /api/recommend` ← primary flow

Returns ranked tire or wheel recommendations without requiring a VIN.

#### Parameters

| Name | Required | Description |
| --- | --- | --- |
| `category` | yes | `tire` or `wheel` |
| `n` | no | Max results to return (1–10, default 4) |

#### Example

```bash
curl "http://127.0.0.1:8000/api/recommend?category=tire&n=3"
```

#### Success response

```json
{
  "category": "tire",
  "count": 3,
  "recommendations": [
    {
      "product_id": "tire-001",
      "name": "Michelin Pilot Sport 4 205/55 R16",
      "category": "tire",
      "price": 6500.0,
      "rating": 4.8,
      "delivery_days": 3,
      "image_url": null,
      "description": "High-performance summer tyre",
      "partner": "Ozon",
      "partner_id": "ozon",
      "score": 0.7988,
      "affiliate_url": "https://ozon.ru/product/tire-001?ref=garagemind",
      "reason": "affiliate partner, highly rated"
    }
  ]
}
```

### `POST /api/track-click`

Records a click event for affiliate attribution.

#### Request body

```json
{
  "product_id": "tire-001",
  "partner_id": "ozon",
  "session_id": "optional-session-token"
}
```

#### Success response

```json
{
  "status": "recorded",
  "event": {
    "product_id": "tire-001",
    "partner_id": "ozon",
    "timestamp": "2026-06-23T11:00:00+00:00",
    "session_id": "optional-session-token"
  }
}
```

### `POST /api/recognize-part` ← secondary / optional

Accepts either `multipart/form-data` with an `image` file field or JSON with a base64 payload.

```bash
curl -X POST http://127.0.0.1:8000/api/recognize-part \
  -F "image=@/absolute/path/to/brake-pad.png"
```

### `GET|POST /api/decode-vin` ← secondary / optional

Accepts a VIN either as a `vin` query parameter or in a JSON body.

```bash
curl "http://127.0.0.1:8000/api/decode-vin?vin=1HGCM82633A004352"
```

## Engineering notes

- Handlers stay thin; validation and business logic live in services.
- `RecommendationRanker` is deterministic and easy to unit-test.
- Partners and products are currently stub in-memory data; swap in a real registry/catalog without touching route handlers.
- `ClickTrackingService` uses an in-memory list; replace with a persistent adapter when needed.
- Part recognition uses a provider port so a real model adapter can replace the stub later.
- Responses include `X-Request-Id` headers for request tracing.

## Roadmap

1. Persist partners, products and click events (SQLite / PostgreSQL).
2. Add real partner API adapters for Ozon, Wildberries, etc.
3. Enrich recommendations with VIN-derived fitment data as an optional step.
4. Plug a real vision provider into the part recognition port.
