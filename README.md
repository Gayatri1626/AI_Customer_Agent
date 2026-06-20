# ShopEase AI Customer Support Agent

A full-stack AI agent that processes or denies e-commerce refund requests using a LangGraph ReAct loop, streamed in real-time to a Next.js frontend with voice support via the OpenAI Realtime API.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Next.js Frontend (port 3000)                                │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │  Customer Chat UI   │  │  Admin Dashboard             │  │
│  │  + Voice (WebRTC)   │  │  WebSocket real-time logs    │  │
│  └─────────────────────┘  └──────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │  HTTP + WebSocket
┌────────────────────────▼─────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  LangGraph ReAct Agent (GPT-4o)                        │ │
│  │  Tools:                                                 │ │
│  │    lookup_customer · get_order_details                  │ │
│  │    get_refund_policy · validate_refund_eligibility      │ │
│  │    approve_refund · deny_refund · list_customers        │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌───────────────────┐  ┌──────────────────────────────────┐ │
│  │  Mock CRM DB      │  │  Refund Policy Document          │ │
│  │  (15 customers)   │  │  (policy rules + full text)      │ │
│  └───────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

- **LangGraph ReAct agent** — tool-calling loop that looks up customers, checks orders, validates policy, and approves/denies refunds
- **Streaming responses** — Server-Sent Events stream tokens and reasoning steps in real-time
- **WebSocket reasoning logs** — admin dashboard receives every tool call and result as it happens
- **Voice pipeline** — OpenAI Realtime API (WebRTC) for voice-based support requests
- **Admin dashboard** — customer CRM view, live reasoning logs, refund policy viewer
- **Strict policy enforcement** — 7 rule categories covering return windows, item condition, digital goods, consumables, loyalty tiers, and more

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key with access to `gpt-4o` and `gpt-4o-realtime-preview`

### 1. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the server
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.  
API docs: `http://localhost:8000/docs`

### 2. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## Usage

### Customer chat (`/`)

1. Open `http://localhost:3000`
2. Tell the agent your customer ID (e.g. `C001`) or email, and describe your return request
3. The agent will look up your order, check the refund policy, and give you a decision
4. Click **"Show reasoning"** to see tool calls in the sidebar
5. Click the **microphone** button to use voice instead of text

### Admin dashboard (`/admin`)

1. Open `http://localhost:3000/admin`
2. **Customers tab** — browse all 15 CRM profiles; expand each to see order details
3. **Logs tab** — live feed of all agent tool calls and results across sessions
4. **Policy tab** — full text of the ShopEase refund policy

---

## Test scenarios

| Customer | Order | Expected outcome | Why |
|----------|-------|-----------------|-----|
| C001 (Alice, Gold) | ORD-10021 | **Approved** (store credit) | Electronics, 8 days old, Gold adds 5 days → within 20-day window |
| C002 (Brian, Silver) | ORD-10022 | **Denied** | Footwear, worn, 35 days old → window expired |
| C003 (Carmen) | ORD-10023 | **Approved** (original payment) | Unopened, within 7 days |
| C004 (David) | ORD-10024 | **Approved** (original payment) | Defective TV, 3 days old |
| C005 (Eva) | ORD-10025 | **Denied** | Digital download — non-refundable |
| C007 (Grace) | ORD-10027 | **Approved** | Allergic reaction to Beauty product within 7 days |
| C008 (Henry) | ORD-10028 | **Denied** | Accessories, 60 days old → window expired |
| C013 (Mia) | ORD-10033 | **Approved** | Wrong colour received, store credit |
| C014 (Noah) | ORD-10034 | **Denied** | Opened protein powder — non-refundable consumable |

---

## Project structure

```
├── backend/
│   ├── main.py                  # FastAPI app, SSE chat, WebSocket logs, voice session
│   ├── requirements.txt
│   ├── .env.example
│   ├── agent/
│   │   ├── graph.py             # LangGraph ReAct graph
│   │   ├── state.py             # AgentState TypedDict
│   │   └── tools.py             # 7 agent tools
│   └── data/
│       ├── crm_database.py      # 15 customer profiles + orders
│       └── refund_policy.py     # Policy text + machine-readable rules
└── frontend/
    ├── app/
    │   ├── page.tsx             # Customer chat + voice UI
    │   ├── admin/page.tsx       # Admin dashboard
    │   ├── layout.tsx
    │   └── globals.css
    ├── next.config.ts           # API proxy to :8000
    ├── tailwind.config.ts
    └── package.json
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send a message; returns SSE stream |
| `WS` | `/ws/admin` | Admin WebSocket — all session logs |
| `WS` | `/ws/logs/{session_id}` | Per-session reasoning log stream |
| `POST` | `/api/voice/session` | Create OpenAI Realtime ephemeral token |
| `GET` | `/api/customers` | List all CRM customers |
| `GET` | `/api/customers/{id}` | Get single customer |
| `GET` | `/api/refund-policy` | Return policy document |
| `GET` | `/api/sessions` | List chat sessions with log counts |
| `GET` | `/api/sessions/{id}/logs` | Get all logs for a session |

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| LLM | OpenAI GPT-4o |
| Agent framework | LangGraph (ReAct pattern) |
| Backend | FastAPI + uvicorn |
| Streaming | Server-Sent Events (SSE) |
| Real-time logs | WebSocket |
| Voice | OpenAI Realtime API (WebRTC) |
| Frontend | Next.js 15 + React 19 |
| Styling | Tailwind CSS |
| Language | Python 3.11 + TypeScript |
