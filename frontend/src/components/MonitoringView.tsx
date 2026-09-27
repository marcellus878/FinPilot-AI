import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Layers,
  RefreshCw,
  Scale,
  Shield,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';

import {
  fetchMonitoringStatus,
  runMonitoringCycle,
} from '../services/api';
import { formatINR } from '../utils/formatters';
import type {
  MonitoringRunResponse,
  MonitoringStatusResponse,
  PlanComparisonItem,
  ReplanningStrategyOption,
} from '../types';

export const MonitoringView: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [status, setStatus] = useState<MonitoringStatusResponse | null>(null);
  const [runResult, setRunResult] = useState<MonitoringRunResponse | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const statusData = await fetchMonitoringStatus();
      setStatus(statusData);
      
      const runData = await runMonitoringCycle();
      setRunResult(runData);
      if (runData.strategies && runData.strategies.length > 0) {
        setSelectedStrategy(runData.strategies[0].strategy_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const handleRunDiagnostic = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await runMonitoringCycle();
      setRunResult(res);
      const statusData = await fetchMonitoringStatus();
      setStatus(statusData);
      setSuccessMessage('Diagnostic completed! Live metrics updated.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to execute monitoring cycle');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
            <ShieldAlert className="w-3 h-3" /> Critical
          </span>
        );
      case 'high':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-orange-500/20 text-orange-400 border border-orange-500/30">
            <AlertTriangle className="w-3 h-3" /> High
          </span>
        );
      case 'medium':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <AlertCircle className="w-3 h-3" /> Medium
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Activity className="w-3 h-3" /> Nominal
          </span>
        );
    }
  };

  const getPlanStatusDisplay = (planStatus: string) => {
    switch (planStatus) {
      case 'replanning_required':
        return {
          label: 'Replanning Required',
          badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          icon: <ShieldAlert className="w-5 h-5 text-rose-400" />,
          desc: 'Critical deviations detected. An adaptive plan proposal is available below.',
        };
      case 'needs_attention':
        return {
          label: 'Needs Attention',
          badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
          desc: 'Moderate financial drift detected. Review your budget allocations.',
        };
      default:
        return {
          label: 'Plan On Track',
          badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
          desc: 'All key financial parameters remain within healthy tolerances.',
        };
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] space-y-4">
        <RefreshCw className="w-10 h-10 text-cyan-400 animate-spin" />
        <p className="text-slate-400 font-medium text-sm">Evaluating continuous financial monitoring telemetry...</p>
      </div>
    );
  }

  const currentSnapshot = runResult?.current_snapshot;
  const baselineSnapshot = runResult?.baseline_snapshot;
  const statusDisplay = getPlanStatusDisplay(runResult?.plan_status || status?.plan_status || 'on_track');
  const changes = runResult?.changes || [];
  const assessment = runResult?.assessment;
  const comparison = runResult?.plan_comparison;
  const strategies = runResult?.strategies || [];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/60 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-cyan-500/20 border border-cyan-500/30 rounded-xl text-cyan-400">
                <Activity className="w-6 h-6" />
              </div>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                Continuous Monitoring & Plan Adaptation
              </h1>
            </div>
            <p className="text-slate-400 text-sm max-w-2xl">
              FinPilot observes your live cash flows, detects spending and income drift, assesses target milestone impacts,
              and generates non-destructive adaptive plan strategies.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunDiagnostic}
              disabled={running}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-cyan-600/20 transition-all duration-200 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
              {running ? 'Running Diagnostic...' : 'Run Live Diagnostic'}
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMessage && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-sm flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Surveillance Status Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Status Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Plan Health Status</span>
            <div className={`px-2.5 py-1 text-xs font-bold rounded-lg border flex items-center gap-1.5 ${statusDisplay.badgeClass}`}>
              {statusDisplay.icon}
              {statusDisplay.label}
            </div>
          </div>
          <p className="text-xs text-slate-400">{statusDisplay.desc}</p>
        </div>

        {/* Health Score */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Financial Health Score</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{currentSnapshot?.financial_health_score || '0'}</span>
            <span className="text-xs text-cyan-400 font-medium">/ 100 ({currentSnapshot?.financial_health_grade || 'B'})</span>
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1">
            Baseline: {baselineSnapshot?.monthly_income ? formatINR(baselineSnapshot.monthly_income) : '₹0'} income
          </div>
        </div>

        {/* Safe-to-Spend Daily */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Safe Daily Spend</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-emerald-400">
              {formatINR(currentSnapshot?.safe_to_spend_daily || 0, { minimumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-slate-400">/ day</span>
          </div>
          <p className="text-xs text-slate-400">
            Emergency buffer: {currentSnapshot?.emergency_runway_months || '0'} mo runway
          </p>
        </div>

        {/* Active Goals Feasibility */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Goals Feasibility</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{currentSnapshot?.active_goals_count || 0}</span>
            <span className="text-xs text-slate-400">Active Goals</span>
          </div>
          <p className="text-xs flex items-center gap-1">
            {currentSnapshot?.goals_feasible ? (
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Surplus Covers Targets
              </span>
            ) : (
              <span className="text-amber-400 font-medium flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Allocation Deficit
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Detected Changes Section */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-white">Live Parameter Surveillance & Detected Drift</h2>
          </div>
          <span className="text-xs text-slate-400">
            {changes.length} {changes.length === 1 ? 'drift detected' : 'drifts detected'}
          </span>
        </div>

        {changes.length === 0 ? (
          <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-700/40 space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
            <p className="text-sm font-semibold text-slate-200">All Financial Metrics Stable</p>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              No significant deviations detected against your established financial plan baseline.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {changes.map((item, idx) => (
              <div
                key={idx}
                className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-3 hover:border-slate-600/80 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    {item.metric.replace(/_/g, ' ')}
                  </span>
                  {getSeverityBadge(item.severity)}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{item.description}</p>
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-500 block">Baseline</span>
                    <span className="font-semibold text-slate-300">{item.baseline}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Current</span>
                    <span className="font-semibold text-white">{item.current}</span>
                  </div>
                </div>
                <div className="text-xs flex items-center justify-between text-slate-400 pt-1">
                  <span>Delta: {item.absolute_change}</span>
                  <span className="font-semibold text-amber-400">{item.percentage_change}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Replanning Assessment & Triggers */}
      {assessment && (
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-cyan-400" />
              <h2 className="text-lg font-semibold text-white">Replanning Assessment & Impact Analysis</h2>
            </div>
            {getSeverityBadge(assessment.severity)}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Trigger Reasons</h3>
              <ul className="space-y-2">
                {assessment.reasons.map((reason, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recommended Remediation</h3>
              <ul className="space-y-2">
                {assessment.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {runResult?.ai_explanation && (
            <div className="mt-4 p-4 bg-slate-900/80 border border-slate-700/60 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-4 h-4" /> AI Advisory Assessment
              </div>
              <div className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">
                {runResult.ai_explanation}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Before vs. After Plan Comparison Table */}
      {comparison && comparison.items && comparison.items.length > 0 && (
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-white">Before vs. After Plan Comparison</h2>
          </div>
          <p className="text-xs text-slate-400">{comparison.summary}</p>

          <div className="overflow-x-auto rounded-xl border border-slate-700/60">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-700/60">
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Financial Area</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Metric</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Baseline</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Proposed Adaptive</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Delta</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {comparison.items.map((item: PlanComparisonItem, idx: number) => {
                  const isPositive = !item.delta.startsWith('-');
                  return (
                    <tr key={idx} className="hover:bg-slate-700/20 transition-colors">
                      <td className="py-3 px-4 font-semibold text-white uppercase tracking-wider">{item.area}</td>
                      <td className="py-3 px-4 text-slate-300">{item.metric.replace(/_/g, ' ')}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono">{item.baseline_value}</td>
                      <td className="py-3 px-4 font-semibold text-cyan-400 font-mono">{item.proposed_value}</td>
                      <td className="py-3 px-4 font-mono font-medium">
                        <span
                          className={`inline-flex items-center gap-1 ${
                            isPositive ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                          {item.delta}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{item.explanation}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Affected Goals Breakdown */}
          {comparison.affected_goals && comparison.affected_goals.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-700/60 space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Affected Target Goals</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {comparison.affected_goals.map((g, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/50 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-white text-xs block">{g.goal_name}</span>
                      <span className="text-slate-400 text-xs">
                        Contribution: {g.previous_contribution} → <span className="text-cyan-400">{g.proposed_contribution}</span>
                      </span>
                    </div>
                    <div>
                      {g.timeline_delay_months > 0 ? (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          +{g.timeline_delay_months} mo delay
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          On Track
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Adaptive Replanning Strategies */}
      {strategies.length > 0 && (
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-white">Adaptive Strategy Options</h2>
          </div>
          <p className="text-xs text-slate-400">
            Select an adaptive path. FinPilot presents distinct tradeoff profiles so you remain in control of your financial adjustments.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map((strat: ReplanningStrategyOption) => {
              const isSelected = selectedStrategy === strat.strategy_id;
              return (
                <div
                  key={strat.strategy_id}
                  onClick={() => setSelectedStrategy(strat.strategy_id)}
                  className={`cursor-pointer rounded-xl p-5 border transition-all duration-200 space-y-3 ${
                    isSelected
                      ? 'bg-slate-800 border-cyan-500 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/50'
                      : 'bg-slate-900/60 border-slate-700/60 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-white text-sm">{strat.title}</h3>
                    {isSelected && (
                      <span className="px-2 py-0.5 text-xs font-semibold rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                        Selected Option
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{strat.description}</p>

                  <div className="grid grid-cols-3 gap-2 py-2 border-y border-slate-700/50 text-xs font-mono">
                    <div>
                      <span className="text-slate-500 block text-[10px]">Essential</span>
                      <span className="text-slate-200 font-semibold">{strat.adjusted_essential}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Discretionary</span>
                      <span className="text-slate-200 font-semibold">{strat.adjusted_discretionary}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Buffer</span>
                      <span className="text-emerald-400 font-semibold">{strat.resulting_buffer}</span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                      Tradeoffs
                    </span>
                    <ul className="space-y-1">
                      {strat.tradeoffs.map((t, idx) => (
                        <li key={idx} className="text-xs text-slate-400 flex items-start gap-1.5">
                          <span className="text-cyan-400">•</span>
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
