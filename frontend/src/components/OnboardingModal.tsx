import React, { useState } from 'react';
import { Sparkles, Loader2, ArrowRight, IndianRupee, Users, AlertCircle, X } from 'lucide-react';
import { saveFinancialProfile } from '../services/api';
import type { FinancialProfileFormData, RiskPreference } from '../types';

interface OnboardingModalProps {
  onComplete: () => void;
  onClose?: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ onComplete, onClose }) => {
  const [formData, setFormData] = useState<FinancialProfileFormData>({
    monthly_income: '',
    current_savings: '',
    monthly_debt_payment: '0',
    essential_expenses: '',
    dependents: 0,
    emergency_savings: '0',
    risk_preference: 'moderate',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await saveFinancialProfile(formData);
      onComplete();
    } catch (err: any) {
      setError(err.message || 'Failed to save financial profile.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-xl w-full p-8 shadow-2xl relative overflow-hidden">
        {/* Glow */}
        <div className="absolute w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none -top-20 -right-20" />

        {/* Close 'X' Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-6 right-6 z-20 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        <div className="relative z-10">
          <div className="flex items-center gap-2.5 mb-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Quick Setup • 1 Minute
            </span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-2">Welcome to FinPilot AI</h2>
          <p className="text-xs text-slate-400 mb-6">
            Configure your initial financial baseline so our agents can accurately plan your cash-flow and calculate your safe-to-spend buffer.
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Monthly Net Income (₹)
                </label>
                <div className="relative">
                  <IndianRupee className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="number"
                    step="1"
                    min="0"
                    required
                    placeholder="e.g. 75000"
                    value={formData.monthly_income}
                    onChange={(e) => setFormData({ ...formData, monthly_income: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Current Liquid Savings (₹)
                </label>
                <div className="relative">
                  <IndianRupee className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="number"
                    step="1"
                    min="0"
                    required
                    placeholder="e.g. 150000"
                    value={formData.current_savings}
                    onChange={(e) => setFormData({ ...formData, current_savings: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Essential Living Expenses (₹)
                </label>
                <div className="relative">
                  <IndianRupee className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="number"
                    step="1"
                    min="0"
                    required
                    placeholder="e.g. 35000 (Rent, groceries, utilities)"
                    value={formData.essential_expenses}
                    onChange={(e) => setFormData({ ...formData, essential_expenses: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Monthly Debt Payments / EMIs (₹)
                </label>
                <div className="relative">
                  <IndianRupee className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="0"
                    value={formData.monthly_debt_payment}
                    onChange={(e) => setFormData({ ...formData, monthly_debt_payment: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Emergency Fund Savings (₹)
                </label>
                <div className="relative">
                  <IndianRupee className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="0"
                    value={formData.emergency_savings}
                    onChange={(e) => setFormData({ ...formData, emergency_savings: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Number of Dependents
                </label>
                <div className="relative">
                  <Users className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="number"
                    min="0"
                    max="20"
                    required
                    placeholder="0"
                    value={formData.dependents}
                    onChange={(e) => setFormData({ ...formData, dependents: parseInt(e.target.value) || 0 })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Risk Preference
              </label>
              <select
                value={formData.risk_preference}
                onChange={(e) => setFormData({ ...formData, risk_preference: e.target.value as RiskPreference })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="conservative">Conservative (Safety-first, high liquid buffer)</option>
                <option value="moderate">Moderate (Balanced savings & growth)</option>
                <option value="aggressive">Aggressive (Accelerated goal funding & investments)</option>
              </select>
            </div>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-end gap-3">
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full sm:w-auto px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
                >
                  Skip for now
                </button>
              )}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full sm:flex-1 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md shadow-indigo-600/20 transition flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving Baseline Profile...
                  </>
                ) : (
                  <>
                    Complete Onboarding & Open Dashboard
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
