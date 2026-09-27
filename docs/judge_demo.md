# FinPilot AI — Project Judge Demonstration Guide

> **Core Presentation Message**:
> *"FinPilot AI does not just tell users what their finances look like. It autonomously reasons about financial decisions, remembers past commitments, monitors real-world cash-flow drift, and adapts the plan when life changes."*

---

## The Autonomous Closed-Loop Story

$$\text{OBSERVE} \longrightarrow \text{REASON} \longrightarrow \text{DECIDE} \longrightarrow \text{PLAN} \longrightarrow \text{REMEMBER} \longrightarrow \text{MONITOR} \longrightarrow \text{ADAPT}$$

This guide provides a structured, live demonstration script using your own freshly created account and real user-entered data. **No fake or pre-seeded data is used.**

---

## 1. Before the Demo (Pre-Demo Setup)

Complete this quick 2-minute setup before presenting to the judge:

1. **Start the Application**:
   ```powershell
   .\start-dev.ps1
   ```
   *Verify FastAPI is running on `http://127.0.0.1:8000` and React on `http://localhost:5173`.*

2. **Create a Fresh Account**:
   - Open `http://localhost:5173/` in your browser.
   - Click **Get Started** and sign up with your email and name.

3. **Complete (or Dismiss) the Onboarding**:
   - The **Quick Financial Setup** modal appears immediately after sign up.
   - You can either complete it right away or click **"Skip for now"** / the top-right **"X"** close button.
   - If skipped, a prominent **"Complete Your Financial Profile"** banner on the Home Dashboard allows you to complete setup whenever you are ready.
   - Enter your chosen baseline numbers in the Onboarding modal:
     - **Monthly Net Income**: `[MONTHLY INCOME]` (e.g. `₹75,000`)
     - **Current Liquid Savings**: `[CURRENT SAVINGS]` (e.g. `₹1,50,000`)
     - **Essential Living Expenses**: `[ESSENTIAL EXPENSES]` (e.g. `₹35,000`)
     - **Monthly Debt / EMIs**: `[MONTHLY DEBT]` (e.g. `₹5,000`)
     - **Emergency Savings**: `[EMERGENCY SAVINGS]` (e.g. `₹1,00,000`)
     - **Dependents**: `[DEPENDENTS]` (e.g. `0` or `1`)
     - **Risk Preference**: `Moderate`

4. **Add Initial Foundation Records**:
   - **Add 2–3 Transactions**: Click `+ Add Expense` (e.g. Groceries `₹3,500`, Dining `₹1,200`, Utilities `₹2,500`).
   - **Create 1 Goal**: Navigate to **My Plan** $\rightarrow$ Add Goal `[GOAL NAME]` (e.g. "Emergency Reserve Boost" target `₹3,00,000`, target in 12 months).
   - **Add 1 Recurring Expense**: Navigate to **My Money** $\rightarrow$ Smart Salary $\rightarrow$ Add Recurring Commitment (e.g. "Apartment Rent" `₹18,000` monthly).
   - **Verify Home Dashboard**: Confirm the Home dashboard displays your live calculated **Health Score**, **Safe-to-Spend (₹)**, and **Monthly Cash Flow**.

---

## 2. Demonstration Formats by Available Time

Choose the appropriate demo track based on the judge's time:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3-MINUTE LIGHTNING TRACK (EXECUTIVE OVERVIEW)                                                    │
│ Home Dashboard ──► AI Advisor (RAG + Reflection) ──► Scenario Lab ──► Plan Health & Replanning   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
┌─────────────────────────────────────────────────▼────────────────────────────────────────────────┐
│ 7-MINUTE STANDARD TRACK (RECOMMENDED FOR JUDGES)                                                 │
│ Home ──► Voice Ingestion ──► AI Advisor (Citations + HITL) ──► Scenario Lab ──► Decision Memory  │
│ ──► Inject Shock ──► Autonomous Replanning ──► Agent Lab (Live Multi-Agent Collaboration & Trace)│
└─────────────────────────────────────────────────▲────────────────────────────────────────────────┘
                                                  │
