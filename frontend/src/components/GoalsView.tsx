import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  DollarSign,
  Edit2,
  Plus,
  RefreshCw,
  Target,
  Trash2,
  X,
  XCircle,
} from 'lucide-react';

import {
  createGoal,
  deleteGoal,
  fetchGoalAnalysis,
  fetchGoals,
  updateGoal,
} from '../services/api';
import type {
  Goal,
  GoalAnalysisResponse,
  GoalFormData,
  GoalPriority,
} from '../types';
import { formatINR } from '../utils/formatters';

const CATEGORY_COLORS: Record<string, string> = {
  Emergency: 'bg-amber-950/80 text-amber-300 border-amber-800/80',
  Technology: 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80',
  Laptop: 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80',
  Travel: 'bg-purple-950/80 text-purple-300 border-purple-800/80',
  Vacation: 'bg-purple-950/80 text-purple-300 border-purple-800/80',
  Education: 'bg-blue-950/80 text-blue-300 border-blue-800/80',
  Vehicle: 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80',
  Housing: 'bg-indigo-950/80 text-indigo-300 border-indigo-800/80',
  General: 'bg-slate-800 text-slate-300 border-slate-700',
};

const PRIORITY_BADGES: Record<GoalPriority, { label: string; class: string }> = {
  high: { label: 'High Priority', class: 'bg-rose-950/80 text-rose-300 border-rose-800/80' },
  medium: { label: 'Medium Priority', class: 'bg-amber-950/80 text-amber-300 border-amber-800/80' },
  low: { label: 'Low Priority', class: 'bg-slate-800 text-slate-300 border-slate-700' },
};

