import type {
  AuthResponse,
  User,
  UserUpdateRequest,
  Budget,
  BudgetFormData,
  BudgetPerformance,
  CategorySpending,
  ExpenseSummary,
  FinancialProfile,
  FinancialProfileFormData,
  HealthStatus,
  NLParseResponse,
  SpendingIntelligenceResult,
  StatementImportConfirmItem,
  StatementImportConfirmResponse,
  StatementImportPreviewResponse,
  Transaction,
  TransactionFormData,
  SalaryProfile,
  SalaryProfileFormData,
  RecurringCommitment,
  RecurringCommitmentFormData,
  SalaryAllocation,
  SafeToSpend,
  SurvivalProjection,
  MonthlyFinancialPlan,
  Goal,
  GoalFormData,
  GoalAnalysisResponse,
  GoalConflictResponse,
  ScenarioSimulateRequest,
  ScenarioSimulateResponse,
  ScenarioCompareRequest,
  ScenarioCompareResponse,
  AdvisorChatRequest,
  AdvisorChatResponse,
  AdvisorRecommendationItem,
  MonitoringStatusResponse,
  MonitoringRunResponse,
  FinancialChange,
  DecisionMemoryItem,
  DecisionMemoryCreate,
  ProactiveInsight,
  AgentDefinition,
  AgentLabRunResponse,
  HITLReview,
  KnowledgeSource,
  RAGRetrievalResult,
  EvaluationSummary,
  RAGModeComparisonResult,
  LLMBenchmarkResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'finpilot_access_token';

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  data?: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  fallbackMessage = 'API request failed'
): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };

  const token = getAuthToken();
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      removeAuthToken();
      window.dispatchEvent(new CustomEvent('finpilot-auth-unauthorized'));
    }

    if (!response.ok) {
      let parsedMessage = fallbackMessage;
      try {
        const errorBody = await response.text();
        const json = JSON.parse(errorBody);
        if (json.detail) {
          parsedMessage = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail);
        }
      } catch {
        // use fallback
      }
      throw new ApiError(parsedMessage, response.status);
    }

    if (response.status === 204) {
      return null as unknown as T;
    }

    return await response.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Connection failed to ${url}. Is the backend server running?`, 0);
  }
}

// ---------------- Authentication ----------------

export async function loginApi(credentials: { email: string; password: string }): Promise<AuthResponse> {
  const res = await apiFetch<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  }, 'Login failed');
  if (res.access_token) {
    setAuthToken(res.access_token);
  }
  return res;
}

export async function registerApi(data: { name?: string; email: string; password: string }): Promise<AuthResponse> {
  const res = await apiFetch<AuthResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  }, 'Registration failed');
  if (res.access_token) {
    setAuthToken(res.access_token);
  }
  return res;
}

export async function getCurrentUserApi(): Promise<User> {
  return await apiFetch<User>('/api/v1/auth/me', { method: 'GET' }, 'Failed to fetch current user');
}

export async function updateCurrentUserApi(payload: UserUpdateRequest): Promise<User> {
  return await apiFetch<User>('/api/v1/auth/me', {
    method: 'PUT',
    body: JSON.stringify(payload),
  }, 'Failed to update user profile');
}

// ---------------- Health & Profile ----------------

export async function fetchHealthStatus(): Promise<HealthStatus> {
  return await apiFetch<HealthStatus>('/health', { method: 'GET' }, 'Backend health check failed');
}

export async function fetchFinancialProfile(): Promise<FinancialProfile | null> {
  try {
    return await apiFetch<FinancialProfile>('/api/v1/profile', { method: 'GET' });
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export async function saveFinancialProfile(profileData: FinancialProfileFormData): Promise<FinancialProfile> {
  return await apiFetch<FinancialProfile>('/api/v1/profile', {
    method: 'POST',
    body: JSON.stringify(profileData),
  }, 'Failed to save financial profile');
}

export async function updateFinancialProfile(profileData: Partial<FinancialProfileFormData>): Promise<FinancialProfile> {
  return await apiFetch<FinancialProfile>('/api/v1/profile', {
    method: 'PUT',
    body: JSON.stringify(profileData),
  }, 'Failed to update financial profile');
}

// ---------------- Transactions & NL Parsing ----------------

export async function parseTransactionText(text: string, referenceDate?: string): Promise<NLParseResponse> {
  return await apiFetch<NLParseResponse>('/api/v1/transactions/parse-text', {
    method: 'POST',
    body: JSON.stringify({
      text,
      reference_date: referenceDate || null,
    }),
  }, 'Failed to parse natural language transaction');
}

export async function fetchTransactions(params?: {
  startDate?: string;
  endDate?: string;
  category?: string;
  type?: string;
  limit?: number;
  offset?: number;
}): Promise<Transaction[]> {
  const query = new URLSearchParams();
  if (params?.startDate) query.append('start_date', params.startDate);
  if (params?.endDate) query.append('end_date', params.endDate);
  if (params?.category) query.append('category', params.category);
  if (params?.type) query.append('type', params.type);
  if (params?.limit) query.append('limit', String(params.limit));
  if (params?.offset) query.append('offset', String(params.offset));

  return await apiFetch<Transaction[]>(`/api/v1/transactions?${query.toString()}`, { method: 'GET' }, 'Failed to fetch transactions');
}

export async function createTransaction(txData: TransactionFormData): Promise<Transaction> {
  return await apiFetch<Transaction>('/api/v1/transactions', {
    method: 'POST',
    body: JSON.stringify(txData),
  }, 'Failed to create transaction');
}

export async function updateTransaction(id: string, txData: Partial<TransactionFormData>): Promise<Transaction> {
  return await apiFetch<Transaction>(`/api/v1/transactions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(txData),
  }, 'Failed to update transaction');
}

