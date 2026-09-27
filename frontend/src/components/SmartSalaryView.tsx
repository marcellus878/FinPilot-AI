import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Edit2,
  Flame,
  Layers,
  Plus,
  RefreshCw,
  Repeat,
  ShieldCheck,
  Sparkles,
  Trash2,
  XCircle,
} from 'lucide-react';
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

import {
  calculateCustomAllocation,
  createRecurringCommitment,
  deleteRecurringCommitment,
  fetchRecurringCommitments,
  fetchSafeToSpend,
  fetchSalaryAllocation,
  fetchSalaryProfile,
  fetchSurvivalProjection,
  recalculateMonthlyPlan,
  saveSalaryProfile,
} from '../services/api';
import type {
  AllocationAlternative,
  RecurringCommitment,
  RecurringCommitmentFormData,
  RecurringFrequency,
  SafeToSpend,
  SalaryAllocation,
  SalaryProfile,
  SalaryProfileFormData,
  SurvivalProjection,
  SurvivalStatus,
} from '../types';
import { formatINR } from '../utils/formatters';

const ALLOCATION_COLORS = {
  Fixed: '#8b5cf6',         // violet
  Essentials: '#10b981',    // emerald
  Savings: '#06b6d4',       // cyan
  Discretionary: '#f43f5e', // rose
  Buffer: '#f59e0b',        // amber
};

const SURVIVAL_CONFIG: Record<
  SurvivalStatus,
  { label: string; badgeClass: string; borderClass: string; icon: React.ReactNode }
> = {
  comfortable: {
    label: 'Comfortable',
    badgeClass: 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80',
    borderClass: 'border-emerald-500/30',
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  },
  watch: {
    label: 'Watch Carefully',
    badgeClass: 'bg-amber-950/80 text-amber-300 border-amber-800/80',
    borderClass: 'border-amber-500/30',
    icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  },
  at_risk: {
    label: 'At Risk of Shortfall',
    badgeClass: 'bg-rose-950/80 text-rose-300 border-rose-800/80',
    borderClass: 'border-rose-500/30',
    icon: <XCircle className="w-4 h-4 text-rose-400" />,
  },
  insufficient_data: {
    label: 'Insufficient Data',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-700',
    borderClass: 'border-slate-700',
    icon: <AlertCircle className="w-4 h-4 text-slate-400" />,
  },
};

