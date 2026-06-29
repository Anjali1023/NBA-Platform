# 🚀 Intelligent Next Best Action (NBA) Platform

An **AI-powered Agentic Decision Intelligence Platform** that helps **Customer Success Managers (CSMs)** analyze customer interactions, assess account health, retrieve organizational knowledge, and generate intelligent **Next Best Action (NBA)** recommendations.

The platform combines **LLMs**, **Agentic AI**, **Retrieval-Augmented Generation (RAG)**, **Vector Search**, and **Human-in-the-Loop (HITL)** approval to support faster and more consistent customer success decisions.

---

# 📖 Overview

Customer Success teams often spend significant time reviewing:

* Meeting transcripts
* Customer conversations
* Support tickets
* CRM notes
* Product adoption data

to determine:

* Customer health
* Churn risk
* Renewal probability
* Escalation priority
* Appropriate follow-up actions

The **Intelligent NBA Platform** automates this process using a multi-agent AI workflow that analyzes customer context, retrieves organizational knowledge, evaluates risks, and recommends personalized next best actions.

---

# 🎯 Objectives

* Analyze customer conversations using LLMs
* Retrieve relevant enterprise knowledge with RAG
* Predict customer risk and health score
* Generate personalized Next Best Actions
* Maintain customer interaction history
* Support Human-in-the-Loop approval before execution

---

# 🏗 System Architecture

```text
                    Customer Transcript
                            │
                            ▼
                Planner Agent (LangGraph)
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 Ingestion Agent     Retrieval Agent      Memory Manager
        │                   │                   │
        ▼                   ▼                   ▼
 Structured Data     Chroma Vector DB     Supabase Database
        │
        ▼
 Risk Analysis Agent
        │
        ▼
 Recommendation Agent
        │
        ▼
 Human Approval (HITL)
        │
        ▼
 Final Next Best Actions
```

---

# 🤖 AI Agents

## 🧠 Planner Agent

Acts as the workflow orchestrator.

**Responsibilities**

* Receives customer requests
* Coordinates all AI agents
* Executes LangGraph workflow
* Aggregates outputs
* Returns final recommendations

---

## 📥 Ingestion Agent

Processes raw customer conversations into structured information.

**Responsibilities**

* Clean transcripts
* Extract key entities
* Detect customer intent
* Identify concerns
* Generate structured customer context

---

## 🔍 Retrieval Agent

Implements the Retrieval-Augmented Generation (RAG) pipeline.

**Responsibilities**

* Search organizational knowledge
* Retrieve playbooks and documentation
* Query ChromaDB vector database
* Provide relevant context to the LLM

---

## 📊 Risk Analysis Agent

Evaluates overall customer health.

**Analyzes**

* Churn probability
* Renewal risk
* Adoption issues
* Customer satisfaction
* Escalation likelihood

**Outputs**

* Risk level
* Confidence score
* Key risk factors

---

## 💡 Recommendation Agent

Generates ranked Next Best Actions.

**Example Recommendations**

* Schedule onboarding session
* Escalate support ticket
* Offer pricing review
* Assign dedicated CSM
* Conduct executive business review

Recommendations are ranked by **priority** and **confidence score**.

---

## 🗂 Memory Manager

Maintains customer interaction history using Supabase.

Stores:

* Conversation history
* Recommendations
* Human approvals
* Customer timeline

---

# 🛠 Technology Stack

| Layer           | Technologies                                            |
| --------------- | ------------------------------------------------------- |
| Frontend        | React, Vite, Tailwind CSS, Axios                        |
| Backend         | Python, FastAPI, LangGraph, LangChain                   |
| LLM             | Google Gemini 2.0 Flash                                 |
| Vector Database | ChromaDB                                                |
| Database        | Supabase PostgreSQL                                     |
| Libraries       | Sentence Transformers, Pydantic, Uvicorn, Python Dotenv |

---

# 📂 Project Structure

