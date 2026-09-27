import React, { useState } from 'react';
import { Target, UserCircle, Activity } from 'lucide-react';
import { GoalsView } from './GoalsView';
import { FinancialProfileView } from './FinancialProfileView';
import { MonitoringView } from './MonitoringView';

export const MyPlanView: React.FC = () => {
  const [subTab, setSubTab] = useState<'goals' | 'profile' | 'adaptive'>('goals');

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Section Header & Sub Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Target className="w-6 h-6 text-pink-400" />
            My Plan
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Manage savings goals, baseline profile metrics, conflict resolution, and adaptive plan tracking.
          </p>
        </div>

        {/* Sub Navigation */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl">
          <button
            onClick={() => setSubTab('goals')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'goals'
                ? 'bg-pink-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            Goals & Timeline
          </button>
          <button
            onClick={() => setSubTab('profile')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'profile'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserCircle className="w-3.5 h-3.5" />
            Financial Profile
          </button>
          <button
            onClick={() => setSubTab('adaptive')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'adaptive'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Plan Health & Adaptations
          </button>
        </div>
      </div>

      {/* Render Sub View */}
      {subTab === 'goals' && <GoalsView />}
      {subTab === 'profile' && <FinancialProfileView />}
      {subTab === 'adaptive' && <MonitoringView />}
    </div>
  );
};
