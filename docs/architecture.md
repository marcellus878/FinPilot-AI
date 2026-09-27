# FinPilot AI — System Architecture & Technical Specification

## 1. High-Level Architecture Overview

FinPilot AI combines a **Deterministic Numerical Financial Engine** with a **Stateful LangGraph Multi-Agent Orchestrator**, providing guaranteed mathematical precision paired with natural language financial reasoning.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   REACT 19 + TYPESCRIPT UI                                 │
│  [Home Dashboard]  [My Money]  [My Plan]  [AI Advisor]  [Scenario Lab]  [Insights]  [Auth]  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ HTTP / REST (JWT Bearer Auth)
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FASTAPI BACKEND                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    API Route Controllers (Strict Multi-Tenant Isolation)              │  │
│  │  /auth  /profile  /transactions  /budgets  /salary  /goals  /scenarios  /advisor ...  │  │
│  └───────────────────────────────────────────┬───────────────────────────────────────────┘  │
│                                              │                                              │
│                     ┌────────────────────────┴────────────────────────┐                     │
│                     ▼                                                 ▼                     │
│  ┌─────────────────────────────────────┐   ┌─────────────────────────────────────────────┐  │
│  │    DETERMINISTIC FINANCIAL ENGINE   │   │       LANGGRAPH MULTI-AGENT SYSTEM          │  │
│  │  • Health Score (0-100) & Grade     │   │  • Orchestrator & Intent Classifier         │  │
│  │  • Safe-to-Spend & Daily Budget     │◄──┤  • Spending Analyst & Leak Detector         │  │
│  │  • 50/30/20 Salary Allocation       │   │  • Planning & Goal Conflict Agent           │  │
│  │  • Goal Priority Conflict Solver    │   │  • Decision & Counterfactual Agent          │  │
│  │  • Multi-Factor Scenario Simulator  │   │  • Replanning & Recovery Agent              │  │
│  │  • Monitoring Drift Quantifier      │   │  • Validation Layer (Anti-Hallucination)    │  │
│  └──────────────────┬──────────────────┘   └──────────────────────┬──────────────────────┘  │
│                     │                                             │                         │
│                     └────────────────────────┬────────────────────┘                         │
│                                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                       SQLAlchemy ORM + PostgreSQL Persistence Layer                   │  │
│  │  Users | Profiles | Transactions | Budgets | Goals | Salaries | Decisions | Events    │  │
│  └───────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Agent Agentic Architecture (LangGraph + Groq)

### State Graph Specification
The LangGraph agent graph (`app/agent/graph.py`) is structured as a cyclic state machine:

```
                      ┌──────────────────────┐
                      │      USER INPUT      │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │     ORCHESTRATOR     │
                      │ (Intent Classifier)  │
                      └──────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ SPENDING ANALYST│     │ PLANNING AGENT  │     │ DECISION AGENT  │
│ (Leak Detector) │     │ (50/30/20 & Goal│     │ (Scenario &     │
└────────┬────────┘     │  Conflicts)     │     │  Trade-offs)    │
         │              └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │   VALIDATION NODE    │
                      │ (Fact Grounding Gate)│
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ PERSISTENCE & OUTPUT │
                      │  (Decision Memory &  │
                      │   Advisor Response)  │
                      └──────────────────────┘
```

### Agent Roles & Responsibilities
1. **Orchestrator Agent**:
   - Parses the user prompt, context history, and current financial baseline.
   - Routes to specialized agents: `spending_analyst`, `planning_agent`, `decision_agent`, `replanning_agent`, or `general_advisor`.
2. **Spending Analyst**:
   - Analyzes transaction histories, essential vs. discretionary ratios, recurring leaks, and category anomalies.
3. **Planning Agent**:
   - Computes viable 50/30/20 salary allocations and solves multi-goal milestone deadlines.
4. **Decision Agent**:
   - Evaluates big purchases, loan EMIs, and career changes, quantifying emergency runway impact and opportunity costs.
5. **Replanning Agent**:
   - Compares baseline vs. compromised financial states and generates actionable recovery strategies.
6. **Agent Output Validator (`app/agent/validator.py`)**:
   - Intercepts all generated agent output and cross-checks every numeric monetary reference against facts supplied by the `FinancialEngine`.

---

