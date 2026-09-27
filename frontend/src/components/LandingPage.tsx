import React from 'react';
import {
  ArrowRight,
  Brain,
  ShieldCheck,
  TrendingUp,
  Activity,
  Compass,
  Cpu,
  Target,
  Sparkles,
  CheckCircle2,
  Lock,
} from 'lucide-react';

interface LandingPageProps {
  onNavigate: (route: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-400 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
              FinPilot <span className="text-indigo-400">AI</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('/login')}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition"
            >
              Sign In
            </button>
            <button
              onClick={() => onNavigate('/signup')}
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm shadow-indigo-500/20 transition flex items-center gap-1.5"
            >
              Get Started
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative px-6 pt-20 pb-24 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous Financial Intelligence & Planning
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
          Your Financial Life, <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
            Planned by AI.
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto mb-10 leading-relaxed">
          FinPilot is your autonomous financial copilot. We combine deterministic financial calculation precision
          with intelligent multi-agent reasoning to continuously plan, evaluate decisions, and adapt as life changes.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => onNavigate('/signup')}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-base shadow-lg shadow-indigo-600/25 transition flex items-center justify-center gap-2"
          >
            Start Free Today
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigate('/login')}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-medium text-base border border-slate-800 transition"
          >
            Sign In to Account
          </button>
        </div>

        {/* Value Props Pills */}
        <div className="mt-14 pt-10 border-t border-slate-900 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <div className="text-indigo-400 font-semibold text-sm mb-1 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" /> 100% Deterministic
            </div>
            <p className="text-xs text-slate-400">Every calculation is mathematically verified before reasoning.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <div className="text-purple-400 font-semibold text-sm mb-1 flex items-center gap-1.5">
              <Target className="w-4 h-4" /> Goal-Aware
            </div>
            <p className="text-xs text-slate-400">Every decision is evaluated against your prioritized savings goals.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <div className="text-emerald-400 font-semibold text-sm mb-1 flex items-center gap-1.5">
              <Activity className="w-4 h-4" /> Continuous Monitoring
            </div>
            <p className="text-xs text-slate-400">Tracks spending drift and income shifts in real time.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <div className="text-pink-400 font-semibold text-sm mb-1 flex items-center gap-1.5">
              <Brain className="w-4 h-4" /> Decision Memory
            </div>
            <p className="text-xs text-slate-400">Remembers past commitments and re-evaluates outcomes proactively.</p>
          </div>
        </div>
      </section>

      {/* How FinPilot Works */}
      <section className="py-20 bg-slate-900/50 border-y border-slate-900 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">How FinPilot Works</h2>
            <p className="text-slate-400 text-sm sm:text-base">
              A closed-loop system designed to make sophisticated financial planning seamless and automatic.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              {
                step: '01',
                title: 'Understand',
                desc: 'Ingest transactions, parse natural voice logs, and structure salary cash-flows.',
              },
              {
                step: '02',
                title: 'Plan',
                desc: 'Allocate salary across essential bills, savings targets, and safe-to-spend funds.',
              },
              {
                step: '03',
                title: 'Evaluate',
                desc: 'Simulate major purchases, EMIs, or income changes before committing money.',
              },
              {
                step: '04',
                title: 'Monitor',
                desc: 'Continuously observe financial health, drift against budgets, and subscription leaks.',
              },
              {
                step: '05',
                title: 'Adapt',
                desc: 'Automatically generate intelligent replanning strategies when financial realities change.',
              },
            ].map((item, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-slate-950 border border-slate-800/80 relative flex flex-col justify-between"
              >
                <div>
                  <div className="text-xs font-mono font-bold text-indigo-400 mb-2">{item.step}</div>
                  <h3 className="text-base font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core Capabilities */}
      <section className="py-20 px-6 max-w-6xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Core Product Capabilities</h2>
          <p className="text-slate-400 text-sm sm:text-base">
            Everything you need for total confidence in your daily, monthly, and long-term financial life.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Spending Intelligence</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Auto-categorization, essentiality tagging, recurring bill detection, hidden fees identification, and leak mitigation.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
              <Brain className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">AI Financial Advisor</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Multi-agent reasoning orchestrated by LangGraph that grounds all advice strictly in verified financial math.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
              <Compass className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Scenario Lab</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Simulate purchase decisions, new loans, or income changes to see precise impact on goals and cash-flow runway.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="w-10 h-10 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 mb-4">
              <Target className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Goal Planning & Conflict Solver</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Multi-goal portfolio tracking with automated algorithmic resolution for competing milestones and timelines.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
              <Activity className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Continuous Monitoring</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Real-time plan drift detection comparing live snapshots against baseline budgets and financial trajectories.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Adaptive Replanning</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Proactive recovery plans with side-by-side trade-off analysis whenever a life change or emergency occurs.
            </p>
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section className="py-20 bg-gradient-to-b from-slate-900 to-slate-950 border-t border-slate-900 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">The FinPilot Engine</h2>
          <p className="text-slate-400 text-sm sm:text-base mb-10 max-w-2xl mx-auto">
            Traditional tools only categorize past expenses. Generic chatbots invent numbers. FinPilot combines the best of both worlds.
          </p>

          <div className="p-8 rounded-3xl bg-slate-950 border border-slate-800 text-left grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="text-indigo-400 font-bold text-base flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> AI Agents
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Specialized agents for spending analysis, expense reduction, decision evaluation, planning, and monitoring.
              </p>
            </div>
            <div className="space-y-2">
              <div className="text-purple-400 font-bold text-base flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> Deterministic Engine
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Strict mathematical validation for cash-flows, emergency buffers, debt metrics, and goal allocations.
              </p>
            </div>
            <div className="space-y-2">
              <div className="text-emerald-400 font-bold text-base flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> Isolated Persistence
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                PostgreSQL decision memory with secure JWT authentication ensuring 100% data privacy and isolation.
              </p>
            </div>
          </div>

          <div className="mt-12">
            <button
              onClick={() => onNavigate('/signup')}
              className="px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-base shadow-lg shadow-indigo-600/25 transition inline-flex items-center gap-2"
            >
              Get Started with FinPilot AI
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-900 py-8 px-6 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>FinPilot AI — Autonomous Financial Planning & Decision Intelligence</div>
          <div className="flex items-center gap-6 text-slate-500">
            <span className="flex items-center gap-1"><Lock className="w-3.5 h-3.5" /> Isolated User Security</span>
            <span>Deterministic Financial Engine</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
