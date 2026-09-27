from app.financial_engine.budget_intelligence import (
    BudgetPerformanceResult,
    CategoryBudgetStatusItem,
    calculate_budget_performance,
)
from app.financial_engine.categorization import (
    VALID_CATEGORIES,
    CategorizationResult,
    EssentialityResult,
    categorize_transaction,
    classify_essentiality,
)
from app.financial_engine.constants import (
    DEFAULT_EMERGENCY_MONTHS,
    DEFAULT_HEALTH_WEIGHTS,
)
from app.financial_engine.core_metrics import (
    BudgetVarianceResult,
    EmergencyFundResult,
    calculate_budget_variance,
    calculate_debt_to_income_ratio,
    calculate_disposable_income,
    calculate_emergency_fund_status,
    calculate_expense_ratio,
    calculate_savings_rate,
)
from app.financial_engine.expense_intelligence import (
    CategorySpendingItem,
    ExpenseSummaryResult,
    MonthOverMonthResult,
    SpendingFlagItem,
    calculate_category_breakdown,
    calculate_expense_summary,
    detect_unusual_spending,
    is_category_essential,
)
from app.financial_engine.goals import (
    GoalAllocationItem,
    GoalConflictAllocationResult,
    GoalConflictStrategy,
    GoalContributionResult,
    GoalPortfolioAnalysisResult,
    GoalTimelineResult,
    allocate_goals_conflict,
    analyze_goal_portfolio,
    calculate_goal_completion_timeline,
    calculate_required_goal_contribution,
    generate_goal_conflict_strategies,
)
from app.financial_engine.health_score import (
    FinancialHealthScoreResult,
    calculate_financial_health_score,
)
from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    safe_divide,
    to_decimal,
)
from app.financial_engine.nl_parser import (
    ParsedTransaction,
    parse_natural_language_transaction,
)
from app.financial_engine.salary_planner import (
    AllocationAlternative,
    RecurringCommitmentItem,
    SafeToSpendResult,
    SalaryAllocationResult,
    SalaryCycleDates,
    SurvivalProjectionResult,
    calculate_monthly_recurring_commitments,
    calculate_safe_to_spend,
    calculate_salary_allocation,
    calculate_salary_cycle_dates,
    calculate_survival_projection,
    normalize_commitment_to_monthly,
)
from app.financial_engine.scenarios import (
    DetailedScenarioResult,
    FinancialSnapshot,
    FinancialSnapshotDelta,
    GoalScenarioImpact,
    PurchaseAffordabilityResult,
    ScenarioComparisonResult,
    ScenarioImpactResult,
    build_financial_snapshot,
    compare_decision_scenarios,
    evaluate_purchase_affordability,
    simulate_detailed_decision_scenario,
    simulate_scenario_impact,
)
from app.financial_engine.spending_intelligence import (
    HiddenExpenseItem,
    MiscellaneousSpendingResult,
    RecurringExpenseItem,
    SpendingHabitItem,
    SpendingIntelligenceResult,
    SpendingPatternItem,
    analyze_spending_patterns,
    calculate_spending_intelligence,
    detect_hidden_expenses,
    detect_miscellaneous_spending,
    detect_recurring_expenses,
    detect_spending_habits,
    normalize_merchant_name,
)
from app.financial_engine.statement_importer import (
    NormalizedStatementTransaction,
    StatementImportPreviewResult,
    detect_column_mapping,
    generate_transaction_fingerprint,
    process_statement_file,
)

__all__ = [
    # Core Metrics
    "calculate_disposable_income",
    "calculate_savings_rate",
    "calculate_expense_ratio",
    "calculate_debt_to_income_ratio",
    "calculate_budget_variance",
    "calculate_emergency_fund_status",
    "BudgetVarianceResult",
    "EmergencyFundResult",
    # Expense Intelligence
    "calculate_expense_summary",
    "calculate_category_breakdown",
    "detect_unusual_spending",
    "is_category_essential",
    "CategorySpendingItem",
    "ExpenseSummaryResult",
    "MonthOverMonthResult",
    "SpendingFlagItem",
    # Budget Intelligence
    "calculate_budget_performance",
    "CategoryBudgetStatusItem",
    "BudgetPerformanceResult",
    # Categorization & Essentiality
    "VALID_CATEGORIES",
    "categorize_transaction",
    "classify_essentiality",
    "CategorizationResult",
    "EssentialityResult",
    # NL / Voice Parsing
    "parse_natural_language_transaction",
    "ParsedTransaction",
    # Statement Importer
    "process_statement_file",
    "generate_transaction_fingerprint",
    "detect_column_mapping",
    "NormalizedStatementTransaction",
    "StatementImportPreviewResult",
    # Spending Intelligence
    "calculate_spending_intelligence",
    "analyze_spending_patterns",
    "detect_miscellaneous_spending",
    "detect_spending_habits",
    "detect_recurring_expenses",
    "detect_hidden_expenses",
    "normalize_merchant_name",
    "SpendingIntelligenceResult",
    "SpendingPatternItem",
    "SpendingHabitItem",
    "RecurringExpenseItem",
    "HiddenExpenseItem",
    "MiscellaneousSpendingResult",
    # Smart Salary & Cash-Flow Planning
    "calculate_salary_cycle_dates",
    "normalize_commitment_to_monthly",
    "calculate_monthly_recurring_commitments",
    "calculate_salary_allocation",
    "calculate_safe_to_spend",
    "calculate_survival_projection",
    "SalaryCycleDates",
    "RecurringCommitmentItem",
    "SalaryAllocationResult",
    "AllocationAlternative",
    "SafeToSpendResult",
    "SurvivalProjectionResult",
    # Goals
    "calculate_required_goal_contribution",
    "calculate_goal_completion_timeline",
    "allocate_goals_conflict",
    "GoalContributionResult",
    "GoalTimelineResult",
    "GoalAllocationItem",
    "GoalConflictAllocationResult",
    # Scenarios & Affordability
    "evaluate_purchase_affordability",
    "simulate_scenario_impact",
    "PurchaseAffordabilityResult",
    "ScenarioImpactResult",
    # Health Score
    "calculate_financial_health_score",
    "FinancialHealthScoreResult",
    # Helpers & Constants
    "to_decimal",
    "quantize_currency",
    "quantize_percentage",
    "safe_divide",
    "DEFAULT_HEALTH_WEIGHTS",
    "DEFAULT_EMERGENCY_MONTHS",
]
