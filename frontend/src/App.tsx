import React, { useEffect, useState } from 'react';
import {
  Bot,
  Compass,
  CreditCard,
  FileSpreadsheet,
  Home,
  LogOut,
  PlusCircle,
  Settings,
  Sparkles,
  Target,
  User as UserIcon,
} from 'lucide-react';

import { AuthProvider, useAuth } from './context/AuthContext';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { SignupPage } from './components/SignupPage';
import { OnboardingModal } from './components/OnboardingModal';
import { HomeDashboardView } from './components/HomeDashboardView';
import { MyMoneyView } from './components/MyMoneyView';
import { MyPlanView } from './components/MyPlanView';
import { AdvisorView } from './components/AdvisorView';
import { ScenarioLabView } from './components/ScenarioLabView';
import { InsightsView } from './components/InsightsView';
import { SettingsView } from './components/SettingsView';
import { AgentLabView } from './components/AgentLabView';
import { TransactionEntryModal } from './components/TransactionEntryModal';
import { StatementImportModal } from './components/StatementImportModal';

type AppRoute =
  | '/'
  | '/login'
  | '/signup'
  | '/home'
  | '/money'
  | '/plan'
  | '/advisor'
  | '/agent-lab'
  | '/scenario-lab'
  | '/insights'
  | '/settings';

