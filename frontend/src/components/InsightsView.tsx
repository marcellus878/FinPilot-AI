import React, { useState } from 'react';
import { Sparkles, Brain, TrendingDown } from 'lucide-react';
import { DecisionHistoryView } from './DecisionHistoryView';
import { SpendingIntelligenceSection } from './SpendingIntelligenceSection';

interface InsightsViewProps {
  onSelectPrompt?: (prompt: string) => void;
}

export const InsightsView: React.FC<InsightsViewProps> = ({ onSelectPrompt }) => {
  const [subTab, setSubTab] = useState<'memory' | 'spending'>('memory');

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            Financial Insights & Decision Memory
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Proactive AI optimization alerts, memory drift tracking, and spending anomaly analytics.
          </p>
        </div>

        {/* Sub Navigation */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl">
          <button
            onClick={() => setSubTab('memory')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'memory'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            Decision Memory & Opportunities
          </button>
          <button
            onClick={() => setSubTab('spending')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'spending'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingDown className="w-3.5 h-3.5" />
            Spending Intelligence & Leaks
          </button>
        </div>
      </div>

      {/* Render Sub View */}
      {subTab === 'memory' && <DecisionHistoryView onSelectPrompt={onSelectPrompt} />}
      {subTab === 'spending' && (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6">
          <SpendingIntelligenceSection />
        </div>
      )}
    </div>
  );
};
