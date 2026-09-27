import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CreditCard,
  Flame,
  Layers,
  Lightbulb,
  RefreshCw,
  Repeat,
  Search,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';

import {
  fetchDecisionMemories,
  fetchProactiveInsights,
} from '../services/api';
import type {
  DecisionMemoryItem,
  ProactiveInsight,
} from '../types';
import { formatINR } from '../utils/formatters';

interface DecisionHistoryViewProps {
  onSelectPrompt?: (prompt: string) => void;
}

export const DecisionHistoryView: React.FC<DecisionHistoryViewProps> = ({ onSelectPrompt }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [memories, setMemories] = useState<DecisionMemoryItem[]>([]);
  const [insights, setInsights] = useState<ProactiveInsight[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [expandedDecisionId, setExpandedDecisionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [memData, insightsData] = await Promise.all([
        fetchDecisionMemories({
          q: searchQuery || undefined,
          decision_type: selectedType !== 'all' ? selectedType : undefined,
        }),
        fetchProactiveInsights(),
      ]);
      setMemories(memData);
      setInsights(insightsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load decision memory history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedType]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const toggleExpand = (id: string) => {
    setExpandedDecisionId(expandedDecisionId === id ? null : id);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'large_purchase':
        return <CreditCard className="w-4 h-4 text-cyan-400" />;
      case 'new_recurring_expense':
        return <Repeat className="w-4 h-4 text-purple-400" />;
      case 'income_change':
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case 'unexpected_expense':
        return <Flame className="w-4 h-4 text-rose-400" />;
      case 'salary_allocation':
        return <Layers className="w-4 h-4 text-blue-400" />;
      case 'goal_conflict':
        return <Target className="w-4 h-4 text-amber-400" />;
      default:
        return <Brain className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/60 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/20 border border-indigo-500/30 rounded-xl text-indigo-400">
                <Brain className="w-6 h-6" />
              </div>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                Decision Memory & Strategic History
              </h1>
            </div>
            <p className="text-slate-400 text-sm max-w-2xl">
              FinPilot remembers previous financial evaluations, compares live circumstances against past assumptions,
              and identifies when changed financial conditions warrant reconsidering past choices.
            </p>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh Memory
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Proactive Insights Section */}
      {insights.length > 0 && (
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-white">Proactive AI Insights & Re-Evaluation Triggers</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {insights.map((ins) => (
              <div
                key={ins.id}
                className="bg-slate-900/80 border border-slate-700/70 rounded-xl p-4 space-y-3 flex flex-col justify-between hover:border-slate-600 transition"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      {ins.title}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                        ins.severity === 'high'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                          : ins.severity === 'medium'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                      }`}
                    >
                      {ins.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{ins.description}</p>
                </div>

                {ins.action_prompt && (
                  <button
                    onClick={() => onSelectPrompt && onSelectPrompt(ins.action_prompt!)}
                    className="mt-2 text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 text-left"
                  >
                    <span>{ins.action_prompt}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
        <form onSubmit={handleSearch} className="flex items-center gap-2 w-full sm:w-80">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search previous decisions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
          {['all', 'large_purchase', 'new_recurring_expense', 'income_change', 'unexpected_expense'].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                selectedType === t
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800/50'
              }`}
            >
              {t === 'all'
                ? 'All Types'
                : t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>
      </div>

      {/* Decision Memory List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[300px] space-y-3">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
          <p className="text-slate-400 text-xs">Retrieving indexed decision memories...</p>
        </div>
      ) : memories.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
          <Brain className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-bold text-slate-300">No Decision Memories Stored Yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            When you evaluate purchases, EMI loans, or financial goals in the AI Advisor or Scenario Lab,
            structured decision records will automatically appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {memories.map((dec) => {
            const isExpanded = expandedDecisionId === dec.id;
            const drift = dec.drift_assessment;
            const dateStr = new Date(dec.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });

            return (
              <div
                key={dec.id}
                className="bg-slate-800/70 border border-slate-700/60 rounded-xl overflow-hidden shadow-sm hover:border-slate-600 transition"
              >
                {/* Summary Row */}
                <div
                  onClick={() => toggleExpand(dec.id)}
                  className="p-5 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 select-none"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-slate-900 border border-slate-700/80 rounded-lg mt-0.5">
                      {getTypeIcon(dec.decision_type)}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-white text-sm">
                          {dec.item_name || dec.user_action}
                        </span>
                        {dec.amount && (
                          <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            {formatINR(dec.amount)}
                          </span>
                        )}
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
                          {dec.decision_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-1">{dec.decision}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end md:self-auto">
                    {/* Drift Badge */}
                    {drift && drift.has_drifted ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        <AlertTriangle className="w-3 h-3" /> Circumstances Shifted
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-700/50 text-slate-300 border border-slate-600">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Circumstances Stable
                      </span>
                    )}

                    <span className="text-xs text-slate-400 font-mono whitespace-nowrap">{dateStr}</span>

                    <button className="text-slate-400 hover:text-slate-200">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-700/60 bg-slate-900/60 space-y-5">
                    {/* Drift Alert Box */}
                    {drift && drift.has_drifted && (
                      <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-2">
                        <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase tracking-wider">
                          <AlertTriangle className="w-4 h-4" /> Financial Drift Detected
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{drift.explanation}</p>
                      </div>
                    )}

                    {/* Baseline vs Current Metrics Table */}
                    {drift && drift.metrics_comparison && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Baseline vs. Live Metrics
                        </h4>
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                          {Object.entries(drift.metrics_comparison).map(([metric, data]) => (
                            <div key={metric} className="p-3 bg-slate-800/80 rounded-lg border border-slate-700/60 space-y-1">
                              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                                {metric.replace(/_/g, ' ')}
                              </span>
                              <div className="text-xs font-semibold text-white">{data.current}</div>
                              <div className="text-[10px] text-slate-400 flex items-center justify-between">
                                <span>Base: {data.baseline}</span>
                                <span className={data.changed ? 'text-amber-400 font-bold' : 'text-slate-500'}>
                                  {data.delta}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Alternatives Considered */}
                    {dec.alternatives_considered && dec.alternatives_considered.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Evaluated Alternatives
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {dec.alternatives_considered.map((alt, idx) => (
                            <div key={idx} className="p-3 bg-slate-800/70 rounded-lg border border-slate-700/50 space-y-1">
                              <div className="text-xs font-bold text-white">{alt.title}</div>
                              <p className="text-xs text-slate-300">{alt.description}</p>
                              {alt.impact && <p className="text-[11px] text-cyan-400">{alt.impact}</p>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Assumptions & Recommendation */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {dec.assumptions && dec.assumptions.length > 0 && (
                        <div className="space-y-1.5">
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Assumptions</h4>
                          <ul className="space-y-1">
                            {dec.assumptions.map((assump, idx) => (
                              <li key={idx} className="text-xs text-slate-300 flex items-start gap-1.5">
                                <span className="text-cyan-400">•</span>
                                <span>{assump}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {dec.recommendation_summary && (
                        <div className="space-y-1.5">
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                            Recommendation
                          </h4>
                          <p className="text-xs text-slate-300 leading-relaxed">{dec.recommendation_summary}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
