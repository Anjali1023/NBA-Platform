# Intelligent Next Best Action (NBA) Platform
## Technical Documentation

---

# 1. Introduction

The **Intelligent Next Best Action (NBA) Platform** is an AI-powered Agentic Decision Intelligence platform developed to help **Customer Success Managers (CSMs)** make faster, smarter, and data-driven customer engagement decisions.

The platform leverages Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), vector search, and multiple collaborating AI agents to analyze customer interactions, retrieve organizational knowledge, assess customer risk, and recommend the most appropriate next actions.

Unlike traditional customer support systems that rely heavily on manual analysis, the NBA Platform automates customer understanding while ensuring that all recommendations pass through a Human-in-the-Loop (HITL) approval process before execution.

---

# 2. Problem Statement

Customer Success Managers are responsible for maintaining customer satisfaction, improving product adoption, reducing churn, and ensuring successful renewals.

However, making informed decisions requires analyzing information from multiple sources such as:

- Customer meeting transcripts
- CRM notes
- Product adoption reports
- Support tickets
- Historical customer interactions
- Internal knowledge documents

This manual process presents several challenges:

- Time-consuming manual analysis
- Inconsistent decision-making
- Difficulty identifying churn risks
- Limited visibility into customer history
- Delayed follow-up actions
- Knowledge scattered across multiple systems

As customer portfolios continue to grow, manual decision-making becomes increasingly inefficient and difficult to scale.

---

# 3. Proposed Solution

The Intelligent NBA Platform automates customer analysis through an orchestrated multi-agent AI workflow.

Instead of manually reviewing customer information, the system processes customer conversations using specialized AI agents that collaborate to:

- Understand customer intent
- Retrieve relevant enterprise knowledge
- Evaluate customer health
- Identify potential risks
- Generate ranked Next Best Actions
- Maintain customer memory
- Route recommendations for human approval

This approach significantly reduces analysis time while improving recommendation consistency and decision quality.

---

# 4. Project Objectives

The primary objectives of the platform include:

- Automate customer conversation analysis using LLMs
- Retrieve enterprise knowledge using Retrieval-Augmented Generation (RAG)
- Evaluate customer health and churn probability
- Generate personalized Next Best Action recommendations
- Maintain long-term customer interaction history
- Enable Human-in-the-Loop approval before action execution
- Improve customer retention through proactive recommendations
- Provide explainable AI-generated insights for Customer Success teams

---

# 5. System Architecture

The platform follows a modular multi-agent architecture orchestrated by a central Planner Agent.

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

---

# 6. System Workflow

The platform processes customer interactions through the following workflow:

### Step 1 – Customer Transcript Submission

The user submits a customer conversation or meeting transcript.

↓

### Step 2 – Planner Agent

The Planner Agent initiates the LangGraph workflow and coordinates all AI agents.

↓

### Step 3 – Ingestion Agent

The transcript is cleaned and converted into structured customer insights.

↓

### Step 4 – Retrieval Agent

Relevant organizational knowledge is retrieved from the ChromaDB vector database.

↓

### Step 5 – Risk Analysis Agent

Customer health and business risks are evaluated.

↓

### Step 6 – Recommendation Agent

Multiple Next Best Actions are generated and ranked according to priority and confidence.

↓

### Step 7 – Human Approval

A Customer Success Manager reviews and approves or rejects the generated recommendations.

↓

### Step 8 – Memory Manager

The interaction, approval decision, and recommendations are stored in Supabase for future reference.

---

# 7. AI Agent Architecture

## 7.1 Planner Agent

The Planner Agent serves as the central orchestrator of the platform.

### Responsibilities

- Receive customer requests
- Execute LangGraph workflows
- Coordinate AI agents
- Aggregate outputs
- Generate final response

---

## 7.2 Ingestion Agent

Transforms raw customer conversations into structured business information.

### Responsibilities

- Transcript preprocessing
- Entity extraction
- Customer intent detection
- Concern identification
- Structured customer context generation

---

## 7.3 Retrieval Agent

Implements the Retrieval-Augmented Generation pipeline.

### Responsibilities

- Search enterprise documents
- Retrieve relevant playbooks
- Query ChromaDB
- Provide contextual information to the LLM

---

## 7.4 Risk Analysis Agent

Evaluates customer account health using structured insights.

### Risk Factors

- Churn probability
- Renewal likelihood
- Product adoption
- Customer satisfaction
- Escalation probability

### Outputs

- Risk level
- Confidence score
- Key risk indicators

---

## 7.5 Recommendation Agent

Generates intelligent Next Best Actions.

### Example Recommendations

- Schedule onboarding sessions
- Assign dedicated Customer Success Manager
- Escalate support requests
- Offer pricing reviews
- Conduct Executive Business Reviews

Recommendations are prioritized based on confidence and business impact.

---

## 7.6 Memory Manager

Maintains historical customer information.

### Stores

- Customer interactions
- Recommendations
- Approval history
- Customer timelines
- Previous conversations

This enables continuous context across future customer engagements.

---

# 8. Retrieval-Augmented Generation (RAG)

The platform integrates Retrieval-Augmented Generation to improve the accuracy of AI-generated recommendations.

