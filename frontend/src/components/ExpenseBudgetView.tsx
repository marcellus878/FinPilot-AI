import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  DollarSign,
  Plus,
  RefreshCw,
  Tag,
  Trash2,
  TrendingDown,
  TrendingUp,
  Upload,
  Wallet,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {
  deleteTransaction,
  fetchBudgetPerformance,
  fetchExpenseSummary,
  fetchTransactions,
  saveBudget,
} from '../services/api';
import type {
  BudgetFormData,
  BudgetPerformance,
  ExpenseSummary,
  Transaction,
} from '../types';
import { SpendingIntelligenceSection } from './SpendingIntelligenceSection';
import { StatementImportModal } from './StatementImportModal';
import { TransactionEntryModal } from './TransactionEntryModal';
import { formatINR } from '../utils/formatters';

const CATEGORY_COLORS: { [key: string]: string } = {
  Food: '#f59e0b',
  Groceries: '#10b981',
  Transport: '#ec4899',
  Shopping: '#f97316',
  Entertainment: '#8b5cf6',
  'Bills & Utilities': '#06b6d4',
  Healthcare: '#ef4444',
  Education: '#6366f1',
  'Rent/Housing': '#3b82f6',
  'EMI/Debt': '#e11d48',
  'Salary/Income': '#22c55e',
  'Savings/Investment': '#14b8a6',
  'Cash Withdrawal': '#64748b',
  Miscellaneous: '#94a3b8',
};

const DEFAULT_COLOR = '#64748b';