export const GoalsView: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Analysis & Raw Goals
  const [analysis, setAnalysis] = useState<GoalAnalysisResponse | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);

  // Filter tab
  const [statusFilter, setStatusFilter] = useState<'all' | 'in_progress' | 'achieved'>('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingGoalId, setEditingGoalId] = useState<string | null>(null);
  const [goalForm, setGoalForm] = useState<GoalFormData>({
    name: '',
    target_amount: '',
    current_amount: '0',
    target_date: '',
    priority: 'medium',
    category: 'General',
    monthly_contribution: '',
    status: 'in_progress',
  });

  const loadGoalsData = async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    setErrorMessage(null);

    try {
      const [goalsList, analysisData] = await Promise.all([
        fetchGoals(),
        fetchGoalAnalysis(),
      ]);
      setGoals(goalsList);
      setAnalysis(analysisData);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load goals.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadGoalsData();
  }, []);

  const openCreateModal = () => {
    setEditingGoalId(null);
    setGoalForm({
      name: '',
      target_amount: '',
      current_amount: '0',
      target_date: '',
      priority: 'medium',
      category: 'General',
      monthly_contribution: '',
      status: 'in_progress',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (goal: Goal) => {
    setEditingGoalId(goal.id);
    setGoalForm({
      name: goal.name,
      target_amount: goal.target_amount,
      current_amount: goal.current_amount,
      target_date: goal.target_date || '',
      priority: goal.priority,
      category: goal.category || 'General',
      monthly_contribution: goal.monthly_contribution || '',
      status: goal.status,
    });
    setIsModalOpen(true);
  };

  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalForm.name || !goalForm.target_amount) return;

    setErrorMessage(null);
    try {
      if (editingGoalId) {
        await updateGoal(editingGoalId, goalForm);
        setSuccessMessage('Goal updated successfully.');
      } else {
        await createGoal(goalForm);
        setSuccessMessage('Goal created successfully.');
      }
      setIsModalOpen(false);
      await loadGoalsData(true);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save goal.');
    }
  };

  const handleDeleteGoal = async (id: string) => {
    if (!confirm('Are you sure you want to delete this goal?')) return;
    try {
      await deleteGoal(id);
      setSuccessMessage('Goal deleted.');
      await loadGoalsData(true);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete goal.');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 gap-3 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
        <p className="text-sm font-medium">Analyzing goals and calculating timeline projections...</p>
      </div>
    );
  }

  const evaluations = analysis?.goal_evaluations || [];
  const filteredEvaluations = evaluations.filter((ev) => {
    if (statusFilter === 'in_progress') return ev.status !== 'achieved';
    if (statusFilter === 'achieved') return ev.status === 'achieved';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Toast Notifications */}
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

      {/* Header & Portfolio Metrics Card */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-gradient-to-br from-cyan-500/5 to-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Target className="w-4 h-4" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">Goal Planning & Portfolio Engine</h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic goal completion forecasting, capacity validation, and multi-goal conflict resolution.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={() => loadGoalsData(true)}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 transition border border-slate-700"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={openCreateModal}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 transition shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              New Goal
            </button>
          </div>
        </div>

        {/* Portfolio KPI Grid */}
        {analysis && (
          <div className="mt-6 pt-5 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Total Target Goal Capital
              </span>
              <span className="text-lg font-bold text-white mt-0.5 block">
                {formatINR(analysis.total_target_amount, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-500">
                Across {analysis.active_goals_count + analysis.achieved_goals_count} goals
              </span>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Total Saved So Far
              </span>
              <span className="text-lg font-bold text-emerald-400 mt-0.5 block">
                {formatINR(analysis.total_saved_amount, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-500">
                {analysis.overall_progress_percentage}% funded
              </span>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Required Monthly Inflow
              </span>
              <span className="text-lg font-bold text-cyan-400 mt-0.5 block">
                {formatINR(analysis.total_required_monthly, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-500">
                To meet all deadlines
              </span>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Monthly Available Capacity
              </span>
              <span
                className={`text-lg font-bold mt-0.5 block ${
                  parseFloat(analysis.net_monthly_surplus_or_shortfall) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {formatINR(analysis.available_monthly_capacity, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-500">
                {parseFloat(analysis.net_monthly_surplus_or_shortfall) >= 0
                  ? `+${formatINR(analysis.net_monthly_surplus_or_shortfall)} surplus buffer`
                  : `-${formatINR(Math.abs(parseFloat(analysis.net_monthly_surplus_or_shortfall)))} shortfall`}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Goal Conflict Alert & Resolution Strategies */}
      {analysis && analysis.conflict_detected && analysis.conflict_alternatives.length > 0 && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <span className="p-2 bg-rose-500/20 text-rose-400 rounded-xl border border-rose-500/30 flex-shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </span>
              <div>
                <h3 className="text-base font-bold text-white tracking-tight">
                  Goal Conflict Detected — Funding Shortfall
                </h3>
                <p className="text-xs text-rose-300 mt-0.5 leading-relaxed">
                  Your active goals require a combined{' '}
                  <strong className="text-white">{formatINR(analysis.total_required_monthly, { minimumFractionDigits: 2 })}/month</strong>,
                  which exceeds your available monthly savings capacity of{' '}
                  <strong className="text-white">{formatINR(analysis.available_monthly_capacity, { minimumFractionDigits: 2 })}/month</strong>{' '}
                  by <strong className="text-rose-200">{formatINR(Math.abs(parseFloat(analysis.net_monthly_surplus_or_shortfall)), { minimumFractionDigits: 2 })}/month</strong>.
                </p>
              </div>
            </div>

            <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-rose-900/80 text-rose-200 border border-rose-700">
              Shortfall: {formatINR(Math.abs(parseFloat(analysis.net_monthly_surplus_or_shortfall)))}/mo
            </span>
          </div>

          <div className="pt-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-3">
              Deterministic Allocation Alternatives
            </span>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {analysis.conflict_alternatives.map((alt) => (
                <div
                  key={alt.strategy_id}
                  className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-300">{alt.strategy_name}</span>
                      <span className="text-[10px] text-slate-400 font-medium">
                        {alt.fully_funded_count} funded
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                      {alt.description}
                    </p>

                    <div className="mt-3 space-y-1.5 pt-2 border-t border-slate-800 text-xs">
                      {alt.allocations.map((a) => (
                        <div key={a.goal_id} className="flex justify-between text-[11px]">
                          <span className="text-slate-300 truncate max-w-[140px]">{a.goal_name}:</span>
                          <span
                            className={`font-mono font-semibold ${
                              a.is_fully_funded ? 'text-emerald-400' : parseFloat(a.allocated_amount) > 0 ? 'text-amber-400' : 'text-slate-500'
                            }`}
                          >
                            {formatINR(a.allocated_amount)}/mo
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-4 pt-2 border-t border-slate-800/80 flex justify-between items-center text-[10px] text-slate-400">
                    <span>Allocated: {formatINR(alt.total_allocated)}</span>
                    <span>Unallocated: {formatINR(alt.remaining_unallocated)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs & Goal Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${
                statusFilter === 'all'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Goals ({evaluations.length})
            </button>
            <button
              onClick={() => setStatusFilter('in_progress')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${
                statusFilter === 'in_progress'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              In Progress ({analysis?.active_goals_count || 0})
            </button>
            <button
              onClick={() => setStatusFilter('achieved')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${
                statusFilter === 'achieved'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Achieved ({analysis?.achieved_goals_count || 0})
            </button>
          </div>
        </div>

        {filteredEvaluations.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-12 text-center text-slate-400 space-y-3">
            <Target className="w-10 h-10 mx-auto text-slate-600" />
            <h3 className="text-sm font-semibold text-white">No Goals Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Start building wealth with purpose by defining your first financial goal.
            </p>
            <button
              onClick={openCreateModal}
              className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              Create First Goal
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEvaluations.map((ev) => {
              const rawGoal = goals.find((g) => g.id === ev.id);
              const categoryStyle = CATEGORY_COLORS[ev.category] || CATEGORY_COLORS.General;
              const priorityInfo = PRIORITY_BADGES[ev.priority] || PRIORITY_BADGES.medium;
              const progressNum = Math.min(100, Math.max(0, parseFloat(ev.progress_percentage) || 0));

              return (
                <div
                  key={ev.id}
                  className={`bg-slate-900 border rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition ${
                    ev.is_completed ? 'border-emerald-500/40' : !ev.is_feasible ? 'border-rose-500/30' : 'border-slate-800/80'
                  }`}
                >
                  <div>
                    {/* Header: Name + Category & Priority Badges */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="font-bold text-white text-sm leading-tight">{ev.name}</h4>
                        <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${categoryStyle}`}>
                            {ev.category}
                          </span>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${priorityInfo.class}`}>
                            {priorityInfo.label}
                          </span>
                        </div>
                      </div>

                      {ev.is_completed ? (
                        <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/80">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Achieved
                        </span>
                      ) : ev.is_feasible ? (
                        <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/80">
                          <CheckCircle2 className="w-3 h-3" /> Feasible
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800/80">
                          <XCircle className="w-3 h-3" /> At Risk
                        </span>
                      )}
                    </div>

                    {/* Progress Bar & Amounts */}
                    <div className="mt-4">
                      <div className="flex justify-between items-baseline text-xs mb-1.5">
                        <span className="text-slate-400 font-medium">
                          {formatINR(ev.current_amount, { minimumFractionDigits: 2 })}
                        </span>
                        <span className="font-bold text-white">
                          {formatINR(ev.target_amount, { minimumFractionDigits: 2 })}
                        </span>
                      </div>

                      <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className={`h-full rounded-full transition-all ${
                            ev.is_completed
                              ? 'bg-emerald-500'
                              : progressNum >= 75
                              ? 'bg-gradient-to-r from-cyan-500 to-emerald-400'
                              : 'bg-gradient-to-r from-blue-500 to-cyan-400'
                          }`}
                          style={{ width: `${progressNum}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1 block text-right font-mono">
                        {progressNum}% Completed
                      </span>
                    </div>

                    {/* Timeline & Monthly Contribution Metrics */}
                    <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 bg-slate-950/60 rounded-xl border border-slate-800/80">
                        <span className="text-[10px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-cyan-400" /> Target Date
                        </span>
                        <span className="font-bold text-slate-200 mt-0.5 block text-[11px]">
                          {ev.target_date
                            ? new Date(ev.target_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
                            : 'No deadline'}
                        </span>
                      </div>

                      <div className="p-2 bg-slate-950/60 rounded-xl border border-slate-800/80">
                        <span className="text-[10px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                          <DollarSign className="w-3 h-3 text-emerald-400" /> Req. Monthly
                        </span>
                        <span className="font-bold text-emerald-300 mt-0.5 block font-mono text-[11px]">
                          {formatINR(ev.required_monthly_contribution)}/mo
                        </span>
                      </div>
                    </div>

                    {/* Projected Completion Date */}
                    {ev.projected_completion_date && !ev.is_completed && (
                      <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between px-1">
                        <span>Projected Finish:</span>
                        <span className="font-semibold text-slate-300">
                          {new Date(ev.projected_completion_date).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}
                        </span>
                      </div>
                    )}

                    {/* Feasibility Warning Message if Infeasible */}
                    {!ev.is_feasible && (
                      <p className="mt-2.5 text-[11px] text-rose-300 bg-rose-950/40 p-2 rounded-lg border border-rose-800/60 leading-relaxed">
                        {ev.feasibility_explanation}
                      </p>
                    )}
                  </div>

                  {/* Actions Footer */}
                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 font-mono">
                      Rem: {formatINR(ev.remaining_amount)}
                    </span>

                    <div className="flex items-center gap-1.5">
                      {rawGoal && (
                        <button
                          onClick={() => openEditModal(rawGoal)}
                          className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800 rounded-lg transition"
                          title="Edit Goal"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteGoal(ev.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
                        title="Delete Goal"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add / Edit Goal Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Target className="w-4 h-4 text-cyan-400" />
                {editingGoalId ? 'Edit Goal' : 'Create New Financial Goal'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveGoal} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Goal Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Emergency Reserve, MacBook Pro, Goa Vacation"
                  value={goalForm.name}
                  onChange={(e) => setGoalForm({ ...goalForm, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Category</label>
                  <select
                    value={goalForm.category}
                    onChange={(e) => setGoalForm({ ...goalForm, category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="Emergency">Emergency Fund</option>
                    <option value="Technology">Technology / Laptop</option>
                    <option value="Travel">Travel / Vacation</option>
                    <option value="Education">Education</option>
                    <option value="Vehicle">Vehicle / Transport</option>
                    <option value="Housing">Housing / Real Estate</option>
                    <option value="General">General Savings</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Priority Tier</label>
                  <select
                    value={goalForm.priority}
                    onChange={(e) => setGoalForm({ ...goalForm, priority: e.target.value as GoalPriority })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="high">High Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="low">Low Priority</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Target Amount (₹)</label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    required
                    placeholder="e.g. 100000"
                    value={goalForm.target_amount}
                    onChange={(e) => setGoalForm({ ...goalForm, target_amount: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Current Saved Amount (₹)</label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="0"
                    value={goalForm.current_amount}
                    onChange={(e) => setGoalForm({ ...goalForm, current_amount: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Target Completion Date</label>
                  <input
                    type="date"
                    value={goalForm.target_date || ''}
                    onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Planned Monthly Contrib (₹)</label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="Optional fixed contribution"
                    value={goalForm.monthly_contribution || ''}
                    onChange={(e) => setGoalForm({ ...goalForm, monthly_contribution: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-cyan-600 text-white font-semibold hover:bg-cyan-500 transition shadow-sm"
                >
                  {editingGoalId ? 'Update Goal' : 'Save Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GoalsView;
