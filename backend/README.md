# Whitfield WMS — Backend

Backend for the Whitfield Fulfillment Warehouse Management System (WMS), following
the [Eigi backend standards](https://github.com/eigi-ai/eigi-skills/blob/main/.codex/skills/eigi-backend-standards/SKILL.md)
(routes → controllers → CRUD/services → models) and the MongoDB data design from the case study.

This is the **backend only**. The scheduled automation described in the case study's
"AI Agent" section is implemented as **plain, non-AI background jobs** (see
[`core/jobs/`](core/jobs/)).

### AI features (optional, opt-in via API keys)

- **WMS Chatbot** — a Groq agent loop with WMS MongoDB tools, integrated into the
  API at `POST /v1/chat` and `POST /v1/chat/stream`. Tools replace the web tools
  from the `genai_chatbot` reference with WMS queries (stock by UPC, pending orders,
  bin locations, shipment status, damage process, inventory/order/seller overviews).
  Per-session history. Set `GROQ_API_KEY`/`GROQ_MODEL` in `.env`. Without a key,
  the tools and endpoints still exist but `/v1/chat` returns 503.

- **WMS Voice AI** — a Pipecat realtime voice assistant (Deepgram STT/TTS + Groq),
  adapted from the `clinic-voice-ai` reference. Lives in [`voice_ai/`](voice_ai/).
  It answers questions and can execute warehouse actions (record a receipt, ship an
  order) by calling this backend. See [`voice_ai/README.md`](voice_ai/README.md).

## Tech stack

- Python 3.11+
- FastAPI + Uvicorn
- MongoDB via `motor` (async) / `pymongo`
- Pydantic v2 schemas
- JWT (python-jose) auth + role-based access control
- APScheduler for periodic jobs

## Folder structure

```
backend/
  main.py                     # runtime entrypoint (uvicorn)
  commons/
    logger.py                 # central logging setup
    auth.py                   # JWT encode/decode helpers
  core/
    config.py                 # environment configuration
    database/database.py      # shared MongoDB client/collection helpers
    database/init_db.py       # indexes + seed data
    models/                   # Mongo document shapes (ODMantic-style dataclasses)
    apis/
      api.py                  # FastAPI app aggregator
      routes/                 # thin HTTP routes
      schemas/requests/       # request wire contracts
      schemas/responses/      # response wire contracts
    controllers/              # domain orchestration + RBAC/business rules
    cruds/                    # persistence layer
    services/                 # notifications, billing, forecasting
    jobs/                     # scheduled (non-AI) automation
```

## Setup & run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit MONGODB_URI / SECRET_KEY
python main.py                 # == uvicorn core.apis.api:app --reload
# or, without auto-reload:
uvicorn core.apis.api:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t whitfield-wms .
docker run -p 8000:8000 --env-file .env whitfield-wms
```

## Auth & roles

`POST /v1/auth/login` returns a JWT. Endpoints decode the bearer token and enforce
role-based access in the controller layer. Roles: `admin`, `manager`, `staff`
(staff combines receiving and picking work). Sellers authenticate separately and
are scoped to their own data.

## Core guarantees (the four problems)

1. **Duplicate entry prevention** — unique index on `shipments.shipment_ref` + pre-insert check.
2. **Concurrent editing** — atomic `find_one_and_update` with `$gte` guards and multi-doc transactions.
3. **Audit trail** — every mutation writes to `audit_logs`; API exposes no update/delete for logs.
4. **Access control** — RBAC enforced in controllers per warehouse.

## Docs

With the server running, interactive API docs are at `http://localhost:8000/docs`.