export const ExpenseBudgetView: React.FC = () => {
  const [summary, setSummary] = useState<ExpenseSummary | null>(null);
  const [budgetPerf, setBudgetPerf] = useState<BudgetPerformance | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [intelRefreshKey, setIntelRefreshKey] = useState<number>(0);

  // Filters & State for Transactions
  const [txTypeFilter, setTxTypeFilter] = useState<string>('all');
  const [searchFilter, setSearchFilter] = useState<string>('');

  // Modals state
  const [isTxModalOpen, setIsTxModalOpen] = useState<boolean>(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState<boolean>(false);

  // Budget Modal / Form state
  const [budgetFormData, setBudgetFormData] = useState<BudgetFormData>({
    category: 'Groceries',
    monthly_limit: '',
    period: 'monthly',
  });
  const [submittingBudget, setSubmittingBudget] = useState<boolean>(false);

  const loadData = async (showLoadingSpinner = true) => {
    if (showLoadingSpinner) setLoading(true);
    else setRefreshing(true);
    setErrorMessage(null);

    try {
      const [sumData, perfData, txData] = await Promise.all([
        fetchExpenseSummary(),
        fetchBudgetPerformance(),
        fetchTransactions({ limit: 100 }),
      ]);
      setSummary(sumData);
      setBudgetPerf(perfData);
      setTransactions(txData);
      setIntelRefreshKey((prev) => prev + 1);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load expense and budget data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDeleteTransaction = async (id: string) => {
    if (!confirm('Are you sure you want to delete this transaction?')) return;
    try {
      await deleteTransaction(id);
      await loadData(false);
    } catch (err: any) {
      alert(`Error deleting transaction: ${err.message}`);
    }
  };

  const handleSaveBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!budgetFormData.monthly_limit || Number(budgetFormData.monthly_limit) < 0) {
      alert('Please enter a valid non-negative monthly limit.');
      return;
    }
    if (!budgetFormData.category.trim()) {
      alert('Please specify a category.');
      return;
    }

    setSubmittingBudget(true);
    try {
      await saveBudget({
        ...budgetFormData,
        monthly_limit: Number(budgetFormData.monthly_limit).toFixed(2),
      });
      setIsBudgetModalOpen(false);
      setBudgetFormData({
        category: 'Groceries',
        monthly_limit: '',
        period: 'monthly',
      });
      await loadData(false);
    } catch (err: any) {
      alert(`Error saving budget: ${err.message}`);
    } finally {
      setSubmittingBudget(false);
    }
  };

  // Filter transactions
  const filteredTransactions = transactions.filter((tx) => {
    if (txTypeFilter !== 'all' && tx.type !== txTypeFilter) return false;
    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase();
      const matchCat = tx.category.toLowerCase().includes(q);
      const matchDesc = tx.description ? tx.description.toLowerCase().includes(q) : false;
      return matchCat || matchDesc;
    }
    return true;
  });

  // Prepare Pie Chart Data
  const pieData = (summary?.category_breakdown || [])
    .filter((c) => Number(c.total_amount) > 0)
    .map((c) => ({
      name: c.category,
      value: Number(c.total_amount),
      percentage: c.percentage_of_total,
      isEssential: c.is_essential,
    }));

  // Prepare Bar Chart Data for Budget vs Actual
  const barData = (budgetPerf?.category_statuses || []).map((b) => ({
    category: b.category,
    Budget: Number(b.monthly_limit),
    Actual: Number(b.actual_spent),
    isOver: b.is_over_budget,
  }));

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4">
        <RefreshCw className="w-8 h-8 text-emerald-500 animate-spin" />
        <p className="text-slate-400 text-sm">Analyzing transactions, expenses, and budget variance...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Header & Ingestion Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Wallet className="w-7 h-7 text-emerald-400" />
            Expense & Spending Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic data ingestion (Voice, Natural Text, Bank Statements), budget variance, and spending habits.
          </p>
        </div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => loadData(false)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition disabled:opacity-50"
            title="Refresh analytics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-blue-300 bg-blue-950/60 border border-blue-800/60 rounded-xl hover:bg-blue-900/60 transition shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            Import Statement
          </button>
          <button
            onClick={() => setIsBudgetModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-emerald-300 bg-emerald-950/60 border border-emerald-800/60 rounded-xl hover:bg-emerald-900/60 transition"
          >
            <Tag className="w-3.5 h-3.5" />
            Set Budget
          </button>
          <button
            onClick={() => setIsTxModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-xl shadow-sm transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Record Transaction
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-sm flex items-center justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => loadData(true)} className="underline text-xs hover:text-white">
            Retry
          </button>
        </div>
      )}

      {/* Spending Flags & Spike Alerts */}
      {summary?.spending_flags && summary.spending_flags.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {summary.spending_flags.map((flag, idx) => (
            <div
              key={idx}
              className={`p-3.5 rounded-xl border flex items-start gap-3 text-xs ${
                flag.severity === 'high' || flag.severity === 'critical'
                  ? 'bg-rose-950/30 border-rose-800/60 text-rose-200'
                  : 'bg-amber-950/30 border-amber-800/60 text-amber-200'
              }`}
            >
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold uppercase tracking-wider text-[10px] opacity-80 block mb-0.5">
                  {flag.flag_type.replace('_', ' ')} • {flag.category}
                </span>
                <p>{flag.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 4 Metric Highlight Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Income */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Period Income</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {formatINR(summary?.total_income, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            <span>{summary?.income_transaction_count || 0} income deposits</span>
          </div>
        </div>

        {/* Total Expenses */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Period Expenses</span>
            <ArrowDownRight className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {formatINR(summary?.total_expenses, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-2">
            <span>Essential: {summary?.essential_percentage || '0'}%</span>
            <span>•</span>
            <span>Discretionary: {summary?.non_essential_percentage || '0'}%</span>
          </div>
        </div>

        {/* Net Savings & Rate */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Net Savings</span>
            {Number(summary?.net_savings || 0) >= 0 ? (
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-rose-400" />
            )}
          </div>
          <div
            className={`text-2xl font-bold mt-1 ${
              Number(summary?.net_savings || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {formatINR(summary?.net_savings, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Savings Rate:{' '}
            <span className="font-semibold text-slate-200">{summary?.savings_rate || '0.00'}%</span>
          </div>
        </div>

        {/* Overall Budget Consumption */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Budget Consumed</span>
            <DollarSign className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {budgetPerf?.overall_percentage_consumed || '0.00'}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
            <span>
              {formatINR(budgetPerf?.total_spent)} / {formatINR(budgetPerf?.total_budgeted)}
            </span>
            {budgetPerf && budgetPerf.over_budget_count > 0 && (
              <span className="text-rose-400 font-semibold">{budgetPerf.over_budget_count} over budget</span>
            )}
          </div>
        </div>
      </div>

      {/* Spending Intelligence Section */}
      <SpendingIntelligenceSection onRefreshTrigger={intelRefreshKey} />

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Category Breakdown Pie Chart */}
        <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 flex items-center justify-between">
              <span>Category Breakdown</span>
              <span className="text-xs font-normal text-slate-400">Total Spent Distribution</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic categorization separating essential vs discretionary spending.
            </p>
          </div>

          <div className="h-64 my-4 w-full">
            {pieData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <Tag className="w-8 h-8 mb-2 opacity-40" />
                No expense transactions logged in this period.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CATEGORY_COLORS[entry.name] || DEFAULT_COLOR}
                        stroke="#0f172a"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: any, name: any) => [formatINR(val, { minimumFractionDigits: 2 }), name]}
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value) => <span className="text-xs text-slate-300">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="text-[11px] text-slate-400 border-t border-slate-800 pt-3 flex justify-between items-center">
            <span>Essential: {formatINR(summary?.essential_spending)}</span>
            <span>Discretionary: {formatINR(summary?.non_essential_spending)}</span>
          </div>
        </div>

        {/* Budget vs Actual Performance Bar Chart */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 flex items-center justify-between">
              <span>Budget vs. Actual Spending</span>
              <span className="text-xs font-normal text-slate-400">Monthly Targets</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Category-level variance highlighting over-budget lines and remaining allowance.
            </p>
          </div>

          <div className="h-64 my-4 w-full">
            {barData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <DollarSign className="w-8 h-8 mb-2 opacity-40" />
                No category budgets configured yet. Click "Set Budget" to create one.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="category" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    formatter={(val: any, name: any) => [formatINR(val, { minimumFractionDigits: 2 }), name]}
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend
                    verticalAlign="top"
                    align="right"
                    formatter={(val) => <span className="text-xs text-slate-300">{val}</span>}
                  />
                  <Bar dataKey="Budget" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Actual" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="text-[11px] text-slate-400 border-t border-slate-800 pt-3 flex justify-between items-center">
            <span>Total Remaining: {formatINR(budgetPerf?.total_remaining)}</span>
            <span>Total Variance: {formatINR(budgetPerf?.overall_variance)}</span>
          </div>
        </div>
      </div>

      {/* Category Budgets List & Progress */}
      <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Category Budgets & Variance</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live consumption against configured spending limits.
            </p>
          </div>
          <button
            onClick={() => setIsBudgetModalOpen(true)}
            className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" />
            Add / Update Limit
          </button>
        </div>

        {budgetPerf?.category_statuses.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
            No budget limits defined. Set limits to monitor category variance and overspending.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {budgetPerf?.category_statuses.map((cat, idx) => {
              const pct = Number(cat.percentage_consumed);
              const isOver = cat.is_over_budget;
              const isNear = pct >= 85 && !isOver;

              return (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/70 space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{cat.category}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                        isOver
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
                          : isNear
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                          : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                      }`}
                    >
                      {cat.status.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isOver ? 'bg-rose-500' : isNear ? 'bg-amber-400' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>
                      Spent: <strong className="text-slate-200">{formatINR(cat.actual_spent, { minimumFractionDigits: 2 })}</strong> /{' '}
                      {formatINR(cat.monthly_limit, { minimumFractionDigits: 2 })}
                    </span>
                    <span className={isOver ? 'text-rose-400 font-semibold' : 'text-slate-300'}>
                      {isOver
                        ? `Over by ${formatINR(Math.abs(Number(cat.variance)), { minimumFractionDigits: 2 })}`
                        : `${formatINR(cat.remaining_amount, { minimumFractionDigits: 2 })} left`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Transaction Ledger */}
      <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-white">Transaction Ledger</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Historical ledger of recorded incomes, expenses, and imported statement transactions.
            </p>
          </div>

          {/* Controls / Filter Bar */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search transactions..."
                className="w-44 sm:w-56 px-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <select
              value={txTypeFilter}
              onChange={(e) => setTxTypeFilter(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Types</option>
              <option value="expense">Expenses Only</option>
              <option value="income">Income Only</option>
            </select>
          </div>
        </div>

        {/* Transactions Table */}
        {filteredTransactions.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
            No transactions found matching the filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3 text-right">Amount</th>
                  <th className="py-2.5 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(tx.transaction_date).toLocaleDateString()}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          tx.type === 'income'
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/40'
                            : 'bg-rose-950/60 text-rose-300 border border-rose-800/40'
                        }`}
                      >
                        {tx.type === 'income' ? (
                          <ArrowUpRight className="w-3 h-3" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3" />
                        )}
                        {tx.type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-medium text-slate-200">{tx.category}</td>
                    <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate">{tx.description || '—'}</td>
                    <td
                      className={`py-2.5 px-3 text-right font-mono font-semibold ${
                        tx.type === 'income' ? 'text-emerald-400' : 'text-slate-100'
                      }`}
                    >
                      {tx.type === 'income' ? '+' : '-'}{formatINR(tx.amount, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => handleDeleteTransaction(tx.id)}
                        className="text-slate-500 hover:text-rose-400 transition p-1"
                        title="Delete transaction"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Transaction Entry Modal (Manual, Voice, Natural Language) */}
      <TransactionEntryModal
        isOpen={isTxModalOpen}
        onClose={() => setIsTxModalOpen(false)}
        onSuccess={async () => {
          await loadData(false);
        }}
      />

      {/* Statement Import Modal (CSV, XLSX, PDF) */}
      <StatementImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={async (importedCount) => {
          alert(`Successfully imported ${importedCount} transactions!`);
          await loadData(false);
        }}
      />

      {/* Set Budget Modal */}
      {isBudgetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 text-xs">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Tag className="w-4 h-4 text-emerald-400" />
              Configure Category Budget Limit
            </h3>

            <form onSubmit={handleSaveBudget} className="space-y-4">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Category</label>
                <input
                  type="text"
                  required
                  list="budget-cat-list"
                  value={budgetFormData.category}
                  onChange={(e) => setBudgetFormData({ ...budgetFormData, category: e.target.value })}
                  placeholder="e.g. Groceries"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
                <datalist id="budget-cat-list">
                  <option value="Food" />
                  <option value="Groceries" />
                  <option value="Transport" />
                  <option value="Shopping" />
                  <option value="Entertainment" />
                  <option value="Bills & Utilities" />
                  <option value="Healthcare" />
                  <option value="Education" />
                  <option value="Rent/Housing" />
                  <option value="EMI/Debt" />
                  <option value="Salary/Income" />
                  <option value="Savings/Investment" />
                  <option value="Cash Withdrawal" />
                  <option value="Miscellaneous" />
                </datalist>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Monthly Spending Limit (₹)</label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  required
                  value={budgetFormData.monthly_limit}
                  onChange={(e) => setBudgetFormData({ ...budgetFormData, monthly_limit: e.target.value })}
                  placeholder="e.g. 15000"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsBudgetModalOpen(false)}
                  className="px-4 py-2 text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingBudget}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl shadow-sm transition disabled:opacity-50"
                >
                  {submittingBudget ? 'Saving...' : 'Set Limit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
