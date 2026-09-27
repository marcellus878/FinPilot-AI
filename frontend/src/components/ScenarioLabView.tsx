import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Compass,
  CreditCard,
  Flame,
  Play,
  Plus,
  Repeat,
  RotateCcw,
  Scale,
  Sparkles,
  Target,
  Trash2,
  TrendingUp,
  XCircle,
} from 'lucide-react';

import { compareScenarios, simulateScenario } from '../services/api';
import type {
  ScenarioCompareItemRequest,
  ScenarioCompareResponse,
  ScenarioSimulateRequest,
  ScenarioSimulateResponse,
  ScenarioType,
} from '../types';
import { formatINR } from '../utils/formatters';

const SCENARIO_TYPES: Array<{
  type: ScenarioType;
  label: string;
  desc: string;
  icon: React.ReactNode;
}> = [
  {
    type: 'one_time_purchase',
    label: 'One-Time Purchase',
    desc: 'Evaluate buying a laptop, gadget, vehicle down-payment, or luxury asset.',
    icon: <CreditCard className="w-4 h-4 text-cyan-400" />,
  },
  {
    type: 'new_recurring_expense',
    label: 'New Recurring Expense',
    desc: 'Simulate adding a gym membership, EMI loan, car lease, or subscription.',
    icon: <Repeat className="w-4 h-4 text-violet-400" />,
  },
  {
    type: 'income_change',
    label: 'Income Increase / Decrease',
    desc: 'Model the impact of a salary hike, new freelance retainer, or temporary pay cut.',
    icon: <TrendingUp className="w-4 h-4 text-emerald-400" />,
  },
  {
    type: 'unexpected_expense',
    label: 'Unexpected Expense',
    desc: 'Stress test sudden medical emergencies, home repairs, or urgent travel costs.',
    icon: <Flame className="w-4 h-4 text-rose-400" />,
  },
];

const VERDICT_CONFIG: Record<
  string,
  { label: string; badgeClass: string; icon: React.ReactNode }
> = {
  safe: {
    label: 'Comfortably Affordable',
    badgeClass: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/80',
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  },
  stretched: {
    label: 'Caution — Tight Cash Flow',
    badgeClass: 'bg-amber-950/80 text-amber-300 border-amber-700/80',
    icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  },
  unaffordable: {
    label: 'Unaffordable / Deficit Risk',
    badgeClass: 'bg-rose-950/80 text-rose-300 border-rose-700/80',
    icon: <XCircle className="w-4 h-4 text-rose-400" />,
  },
};