export async function deleteTransaction(id: string): Promise<void> {
  return await apiFetch<void>(`/api/v1/transactions/${id}`, { method: 'DELETE' }, 'Failed to delete transaction');
}

// ---------------- Statement Import Pipeline ----------------

export async function previewStatementImport(file: File, customMapping?: Record<string, string>): Promise<StatementImportPreviewResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (customMapping) {
    formData.append('custom_mapping', JSON.stringify(customMapping));
  }

  return await apiFetch<StatementImportPreviewResponse>('/api/v1/transactions/import/preview', {
    method: 'POST',
    body: formData,
  }, 'Failed to preview statement');
}

export async function confirmStatementImport(transactions: StatementImportConfirmItem[]): Promise<StatementImportConfirmResponse> {
  return await apiFetch<StatementImportConfirmResponse>('/api/v1/transactions/import/confirm', {
    method: 'POST',
    body: JSON.stringify({ transactions }),
  }, 'Failed to import statement transactions');
}

// ---------------- Spending Intelligence & Analytics ----------------

export async function fetchSpendingIntelligence(startDate?: string, endDate?: string): Promise<SpendingIntelligenceResult> {
  const query = new URLSearchParams();
  if (startDate) query.append('start_date', startDate);
  if (endDate) query.append('end_date', endDate);

  return await apiFetch<SpendingIntelligenceResult>(`/api/v1/transactions/intelligence?${query.toString()}`, { method: 'GET' }, 'Failed to load spending intelligence');
}

export async function fetchSpendingPatterns(): Promise<any[]> {
  return await apiFetch<any[]>('/api/v1/transactions/patterns', { method: 'GET' }, 'Failed to load spending patterns');
}

export async function fetchRecurringExpenses(): Promise<any[]> {
  return await apiFetch<any[]>('/api/v1/transactions/recurring', { method: 'GET' }, 'Failed to load recurring expenses');
}

export async function fetchHiddenExpenses(): Promise<any[]> {
  return await apiFetch<any[]>('/api/v1/transactions/hidden-expenses', { method: 'GET' }, 'Failed to load hidden expenses');
}

