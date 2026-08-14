# WMS Voice AI

Realtime voice assistant for the Whitfield WMS, adapted from the
`clinic-voice-ai` reference (Pipecat). Staff talk to it, it answers from live
WMS data and can **execute actions** (record a receipt, mark an order shipped)
through your WMS backend.

```
┌──────────────────┐        WebRTC audio        ┌──────────────────┐
│  client/         │ ◄────────────────────────► │  server/         │
│  React + Vite    │                            │  Pipecat bot     │
│  (browser)       │ ──── POST /api/offer ────► │  (:7860)         │
└──────────────────┘         SDP handshake      └──────────────────┘
                                                    │      │      │
                                            Deepgram  │      │  Groq
                                            STT/TTS         (WMS tools → your backend)
```

| Piece | Service |
| ----- | ------- |
| Speech-to-text | Deepgram |
| LLM | Groq (with WMS tool-calling) |
| Text-to-speech | Deepgram Aura |
| WMS data + actions | Your WMS backend REST API (`core/apis`) |

## Layout

```
voice_ai/
├── server/
│   ├── bot.py              Pipecat pipeline (start here)
│   ├── wms_tools.py        WMS read tools + action tools (call the backend)
│   └── .env.example        DEEPGRAM_API_KEY, GROQ_API_KEY, WMS_*
└── client/                 React + Vite voice UI
```

> Dependencies (including Pipecat) are shared in the single `requirements.txt`
> at the repo root — there is no separate voice requirements file.

## Getting started

### Prerequisites
- Python 3.10+, Node 18+
- Deepgram API key (STT + TTS), Groq API key (LLM)
- The WMS backend running on `:8000`, and a service-account user for actions

### 1. Install dependencies (from the repo root — single `requirements.txt`)
```bash
pip install -r requirements.txt
```

### 2. Server
```bash
cd voice_ai/server
cp .env.example .env        # paste your Deepgram, Groq, and WMS service keys
python bot.py               # starts Pipecat runner on :7860
```

### 2. Client
```bash
cd voice_ai/client
npm install
npm run dev                 # http://localhost:5173 — click Start call, allow mic
```

## Voice commands the bot handles
- "How many Widget A do we have?" → `stock_by_upc`
- "Which orders are pending?" → `pending_orders`
- "Where is Widget A stored?" → `bin_location`
- "What do I do with a Grade C damaged item?" → `damage_process`
- "Received 24 units of UPC 012345678905, 2 damaged Grade B" → `record_receipt` (action)
- "Mark order ORD-5521 as shipped" → `mark_order_shipped` (action)

## Action security
Action tools (`record_receipt`, `mark_order_shipped`) call the WMS backend using a
service-account token from `.env` (`WMS_SERVICE_EMAIL`/`WMS_SERVICE_PASSWORD`).
Create a dedicated admin user for this — do not reuse the default bootstrap admin
or share staff passwords. If those keys are missing, the bot can still answer
questions but action tools return an error.
