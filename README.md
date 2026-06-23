# GarageMind

GarageMind exposes a production-oriented HTTP API for two first-iteration capabilities:

- photo-based part recognition with a deterministic local stub provider;
- VIN validation and decoding with proper check-digit verification.

Starting with this iteration the project gains a **database-backed part catalog**.  A SQLite database is created automatically on first startup and seeded with the default part catalog.  The architecture keeps provider and service boundaries explicit so a real catalog, model provider, and persistence layer can be added later without rewriting the HTTP contract.

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
| `DATABASE_PATH` | `garagemind.db` | Path to the SQLite database file; use `:memory:` for an ephemeral in-process database |

## Project structure

```text
app/
  api/
    errors.py
    routes.py
  adapters/
    in_memory_catalog_repository.py
    sqlite_catalog_repository.py
    stub_part_recognition.py
  config/
    settings.py
  domain/
    models.py
  ports/
    catalog_repository.py
    part_recognition.py
  services/
    part_recognition.py
    vin_decoder.py
  main.py
tests/
  test_api.py
  test_catalog.py
  test_vin_decoder.py
```

## API

### `GET /api/catalog`

Returns all parts in the catalog.  The catalog is seeded from the built-in part list on first startup.

#### Response

```json
{
  "parts": [
    {
      "id": 1,
      "part_name": "Brake Pad Set",
      "category": "braking",
      "created_at": "2024-01-01T00:00:00+00:00"
    }
  ],
  "total": 8
}
```

### `GET /api/catalog/<id>`

Returns a single catalog part by its integer id.

#### Success response

```json
{
  "id": 1,
  "part_name": "Brake Pad Set",
  "category": "braking",
  "created_at": "2024-01-01T00:00:00+00:00"
}
```

#### Not-found response

Status: `404 Not Found`

```json
{
  "error": {
    "code": "part_not_found",
    "message": "No catalog part with id 999.",
    "request_id": "8a9f..."
  }
}
```

### `POST /api/recognize-part`

Accepts either `multipart/form-data` with an `image` file field or JSON with a base64 payload.

#### Multipart example

```bash
curl -X POST http://127.0.0.1:8000/api/recognize-part \
  -F "image=@/absolute/path/to/brake-pad.png"
```

#### JSON base64 example

```bash
curl -X POST http://127.0.0.1:8000/api/recognize-part \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5+G94AAAAASUVORK5CYII=",
    "content_type": "image/png",
    "filename": "part.png"
  }'
```

#### Success response

```json
{
  "part_name": "Brake Pad Set",
  "category": "braking",
  "confidence": 0.74,
  "possible_matches": [
    {
      "part_name": "Brake Pad Set",
      "category": "braking",
      "confidence": 0.74
    },
    {
      "part_name": "Oil Filter",
      "category": "engine",
      "confidence": 0.44
    },
    {
      "part_name": "Shock Absorber",
      "category": "suspension",
      "confidence": 0.31
    }
  ],
  "source": "stub"
}
```

#### Error examples

Unsupported media type:

```json
{
  "error": {
    "code": "unsupported_media_type",
    "message": "Use multipart/form-data or application/json for this endpoint.",
    "request_id": "8a9f..."
  }
}
```

Malformed base64:

```json
{
  "error": {
    "code": "invalid_base64_image",
    "message": "image_base64 must be a valid base64-encoded string.",
    "request_id": "8a9f..."
  }
}
```

### `GET|POST /api/decode-vin`

Accepts a VIN either as a `vin` query parameter or in a JSON body.

#### Request examples

```bash
curl "http://127.0.0.1:8000/api/decode-vin?vin=1HGCM82633A004352"
```

```bash
curl -X POST http://127.0.0.1:8000/api/decode-vin \
  -H "Content-Type: application/json" \
  -d '{"vin":"1HGCM82633A004352"}'
```

#### Success response

```json
{
  "vin": "1HGCM82633A004352",
  "is_valid": true,
  "validation_errors": [],
  "decoded": {
    "wmi": "1HG",
    "region": "United States",
    "manufacturer": "Honda",
    "model_year": 2003,
    "plant_code": "A",
    "serial": "004352"
  }
}
```

#### Invalid VIN response

Status: `422 Unprocessable Entity`

```json
{
  "vin": "1HGCM82633A004353",
  "is_valid": false,
  "validation_errors": [
    "VIN check digit mismatch: expected 5, got 3."
  ],
  "decoded": {
    "wmi": "1HG",
    "region": "United States",
    "manufacturer": "Honda",
    "model_year": 2003,
    "plant_code": "A",
    "serial": "004353"
  }
}
```

## Engineering notes

- Handlers stay thin; validation and business logic live in services.
- Part recognition is implemented behind a provider port so a real model adapter can replace the stub later.
- VIN decoding is deterministic and fully test-covered for checksum and edge cases.
- Responses include `X-Request-Id` headers for request tracing.
- The catalog repository is accessed through the `CatalogRepository` port; the SQLite adapter can be replaced with any other storage backend without touching the HTTP layer.

## Storage

On startup, `create_app` builds a `SqliteCatalogRepository` from `DATABASE_PATH` and seeds it with the default part catalog if the table is empty.  The database schema is created automatically via `CREATE TABLE IF NOT EXISTS` so no migration tooling is required for the initial schema.

## Current limitation and roadmap

Suggested follow-up path:

1. plug a real vision provider into the part recognition port;
2. enrich VIN decoding with a larger WMI/manufacturer dataset;
3. add inventory/catalog joins once the catalog schema stabilises.
