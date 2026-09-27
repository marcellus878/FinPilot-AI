# FinPilot AI — Autonomous Multi-Agent Financial Copilot

FinPilot AI is an **autonomous agentic financial copilot** built with a **Hybrid AI + Deterministic Numerical Engine** architecture. It pairs mathematical precision with stateful multi-agent reasoning to help users plan cash flow, simulate life decisions, remember commitments, and continuously adapt to financial change.

---

## 🌟 The Autonomous Closed Loop

$$\text{OBSERVE} \longrightarrow \text{REASON} \longrightarrow \text{DECIDE} \longrightarrow \text{PLAN} \longrightarrow \text{REMEMBER} \longrightarrow \text{MONITOR} \longrightarrow \text{ADAPT}$$

Unlike standard personal finance dashboards that merely chart historical numbers, or ungrounded chatbots that hallucinate monetary arithmetic, FinPilot AI **observes real-world financial state, reasons through multi-agent collaboration, evaluates counterfactual scenarios, stores structured decision memory, and autonomously triggers replanning when financial drift is detected.**

---

## 🚀 Core Capabilities

### 1. 🏠 Home Insight Dashboard (`/home`)
- **Financial Health Score ($0 - 100$)**: Multi-factor health index (savings rate, emergency runway, debt-to-income, budget adherence).
- **Safe-to-Spend Buffer**: Discretionary spending capacity computed strictly after protecting recurring obligations, essential allowances, and goal savings.
- **Proactive AI Optimization**: Auto-generated optimization suggestions with 1-click execution in the Advisor.

### 2. 💳 My Money (`/money`)
- **Intelligent Ingestion**: Freeform Natural Language & Voice Speech-to-Transaction entry with rule-based essentiality classification.
- **Statement Import Pipeline**: CSV, Excel, and PDF bank statement ingestion with intra-file duplicate detection.
- **Smart Salary Planner**: Salary cycle tracker, recurring commitments calendar, and 50/30/20 budget allocation.
- **Spending Intelligence**: Anomaly spike detection, micro-transaction leak identification, and subscription creep analytics.

### 3. 🎯 My Plan (`/plan`)
- **Goal Priority Conflict Solver**: Automated trade-off resolution when competing goals exceed surplus capacity.
- **Financial Profile Baseline**: Comprehensive baseline tracking (income, liquid savings, EMIs, dependents, risk preference).
- **Adaptive Plan Health**: Live drift indicators tracking whether real-world cash flow adheres to planned milestones.

### 4. 🤖 AI Advisor (`/advisor`)
- **Multi-Agent LangGraph Orchestrator**: Intent routing to specialized agents (`Spending Analyst`, `Planning Agent`, `Decision Agent`, `Replanning Agent`).
- **Grounded Verification Layer**: Output validator that verifies all numeric claims against the deterministic Financial Engine before rendering advice.

### 5. 🧪 Scenario Lab (`/scenario-lab`)
- **Counterfactual Decision Simulator**: Model one-time purchases, delayed acquisitions, new recurring expenses, and career shifts.
- **Side-by-Side Scenario Comparison**: Real-time evaluation of emergency runway impact, safe-to-spend changes, and goal timeline delays.

### 6. 📊 Insights & Decision Memory (`/insights`)
- **Structured Decision History**: Persistent storage of financial decisions, underlying assumptions, and selected alternatives.
- **Memory Drift Engine**: Relational comparison of baseline metrics at decision time vs. current live finances.

### 7. ⚙ Settings & Security (`/settings`)
- **User Authentication**: Standard JWT Bearer token authentication with bcrypt password hashing.
- **Strict Multi-Tenant Isolation**: Zero IDOR vulnerabilities; all data lookups scoped strictly to authenticated user IDs.

---

## 🏗 Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
- **Backend API**: Python 3.11+, FastAPI (ASGI), Pydantic v2.
- **Database & ORM**: PostgreSQL, SQLAlchemy 2.0, Alembic database migrations.
- **Agentic AI & LLM**: LangGraph (cyclic stateful workflows), Groq API (low-latency LPU inference), with deterministic rule-based mock mode for offline testing.
- **Financial Engine**: Deterministic Python numerical engine with exact `Decimal` precision.

---

## ⚡ Quickstart

### 🚀 Single-Command Startup (Windows / PowerShell)

From the project root directory, run:
```powershell
.\start-dev.ps1
```
This script automatically:
1. Verifies the backend virtual environment and installs dependencies if needed.
2. Initializes `.env` configuration files from `.env.example`.
3. Checks frontend `node_modules` and builds dependencies.
4. Starts FastAPI (`http://127.0.0.1:8000`) and React Vite (`http://localhost:5173`).
5. Opens Google Chrome to the application homepage.

To cleanly stop all development servers, press `Ctrl+C` or execute:
```powershell
.\stop-dev.ps1
```

---

## 🔧 Environment Configuration

### Backend (`backend/.env`)
```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/finpilot

# JWT Authentication
JWT_SECRET_KEY=finpilot_super_secure_jwt_secret_key_change_in_production_2026
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Groq LLM Provider (Leave empty for deterministic mock mode)
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🧪 Testing & Verification

### Run Backend Pytest Suite
```powershell
cd backend
.venv\Scripts\python.exe -m pytest -v
```
*Current test suite: **160/160 tests passing** across 14 test modules.*

### Run Frontend Production Build
```powershell
cd frontend
npm run build
```
*Compiles TypeScript with `tsc -b` and bundles production assets via Vite.*

---

## 📚 Project Documentation

- 📖 [**Judge Demonstration Guide**](docs/judge_demo.md): Live presentation walkthrough, 3-min / 7-min / 15-min scripts, talking points, and showcase checklists.
- ❓ [**Judge Technical Q&A Guide**](docs/judge_qa.md): In-depth answers covering AI agents, math engine, memory, monitoring, and security.
- 🏛 [**System Architecture Specification**](docs/architecture.md): Full technical specification, state graphs, relational schemas, and data flow.