export async function fetchMiscellaneousAnalysis(): Promise<any> {
  return await apiFetch<any>('/api/v1/transactions/miscellaneous', { method: 'GET' }, 'Failed to load miscellaneous analysis');
}

export async function fetchExpenseSummary(startDate?: string, endDate?: string): Promise<ExpenseSummary> {
  const query = new URLSearchParams();
  if (startDate) query.append('start_date', startDate);
  if (endDate) query.append('end_date', endDate);

  return await apiFetch<ExpenseSummary>(`/api/v1/expenses/summary?${query.toString()}`, { method: 'GET' }, 'Failed to load expense summary');
}

export async function fetchCategoryBreakdown(startDate?: string, endDate?: string): Promise<CategorySpending[]> {
  const query = new URLSearchParams();
  if (startDate) query.append('start_date', startDate);
  if (endDate) query.append('end_date', endDate);

  return await apiFetch<CategorySpending[]>(`/api/v1/expenses/categories?${query.toString()}`, { method: 'GET' }, 'Failed to load category breakdown');
}

// ---------------- Budgets ----------------

export async function fetchBudgets(period?: string): Promise<Budget[]> {
  const query = new URLSearchParams();
  if (period) query.append('period', period);

  return await apiFetch<Budget[]>(`/api/v1/budgets?${query.toString()}`, { method: 'GET' }, 'Failed to fetch budgets');
}

export async function createOrUpdateBudget(budgetData: BudgetFormData): Promise<Budget> {
  return await apiFetch<Budget>('/api/v1/budgets', {
    method: 'POST',
    body: JSON.stringify(budgetData),
  }, 'Failed to save budget');
}

export async function updateBudget(id: string, budgetData: Partial<BudgetFormData>): Promise<Budget> {
  return await apiFetch<Budget>(`/api/v1/budgets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(budgetData),
  }, 'Failed to update budget');
}

export async function deleteBudget(id: string): Promise<void> {
  return await apiFetch<void>(`/api/v1/budgets/${id}`, { method: 'DELETE' }, 'Failed to delete budget');
}

export async function fetchBudgetPerformance(params?: {
  period?: string;
  startDate?: string;
  endDate?: string;
}): Promise<BudgetPerformance> {
  const query = new URLSearchParams();
  if (params?.period) query.append('period', params.period);
  if (params?.startDate) query.append('start_date', params.startDate);
  if (params?.endDate) query.append('end_date', params.endDate);

  return await apiFetch<BudgetPerformance>(`/api/v1/budgets/performance?${query.toString()}`, { method: 'GET' }, 'Failed to load budget performance');
}

// ---------------- Smart Salary & Cash-Flow Planning ----------------

export async function fetchSalaryProfile(): Promise<SalaryProfile> {
  return await apiFetch<SalaryProfile>('/api/v1/salary/profile', { method: 'GET' }, 'Failed to fetch salary profile');
}

export async function saveSalaryProfile(data: SalaryProfileFormData): Promise<SalaryProfile> {
  return await apiFetch<SalaryProfile>('/api/v1/salary/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  }, 'Failed to save salary profile');
}

export async function fetchRecurringCommitments(): Promise<RecurringCommitment[]> {
  return await apiFetch<RecurringCommitment[]>('/api/v1/salary/recurring-expenses', { method: 'GET' }, 'Failed to fetch recurring commitments');
}

export async function createRecurringCommitment(data: RecurringCommitmentFormData): Promise<RecurringCommitment> {
  return await apiFetch<RecurringCommitment>('/api/v1/salary/recurring-expenses', {
    method: 'POST',
    body: JSON.stringify(data),
  }, 'Failed to create recurring commitment');
}

export async function updateRecurringCommitment(id: string, data: Partial<RecurringCommitmentFormData>): Promise<RecurringCommitment> {
  return await apiFetch<RecurringCommitment>(`/api/v1/salary/recurring-expenses/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }, 'Failed to update recurring commitment');
}

