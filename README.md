# 🚀 Intelligent Next Best Action (NBA) Platform

An **AI-powered Agentic Decision Intelligence Platform** that helps **Customer Success Managers (CSMs)** analyze customer interactions, assess account health, retrieve organizational knowledge, and generate intelligent **Next Best Action (NBA)** recommendations.

The platform combines **LLMs**, **Agentic AI**, **Retrieval-Augmented Generation (RAG)**, **Vector Search**, and **Human-in-the-Loop (HITL)** approval to support faster and more consistent customer success decisions.

---

# Team Details

| Field | Details |
|--------|---------|
| **Team Name** | **CodeCrafters** |
| **Project Name** | Intelligent Next Best Action (NBA) Platform |
| **Team Size**  | 3 Members |
| **Team Member 1**  | Annavaram Leela Meghana - 23071A6604 |
| **Team Member 2** | Dhanavath Anjali - 23071A6614 |
| **Team Member 3** | Jatavath Vaishnavi - 23071A6627 |

---

# Project Overview

The **Intelligent Next Best Action (NBA) Platform** is an AI-powered
Agentic Decision Intelligence system designed to help Customer Success
Managers analyze customer conversations and generate intelligent,
data-driven recommendations.

The platform combines **Large Language Models (Google Gemini),
LangGraph-based AI agents, Retrieval-Augmented Generation (RAG),
ChromaDB vector search, and Supabase memory management** to automate
customer analysis.

Instead of manually reviewing meeting transcripts, CRM notes, support
tickets, and customer history, the platform orchestrates multiple AI
agents to:

- Understand customer intent
- Retrieve relevant enterprise knowledge
- Evaluate customer health
- Identify potential risks
- Generate ranked Next Best Actions
- Maintain customer memory
- Route recommendations for human approval

This reduces manual effort, improves consistency in decision-making, and
helps Customer Success teams proactively retain customers and improve
business outcomes.

------------------------------------------------------------------------

# GitHub Repository Link

``` text
https://github.com/Anjali1023/NBA-Platform
```

------------------------------------------------------------------------

# Setup Instructions

## Prerequisites

-   Python 3.10+
-   Node.js 18+
-   npm
-   Docker (optional)
-   Supabase account
-   Google Gemini API Key

---

## Running the Project

> **Important:** Start the services in the following order:
>
> 1. ChromaDB
> 2. Backend
> 3. Frontend

---

### Terminal 1 — Start ChromaDB

```bash
cd nba-platform\backend

chroma run --host localhost --port 8002
```

This starts the ChromaDB vector database, which is required by the Retrieval Agent.

---

### Terminal 2 — Start Backend

```bash
## Backend Setup

``` bash
git clone <repository-url>
cd nba-platform/backend
pip install -r requirements.txt
 
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

```

Create a `.env` file:

``` env
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_KEY=YOUR_SUPABASE_KEY
CHROMA_HOST=localhost
CHROMA_PORT=8002
```


The FastAPI backend will be available at:

```
http://localhost:8001
```

---

### Terminal 3 — Start Frontend

```bash
cd nba-platform\frontend

npm run dev
```

The React application will start on:

```
http://localhost:5173
```

---

## Access the Application

Once all three services are running, open your browser and navigate to:

```
http://localhost:5173
```

---

## Startup Sequence

Always start the application in the following order:

1. **ChromaDB** (Port **8002**)
2. **FastAPI Backend** (Port **8001**)
3. **React Frontend** (Port **5173**)

Following this sequence ensures that the backend can successfully connect to the ChromaDB vector database before processing requests.


Frontend: `http://localhost:5173`

Backend: `http://localhost:8000`

---

## Database Setup

1.  Create a Supabase project.
2.  Execute:

``` bash
supabase_setup.sql
```

## Load Knowledge Base

``` bash
python load_knowledge.py
```

## Docker Deployment

``` bash
docker-compose up --build
```

------------------------------------------------------------------------

# Additional Notes

-   Built using a modular multi-agent architecture orchestrated with
    LangGraph.
-   Uses Google Gemini 2.0 Flash as the LLM.
-   Implements Retrieval-Augmented Generation (RAG) with ChromaDB.
-   Stores customer interactions in Supabase PostgreSQL.
-   Supports Human-in-the-Loop (HITL) approval.
-   Includes Docker deployment support.
-   Future enhancements include Salesforce, HubSpot, Microsoft Dynamics,
    Slack, RBAC, predictive churn analytics, multilingual support, and
    AI agent performance monitoring.