```text
nba-platform/
│
├── backend/
│   ├── agents/
│   ├── api/
│   ├── memory/
│   ├── data/
│   ├── chroma/
│   ├── chroma_data/
│   ├── load_knowledge.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── supabase_setup.sql
└── README.md
```

---

# ⚙ Installation

## 1. Clone Repository

```bash
git clone <repository-url>
cd nba-platform
```

---

## 2. Backend Setup

```bash
cd backend

pip install -r requirements.txt
```

Create a `.env` file:

```env
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY

SUPABASE_URL=YOUR_SUPABASE_URL

SUPABASE_KEY=YOUR_SUPABASE_KEY
```

Run the backend:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## 3. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```
http://localhost:5173
```

Backend:

```
http://localhost:8000
```

---

# 🐳 Docker Deployment

Run the entire application:

```bash
docker-compose up --build
```

---

# 🗄 Database Setup

1. Create a Supabase project.
2. Execute:

```text
supabase_setup.sql
```

This creates the required tables for storing customer interactions and approval history.

---

# 📚 Knowledge Base

Load enterprise documents into ChromaDB:

```bash
python load_knowledge.py
```

---

# 🔄 Platform Workflow

1. Customer transcript is submitted.
2. Planner Agent initiates the workflow.
3. Ingestion Agent extracts structured insights.
4. Retrieval Agent fetches relevant company knowledge.
5. Risk Analysis Agent evaluates account health.
6. Recommendation Agent generates ranked actions.
7. Human approves or rejects recommendations.
8. Memory Manager stores interaction history.
9. Results are displayed on the dashboard.

---

# 📡 API Endpoints

## Analyze Customer Conversation

```http
POST /api/analyze
```

**Request**

```json
{
  "customer_id": "C001",
  "session_id": "S001",
  "input_text": "Customer transcript",
  "input_type": "meeting_transcript"
}
```

**Response**

* Structured customer insights
* Risk analysis
* Recommended actions
* Interaction ID
* Processing status

---

## Approve Recommendation

```http
POST /api/approve
```

Used for Human-in-the-Loop approval before recommendations are finalized.

---

# ✨ Key Features

* Multi-Agent AI Workflow
* LangGraph Orchestration
* Retrieval-Augmented Generation (RAG)
* ChromaDB Vector Search
* Google Gemini Integration
* Human-in-the-Loop Approval
* Customer Memory Management
* Risk Scoring
* Ranked Next Best Actions
* FastAPI REST APIs
* React Dashboard
* Docker Deployment

---

# 📥 Example Input

```text
We are frustrated by slow support and confusing onboarding.
We are considering switching to a competitor because pricing feels high.
We need better adoption support before renewal.
```

---

# 📤 Example Output

### Risk Level

```text
High
```

### Recommended Actions

* Schedule onboarding workshop
* Escalate support issue
* Assign dedicated Customer Success Manager
* Conduct pricing review meeting
* Schedule an Executive Business Review (EBR)

---

# 🚀 Future Enhancements

* Salesforce Integration
* HubSpot Integration
* Microsoft Dynamics Integration
* Slack Notifications
* Email Automation
* Role-Based Access Control
* Real-Time Customer Health Dashboard
* Predictive Churn Analytics
* Voice & Meeting Recording Analysis
* Multi-language Support
* Agent Performance Monitoring

---

# 👥 Team Responsibilities

| Role              | Responsibilities                                    |
| ----------------- | --------------------------------------------------- |
| Product Lead      | Customer success workflow, business requirements    |
| AI Engineer       | LangGraph, LLM integration, RAG pipeline, AI agents |
| Frontend Engineer | React dashboard, UI/UX, API integration             |
| Data Engineer     | ChromaDB, Supabase, knowledge ingestion             |

---

# 📄 License

This project is developed for educational purposes and hackathon demonstrations.

---

# 🙏 Acknowledgements

* Google Gemini
* LangGraph
* LangChain
* ChromaDB
* FastAPI
* React
* Supabase
* Tailwind CSS