export async function deleteRecurringCommitment(id: string): Promise<void> {
  return await apiFetch<void>(`/api/v1/salary/recurring-expenses/${id}`, { method: 'DELETE' }, 'Failed to delete recurring commitment');
}

export async function fetchSalaryAllocation(): Promise<SalaryAllocation> {
  return await apiFetch<SalaryAllocation>('/api/v1/salary/allocation', { method: 'GET' }, 'Failed to fetch salary allocation');
}

export async function calculateCustomSalaryAllocation(data: {
  monthly_income?: string | number;
  fixed_commitments?: string | number;
  essential_allowance?: string | number;
  savings_target?: string | number;
  discretionary_allowance?: string | number;
  monthly_net_salary?: string | number;
  savings_target_percentage?: number;
  discretionary_buffer_percentage?: number;
  commitments?: any[];
}): Promise<SalaryAllocation> {
  return await apiFetch<SalaryAllocation>('/api/v1/salary/allocation/calculate', {
    method: 'POST',
    body: JSON.stringify(data),
  }, 'Failed to calculate custom salary allocation');
}

export async function fetchSafeToSpend(): Promise<SafeToSpend> {
  return await apiFetch<SafeToSpend>('/api/v1/salary/safe-to-spend', { method: 'GET' }, 'Failed to fetch safe to spend calculation');
}

export async function fetchSurvivalProjection(): Promise<SurvivalProjection> {
  return await apiFetch<SurvivalProjection>('/api/v1/salary/survival-projection', { method: 'GET' }, 'Failed to fetch cash-flow survival projection');
}

export async function fetchMonthlyFinancialPlan(): Promise<MonthlyFinancialPlan> {
  return await apiFetch<MonthlyFinancialPlan>('/api/v1/salary/monthly-plan', { method: 'GET' }, 'Failed to fetch monthly financial plan');
}

export async function recalculateMonthlyFinancialPlan(): Promise<MonthlyFinancialPlan> {
  return await apiFetch<MonthlyFinancialPlan>('/api/v1/salary/monthly-plan/recalculate', { method: 'POST' }, 'Failed to recalculate monthly financial plan');
}

// ---------------- Goals & Conflict Resolution ----------------

export async function fetchGoals(): Promise<Goal[]> {
  return await apiFetch<Goal[]>('/api/v1/goals', { method: 'GET' }, 'Failed to fetch savings goals');
}

export async function createGoal(goalData: GoalFormData): Promise<Goal> {
  return await apiFetch<Goal>('/api/v1/goals', {
    method: 'POST',
    body: JSON.stringify(goalData),
  }, 'Failed to create savings goal');
}

export async function updateGoal(id: string, goalData: Partial<GoalFormData>): Promise<Goal> {
  return await apiFetch<Goal>(`/api/v1/goals/${id}`, {
    method: 'PUT',
    body: JSON.stringify(goalData),
  }, 'Failed to update savings goal');
}

export async function deleteGoal(id: string): Promise<void> {
  return await apiFetch<void>(`/api/v1/goals/${id}`, { method: 'DELETE' }, 'Failed to delete savings goal');
}

export async function fetchGoalsAnalysis(): Promise<GoalAnalysisResponse> {
  return await apiFetch<GoalAnalysisResponse>('/api/v1/goals/analysis', { method: 'GET' }, 'Failed to analyze goals');
}

export const fetchGoalAnalysis = fetchGoalsAnalysis;
export const saveBudget = createOrUpdateBudget;
export const calculateCustomAllocation = calculateCustomSalaryAllocation;
export const recalculateMonthlyPlan = recalculateMonthlyFinancialPlan;

export async function fetchGoalConflicts(): Promise<GoalConflictResponse> {
  return await apiFetch<GoalConflictResponse>('/api/v1/goals/conflicts', { method: 'GET' }, 'Failed to check goal conflicts');
}

