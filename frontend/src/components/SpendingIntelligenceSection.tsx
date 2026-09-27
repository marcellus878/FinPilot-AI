import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Compass,
  EyeOff,
  Flame,
  PieChart as PieIcon,
  RefreshCw,
  Repeat,
  Sparkles,
} from 'lucide-react';
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

import { fetchSpendingIntelligence } from '../services/api';
import type { SpendingIntelligenceResult } from '../types';
import { formatINR } from '../utils/formatters';

interface SpendingIntelligenceSectionProps {
  onRefreshTrigger?: number;
}

const ESSENTIALITY_COLORS = {
  Essential: '#10b981',      // emerald
  'Semi-Essential': '#3b82f6', // blue
  Discretionary: '#f43f5e',   // rose
};

export const SpendingIntelligenceSection: React.FC<SpendingIntelligenceSectionProps> = ({
  onRefreshTrigger,
}) => {
  const [intel, setIntel] = useState<SpendingIntelligenceResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [confirmedRecurring, setConfirmedRecurring] = useState<Set<string>>(new Set());

  const loadIntelligence = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchSpendingIntelligence();
      setIntel(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load spending intelligence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntelligence();
  }, [onRefreshTrigger]);

  const toggleConfirmRecurring = (merchant: string) => {
    const next = new Set(confirmedRecurring);
    if (next.has(merchant)) next.delete(merchant);
    else next.add(merchant);
    setConfirmedRecurring(next);
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-3 bg-slate-900/50 border border-slate-800 rounded-xl">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-400" />
        <p className="text-xs">Computing deterministic spending intelligence, habits, and recurring commitments...</p>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center justify-between">
        <span>{errorMessage}</span>
        <button onClick={loadIntelligence} className="underline text-xs hover:text-white">
          Retry
        </button>
      </div>
    );
  }

  if (!intel) return null;

  const essentialPieData = [
    { name: 'Essential', value: Number(intel.essential_amount), percentage: intel.essential_percentage },
    { name: 'Semi-Essential', value: Number(intel.semi_essential_amount), percentage: intel.semi_essential_percentage },
    { name: 'Discretionary', value: Number(intel.discretionary_amount), percentage: intel.discretionary_percentage },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            Spending Intelligence & Behavioral Analytics
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic spending patterns, subscription detectors, hidden leaks, and essentiality ratios.
          </p>
        </div>
      </div>

      {/* 1. Essential vs Discretionary Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm">
        <div className="lg:col-span-4 flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-1.5">
              <PieIcon className="w-4 h-4 text-emerald-400" />
              Essential vs. Discretionary Breakdown
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Classified by strict non-negotiable living requirements vs lifestyle choices.
            </p>
          </div>

          <div className="h-44 w-full">
            {essentialPieData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                No expense data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={essentialPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={65}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {essentialPieData.map((entry, idx) => (
                      <Cell
                        key={`cell-${idx}`}
                        fill={ESSENTIALITY_COLORS[entry.name as keyof typeof ESSENTIALITY_COLORS] || '#64748b'}
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
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="lg:col-span-8 flex flex-col justify-center space-y-3.5">
          {/* Essential Progress */}
          <div className="p-3 bg-slate-950/70 border border-slate-800/70 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                Essential Spending ({intel.essential_percentage}%)
              </span>
              <span className="font-mono font-bold text-white">{formatINR(intel.essential_amount)}</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Rent, housing commitments, utilities, debt/EMI, healthcare, basic groceries, and essential commute.
            </p>
          </div>

          {/* Semi-Essential Progress */}
          <div className="p-3 bg-slate-950/70 border border-slate-800/70 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-blue-400 flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
                Semi-Essential Spending ({intel.semi_essential_percentage}%)
              </span>
              <span className="font-mono font-bold text-white">{formatINR(intel.semi_essential_amount)}</span>
            </div>
            <p className="text-[11px] text-slate-400">
              General retail shopping, standard dining, and ride-hailing services.
            </p>
          </div>

          {/* Discretionary Progress */}
          <div className="p-3 bg-slate-950/70 border border-slate-800/70 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-rose-400 flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                Discretionary Spending ({intel.discretionary_percentage}%)
              </span>
              <span className="font-mono font-bold text-white">{formatINR(intel.discretionary_amount)}</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Food delivery apps (Swiggy/Zomato), entertainment streaming, bars, luxury retail, and miscellaneous leaks.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Miscellaneous Expense Leak Warning */}
      {Number(intel.miscellaneous_analysis.total_miscellaneous_amount) > 0 && (
        <div
          className={`p-4 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
            intel.miscellaneous_analysis.leak_severity === 'high'
              ? 'bg-rose-950/30 border-rose-800/60 text-rose-200'
              : 'bg-slate-900 border-slate-800 text-slate-300'
          }`}
        >
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-amber-400 shrink-0 mt-0.5">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider opacity-80 block">
                Miscellaneous Expense Leak Watch
              </span>
              <p className="text-xs font-semibold text-white mt-0.5">{intel.miscellaneous_analysis.description}</p>
              {intel.miscellaneous_analysis.recurring_miscellaneous_merchants.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {intel.miscellaneous_analysis.recurring_miscellaneous_merchants.map((m, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-slate-950 text-[10px] text-slate-300 border border-slate-800">
                      {m.merchant} ({m.count} txs)
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 3. Recurring Expenses & Hidden Subscriptions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recurring Expense Detector */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Repeat className="w-4 h-4 text-emerald-400" />
              Detected Recurring Expenses & Subscriptions
            </h3>
            <span className="text-[11px] text-slate-400">{intel.recurring_expenses.length} detected</span>
          </div>

          {intel.recurring_expenses.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No repeating cadences detected yet. Import multiple months of transactions to find recurring bills.
            </div>
          ) : (
            <div className="space-y-2.5">
              {intel.recurring_expenses.map((rec, idx) => {
                const isConfirmed = confirmedRecurring.has(rec.merchant);
                return (
                  <div
                    key={idx}
                    className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between text-xs hover:border-slate-700 transition"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">{rec.merchant}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-slate-900 text-emerald-400 border border-emerald-800/40">
                          {rec.frequency}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {rec.category} • {rec.occurrence_count} times • {(rec.confidence * 100).toFixed(0)}% confidence
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-white text-sm">
                        ~{formatINR(rec.approximate_amount, { minimumFractionDigits: 2 })}
                      </span>
                      <button
                        type="button"
                        onClick={() => toggleConfirmRecurring(rec.merchant)}
                        className={`p-1.5 rounded-lg border transition ${
                          isConfirmed
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                            : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
                        }`}
                        title={isConfirmed ? 'Confirmed recurring commitment' : 'Click to confirm recurring bill'}
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Hidden Expense Detector */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <EyeOff className="w-4 h-4 text-rose-400" />
              Hidden Expense Detector
            </h3>
            <span className="text-[11px] text-slate-400">Micro-leak aggregation</span>
          </div>

          {intel.hidden_expenses.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No low-ticket compounding leaks detected.
            </div>
          ) : (
            <div className="space-y-2.5">
              {intel.hidden_expenses.map((hid, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between text-xs space-x-3"
                >
                  <div className="space-y-0.5">
                    <span className="font-semibold text-slate-200">{hid.merchant}</span>
                    <p className="text-[11px] text-slate-400">{hid.description}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs font-bold text-rose-400 font-mono block">
                      {formatINR(hid.annualized_cost, { minimumFractionDigits: 2 })}/yr
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      ({formatINR(hid.total_monthly_cost, { minimumFractionDigits: 2 })}/mo)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 4. Spending Patterns & Behavioral Habits */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Spending Patterns */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Compass className="w-4 h-4 text-emerald-400" />
            Detected Spending Patterns
          </h3>

          {intel.patterns.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No notable spending concentration or anomaly patterns detected.
            </div>
          ) : (
            <div className="space-y-3">
              {intel.patterns.map((pat, idx) => (
                <div key={idx} className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{pat.title}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        pat.impact_level === 'high'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800/60'
                          : 'bg-slate-900 text-slate-300 border border-slate-800'
                      }`}
                    >
                      {pat.impact_level} impact
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{pat.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Behavioral Habits */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400" />
            Behavioral Spending Habits
          </h3>

          {intel.habits.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No high-frequency habit loops detected.
            </div>
          ) : (
            <div className="space-y-3">
              {intel.habits.map((hab, idx) => (
                <div key={idx} className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{hab.habit_name}</span>
                    <span className="font-mono font-bold text-amber-400">
                      {formatINR(hab.monthly_cost, { minimumFractionDigits: 2 })}/mo
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{hab.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