const AppContent: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout, refreshUser } = useAuth();
  const [currentPath, setCurrentPath] = useState<AppRoute>(() => {
    const p = window.location.pathname as AppRoute;
    const validRoutes: AppRoute[] = [
      '/',
      '/login',
      '/signup',
      '/home',
      '/money',
      '/plan',
      '/advisor',
      '/scenario-lab',
      '/insights',
      '/settings',
    ];
    return validRoutes.includes(p) ? p : '/';
  });

  const [advisorPrefilledPrompt, setAdvisorPrefilledPrompt] = useState<string | null>(null);
  const [isTxModalOpen, setIsTxModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Sync route on popstate
  useEffect(() => {
    const handlePopState = () => {
      const p = window.location.pathname as AppRoute;
      setCurrentPath(p);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (to: string, extraPrompt?: string) => {
    let normalized = to.startsWith('/') ? to : `/${to}`;
    if (normalized === '/dashboard') normalized = '/home';
    const targetRoute = normalized as AppRoute;

    if (extraPrompt) {
      setAdvisorPrefilledPrompt(extraPrompt);
    }

    if (window.location.pathname !== targetRoute) {
      window.history.pushState({}, '', targetRoute);
    }
    setCurrentPath(targetRoute);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Check onboarding requirement on user change
  useEffect(() => {
    if (isAuthenticated && user && user.has_profile === false) {
      setShowOnboarding(true);
    }
  }, [isAuthenticated, user]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-200">
        <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center animate-pulse mb-4">
          <Sparkles className="w-6 h-6 text-indigo-400" />
        </div>
        <p className="text-sm font-medium text-slate-400">Loading FinPilot AI...</p>
      </div>
    );
  }

  // Unauthenticated routes
  if (!isAuthenticated) {
    if (currentPath === '/login') {
      return <LoginPage onNavigate={navigate} />;
    }
    if (currentPath === '/signup') {
      return <SignupPage onNavigate={navigate} />;
    }
    return <LandingPage onNavigate={navigate} />;
  }

  // If authenticated but visiting public landing/login/signup, show home
  const activeSection: AppRoute =
    currentPath === '/' || currentPath === '/login' || currentPath === '/signup'
      ? '/home'
      : currentPath;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-start">
      {/* Top Application Header */}
      <header className="sticky top-0 z-40 w-full bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Logo & Brand */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/home')}
              className="flex items-center gap-2.5 text-left focus:outline-none group"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition">
                <Sparkles className="w-4.5 h-4.5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-bold tracking-tight text-white">FinPilot AI</span>
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800/60 uppercase">
                    Pro
                  </span>
                </div>
              </div>
            </button>

            {/* Mobile quick actions */}
            <div className="flex items-center gap-1.5 md:hidden">
              <button
                onClick={() => setIsTxModalOpen(true)}
                className="p-2 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600 hover:text-white transition text-xs font-semibold"
                title="Add Transaction"
              >
                <PlusCircle className="w-4 h-4" />
              </button>
              <button
                onClick={() => navigate('/settings')}
                className="p-2 rounded-lg bg-slate-900 text-slate-300 border border-slate-800 hover:text-white transition"
              >
                <UserIcon className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 7-Section Main Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800/80 overflow-x-auto scrollbar-none">
            <button
              onClick={() => navigate('/home')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/home'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Home className="w-3.5 h-3.5" />
              Home
            </button>
            <button
              onClick={() => navigate('/money')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/money'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <CreditCard className="w-3.5 h-3.5" />
              My Money
            </button>
            <button
              onClick={() => navigate('/plan')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/plan'
                  ? 'bg-gradient-to-r from-pink-600 to-rose-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Target className="w-3.5 h-3.5" />
              My Plan
            </button>
            <button
              onClick={() => navigate('/advisor')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/advisor'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Bot className="w-3.5 h-3.5" />
              AI Advisor
            </button>
            <button
              onClick={() => navigate('/agent-lab')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/agent-lab'
                  ? 'bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Bot className="w-3.5 h-3.5 text-indigo-400" />
              🤖 Agent Lab
            </button>
            <button
              onClick={() => navigate('/scenario-lab')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/scenario-lab'
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              Scenario Lab
            </button>
            <button
              onClick={() => navigate('/insights')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/insights'
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Insights
            </button>
            <button
              onClick={() => navigate('/settings')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                activeSection === '/settings'
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              Settings
            </button>
          </nav>

          {/* Desktop Right Actions & User Badge */}
          <div className="hidden md:flex items-center gap-2.5">
            <button
              onClick={() => setIsTxModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm shadow-indigo-600/30 transition"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              Add Expense
            </button>
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              Import
            </button>

            <div className="h-4 w-px bg-slate-800 mx-0.5" />

            <button
              onClick={() => navigate('/settings')}
              className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition group text-left"
              title="Account Settings"
            >
              <div className="w-6 h-6 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-xs font-bold">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="text-xs font-medium text-slate-300 max-w-[100px] truncate group-hover:text-white">
                {user?.full_name || user?.email?.split('@')[0]}
              </span>
            </button>

            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 border border-transparent hover:border-rose-900/40 transition"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl w-full p-4 sm:p-8 flex-1">
        {activeSection === '/home' && (
          <HomeDashboardView
            userName={user?.full_name || user?.email?.split('@')[0]}
            onNavigate={navigate}
            onOpenTransactionModal={() => setIsTxModalOpen(true)}
            onOpenImportModal={() => setIsImportModalOpen(true)}
            onOpenOnboarding={() => setShowOnboarding(true)}
          />
        )}
        {activeSection === '/money' && <MyMoneyView />}
        {activeSection === '/plan' && <MyPlanView />}
        {activeSection === '/advisor' && (
          <AdvisorView
            initialPrompt={advisorPrefilledPrompt}
            onClearInitialPrompt={() => setAdvisorPrefilledPrompt(null)}
          />
        )}
        {activeSection === '/agent-lab' && <AgentLabView />}
        {activeSection === '/scenario-lab' && <ScenarioLabView />}
        {activeSection === '/insights' && (
          <InsightsView
            onSelectPrompt={(prompt) => {
              navigate('/advisor', prompt);
            }}
          />
        )}
        {activeSection === '/settings' && <SettingsView onNavigate={navigate} />}
      </main>

      {/* Modals */}
      {showOnboarding && (
        <OnboardingModal
          onClose={() => setShowOnboarding(false)}
          onComplete={async () => {
            setShowOnboarding(false);
            await refreshUser();
          }}
        />
      )}

      <TransactionEntryModal
        isOpen={isTxModalOpen}
        onClose={() => setIsTxModalOpen(false)}
        onSuccess={() => {
          setIsTxModalOpen(false);
        }}
      />

      <StatementImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={() => {
          setIsImportModalOpen(false);
        }}
      />

      {/* Footer */}
      <footer className="w-full max-w-7xl text-center border-t border-slate-900 mt-12 py-6 text-xs text-slate-600">
        FinPilot AI — Autonomous Multi-Agent Financial Copilot with Deterministic Numerical Engine
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
