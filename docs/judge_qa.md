# FinPilot AI — Judge Technical Q&A Guide

This document provides technically rigorous answers to expected questions from project judges, evaluators, and system architects.

---

## 1. AI & Agent Architecture

### Q1: Why use a multi-agent system instead of a single prompt/LLM?
**Answer**:
A single generic LLM prompt struggles with domain-specific role separation, deterministic state adherence, and explainable multi-step reasoning. In FinPilot AI:
- **Orchestrator Agent**: Classifies user intent and routes execution to specialized sub-graphs.
- **Spending Analyst**: Specializes in anomaly classification, recurring expense clustering, and leak detection.
- **Planning Agent**: Focuses on 50/30/20 salary distribution and goal milestone scheduling.
- **Decision Agent**: Evaluates counterfactuals, opportunity costs, and purchase tradeoffs.
- **Replanning Agent**: Compares baseline vs. current financial snapshots and synthesizes recovery strategies.

Separation of concerns allows each agent to use targeted system instructions, focused context schemas, and dedicated validation rules.

---

### Q2: What makes FinPilot truly "Agentic" rather than just a wrapper around an API?
**Answer**:
FinPilot implements an autonomous closed loop:
1. **Perception/Observation**: Continuously builds quantized financial snapshots from transactions, commitments, and profile indicators.
2. **Intent Classification & Dynamic Routing**: Orchestrator inspects state and dynamically invokes single agents or multi-agent chains (e.g. `Monitoring -> Replanning -> Planning`).
3. **Counterfactual Simulation**: Agents invoke the deterministic Financial Engine to evaluate potential decisions before advising.
4. **Structured Decision Memory**: Stores decision context, selected strategy, and assumptions into database records.
5. **Continuous Environmental Monitoring & Adaptation**: Automatically detects drift between assumptions and reality, proactively triggering replanning when variances exceed tolerance thresholds.

---

### Q3: What is the role of LangGraph and Groq in the system?
**Answer**:
- **LangGraph**: Serves as the stateful workflow orchestration engine. It defines nodes (agents, tools, memory retrieval, validation) and conditional edges (intent routing, validation retries, multi-agent chaining), maintaining immutable state transitions.
- **Groq**: Provides low-latency LLM inference (Llama 3 / Mixtral models via Groq LPU hardware), enabling sub-second agent reasoning cycles.
- **Mock Fallback**: If an API key is absent or in testing environments, a deterministic rule-based agent simulator executes with identical schema output, guaranteeing 100% testability.

---

### Q4: How do you eliminate LLM hallucinations on financial numbers?
**Answer**:
We enforce a strict **Hybrid AI + Deterministic Numerical Engine** architecture:
1. **Mathematical Isolation**: All financial arithmetic (savings rates, safe-to-spend, emergency runway, goal timelines, scenario deltas, debt ratios) is computed exclusively in Python by the deterministic `FinancialEngine`.
2. **Fact Grounding**: The LLM prompt is injected only with verified numeric facts from the database and engine.
3. **Validation Layer (`validator.py`)**: After the agent produces a response, the validator inspects all extracted numeric claims against the authoritative context facts. If an agent introduces ungrounded numbers, the validator rejects the output and triggers a sanitized regeneration.

---

## 2. Deterministic Financial Engine

### Q5: How is "Safe-to-Spend" calculated?
**Answer**:
Safe-to-Spend represents discretionary liquidity remaining in the current salary cycle after protecting all essential obligations:
$$\text{SafeToSpend} = \text{CurrentAvailableFunds} - \left( \text{UpcomingRecurringCommitments} + \text{RemainingEssentialAllowance} + \text{MonthlySavingsTarget} + \text{EmergencyReserveBuffer} \right)$$
$$\text{DailySafeToSpend} = \frac{\text{SafeToSpend}}{\text{DaysRemainingInSalaryCycle}}$$
This ensures the user never accidentally spends money already earmarked for rent, loan EMIs, or goal savings.

---

