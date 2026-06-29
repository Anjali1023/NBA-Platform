
# NBA Platform

NBA Platform is a full-stack agentic AI application for B2B customer success teams. It ingests customer conversations, retrieves playbook guidance, scores account risk, and recommends next best actions for customer success managers.

## Architecture

```text
Frontend (React + Vite + Tailwind)
    │
    ▼
FastAPI Backend
    ├─ Planner Agent (LangGraph)
    ├─ Ingestion Agent (Gemini)
    ├─ Retrieval Agent (ChromaDB)
    ├─ Risk Agent (Gemini)
    ├─ Recommendation Agent (Gemini)
    └─ Memory Manager (Supabase)
```

## Tech Stack

- Python, FastAPI, LangGraph, LangChain
- Google Gemini 2.0 Flash
- ChromaDB local vector database
- Supabase PostgreSQL
- React, Vite, Tailwind CSS, Axios

## Setup

1. Clone the repository
2. Get a Gemini API key from aistudio.google.com
3. Create a Supabase project and run the SQL from supabase_setup.sql
4. Fill in backend/.env with your keys
5. Start the app with Docker Compose or manual commands
6. Open http://localhost:5173

### Docker Compose

```bash
docker-compose up --build
```

### Manual setup

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
```

## Example Transcript

"We are frustrated by slow support and confusing onboarding. We are considering switching to a competitor because pricing feels high. We need better adoption support before renewal."

## Team Members and Roles

- Product Lead: defines the customer success workflow
- AI Engineer: builds agent orchestration and LLM orchestration
- Frontend Engineer: designs the operator experience
- Data Engineer: manages vector and relational storage

## Future Scope

- CRM integration with Salesforce and HubSpot
- Email automation for approved actions
- Multi-tenant workspace support
- Real-time health monitoring dashboards
