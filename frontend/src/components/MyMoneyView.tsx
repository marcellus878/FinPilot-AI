import React, { useState } from 'react';
import { CreditCard, DollarSign, ArrowDownUp } from 'lucide-react';
import { ExpenseBudgetView } from './ExpenseBudgetView';
import { SmartSalaryView } from './SmartSalaryView';

export const MyMoneyView: React.FC = () => {
  const [subTab, setSubTab] = useState<'expenses' | 'salary'>('expenses');

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Section Header & Sub Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <CreditCard className="w-6 h-6 text-indigo-400" />
            My Money
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Manage transactions, budgets, recurring commitments, salary allocations, and bank imports.
          </p>
        </div>

        {/* Sub Navigation */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl">
          <button
            onClick={() => setSubTab('expenses')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'expenses'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ArrowDownUp className="w-3.5 h-3.5" />
            Expenses & Budgets
          </button>
          <button
            onClick={() => setSubTab('salary')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              subTab === 'salary'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <DollarSign className="w-3.5 h-3.5" />
            Smart Salary & Recurring
          </button>
        </div>
      </div>

      {/* Render Sub View */}
      {subTab === 'expenses' && <ExpenseBudgetView />}
      {subTab === 'salary' && <SmartSalaryView />}
    </div>
  );
};