// ---------------- Scenario Lab Simulator ----------------

export async function simulateScenario(req: ScenarioSimulateRequest): Promise<ScenarioSimulateResponse> {
  return await apiFetch<ScenarioSimulateResponse>('/api/v1/scenarios/simulate', {
    method: 'POST',
    body: JSON.stringify(req),
  }, 'Failed to simulate scenario');
}

export async function compareScenarios(req: ScenarioCompareRequest): Promise<ScenarioCompareResponse> {
  return await apiFetch<ScenarioCompareResponse>('/api/v1/scenarios/compare', {
    method: 'POST',
    body: JSON.stringify(req),
  }, 'Failed to compare scenarios');
}

// ---------------- Agentic AI Advisor ----------------

export async function sendAdvisorChatMessage(req: AdvisorChatRequest): Promise<AdvisorChatResponse> {
  return await apiFetch<AdvisorChatResponse>('/api/v1/advisor/chat', {
    method: 'POST',
    body: JSON.stringify(req),
  }, 'Failed to get advisory response from FinPilot AI agent');
}

export async function getAdvisorRecommendations(): Promise<AdvisorRecommendationItem[]> {
  return await apiFetch<AdvisorRecommendationItem[]>('/api/v1/advisor/recommendations', { method: 'GET' }, 'Failed to fetch advisor recommendations');
}

// ---------------- Monitoring & Adaptive Replanning ----------------

export async function fetchMonitoringStatus(): Promise<MonitoringStatusResponse> {
  return await apiFetch<MonitoringStatusResponse>('/api/v1/monitoring/status', { method: 'GET' }, 'Failed to fetch monitoring status');
}

export async function runMonitoringCycle(): Promise<MonitoringRunResponse> {
  return await apiFetch<MonitoringRunResponse>('/api/v1/monitoring/run', { method: 'POST' }, 'Failed to run monitoring cycle');
}

export async function fetchFinancialChanges(): Promise<FinancialChange[]> {
  return await apiFetch<FinancialChange[]>('/api/v1/monitoring/changes', { method: 'GET' }, 'Failed to fetch detected financial changes');
}

export async function fetchReplanningProposal(): Promise<any> {
  return await apiFetch<any>('/api/v1/monitoring/replanning', { method: 'GET' }, 'Failed to fetch replanning proposal');
}

// ---------------- Decision Memory & Proactive Insights ----------------

export async function fetchDecisionMemories(params?: {
  q?: string;
  decision_type?: string;
  item_name?: string;
  goal_name?: string;
  limit?: number;
}): Promise<DecisionMemoryItem[]> {
  const query = new URLSearchParams();
  if (params?.q) query.append('q', params.q);
  if (params?.decision_type) query.append('decision_type', params.decision_type);
  if (params?.item_name) query.append('item_name', params.item_name);
  if (params?.goal_name) query.append('goal_name', params.goal_name);
  if (params?.limit) query.append('limit', String(params.limit));

  return await apiFetch<DecisionMemoryItem[]>(`/api/v1/decisions/memory?${query.toString()}`, { method: 'GET' }, 'Failed to fetch decision memories');
}

export async function fetchDecisionMemoryDetail(id: string): Promise<DecisionMemoryItem> {
  return await apiFetch<DecisionMemoryItem>(`/api/v1/decisions/memory/${id}`, { method: 'GET' }, 'Failed to fetch decision memory details');
}

export async function createDecisionMemory(data: DecisionMemoryCreate): Promise<DecisionMemoryItem> {
  return await apiFetch<DecisionMemoryItem>('/api/v1/decisions/memory', {
    method: 'POST',
    body: JSON.stringify(data),
  }, 'Failed to create decision memory');
}

export async function fetchProactiveInsights(): Promise<ProactiveInsight[]> {
  return await apiFetch<ProactiveInsight[]>('/api/v1/decisions/insights', { method: 'GET' }, 'Failed to fetch proactive financial insights');
}

