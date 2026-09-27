export interface HealthStatus {
  status: string;
  environment: string;
  version: string;
  project: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  has_profile: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface UserUpdateRequest {
  full_name?: string;
  password?: string;
}

export type RiskPreference = 'conservative' | 'moderate' | 'aggressive';

export interface EmergencyFundIndicator {
  months_covered: string;
  target_months: string;
  target_amount: string;
  shortfall: string;
  surplus: string;
  is_adequate: boolean;
  status_label: string;
}

export interface DerivedFinancialIndicators {
  disposable_income: string;
  savings_rate: string;
  expense_ratio: string;
  debt_to_income_ratio: string;
  emergency_fund: EmergencyFundIndicator;
  financial_health_score: string;
  financial_health_grade: string;
}

export interface FinancialProfile {
  id: string;
  user_id: string;
  monthly_income: string;
  current_savings: string;
  monthly_debt_payment: string;
  essential_expenses: string;
  dependents: number;
  emergency_savings: string;
  risk_preference: RiskPreference;
  created_at: string;
  updated_at: string;
  indicators: DerivedFinancialIndicators;
}

export interface FinancialProfileFormData {
  monthly_income: string;
  current_savings: string;
  monthly_debt_payment: string;
  essential_expenses: string;
  dependents: number;
  emergency_savings: string;
  risk_preference: RiskPreference;
}

// Transaction Types
export type TransactionType = 'income' | 'expense';
export type EssentialityType = 'essential' | 'semi_essential' | 'discretionary';

export interface Transaction {
  id: string;
  user_id: string;
  amount: string;
  type: TransactionType;
  category: string;
  description?: string | null;
  transaction_date: string;
  created_at: string;
}

export interface TransactionFormData {
  amount: string;
  type: TransactionType;
  category: string;
  description?: string;
  transaction_date: string;
}

// Natural Language & Voice Parsing
export interface NLParseResponse {
  amount: string | null;
  type: TransactionType;
  category: string;
  description: string | null;
  transaction_date: string;
  essentiality: EssentialityType;
  essentiality_reason: string;
  confidence: number;
  raw_text: string;
  missing_fields: string[];
}

// Statement Ingestion Types
export interface StatementRowPreview {
  row_index: number;
  transaction_date: string;
  amount: string;
  type: TransactionType;
  category: string;
  description: string;
  essentiality: EssentialityType;
  essentiality_reason: string;
  fingerprint: string;
  is_duplicate: boolean;
  is_valid: boolean;
  error_message?: string | null;
}

export interface StatementImportPreviewResponse {
  filename: string;
  file_type: string;
  total_rows: number;
  valid_count: number;
  duplicate_count: number;
  skipped_count: number;
  detected_columns: Record<string, string>;
  transactions: StatementRowPreview[];
  errors: string[];
}

export interface StatementImportConfirmItem {
  transaction_date: string;
  amount: string;
  type: TransactionType;
  category: string;
  description?: string | null;
  fingerprint?: string | null;
}

export interface StatementImportConfirmResponse {
  imported_count: number;
  skipped_duplicates_count: number;
  transactions: Transaction[];
}

// Spending Intelligence & Pattern Types
export interface SpendingPatternItem {
  pattern_type: string;
  category?: string | null;
  title: string;
  description: string;
  impact_level: 'low' | 'medium' | 'high' | string;
  evidence: Record<string, any>;
}

export interface SpendingHabitItem {
  habit_name: string;
  category: string;
  description: string;
  frequency_per_month: number;
  monthly_cost: string;
  severity: 'info' | 'warning' | 'alert' | string;
  evidence: Record<string, any>;
}

export interface RecurringExpenseItem {
  merchant: string;
  category: string;
  approximate_amount: string;
  frequency: string;
  confidence: number;
  occurrence_count: number;
  last_occurrence: string;
  next_expected_date?: string | null;
  is_confirmed: boolean;
  evidence: Record<string, any>;
}

export interface HiddenExpenseItem {
  merchant: string;
  category: string;
  individual_amount: string;
  total_monthly_cost: string;
  occurrence_count: number;
  discretionary_share_pct: string;
  annualized_cost: string;
  description: string;
}

export interface MiscellaneousSpendingResult {
  total_miscellaneous_amount: string;
  percentage_of_expenses: string;
  transaction_count: number;
  largest_miscellaneous_transactions: Array<{
    description: string;
    amount: string;
    date: string;
  }>;
  recurring_miscellaneous_merchants: Array<{
    merchant: string;
    count: number;
  }>;
  leak_severity: 'low' | 'medium' | 'high' | string;
  description: string;
}

export interface SpendingIntelligenceResult {
  essential_amount: string;
  semi_essential_amount: string;
  discretionary_amount: string;
  essential_percentage: string;
  semi_essential_percentage: string;
  discretionary_percentage: string;
  patterns: SpendingPatternItem[];
  habits: SpendingHabitItem[];
  recurring_expenses: RecurringExpenseItem[];
  hidden_expenses: HiddenExpenseItem[];
  miscellaneous_analysis: MiscellaneousSpendingResult;
}

// Category & Summary Types
export interface CategorySpending {
  category: string;
  total_amount: string;
  percentage_of_total: string;
  transaction_count: number;
  is_essential: boolean;
}

export interface SpendingFlag {
  flag_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical' | string;
  category: string;
  description: string;
  amount: string;
  threshold: string;
}

export interface MonthOverMonth {
  previous_total_expenses: string;
  current_total_expenses: string;
  delta_amount: string;
  delta_percentage: string;
  trend: string;
}

export interface ExpenseSummary {
  total_income: string;
  total_expenses: string;
  net_savings: string;
  savings_rate: string;
  essential_spending: string;
  non_essential_spending: string;
  essential_percentage: string;
  non_essential_percentage: string;
  transaction_count: number;
  income_transaction_count: number;
  expense_transaction_count: number;
  month_over_month: MonthOverMonth | null;
  category_breakdown: CategorySpending[];
  largest_categories: CategorySpending[];
  spending_flags: SpendingFlag[];
}

// Budget Types
export interface Budget {
  id: string;
  user_id: string;
  category: string;
  monthly_limit: string;
  period: string;
  created_at: string;
  updated_at: string;
}

export interface BudgetFormData {
  category: string;
  monthly_limit: string;
  period?: string;
}

export interface CategoryBudgetStatus {
  category: string;
  monthly_limit: string;
  actual_spent: string;
  remaining_amount: string;
  percentage_consumed: string;
  variance: string;
  is_over_budget: boolean;
  status: 'under_budget' | 'near_limit' | 'over_budget' | string;
}

export interface BudgetPerformance {
  total_budgeted: string;
  total_spent: string;
  total_remaining: string;
  overall_percentage_consumed: string;
  overall_variance: string;
  over_budget_count: number;
  category_statuses: CategoryBudgetStatus[];
}

// ---------------- Smart Salary & Cash-Flow Planning Types ----------------

export type RecurringFrequency = 'weekly' | 'monthly' | 'quarterly' | 'annual';
export type SurvivalStatus = 'comfortable' | 'watch' | 'at_risk' | 'insufficient_data';

export interface SalaryProfile {
  monthly_income: string;
  expected_salary_day: number;
  additional_recurring_income: string;
  savings_target: string | null;
  essential_spending_allowance: string | null;
  discretionary_allowance: string | null;
  total_monthly_income: string;
  cycle_start_date: string;
  next_salary_date: string;
  days_in_cycle: number;
  days_elapsed: number;
  days_remaining: number;
}

export interface SalaryProfileFormData {
  monthly_income: string;
  expected_salary_day: number;
  additional_recurring_income: string;
  savings_target?: string;
  essential_spending_allowance?: string;
  discretionary_allowance?: string;
}

export interface RecurringCommitment {
  id: string;
  name: string;
  category: string;
  amount: string;
  frequency: RecurringFrequency;
  monthly_equivalent: string;
  next_expected_date: string | null;
  description?: string | null;
  is_active: boolean;
  is_confirmed: boolean;
  is_due_in_current_cycle: boolean;
}

export interface RecurringCommitmentFormData {
  name: string;
  category: string;
  amount: string;
  frequency: RecurringFrequency;
  next_expected_date?: string;
  description?: string;
  is_active?: boolean;
  is_confirmed?: boolean;
}

export interface AllocationAlternative {
  title: string;
  description: string;
  adjusted_savings_target: string;
  adjusted_essential_allowance: string;
  adjusted_discretionary_allowance: string;
  resulting_buffer: string;
}

export interface SalaryAllocation {
  monthly_income: string;
  fixed_commitments: string;
  essential_allowance: string;
  savings_target: string;
  discretionary_allowance: string;
  remaining_buffer: string;
  fixed_percentage: string;
  essential_percentage: string;
  savings_percentage: string;
  discretionary_percentage: string;
  buffer_percentage: string;
  is_feasible: boolean;
  deficit_amount: string;
  explanation: string;
  alternatives: AllocationAlternative[];
}

export interface SafeToSpend {
  current_available_funds: string;
  upcoming_commitments: string;
  remaining_essential_allowance: string;
  savings_reserve: string;
  emergency_reserve: string;
  total_committed_and_reserved: string;
  safe_to_spend_amount: string;
  daily_safe_to_spend: string;
  days_remaining: number;
  explanation: string;
}

export interface SurvivalProjection {
  current_available_funds: string;
  recent_average_daily_burn: string;
  days_remaining: number;
  upcoming_commitments: string;
  projected_remaining_spend: string;
  projected_end_of_month_balance: string;
  daily_spending_capacity: string;
  status: SurvivalStatus;
  explanation: string;
  evidence: Record<string, any>;
}

export interface MonthlyFinancialPlan {
  id: string;
  user_id: string;
  is_active: boolean;
  salary_profile: SalaryProfile;
  recurring_commitments: RecurringCommitment[];
  allocation: SalaryAllocation;
  safe_to_spend: SafeToSpend;
  survival_projection: SurvivalProjection;
  created_at: string;
  updated_at: string;
}

// ---------------- Goal Planning Types ----------------

export type GoalPriority = 'low' | 'medium' | 'high';
export type GoalStatus = 'in_progress' | 'achieved' | 'paused' | 'cancelled';

export interface Goal {
  id: string;
  user_id: string;
  name: string;
  target_amount: string;
  current_amount: string;
  target_date: string | null;
  priority: GoalPriority;
  category: string;
  monthly_contribution: string | null;
  status: GoalStatus;
  created_at: string;
  updated_at: string;
}

export interface GoalFormData {
  name: string;
  target_amount: string;
  current_amount?: string;
  target_date?: string;
  priority: GoalPriority;
  category: string;
  monthly_contribution?: string;
  status?: GoalStatus;
}

export interface GoalAnalysisItem {
  id: string;
  name: string;
  category: string;
  priority: GoalPriority;
  status: GoalStatus;
  target_amount: string;
  current_amount: string;
  remaining_amount: string;
  progress_percentage: string;
  target_date: string | null;
  monthly_contribution: string | null;
  required_monthly_contribution: string;
  months_remaining_deadline: number;
  months_to_projected_completion: number;
  projected_completion_date: string | null;
  is_feasible: boolean;
  is_completed: boolean;
  feasibility_explanation: string;
  shortfall_or_surplus: string;
}

export interface GoalConflictAllocationItem {
  goal_id: string;
  goal_name: string;
  priority: string;
  target_amount: string;
  current_amount: string;
  monthly_target_contribution: string;
  allocated_amount: string;
  is_fully_funded: boolean;
  shortfall: string;
}

export interface GoalConflictStrategy {
  strategy_id: string;
  strategy_name: string;
  description: string;
  allocations: GoalConflictAllocationItem[];
  total_allocated: string;
  remaining_unallocated: string;
  fully_funded_count: number;
  unfunded_count: number;
}

export interface GoalAnalysisResponse {
  total_target_amount: string;
  total_saved_amount: string;
  total_remaining_amount: string;
  overall_progress_percentage: string;
  total_required_monthly: string;
  available_monthly_capacity: string;
  net_monthly_surplus_or_shortfall: string;
  is_portfolio_feasible: boolean;
  conflict_detected: boolean;
  active_goals_count: number;
  achieved_goals_count: number;
  goal_evaluations: GoalAnalysisItem[];
  conflict_alternatives: GoalConflictStrategy[];
  summary_explanation: string;
}

export interface GoalConflictResponse {
  conflict_detected: boolean;
  total_available_capacity: string;
  total_required_monthly: string;
  shortfall: string;
  active_goals_count: number;
  goals_involved: GoalAnalysisItem[];
  strategies: GoalConflictStrategy[];
  explanation: string;
}

// ---------------- Scenario Lab & Decision Simulator Types ----------------

export type ScenarioType =
  | 'one_time_purchase'
  | 'new_recurring_expense'
  | 'income_change'
  | 'unexpected_expense';

export interface ScenarioSimulateRequest {
  scenario_type: ScenarioType;
  amount: string;
  name?: string;
  timing_months?: number;
  description?: string;
}

export interface FinancialMetricsSnapshot {
  monthly_income: string;
  monthly_essential_expenses: string;
  monthly_debt_payments: string;
  monthly_disposable_income: string;
  current_savings: string;
  savings_rate: string;
  debt_to_income_ratio: string;
  emergency_fund_months: string;
  emergency_fund_status: string;
  daily_safe_to_spend: string;
  financial_health_score: string;
  financial_health_grade: string;
}

export interface FinancialMetricsDelta {
  monthly_income_delta: string;
  monthly_essential_expenses_delta: string;
  monthly_disposable_income_delta: string;
  savings_delta: string;
  savings_rate_delta: string;
  debt_to_income_delta: string;
  emergency_fund_months_delta: string;
  daily_safe_to_spend_delta: string;
  financial_health_score_delta: string;
}

export interface GoalScenarioImpact {
  goal_id: string;
  goal_name: string;
  target_amount: string;
  current_amount: string;
  previous_monthly_contribution: string;
  new_monthly_contribution: string;
  previous_months_to_complete: number;
  new_months_to_complete: number;
  timeline_delay_months: number | null;
  is_still_feasible: boolean;
  explanation: string;
}

export interface FinancialFactLabelValue {
  label: string;
  value: any;
  unit?: string;
  source?: string;
}

export interface DecisionImpactItem {
  area: string;
  description: string;
  value: any;
  delta?: string | null;
}

export interface DecisionOptionItem {
  title: string;
  description: string;
  impact: string;
}

export interface DecisionScenarioMetadata {
  description: string;
  assumptions: string[];
}

export interface DecisionResult {
  summary: string;
  scenario: DecisionScenarioMetadata;
  financial_facts: FinancialFactLabelValue[];
  impacts: DecisionImpactItem[];
  tradeoffs: string[];
  options: DecisionOptionItem[];
  recommendation: string;
  confidence: 'high' | 'medium' | 'low';
  is_sustainable: boolean;
  affordability_verdict: string;
}

export interface ScenarioSimulateResponse {
  scenario_id: string;
  scenario_name: string;
  scenario_type: ScenarioType;
  amount: string;
  timing_months: number;
  description?: string | null;
  is_sustainable: boolean;
  affordability_verdict: 'safe' | 'stretched' | 'unaffordable' | string;
  before_state: FinancialMetricsSnapshot;
  after_state: FinancialMetricsSnapshot;
  delta: FinancialMetricsDelta;
  goal_impacts: GoalScenarioImpact[];
  warnings: string[];
  tradeoffs: string[];
  recommendation: string;
  ai_explanation?: string | null;
  decision_result?: DecisionResult | null;
}

export interface ScenarioCompareItemRequest {
  id?: string;
  name: string;
  type: ScenarioType;
  amount: string;
  timing_months?: number;
  description?: string;
}

export interface ScenarioCompareRequest {
  scenarios: ScenarioCompareItemRequest[];
}

export interface ScenarioTradeoffSummaryItem {
  scenario_id: string;
  scenario_name: string;
  verdict: string;
  ending_savings: string;
  monthly_cash_flow: string;
  emergency_runway_months: string;
  health_score: string;
  health_score_change: string;
  key_tradeoffs: string[];
  recommendation: string;
}

export interface ScenarioCompareResponse {
  baseline: FinancialMetricsSnapshot;
  scenarios: ScenarioSimulateResponse[];
  tradeoff_summary: ScenarioTradeoffSummaryItem[];
}

// ---------------- AI Agentic Advisor Types ----------------

export interface FinancialFactItem {
  metric: string;
  value: any;
  category?: string | null;
  interpretation?: string | null;
}

export interface AdvisorRecommendationItem {
  id?: string | null;
  type: string;
  title: string;
  description: string;
  potential_monthly_savings?: number | null;
  priority: 'high' | 'medium' | 'low' | string;
  category?: string | null;
}

export interface AgentTraceItem {
  step: string;
  agent: string;
  action: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface AdvisorChatRequest {
  message: string;
  context_override?: Record<string, any> | null;
}

export interface AdvisorChatResponse {
  request_id: string;
  user_id: string;
  query: string;
  intent: string;
  response: string;
  financial_facts: FinancialFactItem[];
  recommendations: AdvisorRecommendationItem[];
  execution_trace: AgentTraceItem[];
  financial_health_score?: number | null;
}

// ---------------- Monitoring & Adaptive Replanning Types ----------------

export interface FinancialChange {
  metric: string;
  baseline: string;
  current: string;
  absolute_change: string;
  percentage_change: string;
  severity: 'low' | 'medium' | 'high' | 'critical' | string;
  source: string;
  description: string;
}

export interface MonitoringSnapshot {
  monthly_income: string;
  monthly_essential_expenses: string;
  monthly_discretionary_expenses: string;
  monthly_total_expenses: string;
  current_savings: string;
  monthly_debt_payment: string;
  savings_rate: string;
  safe_to_spend_daily: string;
  emergency_runway_months: string;
  emergency_runway_status: string;
  financial_health_score: string;
  financial_health_grade: string;
  budget_variance: string;
  recurring_commitments_monthly: string;
  active_goals_count: number;
  goals_monthly_required: string;
  goals_monthly_capacity: string;
  goals_feasible: boolean;
  timestamp: string;
}

export interface ReplanningAssessment {
  replanning_required: boolean;
  trigger: string;
  severity: 'nominal' | 'low' | 'medium' | 'high' | 'critical' | string;
  affected_areas: string[];
  reasons: string[];
  recommendations: string[];
}

export interface PlanComparisonItem {
  area: string;
  metric: string;
  baseline_value: string;
  proposed_value: string;
  delta: string;
  explanation: string;
}

export interface GoalImpactSummary {
  goal_name: string;
  previous_contribution: string;
  proposed_contribution: string;
  timeline_delay_months: number;
  status: 'on_track' | 'delayed' | string;
}

export interface PlanComparisonTable {
  items: PlanComparisonItem[];
  summary: string;
  affected_goals: GoalImpactSummary[];
}

export interface ReplanningStrategyOption {
  strategy_id: string;
  title: string;
  description: string;
  adjusted_essential: string;
  adjusted_savings: string;
  adjusted_discretionary: string;
  resulting_buffer: string;
  impact_on_goals: string;
  tradeoffs: string[];
}

export interface MonitoringRunResponse {
  baseline_snapshot: MonitoringSnapshot;
  current_snapshot: MonitoringSnapshot;
  changes: FinancialChange[];
  assessment: ReplanningAssessment;
  plan_comparison?: PlanComparisonTable | null;
  strategies: ReplanningStrategyOption[];
  ai_explanation?: string | null;
  plan_status: 'on_track' | 'needs_attention' | 'replanning_required' | string;
}

export interface MonitoringStatusResponse {
  has_baseline: boolean;
  last_monitored_at?: string | null;
  plan_status: 'on_track' | 'needs_attention' | 'replanning_required' | string;
  replanning_required: boolean;
  critical_changes_count: number;
  unresolved_changes: FinancialChange[];
}

// ---------------- Decision Memory & Proactive Insights Types ----------------

export interface AlternativeStrategyItem {
  id?: string;
  title: string;
  description: string;
  impact?: string;
  timeline_delay_months?: number;
  tradeoffs?: string[];
}

export interface MetricComparisonItem {
  baseline: string;
  current: string;
  delta: string;
  changed: boolean;
}

export interface DecisionMemoryDrift {
  decision_id: string;
  decision_type: string;
  item_name?: string | null;
  created_at: string;
  has_drifted: boolean;
  drift_severity: 'none' | 'low' | 'medium' | 'high' | string;
  metrics_comparison: Record<string, MetricComparisonItem>;
  explanation: string;
  can_re_evaluate: boolean;
}

export interface DecisionMemoryItem {
  id: string;
  user_id: string;
  user_action: string;
  decision: string;
  decision_type: string;
  item_name?: string | null;
  amount?: string | null;
  strategy_selected?: string | null;
  alternatives_considered?: AlternativeStrategyItem[] | null;
  affected_goals?: string[] | null;
  baseline_metrics?: Record<string, any> | null;
  resulting_metrics?: Record<string, any> | null;
  assumptions?: string[] | null;
  recommendation_summary?: string | null;
  financial_impact?: Record<string, any> | null;
  status: string;
  created_at: string;
  drift_assessment?: DecisionMemoryDrift | null;
}

export interface DecisionMemoryCreate {
  user_action: string;
  decision: string;
  decision_type?: string;
  item_name?: string | null;
  amount?: string | null;
  strategy_selected?: string | null;
  alternatives_considered?: AlternativeStrategyItem[] | null;
  affected_goals?: string[] | null;
  baseline_metrics?: Record<string, any> | null;
  resulting_metrics?: Record<string, any> | null;
  assumptions?: string[] | null;
  recommendation_summary?: string | null;
  financial_impact?: Record<string, any> | null;
  status?: string;
}

export interface ProactiveInsight {
  id: string;
  insight_type: string;
  title: string;
  description: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical' | string;
  related_decision_id?: string | null;
  related_goal?: string | null;
  metric_facts: Array<{ metric: string; value: any }>;
  action_prompt?: string | null;
  timestamp: string;
}

// Agentic RAG Types
export interface RAGCitationItem {
  source_id: string;
  title: string;
  publisher: string;
  category: string;
  url?: string | null;
  relevant_excerpt: string;
}

export interface KnowledgeChunkItem {
  chunk_id: string;
  source_id: string;
  source_title: string;
  publisher: string;
  category: string;
  chunk_index: number;
  chunk_text: string;
  similarity_score: number;
  url?: string | null;
  tags: string[];
}

export interface RAGRetrievalResult {
  query: string;
  intent: string;
  retrieval_needed: boolean;
  chunks: KnowledgeChunkItem[];
  citations: RAGCitationItem[];
  sufficiency_score: number;
  refinement_count: number;
  latency_ms: number;
}

export interface KnowledgeSource {
  id: string;
  source_id: string;
  title: string;
  publisher: string;
  category: string;
  doc_type: string;
  url?: string | null;
  license?: string | null;
  publication_date?: string | null;
  chunks_count: number;
}

// Reflection & Self-Correction
export interface ReflectionAudit {
  status: 'passed' | 'corrected' | string;
  groundedness_score: number;
  issues_detected: string[];
  corrections_applied: string[];
  reflection_performed: boolean;
  rag_grounded: boolean;
}

// Human-in-the-Loop Review
export interface HITLReview {
  id: string;
  recommendation_id?: string | null;
  agent_name: string;
  action: 'accepted' | 'modified' | 'rejected' | string;
  user_notes?: string | null;
  original_recommendation?: any;
  modified_recommendation?: any;
  created_at: string;
}

// Agent Lab Types
export interface AgentDefinition {
  id: string;
  name: string;
  role: string;
  icon: string;
  purpose: string;
  inputs: string[];
  tools: string[];
  memory_access: string;
  workflow_steps: string[];
  sample_prompts: string[];
}

export interface AgentLabRunResponse {
  agent_id: string;
  query: string;
  intent?: string;
  selected_agents: string[];
  agent_chain: string[];
  final_response: string;
  financial_facts: Array<{ metric: string; value: any; category?: string; interpretation?: string }>;
  rag_citations: RAGCitationItem[];
  recommendations: Array<{
    id?: string;
    type: string;
    title: string;
    description: string;
    potential_monthly_savings?: number;
    priority: string;
    hitl_status?: string;
  }>;
  reflection_audit?: ReflectionAudit | null;
  execution_trace: Array<{ step: string; agent: string; action: string; details: any; timestamp: string }>;
  prompt_versions?: Record<string, string>;
}

// Evaluation Benchmark Types
export interface EvaluationCaseResult {
  case_id: string;
  question: string;
  intent_match: boolean;
  tool_match: boolean;
  retrieval_correctness: boolean;
  groundedness_score: number;
  reflection_success: boolean;
  latency_ms: number;
  sources_cited: string[];
  generated_content_excerpt: string;
}

export interface EvaluationSummary {
  dataset_name: string;
  mode: 'no_rag' | 'basic_rag' | 'agentic_rag' | string;
  llm_provider: string;
  model_name: string;
  total_cases: number;
  intent_accuracy: number;
  tool_selection_accuracy: number;
  groundedness_score: number;
  retrieval_relevance: number;
  structured_output_validity: number;
  reflection_success_rate: number;
  average_latency_ms: number;
  case_results: EvaluationCaseResult[];
}

export interface RAGModeComparisonResult {
  no_rag: EvaluationSummary;
  basic_rag: EvaluationSummary;
  agentic_rag: EvaluationSummary;
  comparative_insights: string[];
}

export interface LLMComparisonItem {
  model_name: string;
  provider: string;
  factual_accuracy: number;
  groundedness_score: number;
  structured_output_validity: number;
  average_latency_ms: number;
  token_efficiency: number;
  cost_tier: string;
}

export interface LLMBenchmarkResult {
  models: LLMComparisonItem[];
  benchmarked_dataset: string;
  timestamp: string;
}