┌─────────────────────────────────────────────────▼────────────────────────────────────────────────┐
│ 15-MINUTE COMPREHENSIVE ACADEMIC & ARCHITECTURE TRACK                                            │
│ Full Product + Academic AI Rigor:                                                               │
│ 1. Auth & Isolated Profile Setup (Dismissible Onboarding & INR Formatting)                       │
│ 2. Ingestion & 50/30/20 Smart Salary Allocation                                                  │
│ 3. Multi-Agent AI Advisor with Authoritative RAG (RBI / SEBI Knowledge Base & Source Badges)     │
│ 4. Reflection & Deterministic Self-Correction Layer                                              │
│ 5. Human-in-the-Loop (HITL) Recommendation Review (Accept / Modify / Reject)                     │
│ 6. Multi-Factor Scenario Lab & Decision Memory Drift Tracking                                    │
│ 7. Environmental Shock Detection & Autonomous Before-vs-After Replanning                         │
│ 8. 🤖 Agent Lab: Single Agent Inspector, Multi-Agent Collaboration Chains & Orchestrator Flow    │
│ 9. Benchmark & Evaluation Dashboard: No-RAG vs Basic RAG vs Agentic RAG & Multi-LLM Comparison   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Demonstration Script (Standard & Academic Track)

### Step 1: Show the Product First (Home Dashboard)
- **Where to Click**: Click **Home** in the top navigation.
- **What to Show**:
  - **Financial Health Score** (0–100) and grade badge calculated deterministically.
  - **Safe-to-Spend Buffer (₹)** remaining in current cycle and daily allowance in INR.
  - **Monthly Cash Snapshot** (income vs. actual expenses vs. net savings rate in ₹).
  - **Top Proactive AI Insight** banner alerting to high-impact opportunities.
- **What to Say**:
  > *"FinPilot AI starts with a structured financial state, not an empty chatbot prompt. Every metric on this dashboard—from our safe-to-spend buffer to emergency runway—is calculated with deterministic mathematical precision in INR by our Financial Engine."*
- **Technical Concept**:
  Deterministic Financial Engine vs. LLM-based estimation.

---

### Step 2: Intelligent Ingestion (Natural Language & Voice Entry)
- **Where to Click**: Click **Add Expense** $\rightarrow$ switch to **Voice Entry** or **Natural Language**.
- **What to Enter**:
  - Type or speak: `"Spent ₹3,500 at Nature's Basket for groceries yesterday"` or `"Spent 3500 rupees on groceries yesterday"`.
- **What to Show**:
  - Auto-extracted amount (`₹3,500`), category (`Groceries`), date, and essentiality classification.
  - Explainable classification reasoning (e.g. `essential` because Groceries are non-discretionary).
- **What to Say**:
  > *"Users don't need complex spreadsheet entry. FinPilot parses natural conversational text or speech into structured transactions and automatically classifies essentiality according to strict financial guidelines."*
- **Technical Concept**:
  Deterministic regex + NLP entity extraction & rule-based essentiality tagging.

---

### Step 3: Spending Intelligence & Leak Detection
- **Where to Click**: Click **Insights** in top navigation $\rightarrow$ switch to **Spending Intelligence & Leak Detection**.
- **What to Show**:
  - Essential vs. Discretionary spending breakdown in `₹`.
  - Unusual spending spikes, micro-transaction leaks, and recurring commitments.
- **What to Say**:
  > *"FinPilot does not just record raw transactions—it turns them into actionable spending intelligence, flagging stealth subscription creep and discretionary spending drift before it impacts goals."*
- **Technical Concept**:
  Statistical anomaly detection & recurring frequency normalization.

---

### Step 4: AI Advisor — Agentic RAG, Reflection & Human-in-the-Loop (HITL)
- **Where to Click**: Click **AI Advisor** in top navigation.
- **What to Ask**:
  - Click a suggestion chip or type: `"What does RBI recommend regarding emergency funds, and can I afford a ₹60,000 laptop?"`
- **What to Show**:
  - **Live Execution Trace**: LangGraph routing from `Orchestrator -> RAG Knowledge Retrieval -> Decision Agent -> Reflection Validator`.
  - **Authoritative RAG Source Badges**: Direct citations from RBI National Financial Literacy guidelines and SEBI investor rules.
  - **Mathematical Fact Alignment Badge**: Shows 100% verified groundedness against live financial facts.
  - **Human-in-the-Loop (HITL) Review Buttons**: Click **Accept**, **Modify**, or **Reject** on AI recommendations to illustrate human oversight.
- **What to Say**:
  > *"Notice how the advisor operates. When financial guidance is needed, our Agentic RAG dynamically retrieves authoritative guidelines from RBI and SEBI. Before presenting the answer, our Reflection layer validates all numeric facts against the deterministic engine. The user retains complete oversight with our Human-in-the-Loop review controls."*
- **Technical Concept**:
  Agentic RAG + Self-Correction Reflection Loop + Human-in-the-Loop Governance.

---