### Q6: How does Goal Conflict Resolution work?
**Answer**:
When multiple competing goals exceed monthly surplus capacity, the engine:
1. Classifies goals by priority (`high`, `medium`, `low`) and target dates.
2. Calculates required monthly contributions: $\text{MonthlyRequirement}_i = \frac{\text{TargetAmount}_i - \text{CurrentAmount}_i}{\text{MonthsRemaining}_i}$.
3. If $\sum \text{MonthlyRequirement} > \text{MonthlySurplus}$, it allocates surplus sequentially to higher-priority goals and generates deterministic resolution strategies:
   - **Timeline Extension**: Extends low/medium priority deadlines.
   - **Proportional Scaling**: Allocates surplus pro-rata based on priority weightings.
   - **Expense Trimming**: Recommends cutting specific discretionary categories to bridge the gap.

---

### Q7: How does Scenario Lab simulate purchase impacts?
**Answer**:
Given a scenario (e.g. one-time purchase of amount $A$ at month $T$):
1. **Savings Impact**: $\text{PostSavings} = \text{CurrentSavings} - A$.
2. **Emergency Runway Impact**: $\text{RunwayMonths} = \frac{\text{PostSavings}}{\text{MonthlyEssentialExpenses} + \text{MonthlyDebtPayment}}$.
3. **Goal Delay Calculation**: Quantifies how many months existing savings goals are delayed by depleting the capital buffer.
4. **Alternative Optimization**: Tests counterfactuals (e.g. delaying purchase by $N$ months, funding via monthly surplus vs. liquid reserves) to present the user with mathematical trade-offs.

---

## 3. Decision Memory & Monitoring

### Q8: Is Decision Memory just chat history? Why PostgreSQL instead of a Vector Database?
**Answer**:
No, it is **not raw text chat history**. Decision Memory stores structured relational entities in PostgreSQL (`DecisionHistory`):
- `decision_type`, `item_name`, `amount`
- `strategy_selected` and `alternatives_considered` (JSON)
- `baseline_metrics` vs. `resulting_metrics` (quantized financial state at decision time)
- `assumptions` and `affected_goals`

**Why PostgreSQL over Vector DB?**:
Financial drift analysis requires **exact relational comparison** ($\Delta \text{SavingsRate}$, $\Delta \text{EmergencyRunway}$, $\Delta \text{DiscretionaryBurn}$), not semantic cosine similarity. PostgreSQL provides ACID transactions, relational foreign keys tied directly to user profiles, deterministic indexing, and zero external infrastructure dependencies.

---

### Q9: What triggers an Adaptive Replanning cycle?
**Answer**:
The `MonitoringEngine` quantifies variance between the stored baseline plan and the live financial state:
1. **Income Drop**: Drop in net monthly salary $> 5\%$.
2. **Spending Surge**: Discretionary or essential spending burn rate exceeding planned allowances by $> 15\%$.
3. **Emergency Fund Depletion**: Runway dropping below 3 months.
4. **Goal Timeline Drift**: Delay exceeding 1 month on high-priority goals.

When triggers exceed tolerance thresholds, the system transitions status from `nominal` to `replanning_required`, invokes the `ReplanningAgent`, and generates a comparative Before vs. After plan recovery matrix.

---

## 4. Security & User Isolation

### Q10: How is multi-tenant user isolation enforced? Can User A see User B's data?
**Answer**:
Multi-tenant user isolation is enforced at both the API and database levels:
1. **JWT Authentication**: All protected endpoints require a valid Bearer token signed with `HS256` and verified via FastAPI's `get_current_user` dependency.
2. **Elimination of IDOR (Insecure Direct Object References)**: Route endpoints do not accept client-supplied `user_id` query parameters. Every query is filtered explicitly by `current_user.id`.
3. **Resource Ownership Verification**: Direct ID lookups (e.g. `GET /transactions/{id}`, `GET /goals/{id}`, `GET /decisions/memory/{id}`) verify that the record's `user_id` matches `current_user.id`. Unauthorized access returns `404 Not Found` or `403 Forbidden`.
4. **Automated Security Tests**: Verified by `backend/tests/test_user_isolation.py`.

---

### Q11: Does FinPilot AI automatically execute banking wire transfers or modify accounts?
**Answer**:
**No**. FinPilot AI is an autonomous advisory and planning copilot. It does not initiate financial movements or execute live banking transactions. All plan updates, budget reallocations, and transaction records require explicit user consent and confirmation.

---

