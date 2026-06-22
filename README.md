# GarageMind

MVP Telegram bot foundation for auto product recommendations (tires/wheels first), with modular architecture for future integrations (LLM, partner APIs, databases).

## Goals

- Build core recommendation logic without external APIs at first.
- Keep architecture extensible (ports/adapters) to plug in DeepSeek, marketplace APIs, and DB later.
- Provide Dockerized local/dev deployment.

## Stack

- Python 3.11
- Aiogram 3.x
- Docker / Docker Compose

## Run

```bash
cp .env.example .env
# set TELEGRAM_BOT_TOKEN
docker compose up --build
```

## Project structure

```text
app/
  bot/
    handlers/
    keyboards/
    states/
  domain/
  services/
  ports/
  adapters/
  config/
data/
  tires_seed.json
  wheels_seed.json
tests/
```

## Feature flags

- `USE_LLM=false`
- `USE_DB=false`
- `USE_PARTNER_API=false`

Configured in `.env` and loaded via `app/config/settings.py`.

## MVP flow

1. `/start`
2. Onboarding profile: make/model/year/season/budget/driving style/category
3. Deterministic recommendation from local seed data
4. Explanation text + pseudo buy links
5. Compare and rerun

## Ideas already embedded into architecture

- Multiple cars support via user profile repository abstraction
- Confidence score in each recommendation
- Tracking provider abstraction for analytics events
- LLM provider abstraction for future explanation enrichment

## Next steps

- Replace `MockLLMProvider` with DeepSeek adapter
- Replace local catalog with partner APIs
- Replace in-memory user repo with PostgreSQL
- Add Redis caching and click attribution persistence
