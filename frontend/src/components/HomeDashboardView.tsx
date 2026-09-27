import React, { useEffect, useState } from 'react';
import {
  Activity,
  ArrowRight,
  Compass,
  CreditCard,
  FileSpreadsheet,
  Mic,
  PlusCircle,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
  Zap,
  UserCheck,
} from 'lucide-react';
import {
  fetchFinancialProfile,
  fetchSafeToSpend,
  fetchExpenseSummary,
  fetchGoals,
  fetchProactiveInsights,
  fetchMonitoringStatus,
} from '../services/api';
import type {
  FinancialProfile,
  SafeToSpend,
  ExpenseSummary,
  Goal,
  ProactiveInsight,
  MonitoringStatusResponse,
} from '../types';
import { formatINR } from '../utils/formatters';

interface HomeDashboardViewProps {
  onNavigate: (route: string, extraPrompt?: string) => void;
  onOpenTransactionModal: () => void;
  onOpenImportModal: () => void;
  onOpenOnboarding?: () => void;
  userName?: string | null;
}

export const HomeDashboardView: React.FC<HomeDashboardViewProps> = ({
  onNavigate,
  onOpenTransactionModal,
  onOpenImportModal,
  onOpenOnboarding,
  userName,
}) => {
  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [safeToSpend, setSafeToSpend] = useState<SafeToSpend | null>(null);
  const [expenseSummary, setExpenseSummary] = useState<ExpenseSummary | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [insights, setInsights] = useState<ProactiveInsight[]>([]);
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringStatusResponse | null>(null);
  const [, setIsLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      setIsLoading(true);
      try {
        const [profData, safeData, expData, goalsData, insightsData, monData] = await Promise.allSettled([
          fetchFinancialProfile(),
          fetchSafeToSpend(),
          fetchExpenseSummary(),
          fetchGoals(),
          fetchProactiveInsights(),
          fetchMonitoringStatus(),
        ]);

        if (profData.status === 'fulfilled') setProfile(profData.value);
        if (safeData.status === 'fulfilled') setSafeToSpend(safeData.value);
        if (expData.status === 'fulfilled') setExpenseSummary(expData.value);
        if (goalsData.status === 'fulfilled') setGoals(goalsData.value);
        if (insightsData.status === 'fulfilled') setInsights(insightsData.value);
        if (monData.status === 'fulfilled') setMonitoringStatus(monData.value);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const hasCompleteProfile = !!profile && !!profile.monthly_income && parseFloat(profile.monthly_income) > 0;

  const healthScore = profile?.indicators?.financial_health_score
    ? parseFloat(profile.indicators.financial_health_score)
    : 0;
  const healthGrade = profile?.indicators?.financial_health_grade || (hasCompleteProfile ? 'Pending' : 'No Profile');

  const topInsight = insights.length > 0 ? insights[0] : null;

  const getPlanStatusBadge = () => {
    const status = monitoringStatus?.plan_status || 'nominal';
    if (status === 'nominal' || status === 'on_track') {
      return {
        label: 'Plan On Track',
        color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
        icon: <ShieldCheck className="w-3.5 h-3.5" />,
      };
    }
    if (status === 'critical_replanning_required' || status === 'replanning_required') {
      return {
        label: 'Replanning Required',
        color: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
        icon: <ShieldAlert className="w-3.5 h-3.5" />,
      };
    }
    return {
      label: 'Needs Attention',
      color: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      icon: <Activity className="w-3.5 h-3.5" />,
    };
  };

  const planStatus = getPlanStatusBadge();

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Incomplete Profile Alert Banner */}
      {!hasCompleteProfile && (
        <div className="bg-gradient-to-r from-amber-500/10 via-indigo-500/10 to-slate-900 border border-amber-500/30 p-5 rounded-3xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30 flex-shrink-0">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Complete your financial baseline</h3>
              <p className="text-xs text-slate-300 mt-0.5">
                Add your monthly income, savings, and living expenses to activate autonomous monitoring, safe-to-spend tracking, and health metrics.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              if (onOpenOnboarding) {
                onOpenOnboarding();
              } else {
                onNavigate('/settings');
              }
            }}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-sm transition whitespace-nowrap flex items-center gap-1.5 self-end sm:self-center"
          >
            Complete Profile
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Header Welcome Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-lg">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
              Autonomous Financial Overview
            </span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${planStatus.color}`}>
              {planStatus.icon}
              {planStatus.label}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Welcome back{userName ? `, ${userName}` : ''}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Your finances are synchronized and continuously monitored by FinPilot AI agents.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('/advisor')}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/20 transition flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            Ask AI Advisor
          </button>
          <button
            onClick={() => onNavigate('/scenario-lab')}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700 transition flex items-center gap-2"
          >
            <Compass className="w-4 h-4" />
            Simulate Decision
          </button>
        </div>
      </div>

      {/* Primary KPI Grid: Health Score, Safe-To-Spend, Monthly Snapshot */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 1. Financial Health Score */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold uppercase tracking-wider">
              <Activity className="w-4 h-4 text-emerald-400" />
              Financial Health
            </div>
            <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Grade {healthGrade}
            </span>
          </div>

          <div className="my-2 flex items-baseline gap-3">
            <div className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
              {healthScore.toFixed(0)}
            </div>
            <span className="text-xs text-slate-400">/ 100 Overall Score</span>
          </div>

          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden my-3">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                healthScore >= 80 ? 'bg-emerald-500' : healthScore >= 60 ? 'bg-indigo-500' : healthScore > 0 ? 'bg-amber-500' : 'bg-slate-700'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, healthScore))}%` }}
            />
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            {healthScore >= 75
              ? 'Healthy savings rate and manageable debt ratio. Ready for goal acceleration.'
              : healthScore > 0
              ? 'Moderate buffer. Consider reviewing discretionary spending leaks.'
              : 'Complete your financial profile to calculate your real-time financial health score.'}
          </p>
        </div>

        {/* 2. Safe to Spend */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold uppercase tracking-wider">
              <Zap className="w-4 h-4 text-indigo-400" />
              Safe to Spend (Current Cycle)
            </div>
            <span className="text-xs text-slate-400">
              {safeToSpend?.days_remaining ?? 0} days left
            </span>
          </div>

          <div className="my-2">
            <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              {formatINR(safeToSpend?.safe_to_spend_amount, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-indigo-300 mt-1">
              Daily budget: ~{formatINR(safeToSpend?.daily_safe_to_spend, { minimumFractionDigits: 2 })} / day
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed mt-3">
            Calculated strictly after protecting monthly savings commitments, recurring bills, and essential living costs.
          </p>
        </div>

        {/* 3. Monthly Snapshot */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold uppercase tracking-wider">
              <CreditCard className="w-4 h-4 text-purple-400" />
              Monthly Cash Snapshot
            </div>
            <button
              onClick={() => onNavigate('/money')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
            >
              Details <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 my-2">
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="text-[10px] uppercase text-slate-400">Income</div>
              <div className="text-sm font-bold text-emerald-400">
                {formatINR(profile?.monthly_income, { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="text-[10px] uppercase text-slate-400">Expenses</div>
              <div className="text-sm font-bold text-slate-200">
                {formatINR(expenseSummary?.total_expenses, { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="text-[10px] uppercase text-slate-400">Net Savings</div>
              <div className="text-sm font-bold text-indigo-400">
                {formatINR(expenseSummary?.net_savings, { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="text-[10px] uppercase text-slate-400">Savings Rate</div>
              <div className="text-sm font-bold text-purple-400">
                {profile?.indicators?.savings_rate ? `${parseFloat(profile.indicators.savings_rate).toFixed(1)}%` : '0.0%'}
              </div>
            </div>
          </div>

          <div className="text-[11px] text-slate-500">
            Emergency Runway: {profile?.indicators?.emergency_fund?.months_covered ? `${parseFloat(profile.indicators.emergency_fund.months_covered).toFixed(1)} months covered` : '0.0 months'}
          </div>
        </div>
      </div>

      {/* Top Proactive AI Insight Banner */}
      {topInsight && (
        <div className="bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-900 border border-indigo-500/30 rounded-3xl p-6 relative shadow-md">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30 flex-shrink-0 mt-0.5">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                    Proactive AI Optimization
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {topInsight.insight_type.toUpperCase()}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white mt-0.5">{topInsight.title}</h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed max-w-3xl">
                  {topInsight.description}
                </p>
              </div>
            </div>

            <button
              onClick={() => onNavigate('/advisor', topInsight.action_prompt || `How can I implement: ${topInsight.title}?`)}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition whitespace-nowrap flex items-center gap-1.5 self-end sm:self-center"
            >
              Take Action
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Goals & Quick Actions Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Goals (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900/70 border border-slate-800 rounded-3xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Target className="w-4 h-4 text-pink-400" />
                Active Savings Goals
              </h2>
              <p className="text-xs text-slate-400">Track milestones and funded timelines</p>
            </div>
            <button
              onClick={() => onNavigate('/plan')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              View Plan <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {goals.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-800 rounded-2xl">
              <Target className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400 mb-3">No active savings goals set up yet.</p>
              <button
                onClick={() => onNavigate('/plan')}
                className="px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 text-xs font-medium border border-indigo-500/30 transition"
              >
                + Add Your First Goal
              </button>
            </div>
          ) : (
            <div className="space-y-3.5">
              {goals.slice(0, 3).map((g) => {
                const cur = parseFloat(g.current_amount || '0');
                const tgt = parseFloat(g.target_amount || '1');
                const pct = Math.min(100, Math.round((cur / tgt) * 100));
                return (
                  <div key={g.id} className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80">
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="font-semibold text-sm text-slate-200">{g.name}</div>
                      <div className="text-xs text-slate-400">
                        <span className="text-white font-bold">{formatINR(cur)}</span> / {formatINR(tgt)} ({pct}%)
                      </div>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-pink-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick Actions (1 col) */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Quick Actions
            </h2>
            <p className="text-xs text-slate-400 mb-4">Fast-track financial entries & planning</p>

            <div className="grid grid-cols-2 gap-2.5">
              <button
                onClick={onOpenTransactionModal}
                className="p-3 rounded-2xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-left transition group"
              >
                <PlusCircle className="w-4 h-4 text-emerald-400 mb-1.5 group-hover:scale-110 transition" />
                <div className="text-xs font-semibold text-slate-200">Add Expense</div>
                <div className="text-[10px] text-slate-500">Record transaction</div>
              </button>

              <button
                onClick={onOpenTransactionModal}
                className="p-3 rounded-2xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-left transition group"
              >
                <Mic className="w-4 h-4 text-indigo-400 mb-1.5 group-hover:scale-110 transition" />
                <div className="text-xs font-semibold text-slate-200">Voice Entry</div>
                <div className="text-[10px] text-slate-500">Natural language</div>
              </button>

              <button
                onClick={onOpenImportModal}
                className="p-3 rounded-2xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-left transition group"
              >
                <FileSpreadsheet className="w-4 h-4 text-purple-400 mb-1.5 group-hover:scale-110 transition" />
                <div className="text-xs font-semibold text-slate-200">Import File</div>
                <div className="text-[10px] text-slate-500">CSV / Excel / PDF</div>
              </button>

              <button
                onClick={() => onNavigate('/scenario-lab')}
                className="p-3 rounded-2xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-left transition group"
              >
                <Compass className="w-4 h-4 text-pink-400 mb-1.5 group-hover:scale-110 transition" />
                <div className="text-xs font-semibold text-slate-200">Simulate</div>
                <div className="text-[10px] text-slate-500">Purchase / loan</div>
              </button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80">
            <button
              onClick={() => onNavigate('/insights')}
              className="w-full py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-800 transition flex items-center justify-center gap-1.5"
            >
              Explore Full Insights Dashboard
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