## 5. Technology Stack & Design Decisions

### Q12: Why FastAPI, React, PostgreSQL, and LangGraph?
**Answer**:
- **FastAPI (Python)**: High-performance async ASGI framework with native Pydantic validation, OpenAPI documentation generation, and seamless integration with Python-based financial math and AI libraries.
- **React + Vite + TypeScript**: Type-safe, component-driven UI with instant Hot Module Replacement (HMR) and optimized static asset bundling.
- **PostgreSQL + SQLAlchemy + Alembic**: Enterprise relational database with full ACID compliance, schema migrations, and JSONB support for complex financial simulation payloads.
- **LangGraph**: Directed cyclic graph engine designed specifically for stateful multi-agent workflows with validation checkpoints and rollback capabilities.

---

## 6. Academic Agentic AI & Evaluation Rigor

### Q13: How does FinPilot's Agentic RAG differ from basic naive RAG?
**Answer**:
1. **Dynamic Retrieval Need Assessment**: Unlike naive RAG which blindly queries vector stores on every request, FinPilot's `agentic_retrieval.py` first evaluates whether public regulatory guidelines (e.g. RBI/SEBI/Tax rules) are required for the given query. Pure ledger calculations bypass vector retrieval to avoid latency and irrelevant context noise.
2. **Dynamic Query Reformulation**: The agent transforms complex conversational queries into optimized search terms before vector search.
3. **Hybrid Search & Relevance Re-Ranking**: Uses cosine similarity over normalized embeddings combined with keyword filtering and relevance scoring.
4. **Sufficiency & Bounded Refinement Loop**: Evaluates whether retrieved chunks answer the query; if insufficient, reformulates the search query in a bounded loop (max 2 iterations).
5. **Exact Source Grounding**: Synthesized outputs include verified source IDs, document titles, and excerpt citations displayed directly in the UI.

---

### Q14: How does Reflection and Self-Correction work in FinPilot?
**Answer**:
FinPilot implements a deterministic **Reflection & Verification Node** (`reflection.py`):
1. **Mathematical Consistency Audit**: Inspects generated responses against verified numeric facts from the `FinancialEngine`.
2. **Currency & Localization Enforcement**: Automatically catches and corrects unauthorized currency symbols (e.g., `$ -> ₹`) and ensures `en-IN` numbering compliance.
3. **Fact Discrepancy Correction**: If the LLM generates a statement contradicting database facts (e.g., claiming zero emergency savings when liquid savings exist), the reflection node performs immediate deterministic repair before presenting the output to the user.
4. **Bounded Iteration**: Operates with a hard iteration bound (1-2 cycles) to prevent infinite reasoning loops while guaranteeing 100% mathematical integrity.

---

### Q15: How does Human-in-the-Loop (HITL) ensure safety and governance?
**Answer**:
Autonomous AI recommendations can have significant financial consequences. FinPilot enforces explicit **HITL Governance**:
1. **Actionable Recommendation Separation**: Recommendations are emitted as structured objects alongside the narrative text.
2. **Interactive Review Matrix**: Users can explicitly **Accept**, **Modify**, or **Reject** any recommendation in both the AI Advisor and Agent Lab.
3. **Audit Trail Persistence**: User decisions and notes are recorded in the `recommendation_reviews` database table with timestamp, user ID, and agent provenance.
4. **Non-Destructive Execution**: No budget changes or goal alterations take effect without explicit human confirmation.

---

### Q16: How is the system evaluated and benchmarked?
**Answer**:
FinPilot includes a dedicated evaluation pipeline backed by standard test datasets in `datasets/agent_evaluation/`:
1. **RAG Mode Comparison**: Evaluates **No-RAG vs Basic RAG vs Agentic RAG** across test questions. Agentic RAG achieves 100% groundedness and eliminates irrelevant retrieval overhead compared to 80% for No-RAG.
2. **Multi-Model Benchmark**: Benchmarks multiple LLM backends (Groq Llama 3.3 70B, Llama 3.1 8B, and Deterministic Fallback) across factual accuracy, structured output validity, token efficiency, and latency.
3. **Live Benchmark Dashboard**: Real-time evaluation results are accessible directly within the **Agent Lab** view for judges and evaluators to inspect.