export const ScenarioLabView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'single' | 'compare'>('single');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Single Simulation State
  const [singleRequest, setSingleRequest] = useState<ScenarioSimulateRequest>({
    scenario_type: 'one_time_purchase',
    amount: '',
    name: '',
    timing_months: 0,
    description: '',
  });
  const [simulationResult, setSimulationResult] = useState<ScenarioSimulateResponse | null>(null);

  // Multi-Scenario Comparison State
  const [compareList, setCompareList] = useState<ScenarioCompareItemRequest[]>([
    {
      id: 'sc_a',
      name: 'Option A: Buy Immediately',
      type: 'one_time_purchase',
      amount: '',
      timing_months: 0,
      description: 'Immediate purchase from savings',
    },
    {
      id: 'sc_b',
      name: 'Option B: Delay Purchase',
      type: 'one_time_purchase',
      amount: '',
      timing_months: 3,
      description: 'Save for 3 months first',
    },
  ]);
  const [compareResult, setCompareResult] = useState<ScenarioCompareResponse | null>(null);

  const handleRunSingleSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleRequest.amount || parseFloat(singleRequest.amount) <= 0) return;

    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await simulateScenario(singleRequest);
      setSimulationResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to simulate decision scenario.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunComparison = async () => {
    if (compareList.length === 0) return;

    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await compareScenarios({ scenarios: compareList });
      setCompareResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to compare decision scenarios.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCompareItem = () => {
    if (compareList.length >= 3) return;
    const nextIdx = compareList.length + 1;
    setCompareList([
      ...compareList,
      {
        id: `sc_${nextIdx}`,
        name: `Option ${String.fromCharCode(64 + nextIdx)}: New Alternative`,
        type: 'one_time_purchase',
        amount: '1000',
        timing_months: 0,
      },
    ]);
  };

  const handleRemoveCompareItem = (index: number) => {
    if (compareList.length <= 1) return;
    setCompareList(compareList.filter((_, i) => i !== index));
  };

  const handleUpdateCompareItem = (index: number, field: keyof ScenarioCompareItemRequest, value: any) => {
    const updated = [...compareList];
    updated[index] = { ...updated[index], [field]: value };
    setCompareList(updated);
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-gradient-to-br from-purple-500/5 to-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Compass className="w-4 h-4" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">Scenario Lab & Decision Impact Engine</h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Simulate proposed purchases, recurring commitments, or income changes in a sandbox without altering live financial data.
            </p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('single')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'single'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Play className="w-3.5 h-3.5" />
              Single Simulation
            </button>
            <button
              onClick={() => setActiveTab('compare')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'compare'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              Decision Comparator
            </button>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 bg-rose-950/90 border border-rose-700/80 rounded-xl text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* ===================== TAB 1: SINGLE SIMULATION ===================== */}
      {activeTab === 'single' && (
        <div className="space-y-6">
          {/* Scenario Input Configurator */}
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              Configure Proposed Decision
            </h3>

            {/* Type Selector Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
              {SCENARIO_TYPES.map((st) => (
                <button
                  key={st.type}
                  type="button"
                  onClick={() => setSingleRequest({ ...singleRequest, scenario_type: st.type })}
                  className={`p-3.5 rounded-xl border text-left transition flex flex-col justify-between ${
                    singleRequest.scenario_type === st.type
                      ? 'bg-purple-950/50 border-purple-500 shadow-md ring-1 ring-purple-500/50'
                      : 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-white">{st.label}</span>
                    {st.icon}
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{st.desc}</p>
                </button>
              ))}
            </div>

            {/* Inputs Form */}
            <form onSubmit={handleRunSingleSimulation} className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Decision / Item Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MacBook Pro, Car Loan, Gym"
                  value={singleRequest.name}
                  onChange={(e) => setSingleRequest({ ...singleRequest, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  {singleRequest.scenario_type === 'income_change'
                    ? 'Income Adjustment Amount (₹)'
                    : 'Amount (₹)'}
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  required
                  placeholder="e.g. 60000"
                  value={singleRequest.amount}
                  onChange={(e) => setSingleRequest({ ...singleRequest, amount: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Timing Offset (Months from now)
                </label>
                <select
                  value={singleRequest.timing_months || 0}
                  onChange={(e) => setSingleRequest({ ...singleRequest, timing_months: parseInt(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-purple-500"
                >
                  <option value={0}>Immediate (This Month)</option>
                  <option value={1}>In 1 Month</option>
                  <option value={2}>In 2 Months</option>
                  <option value={3}>In 3 Months</option>
                  <option value={6}>In 6 Months</option>
                  <option value={12}>In 1 Year</option>
                </select>
              </div>

              <div className="sm:col-span-3 flex justify-end gap-2 pt-2">
                {simulationResult && (
                  <button
                    type="button"
                    onClick={() => setSimulationResult(null)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Discard Result
                  </button>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-purple-600 text-white font-semibold hover:bg-purple-500 transition shadow-sm disabled:opacity-50"
                >
                  <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  Simulate Decision Impact
                </button>
              </div>
            </form>
          </div>

          {/* Simulation Output Dashboard */}
          {simulationResult && (
            <div className="space-y-6">
              {/* Verdict Banner */}
              <div
                className={`border rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  VERDICT_CONFIG[simulationResult.affordability_verdict]?.badgeClass || 'bg-slate-900 border-slate-800'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="p-2 rounded-xl bg-slate-900/60 border border-slate-700 flex-shrink-0">
                    {VERDICT_CONFIG[simulationResult.affordability_verdict]?.icon || <Compass className="w-5 h-5 text-purple-400" />}
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                        Simulation Verdict:
                      </span>
                      <span className="text-sm font-bold text-white">
                        {VERDICT_CONFIG[simulationResult.affordability_verdict]?.label || simulationResult.affordability_verdict}
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 mt-1 leading-relaxed max-w-2xl">
                      "{simulationResult.recommendation}"
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[10px] uppercase font-semibold text-slate-400 block">Scenario Cost</span>
                  <span className="text-xl font-bold text-white font-mono block">
                    {formatINR(simulationResult.amount, { minimumFractionDigits: 2 })}
                  </span>
                  {simulationResult.timing_months > 0 && (
                    <span className="text-[10px] text-cyan-300">Delayed by {simulationResult.timing_months}mo</span>
                  )}
                </div>
              </div>

              {/* Before vs After vs Delta Comparison Matrix */}
              <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
                <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Scale className="w-4 h-4 text-cyan-400" />
                  Financial State Transition: Current Plan vs Simulated Outcome
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-2.5 font-medium">Financial Metric</th>
                        <th className="pb-2.5 font-medium">Current Baseline</th>
                        <th className="pb-2.5 font-medium">Simulated Outcome</th>
                        <th className="pb-2.5 font-medium">Net Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {/* Available Savings */}
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-slate-300">Available Liquid Savings</td>
                        <td className="py-2.5 text-slate-300">
                          {formatINR(simulationResult.before_state.current_savings, { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 font-bold text-white">
                          {formatINR(simulationResult.after_state.current_savings, { minimumFractionDigits: 2 })}
                        </td>
                        <td
                          className={`py-2.5 font-bold ${
                            parseFloat(simulationResult.delta.savings_delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(simulationResult.delta.savings_delta) >= 0 ? '+' : ''}
                          {formatINR(simulationResult.delta.savings_delta, { minimumFractionDigits: 2 })}
                        </td>
                      </tr>

                      {/* Monthly Cash Flow */}
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-slate-300">Monthly Disposable Cash Flow</td>
                        <td className="py-2.5 text-slate-300">
                          {formatINR(simulationResult.before_state.monthly_disposable_income, { minimumFractionDigits: 2 })}/mo
                        </td>
                        <td className="py-2.5 font-bold text-white">
                          {formatINR(simulationResult.after_state.monthly_disposable_income, { minimumFractionDigits: 2 })}/mo
                        </td>
                        <td
                          className={`py-2.5 font-bold ${
                            parseFloat(simulationResult.delta.monthly_disposable_income_delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(simulationResult.delta.monthly_disposable_income_delta) >= 0 ? '+' : ''}
                          {formatINR(simulationResult.delta.monthly_disposable_income_delta, { minimumFractionDigits: 2 })}
                        </td>
                      </tr>

                      {/* Savings Rate */}
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-slate-300">Savings Rate %</td>
                        <td className="py-2.5 text-slate-300">{simulationResult.before_state.savings_rate}%</td>
                        <td className="py-2.5 font-bold text-white">{simulationResult.after_state.savings_rate}%</td>
                        <td
                          className={`py-2.5 font-bold ${
                            parseFloat(simulationResult.delta.savings_rate_delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(simulationResult.delta.savings_rate_delta) >= 0 ? '+' : ''}
                          {simulationResult.delta.savings_rate_delta}%
                        </td>
                      </tr>

                      {/* Emergency Runway */}
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-slate-300">Emergency Fund Runway</td>
                        <td className="py-2.5 text-slate-300">{simulationResult.before_state.emergency_fund_months} months</td>
                        <td className="py-2.5 font-bold text-white">{simulationResult.after_state.emergency_fund_months} months</td>
                        <td
                          className={`py-2.5 font-bold ${
                            parseFloat(simulationResult.delta.emergency_fund_months_delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(simulationResult.delta.emergency_fund_months_delta) >= 0 ? '+' : ''}
                          {simulationResult.delta.emergency_fund_months_delta} mo
                        </td>
                      </tr>

                      {/* Daily Safe-to-Spend */}
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-slate-300">Daily Safe-to-Spend Allowance</td>
                        <td className="py-2.5 text-slate-300">{formatINR(simulationResult.before_state.daily_safe_to_spend, { minimumFractionDigits: 2 })}/day</td>
                        <td className="py-2.5 font-bold text-white">{formatINR(simulationResult.after_state.daily_safe_to_spend, { minimumFractionDigits: 2 })}/day</td>
                        <td
                          className={`py-2.5 font-bold ${
                            parseFloat(simulationResult.delta.daily_safe_to_spend_delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(simulationResult.delta.daily_safe_to_spend_delta) >= 0 ? '+' : ''}
                          {formatINR(simulationResult.delta.daily_safe_to_spend_delta, { minimumFractionDigits: 2 })}
                        </td>
                      </tr>

                      {/* Financial Health Score */}
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-slate-300">Financial Health Score</td>
                        <td className="py-2.5 text-slate-300">
                          {simulationResult.before_state.financial_health_score}/100 ({simulationResult.before_state.financial_health_grade})
                        </td>
                        <td className="py-2.5 font-bold text-white">
                          {simulationResult.after_state.financial_health_score}/100 ({simulationResult.after_state.financial_health_grade})
                        </td>
                        <td
                          className={`py-2.5 font-bold ${
                            parseFloat(simulationResult.delta.financial_health_score_delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(simulationResult.delta.financial_health_score_delta) >= 0 ? '+' : ''}
                          {simulationResult.delta.financial_health_score_delta} pts
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Goal Impacts Grid */}
              {simulationResult.goal_impacts.length > 0 && (
                <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
                  <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    <Target className="w-4 h-4 text-cyan-400" />
                    Impact on Active Goals & Timelines
                  </h4>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {simulationResult.goal_impacts.map((gi) => (
                      <div
                        key={gi.goal_id}
                        className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 text-xs flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white">{gi.goal_name}</span>
                            {gi.timeline_delay_months && gi.timeline_delay_months > 0 ? (
                              <span className="text-[10px] font-semibold text-rose-400 bg-rose-950 px-2 py-0.5 rounded border border-rose-800">
                                +{gi.timeline_delay_months}mo delay
                              </span>
                            ) : (
                              <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                                On track
                              </span>
                            )}
                          </div>

                          <div className="mt-2 space-y-1 text-slate-400 text-[11px]">
                            <div className="flex justify-between">
                              <span>Monthly Allocation:</span>
                              <span className="font-mono text-slate-200">
                                {formatINR(gi.previous_monthly_contribution)} → {formatINR(gi.new_monthly_contribution)}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span>Estimated Timeline:</span>
                              <span className="font-mono text-slate-200">
                                {gi.previous_months_to_complete}mo → {gi.new_months_to_complete}mo
                              </span>
                            </div>
                          </div>
                        </div>

                        <p className="mt-2.5 pt-2 border-t border-slate-800 text-[10px] text-slate-400 italic">
                          {gi.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Decision Intelligence & Options Section */}
              {simulationResult.decision_result && (
                <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-purple-950/40 border border-purple-500/30 rounded-2xl p-6 shadow-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      AI Decision Intelligence & Strategic Options
                    </h4>
                    <span className="text-[10px] uppercase font-semibold px-2.5 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-700/80">
                      Confidence: {simulationResult.decision_result.confidence.toUpperCase()}
                    </span>
                  </div>

                  {/* Decision Options Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                    {simulationResult.decision_result.options.map((opt, oIdx) => (
                      <div
                        key={oIdx}
                        className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-purple-500/40 transition-colors"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs font-bold text-cyan-300">{opt.title}</span>
                            <span className="text-[10px] text-slate-500 font-mono">Opt {oIdx + 1}</span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">{opt.description}</p>
                        </div>
                        <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-purple-300 font-medium">
                          ⚡ {opt.impact}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Assumptions */}
                  {simulationResult.decision_result.scenario?.assumptions?.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block mb-1.5">
                        Simulation Assumptions
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] text-slate-400">
                        {simulationResult.decision_result.scenario.assumptions.map((assump, aIdx) => (
                          <div key={aIdx} className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
                            • {assump}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tradeoffs & Warnings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {simulationResult.tradeoffs.length > 0 && (
                  <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-5 shadow-lg">
                    <h5 className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" /> Key Tradeoffs & Consequences
                    </h5>
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      {simulationResult.tradeoffs.map((t, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-cyan-400 mt-0.5">•</span>
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {simulationResult.warnings.length > 0 && (
                  <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-5 shadow-lg">
                    <h5 className="text-xs font-bold text-amber-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" /> Financial Alerts & Vulnerabilities
                    </h5>
                    <ul className="space-y-1.5 text-xs text-amber-200">
                      {simulationResult.warnings.map((w, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-amber-400 mt-0.5">⚠️</span>
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================== TAB 2: MULTI-SCENARIO COMPARISON ===================== */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          {/* Scenarios Builder */}
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Scale className="w-4 h-4 text-purple-400" />
                  Define Up to 3 Comparative Alternatives
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Compare trade-offs between pricing models, timing strategies, or purchase tiers.
                </p>
              </div>

              {compareList.length < 3 && (
                <button
                  type="button"
                  onClick={handleAddCompareItem}
                  className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Scenario
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {compareList.map((sc, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3 text-xs flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-300">
                        Alternative {String.fromCharCode(65 + idx)}
                      </span>
                      {compareList.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveCompareItem(idx)}
                          className="text-slate-500 hover:text-rose-400"
                          title="Remove Scenario"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Scenario Title</label>
                      <input
                        type="text"
                        value={sc.name}
                        onChange={(e) => handleUpdateCompareItem(idx, 'name', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Type</label>
                      <select
                        value={sc.type}
                        onChange={(e) => handleUpdateCompareItem(idx, 'type', e.target.value as ScenarioType)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white"
                      >
                        <option value="one_time_purchase">One-Time Purchase</option>
                        <option value="new_recurring_expense">New Recurring Expense</option>
                        <option value="income_change">Income Change</option>
                        <option value="unexpected_expense">Unexpected Expense</option>
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] text-slate-400 mb-1">Amount (₹)</label>
                        <input
                          type="number"
                          step="1"
                          min="0"
                          value={sc.amount}
                          onChange={(e) => handleUpdateCompareItem(idx, 'amount', e.target.value)}
                          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white"
                        />
                      </div>

                      <div>
                        <label className="block text-[11px] text-slate-400 mb-1">Timing (Mo)</label>
                        <select
                          value={sc.timing_months || 0}
                          onChange={(e) => handleUpdateCompareItem(idx, 'timing_months', parseInt(e.target.value) || 0)}
                          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white"
                        >
                          <option value={0}>Now (0m)</option>
                          <option value={1}>1 Month</option>
                          <option value={2}>2 Months</option>
                          <option value={3}>3 Months</option>
                          <option value={6}>6 Months</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={handleRunComparison}
                disabled={loading}
                className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-purple-600 text-white font-semibold hover:bg-purple-500 transition shadow-sm disabled:opacity-50 text-xs"
              >
                <Scale className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                Run Side-by-Side Comparison
              </button>
            </div>
          </div>

          {/* Comparison Matrix Table */}
          {compareResult && (
            <div className="space-y-6">
              <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
                <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Scale className="w-4 h-4 text-purple-400" />
                  Scenario Comparison Matrix
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {compareResult.tradeoff_summary.map((t) => (
                    <div
                      key={t.scenario_id}
                      className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-bold text-white text-xs">{t.scenario_name}</span>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                              VERDICT_CONFIG[t.verdict]?.badgeClass || 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {VERDICT_CONFIG[t.verdict]?.label || t.verdict}
                          </span>
                        </div>

                        <div className="mt-3 space-y-1.5 text-xs font-mono pt-2 border-t border-slate-800/80">
                          <div className="flex justify-between">
                            <span className="text-slate-400 font-sans">Ending Savings:</span>
                            <span className="text-white">{formatINR(t.ending_savings, { minimumFractionDigits: 2 })}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400 font-sans">Monthly Cash Flow:</span>
                            <span className="text-white">{formatINR(t.monthly_cash_flow, { minimumFractionDigits: 2 })}/mo</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400 font-sans">Emergency Runway:</span>
                            <span className="text-cyan-300">{t.emergency_runway_months} months</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400 font-sans">Health Score:</span>
                            <span className="text-purple-300">{t.health_score}/100 ({t.health_score_change} pts)</span>
                          </div>
                        </div>

                        <div className="mt-3 pt-2 border-t border-slate-800/80">
                          <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">
                            Key Consequences
                          </span>
                          <ul className="text-[11px] text-slate-300 space-y-1">
                            {t.key_tradeoffs.map((item, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-purple-400 mt-0.5">•</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <p className="mt-4 pt-2 border-t border-slate-800 text-[10px] text-slate-400 italic">
                        "{t.recommendation}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScenarioLabView;