// ----------------------------------------------------
// AGENT LAB & MULTI-AGENT STUDIO APIs
// ----------------------------------------------------
export async function fetchAgentRegistry(): Promise<AgentDefinition[]> {
  return await apiFetch<AgentDefinition[]>('/api/v1/agent-lab/agents', { method: 'GET' }, 'Failed to fetch agent registry');
}

export async function runAgentLabAgent(agentId: string, query: string): Promise<AgentLabRunResponse> {
  return await apiFetch<AgentLabRunResponse>('/api/v1/agent-lab/run-agent', {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId, query }),
  }, 'Failed to execute agent run');
}

export async function runMultiAgentWorkflow(workflowId: string, query: string): Promise<AgentLabRunResponse> {
  return await apiFetch<AgentLabRunResponse>('/api/v1/agent-lab/run-workflow', {
    method: 'POST',
    body: JSON.stringify({ workflow_id: workflowId, query }),
  }, 'Failed to execute multi-agent workflow');
}

// ----------------------------------------------------
// HUMAN-IN-THE-LOOP (HITL) APIs
// ----------------------------------------------------
export async function reviewRecommendation(
  recommendationId: string,
  data: {
    action: 'accepted' | 'modified' | 'rejected';
    agent_name?: string;
    decision_id?: string;
    user_notes?: string;
    original_recommendation?: any;
    modified_recommendation?: any;
  }
): Promise<{ status: string; review_id: string; action: string; message: string }> {
  return await apiFetch(`/api/v1/hitl/recommendations/${recommendationId}/review`, {
    method: 'POST',
    body: JSON.stringify(data),
  }, 'Failed to submit recommendation review');
}

export async function fetchUserReviews(): Promise<HITLReview[]> {
  return await apiFetch<HITLReview[]>('/api/v1/hitl/reviews', { method: 'GET' }, 'Failed to fetch user review history');
}

// ----------------------------------------------------
// AGENTIC RAG & KNOWLEDGE BASE APIs
// ----------------------------------------------------
export async function fetchRAGSources(): Promise<KnowledgeSource[]> {
  return await apiFetch<KnowledgeSource[]>('/api/v1/rag/sources', { method: 'GET' }, 'Failed to load knowledge sources');
}

export async function queryRAGKnowledge(data: {
  query: string;
  category?: string;
  mode?: 'no_rag' | 'basic_rag' | 'agentic_rag';
  top_k?: number;
}): Promise<RAGRetrievalResult> {
  return await apiFetch<RAGRetrievalResult>('/api/v1/rag/query', {
    method: 'POST',
    body: JSON.stringify(data),
  }, 'Failed to query RAG knowledge base');
}

// ----------------------------------------------------
// EVALUATION BENCHMARK & MULTI-LLM APIs
// ----------------------------------------------------
export async function runEvaluationBenchmark(datasetName: string = 'rag_questions.jsonl', mode: string = 'agentic_rag'): Promise<EvaluationSummary> {
  return await apiFetch<EvaluationSummary>('/api/v1/evaluation/run', {
    method: 'POST',
    body: JSON.stringify({ dataset_name: datasetName, mode }),
  }, 'Failed to run evaluation benchmark');
}

export async function fetchRAGComparison(datasetName: string = 'rag_questions.jsonl'): Promise<RAGModeComparisonResult> {
  return await apiFetch<RAGModeComparisonResult>(`/api/v1/evaluation/rag-comparison?dataset_name=${encodeURIComponent(datasetName)}`, {
    method: 'GET',
  }, 'Failed to load RAG mode comparison');
}

export async function fetchLLMBenchmark(): Promise<LLMBenchmarkResult> {
  return await apiFetch<LLMBenchmarkResult>('/api/v1/evaluation/llm-benchmark', { method: 'GET' }, 'Failed to load LLM benchmark results');
}
