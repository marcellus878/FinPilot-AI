import React, { useState, useEffect } from 'react';
import type { FinancialProfile, FinancialProfileFormData, RiskPreference } from '../types';
import { fetchFinancialProfile, saveFinancialProfile, ApiError } from '../services/api';
import { formatINR } from '../utils/formatters';

export const FinancialProfileView: React.FC = () => {
  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [formData, setFormData] = useState<FinancialProfileFormData>({
    monthly_income: '',
    current_savings: '',
    monthly_debt_payment: '0',
    essential_expenses: '',
    dependents: 0,
    emergency_savings: '0',
    risk_preference: 'moderate',
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [isFirstTime, setIsFirstTime] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'validation' | 'server' | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    setErrorMessage(null);
    setErrorType(null);
    try {
      const data = await fetchFinancialProfile();
      if (data) {
        setProfile(data);
        setIsFirstTime(parseFloat(data.monthly_income) === 0 && parseFloat(data.current_savings) === 0);
        setFormData({
          monthly_income: data.monthly_income || '0.00',
          current_savings: data.current_savings || '0.00',
          monthly_debt_payment: data.monthly_debt_payment || '0.00',
          essential_expenses: data.essential_expenses || '0.00',
          dependents: data.dependents || 0,
          emergency_savings: data.emergency_savings || '0.00',
          risk_preference: data.risk_preference || 'moderate',
        });
      } else {
        // First-time user without a profile in database
        setIsFirstTime(true);
        setProfile(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 0) {
          setErrorType('network');
          setErrorMessage('Cannot reach backend server. Please make sure the FastAPI server is running on http://127.0.0.1:8000.');
        } else if (err.status >= 500) {
          setErrorType('server');
          setErrorMessage(`Server encountered an error (${err.status}). Please check backend logs.`);
        } else {
          setErrorType('validation');
          setErrorMessage(err.message);
        }
      } else if (err instanceof Error) {
        setErrorType('network');
        setErrorMessage(err.message);
      } else {
        setErrorType('server');
        setErrorMessage('An unexpected error occurred while loading your profile.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'dependents' ? parseInt(value, 10) || 0 : value,
    }));
  };

  const handleRiskChange = (risk: RiskPreference) => {
    setFormData((prev) => ({ ...prev, risk_preference: risk }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage(null);
    setErrorType(null);
    setSuccessMessage(null);
    try {
      const updated = await saveFinancialProfile(formData);
      setProfile(updated);
      setIsFirstTime(false);
      setSuccessMessage('Financial profile saved and metrics recalculated successfully!');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 0) {
          setErrorType('network');
          setErrorMessage('Cannot reach backend server to save profile.');
        } else if (err.status === 422) {
          setErrorType('validation');
          setErrorMessage(`Invalid input: ${err.message}`);
        } else {
          setErrorType('server');
          setErrorMessage(`Save failed (${err.status}): ${err.message}`);
        }
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to save financial profile.');
      }
    } finally {
      setSaving(false);
    }
  };

  const getHealthGradeColor = (grade: string) => {
    switch (grade?.toLowerCase()) {
      case 'excellent':
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-800';
      case 'good':
        return 'text-teal-400 bg-teal-950/40 border-teal-800';
      case 'fair':
        return 'text-amber-400 bg-amber-950/40 border-amber-800';
      case 'needs attention':
        return 'text-orange-400 bg-orange-950/40 border-orange-800';
      case 'critical':
      default:
        return 'text-rose-400 bg-rose-950/40 border-rose-800';
    }
  };

  const getEmergencyLabelBadge = (label: string) => {
    switch (label?.toLowerCase()) {
      case 'optimal':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'adequate':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'insufficient':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'critical':
      default:
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner: First Time Alert */}
      {isFirstTime && (
        <div className="bg-gradient-to-r from-amber-500/20 via-slate-900 to-indigo-500/20 border border-amber-500/40 p-5 rounded-2xl flex items-start gap-3 shadow-lg">
          <div className="p-2 bg-amber-500/20 rounded-xl text-amber-400 shrink-0 mt-0.5">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100">Welcome to FinPilot AI</h3>
            <p className="text-xs text-slate-300 mt-1">
              Please enter your financial baseline below. These deterministic inputs allow our multi-agent planning loop to calculate health ratios, safe-to-spend limits, and emergency reserves.
            </p>
          </div>
        </div>
      )}

      {/* Header with Health Score Card */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Financial Profile & Health Engine</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Deterministic financial health assessment, buffer calculation, and capacity planning.
          </p>
        </div>

        {profile?.indicators && (
          <div className="flex items-center gap-4 bg-slate-950/80 border border-slate-800 p-3.5 rounded-xl">
            <div className="text-right">
              <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Health Grade</div>
              <div className={`text-xs font-semibold px-2 py-0.5 mt-0.5 rounded border inline-block ${getHealthGradeColor(profile.indicators.financial_health_grade)}`}>
                {profile.indicators.financial_health_grade}
              </div>
            </div>
            <div className="h-9 w-px bg-slate-800"></div>
            <div>
              <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Score</div>
              <div className="text-2xl font-black text-emerald-400 font-mono">
                {profile.indicators.financial_health_score}
                <span className="text-xs text-slate-500 font-normal">/100</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Status Notifications */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-200 text-sm flex items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            <div>
              <span className="font-semibold block text-xs uppercase tracking-wider text-rose-300">
                {errorType === 'network' ? 'Connection Error' : errorType === 'validation' ? 'Validation Error' : 'Server Error'}
              </span>
              <span className="text-xs">{errorMessage}</span>
            </div>
          </div>
          <button
            onClick={loadProfile}
            className="px-3 py-1 bg-rose-900/60 hover:bg-rose-800/80 border border-rose-700 text-rose-100 rounded-lg text-xs font-medium transition shrink-0"
          >
            Retry Connection
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-800 text-emerald-200 text-sm flex items-center gap-2 shadow-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Grid: Left = Form, Right = Calculated Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Form (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-7 shadow-xl space-y-6">
          <div className="border-b border-slate-800/80 pb-3 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-100">Financial Inputs</h2>
              <p className="text-xs text-slate-400">Enter your primary income, expenses, debt, and liquid savings baseline.</p>
            </div>
            {profile && (
              <span className="text-[11px] text-slate-500 font-mono">
                Updated: {new Date(profile.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Monthly Income */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Monthly Net Income (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">₹</span>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    name="monthly_income"
                    value={formData.monthly_income}
                    onChange={handleInputChange}
                    required
                    className="w-full pl-7 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="75000"
                  />
                </div>
              </div>

              {/* Essential Monthly Expenses */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Essential Monthly Expenses (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">₹</span>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    name="essential_expenses"
                    value={formData.essential_expenses}
                    onChange={handleInputChange}
                    required
                    className="w-full pl-7 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="35000"
                  />
                </div>
              </div>

              {/* Monthly Debt Payment */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Monthly Debt Payments / EMIs (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">₹</span>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    name="monthly_debt_payment"
                    value={formData.monthly_debt_payment}
                    onChange={handleInputChange}
                    required
                    className="w-full pl-7 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="0"
                  />
                </div>
              </div>

              {/* Dependents */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Dependents (Count)
                </label>
                <input
                  type="number"
                  min="0"
                  name="dependents"
                  value={formData.dependents}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="0"
                />
              </div>

              {/* Current Savings */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Total Liquid Savings (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">₹</span>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    name="current_savings"
                    value={formData.current_savings}
                    onChange={handleInputChange}
                    required
                    className="w-full pl-7 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="150000"
                  />
                </div>
              </div>

              {/* Emergency Savings */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Designated Emergency Savings (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">₹</span>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    name="emergency_savings"
                    value={formData.emergency_savings}
                    onChange={handleInputChange}
                    required
                    className="w-full pl-7 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="100000"
                  />
                </div>
              </div>
            </div>

            {/* Risk Preference */}
            <div className="space-y-2 pt-1">
              <label className="block text-xs font-medium text-slate-300">
                Risk Preference
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['conservative', 'moderate', 'aggressive'] as RiskPreference[]).map((risk) => (
                  <button
                    key={risk}
                    type="button"
                    onClick={() => handleRiskChange(risk)}
                    className={`py-2 px-3 text-xs font-medium capitalize rounded-lg border transition-all ${
                      formData.risk_preference === risk
                        ? 'bg-emerald-600 border-emerald-500 text-white shadow-md'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    {risk}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-3">
              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white text-sm font-semibold tracking-wide transition-colors duration-150 shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2"
              >
                {saving ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                    <span>Saving Profile...</span>
                  </>
                ) : (
                  <span>Save Profile & Calculate Indicators</span>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Calculated Indicators (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div className="border-b border-slate-800/80 pb-3 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-100">Calculated Indicators</h2>
                <p className="text-xs text-slate-400">Deterministic metrics from backend engine</p>
              </div>
              <span className="text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 bg-emerald-950/70 border border-emerald-800 text-emerald-300 rounded">
                Live Engine
              </span>
            </div>

            {loading ? (
              <div className="space-y-3 py-6 animate-pulse">
                <div className="h-16 bg-slate-800/60 rounded-xl"></div>
                <div className="h-16 bg-slate-800/60 rounded-xl"></div>
                <div className="h-16 bg-slate-800/60 rounded-xl"></div>
              </div>
            ) : profile?.indicators ? (
              <div className="space-y-3.5">
                {/* Disposable Income */}
                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400 font-medium">Monthly Disposable Income</div>
                    <div className="text-xs text-slate-500 mt-0.5">Income - Expenses - Debt</div>
                  </div>
                  <div className="text-right">
                    <div className="text-base font-bold text-emerald-400 font-mono">
                      {formatINR(profile.indicators.disposable_income, { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-slate-400">surplus / mo</div>
                  </div>
                </div>

                {/* Savings Rate */}
                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400 font-medium">Savings Rate</div>
                    <div className="text-xs text-slate-500 mt-0.5">Target: ≥ 20.00%</div>
                  </div>
                  <div className="text-right">
                    <div className="text-base font-bold text-slate-100 font-mono">
                      {profile.indicators.savings_rate}%
                    </div>
                    <div className="text-[10px] text-slate-400">of net income</div>
                  </div>
                </div>

                {/* Debt-to-Income (DTI) */}
                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400 font-medium">Debt-to-Income (DTI)</div>
                    <div className="text-xs text-slate-500 mt-0.5">Recommended: ≤ 36.00%</div>
                  </div>
                  <div className="text-right">
                    <div className={`text-base font-bold font-mono ${
                      parseFloat(profile.indicators.debt_to_income_ratio) > 36.0 ? 'text-rose-400' : 'text-slate-100'
                    }`}>
                      {profile.indicators.debt_to_income_ratio}%
                    </div>
                    <div className="text-[10px] text-slate-400">debt burden</div>
                  </div>
                </div>

                {/* Emergency Fund Status */}
                <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">Emergency Fund Runway</span>
                    <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded border ${getEmergencyLabelBadge(profile.indicators.emergency_fund.status_label)}`}>
                      {profile.indicators.emergency_fund.status_label}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div className="text-xl font-bold font-mono text-slate-100">
                      {profile.indicators.emergency_fund.months_covered}{' '}
                      <span className="text-xs font-normal text-slate-400">months</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Target (6mo): {formatINR(profile.indicators.emergency_fund.target_amount)}
                    </div>
                  </div>
                  {parseFloat(profile.indicators.emergency_fund.shortfall) > 0 ? (
                    <div className="text-[11px] text-amber-400">
                      Shortfall: {formatINR(profile.indicators.emergency_fund.shortfall)} to reach 6-month buffer.
                    </div>
                  ) : (
                    <div className="text-[11px] text-emerald-400">
                      Full 6-month emergency reserve maintained!
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-500 py-6 text-center space-y-2">
                <p>No financial metrics recorded yet.</p>
                <p className="text-xs text-slate-600">Save your baseline profile to calculate your live indicators.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