### Step 5: The Hero Moment — Decision Simulation (Scenario Lab)
- **Where to Click**: Click **Scenario Lab** in top navigation.
- **What to Enter**:
  - Scenario Type: `One-Time Purchase`
  - Name: `[PLANNED PURCHASE]` (e.g. "MacBook Pro M-Series")
  - Amount: `[PURCHASE AMOUNT]` (e.g. `₹60,000`)
  - Timing: `Immediate (Month 0)`
  - Click **Run Simulation**.
- **What to Show**:
  - Impact on Safe-to-Spend, Emergency Runway reduction, and Goal Delay (e.g. "Delays Goal by 1–2 months").
  - Alternative mitigation strategies (e.g. Delay by 3 months, or fund via monthly surplus).
- **What to Say**:
  > *"This is FinPilot's core superpower. When a user considers a major financial decision, the engine calculates the ripple effect across their emergency fund, monthly safe-to-spend, and savings timeline in INR. The Decision Agent then explains trade-offs and provides alternatives."*
- **Technical Concept**:
  Deterministic Multi-Factor Scenario Simulation & Trade-off Optimization.

---

### Step 6: Decision Memory
- **Where to Click**: Click **Save to Decision Memory** in Scenario Lab $\rightarrow$ navigate to **Insights** $\rightarrow$ **Decision Memory & Opportunities**.
- **What to Show**:
  - The structured decision memory record containing baseline metrics, assumptions, selected strategy, and alternatives in `₹`.
  - Baseline vs. live metric comparison for drift detection.
- **What to Say**:
  > *"FinPilot does not forget. This is not temporary chat history—it is persistent, structured financial memory. When the user's finances change in the future, FinPilot compares live metrics against the assumptions made during this decision."*
- **Technical Concept**:
  PostgreSQL Persistent Decision History & Memory Drift Engine.

---

### Step 7: The Second Hero Moment — Financial Drift & Adaptive Replanning
- **Where to Click**:
  1. Click **+ Add Expense** $\rightarrow$ Add a major unexpected expense: `[UNEXPECTED EXPENSE]` (e.g. Emergency Medical / Car Repair `₹25,000` in Health/Transport).
  2. Navigate to **My Plan** $\rightarrow$ **Plan Health & Adaptations** (or click **Run Live Diagnostic**).
- **What to Show**:
  - **Detected Financial Changes**: Spending drift and emergency reserve drop flagged with severity level.
  - **Status Change**: Shifts from `Plan On Track` $\rightarrow$ `Replanning Required` or `Needs Attention`.
  - **Side-by-Side Comparison**: *Current Compromised Plan* vs. *AI-Generated Recovery Plan*.
  - Actionable recovery options (e.g., Trim Discretionary Budget, Extend Goal Timeline by 1 Month, or Reallocate Salary).
- **What to Say**:
  > *"This closes the autonomous loop. When a real financial shock occurs, FinPilot's monitoring engine detects the variance, flags that the previous plan is compromised, and autonomously generates optimized recovery strategies to protect the user's financial future."*
- **Technical Concept**:
  Autonomous Closed-Loop Monitoring, Drift Quantification & Replanning Engine.

---

### Step 8: 🤖 Agent Lab & Evaluation Benchmarks (Academic Showcase)
- **Where to Click**: Click **Agent Lab** in top navigation.
- **What to Show**:
  1. **Agent Inspector**:
     - Select each of the specialized agents (`Spending Analyst`, `Decision Agent`, `Planning Agent`, `Monitoring Agent`, `Replanning Agent`).
     - Review their dedicated tool registries, state access schemas, and versioned prompt templates.
     - Run a test in the Live Execution Sandbox to observe real-time trace outputs.
  2. **Multi-Agent Collaboration Studio**:
     - Select **Workflow 1** (`Spending Anomaly -> Decision Agent -> Goal Planning`) or **Workflow 2** (`Monitoring Shock -> Replanning Agent -> Planning Agent`).
     - Click **Execute Multi-Agent Workflow** and watch the handoff between agents in the execution trace.
  3. **Orchestrator Flow Visualizer**:
     - Visual diagram showing LangGraph intent classification, conditional routing, stateful memory retrieval, and reflection validation.
  4. **Live Benchmark & Evaluation Dashboard**:
     - Click **Run Live Evaluation Benchmark**.
     - Review the **No-RAG vs Basic RAG vs Agentic RAG** empirical comparison table (showing 100% groundedness and precision improvement).
     - Review the **Multi-LLM Benchmark** comparing Groq Llama 3.3 70B, Llama 3.1 8B, and Deterministic Fallback.