## 3. Deterministic Financial Engine (`app/financial_engine.py`)

The Financial Engine is the mathematical ground truth of FinPilot AI. All computations use exact decimal precision (`Decimal`):

### Core Formulas & Algorithms

1. **Financial Health Score ($0 - 100$)**:
   $$\text{HealthScore} = 0.30 \cdot S_{\text{savings\_rate}} + 0.25 \cdot S_{\text{emergency\_fund}} + 0.25 \cdot S_{\text{debt\_ratio}} + 0.20 \cdot S_{\text{budget\_discipline}}$$
   - **Savings Rate Score**: $100\%$ at $\ge 30\%$ savings rate; scales linearly down to $0$.
   - **Emergency Fund Score**: $100\%$ at $\ge 6$ months coverage; scales down below 3 months.
   - **Debt-to-Income Score**: $100\%$ at $0\%$ DTI; drops sharply above $36\%$ DTI.

2. **Safe-to-Spend Calculation**:
   $$\text{SafeToSpend} = \text{AvailableFunds} - \left( \sum \text{RecurringCommitments} + \text{RemainingEssentialLiving} + \text{MonthlySavingsTarget} + \text{EmergencyReserve} \right)$$
   $$\text{DailySafeToSpend} = \frac{\text{SafeToSpend}}{\text{DaysRemainingInCycle}}$$

3. **Goal Conflict Solver**:
   - Evaluates surplus $\text{Surplus} = \text{Income} - \text{Essentials} - \text{Debt} - \text{DiscretionaryBuffer}$.
   - Evaluates aggregate monthly required savings $\sum_{i} \frac{\text{Target}_i - \text{Current}_i}{\text{MonthsRemaining}_i}$.
   - When required savings exceed surplus, calculates prioritized milestone extension strategies.

4. **Multi-Scenario Simulator**:
   - Models single/delayed purchases, new recurring commitments, income shifts, and unexpected shocks against future liquid buffers.

---

## 4. Decision Memory & Continuous Monitoring Loop

### Closed-Loop Cycle

```
[1. OBSERVE]   Build quantized baseline snapshot (Income, Essentials, Savings, Runway)
      │
      ▼
[2. REASON]    Multi-agent analysis of user intent and financial facts
      │
      ▼
[3. DECIDE]    Scenario simulation & trade-off evaluation
      │
      ▼
[4. PLAN]      Optimal salary allocation & goal timeline scheduling
      │
      ▼
[5. REMEMBER]  Persist structured DecisionHistory (assumptions, alternatives, baseline)
      │
      ▼
[6. MONITOR]   Track real-world financial variance against baseline assumptions
      │
      ▼
[7. ADAPT]     Autonomous replanning when drift exceeds critical tolerance limits
```

### Relational Schema Design (PostgreSQL)

- **`users`**: Authentication credentials (`email`, `hashed_password`), timestamps, status.
- **`financial_profiles`**: User income, savings, debt, essential living expenses, dependents, risk preference.
- **`transactions`**: Amount, type (`income`, `expense`), category, essentiality classification, dates.
- **`budgets`**: Monthly/weekly category limits and tracking.
- **`goals`**: Target amounts, current balances, priority weightings, target deadlines.
- **`salary_profiles` & `recurring_commitments`**: Salary cycle dates and recurring bills.
- **`decision_history`**: Structured decision memory, baseline vs. resulting metrics, alternatives, assumptions.
- **`agent_events`**: Audit log of orchestrator executions, tool calls, and validator passes.

---

## 5. Multi-Tenant User Isolation & Security

1. **Authentication Flow**:
   - User credentials authenticated via `POST /api/v1/auth/login`.
   - Backend issues signed JWT containing `sub: user.id` with expiration.
   - Frontend stores token in `localStorage` and injects `Authorization: Bearer <token>` into all `apiFetch` requests.
2. **FastAPI Dependency Injection**:
   - Route handlers inject `current_user: User = Depends(get_current_user)`.
   - Requests lacking a valid token receive `401 Unauthorized`.
3. **Insecure Direct Object Reference (IDOR) Elimination**:
   - All query queries enforce `.filter(Model.user_id == current_user.id)`.
   - Manipulated resource IDs belonging to other users return `404 Not Found` or `403 Forbidden`.