export const SmartSalaryView: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Core Data
  const [salaryProfile, setSalaryProfile] = useState<SalaryProfile | null>(null);
  const [commitments, setCommitments] = useState<RecurringCommitment[]>([]);
  const [allocation, setAllocation] = useState<SalaryAllocation | null>(null);
  const [safeToSpend, setSafeToSpend] = useState<SafeToSpend | null>(null);
  const [survival, setSurvival] = useState<SurvivalProjection | null>(null);

  // Profile Edit State
  const [isEditingProfile, setIsEditingProfile] = useState<boolean>(false);
  const [profileForm, setProfileForm] = useState<SalaryProfileFormData>({
    monthly_income: '',
    expected_salary_day: 1,
    additional_recurring_income: '0',
    savings_target: '',
    essential_spending_allowance: '',
    discretionary_allowance: '',
  });

  // Allocation Live Adjuster State
  const [customSavings, setCustomSavings] = useState<string>('');
  const [customEssentials, setCustomEssentials] = useState<string>('');
  const [customDiscretionary, setCustomDiscretionary] = useState<string>('');
  const [previewAllocation, setPreviewAllocation] = useState<SalaryAllocation | null>(null);
  const [calculatingAllocation, setCalculatingAllocation] = useState<boolean>(false);

  // Recurring Modal State
  const [isCommitmentModalOpen, setIsCommitmentModalOpen] = useState<boolean>(false);
  const [newCommitment, setNewCommitment] = useState<RecurringCommitmentFormData>({
    name: '',
    category: 'Housing',
    amount: '',
    frequency: 'monthly',
    next_expected_date: '',
    description: '',
  });

  // Formula Breakdown accordion toggle
  const [showFormulaDetails, setShowFormulaDetails] = useState<boolean>(false);

  const loadAllSalaryData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setErrorMessage(null);

    try {
      const [profileData, commitmentsData, allocData, safeData, survData] = await Promise.all([
        fetchSalaryProfile(),
        fetchRecurringCommitments(),
        fetchSalaryAllocation(),
        fetchSafeToSpend(),
        fetchSurvivalProjection(),
      ]);

      setSalaryProfile(profileData);
      setCommitments(commitmentsData);
      setAllocation(allocData);
      setPreviewAllocation(allocData);
      setSafeToSpend(safeData);
      setSurvival(survData);

      // Populate form defaults
      setProfileForm({
        monthly_income: profileData.monthly_income,
        expected_salary_day: profileData.expected_salary_day,
        additional_recurring_income: profileData.additional_recurring_income,
        savings_target: profileData.savings_target || '',
        essential_spending_allowance: profileData.essential_spending_allowance || '',
        discretionary_allowance: profileData.discretionary_allowance || '',
      });

      setCustomSavings(allocData.savings_target);
      setCustomEssentials(allocData.essential_allowance);
      setCustomDiscretionary(allocData.discretionary_allowance);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load Smart Salary planning data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAllSalaryData();
  }, []);

  // Handle live allocation calculation
  const handleCalculateCustomAllocation = async (savings: string, essentials: string, disc: string) => {
    setCalculatingAllocation(true);
    try {
      const res = await calculateCustomAllocation({
        savings_target: savings ? parseFloat(savings).toFixed(2) : undefined,
        essential_allowance: essentials ? parseFloat(essentials).toFixed(2) : undefined,
        discretionary_allowance: disc ? parseFloat(disc).toFixed(2) : undefined,
      });
      setPreviewAllocation(res);
    } catch (err: any) {
      console.error('Failed to preview allocation', err);
    } finally {
      setCalculatingAllocation(false);
    }
  };

  const handleApplyAlternative = (alt: AllocationAlternative) => {
    setCustomSavings(alt.adjusted_savings_target);
    setCustomEssentials(alt.adjusted_essential_allowance);
    setCustomDiscretionary(alt.adjusted_discretionary_allowance);
    handleCalculateCustomAllocation(
      alt.adjusted_savings_target,
      alt.adjusted_essential_allowance,
      alt.adjusted_discretionary_allowance,
    );
  };

  const handleSaveProfileAndTargets = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await saveSalaryProfile({
        ...profileForm,
        savings_target: customSavings || undefined,
        essential_spending_allowance: customEssentials || undefined,
        discretionary_allowance: customDiscretionary || undefined,
      });
      setIsEditingProfile(false);
      setSuccessMessage('Salary configuration & allocation targets saved successfully!');
      await loadAllSalaryData(true);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save salary settings.');
    }
  };

  const handleRecalculatePlan = async () => {
    setRefreshing(true);
    setErrorMessage(null);
    try {
      await recalculateMonthlyPlan();
      await loadAllSalaryData(true);
      setSuccessMessage('Monthly cash-flow plan refreshed and synchronized.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to recalculate monthly plan.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddCommitment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommitment.name || !newCommitment.amount) return;

    setErrorMessage(null);
    try {
      await createRecurringCommitment(newCommitment);
      setIsCommitmentModalOpen(false);
      setNewCommitment({
        name: '',
        category: 'Housing',
        amount: '',
        frequency: 'monthly',
        next_expected_date: '',
        description: '',
      });
      await loadAllSalaryData(true);
      setSuccessMessage('Recurring commitment added.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to add recurring commitment.');
    }
  };

  const handleDeleteCommitment = async (id: string) => {
    if (!confirm('Are you sure you want to remove this recurring commitment?')) return;
    try {
      await deleteRecurringCommitment(id);
      await loadAllSalaryData(true);
      setSuccessMessage('Recurring commitment deleted.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete commitment.');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 gap-3 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
        <p className="text-sm font-medium">Computing salary cycles, safe-to-spend, and cash-flow projections...</p>
      </div>
    );
  }

  const activeAllocation = previewAllocation || allocation;

  const allocationChartData = activeAllocation
    ? [
        { name: 'Fixed Commitments', value: parseFloat(activeAllocation.fixed_commitments) || 0, color: ALLOCATION_COLORS.Fixed },
        { name: 'Essential Spending', value: parseFloat(activeAllocation.essential_allowance) || 0, color: ALLOCATION_COLORS.Essentials },
        { name: 'Savings Target', value: parseFloat(activeAllocation.savings_target) || 0, color: ALLOCATION_COLORS.Savings },
        { name: 'Discretionary Spend', value: parseFloat(activeAllocation.discretionary_allowance) || 0, color: ALLOCATION_COLORS.Discretionary },
        { name: 'Buffer / Reserve', value: Math.max(0, parseFloat(activeAllocation.remaining_buffer) || 0), color: ALLOCATION_COLORS.Buffer },
      ].filter((item) => item.value > 0)
    : [];

  const cycleProgressPct = salaryProfile && salaryProfile.days_in_cycle > 0
    ? Math.min(100, Math.round((salaryProfile.days_elapsed / salaryProfile.days_in_cycle) * 100))
    : 0;

  return (
    <div className="space-y-6">
      {/* Toast Messages */}
      {successMessage && (
        <div className="p-3 bg-emerald-950/90 border border-emerald-700/80 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-3 bg-rose-950/90 border border-rose-700/80 rounded-xl text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Header / Salary Cycle Overview Card */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Calendar className="w-4 h-4" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">Smart Salary & Cash-Flow Planner</h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Autonomous salary allocation, forward cash-flow forecasting, and dynamic safe-to-spend allowance.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={() => setIsEditingProfile(!isEditingProfile)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 transition border border-slate-700"
            >
              <Edit2 className="w-3.5 h-3.5" />
              {isEditingProfile ? 'Close Settings' : 'Salary Settings'}
            </button>
            <button
              onClick={handleRecalculatePlan}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 transition shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              Recalculate Plan
            </button>
          </div>
        </div>

        {/* Salary Cycle Metrix Bar */}
        {salaryProfile && (
          <div className="mt-6 pt-5 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Total Monthly Inflow
              </span>
              <span className="text-lg font-bold text-emerald-400 mt-0.5 block">
                {formatINR(salaryProfile.total_monthly_income, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-500">
                Base: {formatINR(salaryProfile.monthly_income)} | Addl: {formatINR(salaryProfile.additional_recurring_income)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Salary Day
              </span>
              <span className="text-lg font-bold text-white mt-0.5 block">
                {salaryProfile.expected_salary_day}
                <span className="text-xs text-slate-400 font-normal">th of month</span>
              </span>
              <span className="text-[10px] text-slate-500">
                Next: {new Date(salaryProfile.next_salary_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Cycle Days Left
              </span>
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <span className="text-lg font-bold text-cyan-400">
                  {salaryProfile.days_remaining}
                </span>
                <span className="text-xs text-slate-400 font-medium">/ {salaryProfile.days_in_cycle} days</span>
              </div>
              <span className="text-[10px] text-slate-500">
                {salaryProfile.days_elapsed} days elapsed
              </span>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Cycle Progress
              </span>
              <span className="text-lg font-bold text-slate-200 mt-0.5 block">
                {cycleProgressPct}%
              </span>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all"
                  style={{ width: `${cycleProgressPct}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Inline Profile Settings Form */}
        {isEditingProfile && (
          <form onSubmit={handleSaveProfileAndTargets} className="mt-6 pt-5 border-t border-slate-800 bg-slate-950/70 p-4 rounded-xl border">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Edit2 className="w-4 h-4 text-emerald-400" />
              Configure Salary Inflow & Cycle Date
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Base Monthly Salary (₹)
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  required
                  value={profileForm.monthly_income}
                  onChange={(e) => setProfileForm({ ...profileForm, monthly_income: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Expected Salary Day (1-31)
                </label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  required
                  value={profileForm.expected_salary_day}
                  onChange={(e) => setProfileForm({ ...profileForm, expected_salary_day: parseInt(e.target.value) || 1 })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Additional Recurring Income (₹)
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={profileForm.additional_recurring_income}
                  onChange={(e) => setProfileForm({ ...profileForm, additional_recurring_income: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsEditingProfile(false)}
                className="px-3 py-1.5 text-xs rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-500"
              >
                Save Changes
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Dual Hero Row: Safe-to-Spend & Survival Predictor */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* HERO 1: Safe-to-Spend Calculator */}
        {safeToSpend && (
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />

            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <ShieldCheck className="w-4 h-4" />
                  </span>
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Safe-to-Spend Allowance
                  </span>
                </div>
                <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/60">
                  {safeToSpend.days_remaining} days left
                </span>
              </div>

              {/* Main Daily Allowance */}
              <div className="mt-5">
                <span className="text-xs text-slate-400 font-medium">Daily Safe Allowance</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl sm:text-4xl font-black tracking-tight text-white">
                    {formatINR(safeToSpend.daily_safe_to_spend, { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-slate-400 font-medium">/ day</span>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between text-xs py-2 px-3 bg-slate-950/70 rounded-xl border border-slate-800/80">
                <span className="text-slate-400">Total Unencumbered Pool:</span>
                <span className="font-bold text-emerald-400">
                  {formatINR(safeToSpend.safe_to_spend_amount, { minimumFractionDigits: 2 })}
                </span>
              </div>

              <p className="text-xs text-slate-400 mt-3 italic leading-relaxed">
                "{safeToSpend.explanation}"
              </p>
            </div>

            {/* Formula Breakdown Toggle */}
            <div className="mt-5 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowFormulaDetails(!showFormulaDetails)}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition"
              >
                <span>{showFormulaDetails ? 'Hide' : 'View'} Deterministic Formula Breakdown</span>
                <ArrowRight className={`w-3.5 h-3.5 transform transition ${showFormulaDetails ? 'rotate-90' : ''}`} />
              </button>

              {showFormulaDetails && (
                <div className="mt-3 space-y-1.5 bg-slate-950/90 p-3 rounded-xl border border-slate-800/90 text-xs">
                  <div className="flex justify-between text-slate-300 font-medium pb-1 border-b border-slate-800">
                    <span>Current Available Liquidity:</span>
                    <span className="text-white font-mono">{formatINR(safeToSpend.current_available_funds, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>− Upcoming Fixed Commitments:</span>
                    <span className="text-rose-400 font-mono">−{formatINR(safeToSpend.upcoming_commitments, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>− Remaining Essential Allowance:</span>
                    <span className="text-rose-400 font-mono">−{formatINR(safeToSpend.remaining_essential_allowance, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>− Savings Target Reserve:</span>
                    <span className="text-rose-400 font-mono">−{formatINR(safeToSpend.savings_reserve, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>− Emergency Reserve Buffer:</span>
                    <span className="text-rose-400 font-mono">−{formatINR(safeToSpend.emergency_reserve, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-emerald-300 font-bold pt-1.5 border-t border-slate-800">
                    <span>= Total Safe to Spend ({safeToSpend.days_remaining}d):</span>
                    <span className="font-mono">{formatINR(safeToSpend.safe_to_spend_amount, { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* HERO 2: End-of-Month Survival Predictor */}
        {survival && (
          <div
            className={`bg-slate-900 border rounded-2xl p-6 shadow-xl flex flex-col justify-between relative overflow-hidden ${
              SURVIVAL_CONFIG[survival.status].borderClass
            }`}
          >
            <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />

            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <Flame className="w-4 h-4" />
                  </span>
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    End-of-Month Survival Predictor
                  </span>
                </div>

                <div
                  className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${
                    SURVIVAL_CONFIG[survival.status].badgeClass
                  }`}
                >
                  {SURVIVAL_CONFIG[survival.status].icon}
                  <span>{SURVIVAL_CONFIG[survival.status].label}</span>
                </div>
              </div>

              {/* Projected Balance on Next Salary Date */}
              <div className="mt-5">
                <span className="text-xs text-slate-400 font-medium">Projected Balance on Next Salary Day</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span
                    className={`text-3xl sm:text-4xl font-black tracking-tight ${
                      parseFloat(survival.projected_end_of_month_balance) >= 0 ? 'text-white' : 'text-rose-400'
                    }`}
                  >
                    {formatINR(survival.projected_end_of_month_balance, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 bg-slate-950/70 rounded-xl border border-slate-800/80">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Avg Daily Burn</span>
                  <span className="font-bold text-slate-200 mt-0.5 block font-mono">
                    {formatINR(survival.recent_average_daily_burn)}/day
                  </span>
                </div>
                <div className="p-2.5 bg-slate-950/70 rounded-xl border border-slate-800/80">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Spending Capacity</span>
                  <span className="font-bold text-cyan-300 mt-0.5 block font-mono">
                    {formatINR(survival.daily_spending_capacity)}/day
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-400 mt-3 italic leading-relaxed">
                "{survival.explanation}"
              </p>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Upcoming Cycle Commitments:</span>
              <span className="font-semibold text-rose-400 font-mono">
                {formatINR(survival.upcoming_commitments)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Salary Allocation Visualizer & Interactive Target Adjuster */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Layers className="w-4 h-4" />
              </span>
              <h3 className="text-lg font-bold text-white tracking-tight">Salary Allocation Engine</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic 5-bucket distribution: Fixed, Essentials, Savings, Discretionary, and Buffer.
            </p>
          </div>

          {activeAllocation && (
            <div className="flex items-center gap-2">
              {activeAllocation.is_feasible ? (
                <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-800/80">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Feasible Plan
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg bg-rose-950/80 text-rose-300 border border-rose-800/80">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Infeasible (Deficit: {formatINR(activeAllocation.deficit_amount)})
                </span>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
          {/* Chart & Distribution Legend (5 cols) */}
          <div className="lg:col-span-5 flex flex-col justify-center items-center bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="w-full h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={allocationChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {allocationChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: any) => [formatINR(val, { minimumFractionDigits: 2 }), 'Allocated']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Breakdown Legend */}
            {activeAllocation && (
              <div className="w-full space-y-2 mt-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ALLOCATION_COLORS.Fixed }} />
                    <span className="text-slate-300">Fixed Commitments:</span>
                  </div>
                  <span className="font-bold text-white font-mono">
                    {formatINR(activeAllocation.fixed_commitments, { minimumFractionDigits: 2 })} ({activeAllocation.fixed_percentage}%)
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ALLOCATION_COLORS.Essentials }} />
                    <span className="text-slate-300">Essential Allowance:</span>
                  </div>
                  <span className="font-bold text-emerald-400 font-mono">
                    {formatINR(activeAllocation.essential_allowance, { minimumFractionDigits: 2 })} ({activeAllocation.essential_percentage}%)
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ALLOCATION_COLORS.Savings }} />
                    <span className="text-slate-300">Savings Target:</span>
                  </div>
                  <span className="font-bold text-cyan-400 font-mono">
                    {formatINR(activeAllocation.savings_target, { minimumFractionDigits: 2 })} ({activeAllocation.savings_percentage}%)
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ALLOCATION_COLORS.Discretionary }} />
                    <span className="text-slate-300">Discretionary (Guilty Pleasures):</span>
                  </div>
                  <span className="font-bold text-rose-400 font-mono">
                    {formatINR(activeAllocation.discretionary_allowance, { minimumFractionDigits: 2 })} ({activeAllocation.discretionary_percentage}%)
                  </span>
                </div>

                <div className="flex items-center justify-between pt-1 border-t border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ALLOCATION_COLORS.Buffer }} />
                    <span className="text-slate-300">Remaining Buffer:</span>
                  </div>
                  <span
                    className={`font-bold font-mono ${
                      parseFloat(activeAllocation.remaining_buffer) >= 0 ? 'text-amber-400' : 'text-rose-400'
                    }`}
                  >
                    {formatINR(activeAllocation.remaining_buffer, { minimumFractionDigits: 2 })} ({activeAllocation.buffer_percentage}%)
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Interactive Live Target Adjuster (7 cols) */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                  Live Allocation Adjuster & Simulation
                </span>
                {calculatingAllocation && (
                  <span className="text-[10px] text-cyan-400 font-medium flex items-center gap-1">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Recalculating...
                  </span>
                )}
              </div>

              <div className="space-y-3.5">
                {/* Savings Target Slider/Input */}
                <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
                  <div className="flex justify-between text-xs mb-1">
                    <label className="font-medium text-cyan-300">Target Savings Amount (₹)</label>
                    <span className="font-bold text-white font-mono">{formatINR(customSavings)}</span>
                  </div>
                  <input
                    type="number"
                    step="500"
                    min="0"
                    value={customSavings}
                    onChange={(e) => {
                      setCustomSavings(e.target.value);
                      handleCalculateCustomAllocation(e.target.value, customEssentials, customDiscretionary);
                    }}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
                    placeholder="e.g. 20000"
                  />
                </div>

                {/* Essential Spending Allowance */}
                <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
                  <div className="flex justify-between text-xs mb-1">
                    <label className="font-medium text-emerald-300">Essential Spending Allowance (₹)</label>
                    <span className="font-bold text-white font-mono">{formatINR(customEssentials)}</span>
                  </div>
                  <input
                    type="number"
                    step="500"
                    min="0"
                    value={customEssentials}
                    onChange={(e) => {
                      setCustomEssentials(e.target.value);
                      handleCalculateCustomAllocation(customSavings, e.target.value, customDiscretionary);
                    }}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                    placeholder="e.g. 35000"
                  />
                </div>

                {/* Discretionary Allowance */}
                <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
                  <div className="flex justify-between text-xs mb-1">
                    <label className="font-medium text-rose-300">Discretionary / Guilty Pleasures (₹)</label>
                    <span className="font-bold text-white font-mono">{formatINR(customDiscretionary)}</span>
                  </div>
                  <input
                    type="number"
                    step="500"
                    min="0"
                    value={customDiscretionary}
                    onChange={(e) => {
                      setCustomDiscretionary(e.target.value);
                      handleCalculateCustomAllocation(customSavings, customEssentials, e.target.value);
                    }}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-rose-500"
                    placeholder="e.g. 15000"
                  />
                </div>
              </div>

              {/* Infeasibility Rebalancing Alternatives */}
              {activeAllocation && !activeAllocation.is_feasible && activeAllocation.alternatives.length > 0 && (
                <div className="mt-4 p-3.5 bg-rose-950/40 border border-rose-800/60 rounded-xl space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-300">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>Infeasible Target: Rebalancing Recommendations</span>
                  </div>
                  <p className="text-[11px] text-slate-300">
                    Your desired targets exceed monthly inflow by {formatINR(activeAllocation.deficit_amount)}. Select an alternative below to restore balance:
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                    {activeAllocation.alternatives.map((alt, idx) => (
                      <div
                        key={idx}
                        className="p-2 bg-slate-900/90 rounded-lg border border-slate-800 flex flex-col justify-between"
                      >
                        <div>
                          <span className="text-[11px] font-bold text-emerald-400 block">{alt.title}</span>
                          <span className="text-[10px] text-slate-400 line-clamp-2 mt-0.5">{alt.description}</span>
                          <div className="mt-1.5 text-[10px] text-slate-300 space-y-0.5">
                            <div>Save: <span className="font-mono text-cyan-300">{formatINR(alt.adjusted_savings_target)}</span></div>
                            <div>Disc: <span className="font-mono text-rose-300">{formatINR(alt.adjusted_discretionary_allowance)}</span></div>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleApplyAlternative(alt)}
                          className="mt-2 text-[10px] font-semibold text-center w-full py-1 bg-emerald-600/80 hover:bg-emerald-500 text-white rounded transition"
                        >
                          Use This
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Save Targets Button */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={handleSaveProfileAndTargets}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 transition shadow-sm flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Save Target Allocations
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Recurring Commitments & Subscriptions Manager */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
                <Repeat className="w-4 h-4" />
              </span>
              <h3 className="text-lg font-bold text-white tracking-tight">Recurring Expense & Commitment Planner</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage fixed recurring commitments normalized into monthly cash obligations.
            </p>
          </div>

          <button
            onClick={() => setIsCommitmentModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-violet-600 text-white hover:bg-violet-500 transition shadow-sm self-start sm:self-auto"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Commitment
          </button>
        </div>

        {/* Commitment List */}
        {commitments.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs">
            <Repeat className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            No recurring commitments added yet. Add rent, loans, insurance, or subscriptions to plan your cash-flow.
          </div>
        ) : (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {commitments.map((c) => (
              <div
                key={c.id}
                className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 flex flex-col justify-between hover:border-slate-700 transition"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-white text-xs">{c.name}</span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800/60 uppercase">
                      {c.frequency}
                    </span>
                  </div>

                  <div className="flex items-baseline gap-1.5 mt-2">
                    <span className="text-base font-bold text-slate-200">
                      {formatINR(c.amount, { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-[10px] text-slate-400 font-normal">
                      ({formatINR(c.monthly_equivalent, { minimumFractionDigits: 2 })}/mo)
                    </span>
                  </div>

                  <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
                    <span>Category: {c.category}</span>
                    {c.is_due_in_current_cycle && (
                      <span className="text-amber-400 font-medium">Due in cycle</span>
                    )}
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-900 flex justify-end">
                  <button
                    onClick={() => handleDeleteCommitment(c.id)}
                    className="text-slate-500 hover:text-rose-400 p-1 rounded transition"
                    title="Delete commitment"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Commitment Modal */}
      {isCommitmentModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Plus className="w-4 h-4 text-violet-400" />
              Add Recurring Commitment
            </h3>

            <form onSubmit={handleAddCommitment} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Commitment Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rent, Netflix, Car Loan, Internet"
                  value={newCommitment.name}
                  onChange={(e) => setNewCommitment({ ...newCommitment, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-violet-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    required
                    placeholder="e.g. 15000"
                    value={newCommitment.amount}
                    onChange={(e) => setNewCommitment({ ...newCommitment, amount: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Frequency</label>
                  <select
                    value={newCommitment.frequency}
                    onChange={(e) => setNewCommitment({ ...newCommitment, frequency: e.target.value as RecurringFrequency })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="annual">Annual</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Category</label>
                <select
                  value={newCommitment.category}
                  onChange={(e) => setNewCommitment({ ...newCommitment, category: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-violet-500"
                >
                  <option value="Housing">Housing</option>
                  <option value="Utilities">Utilities</option>
                  <option value="Subscription">Subscription</option>
                  <option value="Insurance">Insurance</option>
                  <option value="Debt">Debt / EMI</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsCommitmentModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-violet-600 text-white font-semibold hover:bg-violet-500"
                >
                  Save Commitment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartSalaryView;
