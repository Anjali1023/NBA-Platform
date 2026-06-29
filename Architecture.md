# Intelligent Next Best Action (NBA) Platform

## High-Level Architecture

The **Intelligent Next Best Action (NBA) Platform** is an AI-powered Agentic Decision Intelligence system that enables Customer Success Managers (CSMs) to make proactive, data-driven decisions. The platform leverages multiple AI agents, Retrieval-Augmented Generation (RAG), vector search, and persistent memory to analyze customer interactions and recommend the most appropriate next actions.

The architecture follows a modular, agent-based design orchestrated by **LangGraph**, where each AI agent is responsible for a specific stage of the workflow.

---

# Architecture Overview

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
 Structured Data     ChromaDB Vector DB   Supabase Database
        └───────────────────┼───────────────────┘
                            │
                            ▼
                 Risk Analysis Agent
                            │
                            ▼
                Recommendation Agent
                            │
                            ▼
             Human-in-the-Loop (HITL)
                            │
                            ▼
               Final Next Best Actions
                            │
                            ▼
                    React Dashboard
```

---

# Core Components

## 1. Frontend Layer

**Technology:** React + Vite + Tailwind CSS

### Responsibilities

- Customer transcript submission
- Customer information display
- Risk score visualization
- Recommendation dashboard
- Human approval interface
- API communication with the backend

The frontend acts as the primary interface for Customer Success Managers to interact with the platform.

---

## 2. Backend Layer

**Technology:** FastAPI

The backend serves as the orchestration layer connecting the frontend, AI agents, vector database, and persistent storage.

### Responsibilities

- Execute LangGraph workflow
- Route API requests
- Coordinate AI agents
- Manage customer sessions
- Handle database interactions
- Return structured responses to the frontend

---

## 3. Planner Agent

**Technology:** LangGraph

The Planner Agent is the central orchestrator responsible for managing the execution flow.

### Responsibilities

- Receive customer requests
- Coordinate specialized AI agents
- Execute workflows
- Aggregate outputs
- Return the final recommendation

This modular orchestration allows individual agents to evolve independently without affecting the overall workflow.

---

## 4. Ingestion Agent

Processes raw customer conversations into structured business insights.

### Responsibilities

- Clean transcripts
- Extract key entities
- Detect customer intent
- Identify customer concerns
- Generate structured customer context

Output from this agent becomes the foundation for downstream analysis.

---

## 5. Retrieval Agent (RAG)

The Retrieval Agent implements the Retrieval-Augmented Generation (RAG) pipeline.

### Responsibilities

- Search enterprise documentation
- Retrieve playbooks
- Query ChromaDB vector database
- Supply contextual information to the LLM

Using RAG grounds AI responses in organization-specific knowledge, improving accuracy and reducing hallucinations.

---

## 6. Risk Analysis Agent

Evaluates customer account health based on conversation insights and retrieved knowledge.

### Analyzes

- Customer health
- Churn probability
- Renewal likelihood
- Product adoption
- Escalation risk
- Customer satisfaction

### Outputs

- Risk level
- Confidence score
- Key risk indicators

---

## 7. Recommendation Agent

Generates ranked Next Best Actions using structured insights and retrieved knowledge.

### Example Recommendations

- Schedule onboarding session
- Escalate support issues
- Offer pricing review
- Assign dedicated Customer Success Manager
- Conduct Executive Business Review (EBR)

Recommendations are prioritized using confidence scores and business impact.

---

## 8. Memory Manager

**Technology:** Supabase PostgreSQL

Maintains persistent customer context across interactions.

### Stores

- Customer profiles
- Historical conversations
- Generated recommendations
- Human approval history
- Customer timelines

Persistent memory enables personalized recommendations across future engagements.

---

# Data Storage Architecture

## ChromaDB

### Purpose

Vector database used for semantic similarity search.

### Stores

- Enterprise documentation
- Knowledge base
- Product guides
- Playbooks
- Embedded vectors

### Usage

Provides contextual knowledge to the Retrieval Agent before recommendation generation.

---

## Supabase PostgreSQL

### Purpose

Persistent relational database for customer interaction history.

### Stores

- Customer IDs
- Session IDs
- Customer conversations
- AI recommendations
- Approval history
- Customer timelines

---

# Request Flow

```text
Customer Transcript
        │
        ▼
React Dashboard
        │
        ▼
FastAPI Backend
        │
        ▼
Planner Agent
        │
        ├────────► Ingestion Agent
        │
        ├────────► Retrieval Agent
        │               │
        │               ▼
        │         ChromaDB
        │
        ├────────► Risk Analysis Agent
        │
        ├────────► Recommendation Agent
        │
        └────────► Memory Manager
                        │
                        ▼
                  Supabase Database
                        │
                        ▼
             Human Approval (HITL)
                        │
                        ▼
             Final Recommendations
                        │
                        ▼
                 React Dashboard
```

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | React, Vite, Tailwind CSS, Axios |
| Backend | FastAPI, Python |
| Workflow Orchestration | LangGraph |
| LLM | Google Gemini 2.0 Flash |
| AI Framework | LangChain |
| Vector Database | ChromaDB |
| Relational Database | Supabase PostgreSQL |
| Embeddings | Sentence Transformers |
| Utilities | Pydantic, Uvicorn, Python Dotenv |

---

# Key Design Decisions

## 1. Multi-Agent Architecture

The platform adopts a modular multi-agent design where each agent performs a specialized task such as ingestion, retrieval, risk analysis, recommendation generation, or memory management.

**Benefits**

- Separation of concerns
- Easier maintenance
- Independent scalability
- Extensible architecture

---

## 2. LangGraph Orchestration

LangGraph is used to coordinate agent execution rather than implementing a monolithic AI workflow.

**Benefits**

- Clear workflow management
- Flexible branching logic
- Improved observability
- Simplified agent integration

---

## 3. Retrieval-Augmented Generation (RAG)

Rather than relying solely on the LLM, the platform retrieves organization-specific knowledge before generating recommendations.

**Benefits**

- Reduced hallucinations
- Context-aware responses
- Organization-specific recommendations
- Improved explainability

---

## 4. Persistent Memory

Customer history is stored in Supabase to maintain long-term context across interactions.

**Benefits**

- Personalized recommendations
- Historical context
- Customer timeline tracking
- Better continuity across sessions

---

## 5. Human-in-the-Loop (HITL)

AI-generated recommendations require human review before execution.

**Benefits**

- Increased trust
- Business governance
- Regulatory compliance
- Human oversight for critical decisions

---

## 6. Modular Storage Strategy

The platform separates storage responsibilities:

- **ChromaDB** for semantic knowledge retrieval
- **Supabase PostgreSQL** for structured customer data

This hybrid approach improves scalability, maintainability, and retrieval performance.

---

# Scalability Considerations

The architecture is designed for future expansion through:

- Salesforce integration
- HubSpot integration
- Microsoft Dynamics support
- Slack notifications
- Email automation
- Role-Based Access Control (RBAC)
- Real-time dashboards
- Predictive churn analytics
- Voice conversation analysis
- Multi-language support
- AI agent performance monitoring

---

# Summary

The Intelligent Next Best Action (NBA) Platform employs a scalable, modular, and agent-driven architecture that combines LangGraph orchestration, Google Gemini, Retrieval-Augmented Generation (RAG), ChromaDB, and Supabase to automate customer success decision-making.

By separating responsibilities across specialized AI agents and incorporating Human-in-the-Loop approval, the platform delivers accurate, explainable, and trustworthy recommendations while maintaining persistent customer context for future interactions.