The Retrieval Agent searches enterprise documentation stored in ChromaDB before generating recommendations.

### Benefits include:

- Reduced hallucinations
- Organization-specific responses
- Context-aware recommendations
- Knowledge grounding
- Improved explainability

The retrieved knowledge is supplied to the LLM as additional context before recommendation generation.

---

# 9. Memory Management

Customer information is stored using Supabase PostgreSQL.

The Memory Manager records:

- Customer IDs
- Session IDs
- Historical conversations
- Generated recommendations
- Approval outcomes
- Customer interaction timelines

This persistent memory enables future conversations to leverage previous customer history for improved personalization.

---

# 10. Technology Stack

| Layer | Technologies |
|--------|-------------|
| Frontend | React, Vite, Tailwind CSS, Axios |
| Backend | Python, FastAPI, LangGraph, LangChain |
| LLM | Google Gemini 2.0 Flash |
| Vector Database | ChromaDB |
| Database | Supabase PostgreSQL |
| AI Libraries | Sentence Transformers |
| Utilities | Pydantic, Uvicorn, Python Dotenv |

---

# 11. Project Structure

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
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── supabase_setup.sql
└── README.md
```

---

# 12. Frontend Architecture

The frontend is developed using React and Vite.

Major responsibilities include:

- Customer transcript submission
- Dashboard visualization
- Risk score display
- Recommendation cards
- Human approval interface
- API communication

Axios is used for backend integration, while Tailwind CSS provides responsive UI components.

---

# 13. Backend Architecture

The backend is implemented using FastAPI.

Its responsibilities include:

- Workflow orchestration
- AI agent execution
- LangGraph integration
- RAG retrieval
- Customer memory management
- API endpoints
- Database communication

The backend acts as the central processing layer connecting the frontend, AI models, vector database, and persistent storage.

---

# 14. Database Architecture

The platform uses two complementary storage systems.

## ChromaDB

### Stores:

- Enterprise documentation
- Playbooks
- Knowledge embeddings

### Purpose:

- Semantic similarity search
- Retrieval-Augmented Generation

## Supabase PostgreSQL

### Stores:

- Customer interactions
- Approval history
- Recommendations
- Customer timelines

### Purpose:

- Persistent storage
- Historical customer context

---

# 15. API Documentation

## Analyze Customer Conversation

### Endpoint

```http
POST /api/analyze
```

### Request

```json
{
  "customer_id": "C001",
  "session_id": "S001",
  "input_text": "Customer transcript",
  "input_type": "meeting_transcript"
}
```

### Response

- Structured customer insights
- Risk assessment
- Ranked recommendations
- Processing status
- Interaction ID

## Approve Recommendation

### Endpoint

```http
POST /api/approve
```

This endpoint records Human-in-the-Loop approval decisions before recommendations are finalized.

---

# 16. Human-in-the-Loop (HITL)

Although AI generates recommendations automatically, final business decisions remain under human control.

The approval workflow allows Customer Success Managers to:

- Review AI recommendations
- Validate risk analysis
- Approve recommendations
- Reject recommendations
- Maintain governance and accountability

This ensures trustworthy AI-assisted decision-making.

---

# 17. Platform Workflow

```text
Customer Transcript
        │
        ▼
Planner Agent
        │
        ▼
Ingestion Agent
        │
        ▼
Retrieval Agent
        │
        ▼
Risk Analysis Agent
        │
        ▼
Recommendation Agent
        │
        ▼
Human Approval
        │
        ▼
Memory Manager
        │
        ▼
Dashboard Results
```

---

# 18. Key Features

- Multi-Agent AI Workflow
- LangGraph Orchestration
- Retrieval-Augmented Generation (RAG)
- ChromaDB Vector Search
- Google Gemini Integration
- Customer Health Analysis
- Risk Scoring
- Personalized Next Best Actions
- Human-in-the-Loop Approval
- Customer Memory Management
- FastAPI REST APIs
- React Dashboard
- Docker Support

---

# 19. Installation Guide

## Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Frontend

```bash
cd frontend

npm install

npm run dev
```

## Knowledge Base

```bash
python load_knowledge.py
```

---

# 20. Docker Deployment

Run the entire application using Docker Compose.

```bash
docker-compose up --build
```

This starts both the frontend and backend services with the required dependencies.

---

# 21. Future Enhancements

Potential future improvements include:

- Salesforce integration
- HubSpot integration
- Microsoft Dynamics support
- Slack notifications
- Automated email workflows
- Role-Based Access Control (RBAC)
- Real-time customer health dashboards
- Predictive churn analytics
- Voice conversation analysis
- Multi-language support
- AI agent performance monitoring

---

# 22. Conclusion

The Intelligent Next Best Action Platform demonstrates how Agentic AI can transform customer success operations by combining LLMs, Retrieval-Augmented Generation, vector search, and collaborative AI agents within a unified workflow.

By automating customer understanding, risk assessment, and recommendation generation while preserving Human-in-the-Loop oversight, the platform enables Customer Success Managers to make faster, more consistent, and data-driven decisions.

Its modular architecture, scalable AI workflow, and enterprise-ready design make it a strong foundation for next-generation customer success intelligence platforms.
````

