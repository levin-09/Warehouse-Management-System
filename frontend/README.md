# Whitfield WMS — Frontend

React + TypeScript + Vite frontend for the Whitfield WMS backend, styled to match
your reference image (dark-teal sidebar `#1B475D`, warm canvas `#F2F3EC`, mint/amber
status chips). It connects to the FastAPI backend and everything you do in the UI is
persisted to the backend (and MongoDB).

## Quick start

1. **Backend running** on `http://localhost:8000` (see the `backend/` README).
2. Install and run the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev        # http://localhost:5173
   ```
3. Log in with the seeded admin:
   ```
   email:    dan@whitfieldfulfillment.com
   password: admin123
   ```

Vite proxies `/v1` and `/api` to `http://localhost:8000`, so the browser stays
same-origin and no CORS setup is needed.

## Pages

| Route | Page | Roles |
|-------|------|-------|
| `/` | Dashboard (KPIs, warehouse overview, inventory, activity feed) | all |
| `/inventory` | Stock levels + low-stock filter + adjust dialog | all |
| `/products` | Product catalog + add | all |
| `/shipments` | Inbound receiving (draft → confirm) | all |
| `/orders` | Kanban order board + create | all |
| `/returns` | Return processing | admin/manager/staff |
| `/damage` | Damage records + log | admin/manager/staff |
| `/bins` | Bin locations + add | all |
| `/sellers` | Sellers + add | admin/manager |
| `/warehouses` | Warehouses + add | admin/manager |
| `/users` | Users + add/delete (admin) | admin |
| `/invoices` | Invoices + generate | admin |
| `/notifications` | Alerts, mark read | all |
| `/audit` | Audit trail (read-only) | admin |
| `/assistant` | AI chatbot (needs GROQ_API_KEY) | all |
| `/voice` | Voice assistant (needs Pipecat server + keys) | all |

Separate **seller login** at `/seller-login` (calls `POST /v1/auth/seller/login`).

## Voice Assistant

The **Voice Assistant** page at `/voice` connects over WebRTC to the Pipecat voice
bot in `../backend/voice_ai/`. Vite proxies `/api` to the Pipecat server on `:7860`.

To use it you need the voice server running:
```bash
cd backend/voice_ai/server
pip install -r ../../requirements.txt
cp .env.example .env      # add DEEPGRAM_API_KEY, GROQ_API_KEY, WMS_SERVICE_EMAIL/PASSWORD
python bot.py             # Pipecat runner on :7860
```
Then open the frontend `/voice` page, click **Start call**, and allow the
microphone. You can ask it to check stock, find bin locations, or record a
receipt by voice.

## Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts          # proxies /v1 and /api to :8000
└── src/
    ├── api/
    │   ├── client.ts        # axios instance, auth header, 401 redirect
    │   ├── endpoints.ts     # every backend endpoint
    │   └── types.ts         # TS types for all entities/enums
    ├── components/          # Modal, Table, Field, EmptyState
    ├── lib/
    │   ├── auth.tsx         # auth context (JWT in localStorage)
    │   ├── toast.tsx        # toast notifications
    │   └── status.ts        # status chip + number/currency formatting
    └── pages/               # one page per route
```

## Env

Optional `VITE_API_URL` (defaults to same-origin, which works via the dev proxy):
```bash
# .env.local
VITE_API_URL=http://localhost:8000
```