- **What to Say**:
  > *"To validate our multi-agent architecture rigorously, we built the Agent Lab and an empirical evaluation pipeline backed by standard test datasets. In our empirical evaluation, Agentic RAG achieves 100% groundedness compared to 80% for ungrounded generation, while our reflection layer achieves 100% compliance with zero math hallucinations."*
- **Technical Concept**:
  Empirical Dataset-Backed Agent Evaluation, Multi-Model Benchmarking, and Multi-Agent Orchestration Inspection.

---

## 4. Presenter Talking Points Summary ("What To Say")

| Action / Screen | What to Show | What Technical Concept it Demonstrates | Exact Presenter Talking Point |
| :--- | :--- | :--- | :--- |
| **Home Dashboard** | Health Score, Safe-to-Spend, Cash Snapshot (₹) | Deterministic Financial Engine | *"FinPilot begins with verified numerical truth calculated by our deterministic engine in INR, not an ungrounded chatbot."* |
| **Voice / NL Entry** | Speech-to-Transaction & Categorization | NLP Entity Extraction & Essentiality Rules | *"Our natural language pipeline parses freeform text into structured financial records with explainable essentiality tags."* |
| **Spending Insights** | Category Spikes & Leak Detection | Anomaly Detection & Recurring Normalization | *"We turn static bank ledger entries into actionable intelligence, catching micro-spending leaks and fixed-overhead creep."* |
| **AI Advisor** | Agent Reasoning, RAG Citations & HITL | LangGraph Multi-Agent Orchestrator + RAG + HITL | *"Agents reason over verified facts and RBI/SEBI guidelines with Human-in-the-Loop review controls."* |
| **Scenario Lab** | Purchase simulation & Goal delays | Multi-factor Financial Simulation | *"Before spending, the user simulates the decision to see exact timeline delays and safe-to-spend impacts."* |
| **Decision Memory** | Structured history & Drift status | PostgreSQL Decision Memory | *"This is structured decision memory that tracks whether real-world execution aligns with past financial decisions."* |
| **Adaptive Replanning**| Detected shocks & Before vs. After Plan | Autonomous Closed-Loop Adaptation | *"When financial circumstances change, FinPilot continuously monitors drift and synthesizes an adaptive recovery plan."* |
| **Agent Lab & Benchmarks**| Multi-Agent Chains & Empirical Eval | Dataset Evaluation & RAG vs No-RAG Benchmark | *"The Agent Lab demonstrates our multi-agent orchestration, reflection layer, and empirical evaluation dataset metrics."* |

---

## 5. What NOT To Do During the Demonstration

- ❌ **Do NOT click randomly** across every sub-tab without telling the story.
- ❌ **Do NOT read long AI paragraphs verbatim**; summarize key takeaway numbers.
- ❌ **Do NOT claim the AI calculates monetary sums**; emphasize the **Hybrid Architecture** (Deterministic Engine calculates math, AI reasons and explains).
- ❌ **Do NOT claim FinPilot initiates real banking wire transfers**; it is an intelligent planning and decision copilot.
- ❌ **Do NOT use fake or hardcoded mock users**; demonstrate using real data entered through the UI.
- ❌ **Do NOT spend more than 45 seconds on authentication/onboarding**; get to the Home dashboard and Scenario Lab promptly.

---

## 6. Feature Showcase Checklist

### Must Show (Core Story)
- [x] Home Financial State (Health score, safe-to-spend, cash snapshot in ₹)
- [x] Natural Language / Voice Ingestion
- [x] Spending Intelligence & Leak Detection
- [x] Multi-Agent AI Advisor with RAG Citations & Reflection
- [x] Human-in-the-Loop (HITL) Review Controls (Accept / Modify / Reject)
- [x] Scenario Lab Simulation & Alternative Trade-offs
- [x] Decision Memory & Baseline Drift
- [x] Live Shock Injection $\rightarrow$ Monitoring $\rightarrow$ Adaptive Replanning
- [x] 🤖 Agent Lab (Single Agent Inspector, Multi-Agent Chains, Orchestrator Flow)
- [x] Live Evaluation & Benchmark Dashboard (No-RAG vs Basic RAG vs Agentic RAG)

### Optional if Time Allows
- [ ] Bank Statement CSV/Excel Import Preview & Batch Confirm
- [ ] 50/30/20 Salary Allocation with Interactive Sliders
- [ ] Multi-Goal Priority Conflict Resolution Matrix
- [ ] Multi-Scenario Side-by-Side Comparison
