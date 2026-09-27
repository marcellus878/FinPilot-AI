import React, { useEffect, useState } from 'react';
import {
  Activity,
  ArrowRight,
  Bot,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  Layers,
  Play,
  RefreshCw,
  Scale,
  Scissors,
  ShieldCheck,
  Sparkles,
  Target,
  ThumbsDown,
  ThumbsUp,
  TrendingDown,
  Workflow,
} from 'lucide-react';

import {
  fetchAgentRegistry,
  fetchLLMBenchmark,
  fetchRAGComparison,
  fetchRAGSources,
  reviewRecommendation,
  runAgentLabAgent,
  runMultiAgentWorkflow,
} from '../services/api';
import type {
  AgentDefinition,
  AgentLabRunResponse,
  KnowledgeSource,
  LLMBenchmarkResult,
  RAGModeComparisonResult,
} from '../types';
import { formatINR } from '../utils/formatters';

export const AgentLabView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'inspect' | 'workflows' | 'orchestrator' | 'evaluation'>('inspect');
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('orchestrator');

  // Inspector sandbox state
  const [sandboxQuery, setSandboxQuery] = useState<string>('');
  const [runningAgent, setRunningAgent] = useState<boolean>(false);
  const [agentResult, setAgentResult] = useState<AgentLabRunResponse | null>(null);
  const [hitlFeedbackMsg, setHitlFeedbackMsg] = useState<string | null>(null);
  const [expandedTrace, setExpandedTrace] = useState<boolean>(false);

  // Multi-Agent Workflow state
  const [selectedWorkflow, setSelectedWorkflow] = useState<'spending_decision_planning' | 'monitoring_replanning_planning'>('spending_decision_planning');
  const [workflowQuery, setWorkflowQuery] = useState<string>('My discretionary dining spending jumped by ₹8,000 this month. Will this delay my emergency savings goal?');
  const [runningWorkflow, setRunningWorkflow] = useState<boolean>(false);
  const [workflowResult, setWorkflowResult] = useState<AgentLabRunResponse | null>(null);

  // Evaluation & Benchmark state
  const [loadingEval, setLoadingEval] = useState<boolean>(false);
  const [ragComparison, setRagComparison] = useState<RAGModeComparisonResult | null>(null);
  const [llmBenchmark, setLlmBenchmark] = useState<LLMBenchmarkResult | null>(null);
  const [knowledgeSources, setKnowledgeSources] = useState<KnowledgeSource[]>([]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [reg, sources, ragComp, llmBench] = await Promise.all([
        fetchAgentRegistry(),
        fetchRAGSources(),
        fetchRAGComparison(),
        fetchLLMBenchmark(),
      ]);
      setAgents(reg);
      setKnowledgeSources(sources);
      setRagComparison(ragComp);
      setLlmBenchmark(llmBench);
      if (reg.length > 0) {
        setSelectedAgentId(reg[0].id);
        setSandboxQuery(reg[0].sample_prompts[0] || '');
      }
    } catch (err) {
      console.error('Failed to load Agent Lab data:', err);
    }
  };

  const handleSelectAgent = (agent: AgentDefinition) => {
    setSelectedAgentId(agent.id);
    setSandboxQuery(agent.sample_prompts[0] || '');
    setAgentResult(null);
    setHitlFeedbackMsg(null);
  };

  const handleRunAgentSandbox = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!sandboxQuery.trim()) return;

    try {
      setRunningAgent(true);
      setHitlFeedbackMsg(null);
      const res = await runAgentLabAgent(selectedAgentId, sandboxQuery);
      setAgentResult(res);
    } catch (err: any) {
      alert(`Agent execution error: ${err.message}`);
    } finally {
      setRunningAgent(false);
    }
  };

  const handleRunWorkflow = async () => {
    if (!workflowQuery.trim()) return;
    try {
      setRunningWorkflow(true);
      const res = await runMultiAgentWorkflow(selectedWorkflow, workflowQuery);
      setWorkflowResult(res);
    } catch (err: any) {
      alert(`Workflow execution error: ${err.message}`);
    } finally {
      setRunningWorkflow(false);
    }
  };

  const handleHITLReview = async (recommendationId: string, action: 'accepted' | 'modified' | 'rejected') => {
    try {
      await reviewRecommendation(recommendationId, {
        action,
        agent_name: selectedAgent?.name || 'Agent Lab',
      });
      setHitlFeedbackMsg(`Human review recorded: Recommendation ${action.toUpperCase()} by user.`);
      if (agentResult) {
        setAgentResult({
          ...agentResult,
          recommendations: agentResult.recommendations.map((r, i) =>
            (r.id === recommendationId || String(i) === recommendationId)
              ? { ...r, hitl_status: action }
              : r
          ),
        });
      }
    } catch (err: any) {
      alert(`Review submission error: ${err.message}`);
    }
  };

  const handleRunLiveBenchmark = async () => {
    try {
      setLoadingEval(true);
      const [ragComp, llmBench] = await Promise.all([
        fetchRAGComparison('rag_questions.jsonl'),
        fetchLLMBenchmark(),
      ]);
      setRagComparison(ragComp);
      setLlmBenchmark(llmBench);
    } catch (err: any) {
      alert(`Benchmark error: ${err.message}`);
    } finally {
      setLoadingEval(false);
    }
  };

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  const getAgentIcon = (iconName: string) => {
    switch (iconName) {
      case 'Layers': return <Layers className="w-5 h-5" />;
      case 'TrendingDown': return <TrendingDown className="w-5 h-5" />;
      case 'Scissors': return <Scissors className="w-5 h-5" />;
      case 'Scale': return <Scale className="w-5 h-5" />;
      case 'Target': return <Target className="w-5 h-5" />;
      case 'Activity': return <Activity className="w-5 h-5" />;
      case 'RefreshCw': return <RefreshCw className="w-5 h-5" />;
      default: return <Sparkles className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn pb-16">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-500/20 border border-indigo-500/40 rounded-2xl text-indigo-400 shadow-inner">
                <Bot className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                    🤖 Agent Lab & Academic Studio
                  </h1>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-mono">
                    8 Autonomous Agents
                  </span>
                </div>
                <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-2xl">
                  Inspect specialized agents, execute multi-agent collaboration chains, observe Agentic RAG citations,
                  verify deterministic mathematical reflection, and benchmark LLM performances.
                </p>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 p-1.5 rounded-2xl self-start md:self-auto overflow-x-auto max-w-full">
            <button
              onClick={() => setActiveTab('inspect')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'inspect'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              Agent Inspector
            </button>
            <button
              onClick={() => setActiveTab('workflows')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'workflows'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Workflow className="w-3.5 h-3.5" />
              Multi-Agent Studio
            </button>
            <button
              onClick={() => setActiveTab('orchestrator')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'orchestrator'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Orchestrator Flow
            </button>
            <button
              onClick={() => setActiveTab('evaluation')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'evaluation'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Benchmark & Evaluation
            </button>
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------- */}
      {/* TAB 1: AGENT INSPECTOR & SANDBOX                      */}
      {/* ---------------------------------------------------- */}
      {activeTab === 'inspect' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Agent Selection List */}
          <div className="lg:col-span-4 space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
              Select Specialized Agent ({agents.length})
            </h3>
            <div className="space-y-2">
              {agents.map((agent) => {
                const isSelected = selectedAgentId === agent.id;
                return (
                  <button
                    key={agent.id}
                    onClick={() => handleSelectAgent(agent)}
                    className={`w-full text-left p-3.5 rounded-2xl border transition-all duration-200 flex items-start gap-3 ${
                      isSelected
                        ? 'bg-indigo-950/60 border-indigo-500 shadow-md ring-1 ring-indigo-500/40 text-white'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className={`p-2 rounded-xl shrink-0 ${isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                      {getAgentIcon(agent.icon)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sm text-white truncate">{agent.name}</span>
                        {isSelected && <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />}
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">{agent.role}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Knowledge Base Sources Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 mt-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-indigo-400" />
                  RAG Knowledge Sources ({knowledgeSources.length})
                </span>
                <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                  pgvector ready
                </span>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {knowledgeSources.map((s) => (
                  <div key={s.id} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs">
                    <div className="font-semibold text-slate-200 truncate">{s.title}</div>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
                      <span>{s.publisher}</span>
                      <span className="text-indigo-400 font-mono">{s.chunks_count} chunks</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Inspector & Interactive Sandbox */}
          <div className="lg:col-span-8 space-y-6">
            {selectedAgent && (
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-xl space-y-6">
                {/* Agent Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
                  <div className="flex items-center gap-3.5">
                    <div className="p-3 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl text-indigo-400">
                      {getAgentIcon(selectedAgent.icon)}
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">{selectedAgent.name}</h2>
                      <p className="text-xs text-indigo-300 font-medium">{selectedAgent.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                      Prompt v1.2.0
                    </span>
                    <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Reflected & Grounded
                    </span>
                  </div>
                </div>

                {/* Specs Grid: Purpose, Inputs, Tools, Memory */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1.5">
                    <span className="font-bold text-indigo-400 uppercase tracking-wider block text-[10px]">
                      Agent Purpose
                    </span>
                    <p className="text-slate-300 leading-relaxed">{selectedAgent.purpose}</p>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1.5">
                    <span className="font-bold text-cyan-400 uppercase tracking-wider block text-[10px]">
                      Memory Subsystems Accessed
                    </span>
                    <p className="text-slate-300 leading-relaxed font-mono">{selectedAgent.memory_access}</p>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
                    <span className="font-bold text-amber-400 uppercase tracking-wider block text-[10px]">
                      Input Parameters
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedAgent.inputs.map((inp, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[11px]">
                          {inp}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
                    <span className="font-bold text-emerald-400 uppercase tracking-wider block text-[10px]">
                      Active Tools & Services
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedAgent.tools.map((t, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-mono text-[11px]">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Workflow Diagram */}
                <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-2.5">
                  <span className="font-bold text-slate-400 uppercase tracking-wider block text-[10px]">
                    High-Level Execution Workflow
                  </span>
                  <div className="flex items-center gap-2 overflow-x-auto py-1">
                    {selectedAgent.workflow_steps.map((step, sIdx) => (
                      <React.Fragment key={sIdx}>
                        <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-slate-200 font-semibold whitespace-nowrap shadow-sm">
                          {step}
                        </div>
                        {sIdx < selectedAgent.workflow_steps.length - 1 && (
                          <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                {/* Interactive Agent Sandbox */}
                <div className="pt-4 border-t border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Play className="w-4 h-4 text-emerald-400" />
                      Live Agent Execution Sandbox
                    </h3>
                    <div className="flex items-center gap-1.5">
                      {selectedAgent.sample_prompts.map((sp, pIdx) => (
                        <button
                          key={pIdx}
                          onClick={() => setSandboxQuery(sp)}
                          className="px-2.5 py-1 text-[11px] rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 transition"
                        >
                          Sample {pIdx + 1}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleRunAgentSandbox} className="space-y-3">
                    <div className="relative">
                      <textarea
                        value={sandboxQuery}
                        onChange={(e) => setSandboxQuery(e.target.value)}
                        placeholder={`Provide input scenario for ${selectedAgent.name}...`}
                        rows={2}
                        className="w-full bg-slate-950 border border-slate-700 rounded-2xl p-4 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-500">
                        Reasons over live verified financial facts & public knowledge base.
                      </span>
                      <button
                        type="submit"
                        disabled={runningAgent || !sandboxQuery.trim()}
                        className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                      >
                        {runningAgent ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
                        {runningAgent ? 'Running Agent...' : `Run ${selectedAgent.name}`}
                      </button>
                    </div>
                  </form>
                </div>

                {/* Sandbox Output Results */}
                {agentResult && (
                  <div className="mt-6 space-y-5 pt-6 border-t border-slate-800 animate-fadeIn">
                    {/* Reflection Status Banner */}
                    {agentResult.reflection_audit && (
                      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            <ShieldCheck className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="text-xs font-bold text-white flex items-center gap-2">
                              Reflection & Self-Correction Validator
                              <span className="px-2 py-0.5 text-[10px] rounded bg-emerald-500/20 text-emerald-300 font-mono">
                                {agentResult.reflection_audit.status.toUpperCase()}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">
                              Mathematical Groundedness: <span className="text-emerald-400 font-bold font-mono">{intPercent(agentResult.reflection_audit.groundedness_score)}</span>
                              {agentResult.reflection_audit.corrections_applied.length > 0 && ` • Applied ${agentResult.reflection_audit.corrections_applied.length} self-corrections`}
                            </div>
                          </div>
                        </div>
                        {agentResult.reflection_audit.rag_grounded && (
                          <span className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 self-start sm:self-auto">
                            📚 RAG Grounded
                          </span>
                        )}
                      </div>
                    )}

                    {/* Verified Facts & RAG Citations */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Verified Facts */}
                      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                        <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block">
                          Verified Numerical Facts (Deterministic Engine)
                        </span>
                        {agentResult.financial_facts.length === 0 ? (
                          <p className="text-xs text-slate-500">No numerical overrides needed for this general query.</p>
                        ) : (
                          <div className="space-y-1.5">
                            {agentResult.financial_facts.map((f, fIdx) => (
                              <div key={fIdx} className="flex items-center justify-between text-xs p-1.5 rounded bg-slate-900 border border-slate-850">
                                <span className="text-slate-400">{f.metric.replace(/_/g, ' ')}</span>
                                <span className="font-mono font-bold text-white">{String(f.value)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* RAG Citations */}
                      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">
                          Retrieved Public Knowledge Citations
                        </span>
                        {agentResult.rag_citations.length === 0 ? (
                          <p className="text-xs text-slate-500">Pure user math query — no external guidelines required.</p>
                        ) : (
                          <div className="space-y-2">
                            {agentResult.rag_citations.map((c, cIdx) => (
                              <div key={cIdx} className="p-2 rounded bg-slate-900 border border-slate-800 text-xs space-y-1">
                                <div className="font-semibold text-indigo-300 flex items-center justify-between">
                                  <span>{c.title}</span>
                                  <span className="text-[10px] text-slate-500">{c.publisher}</span>
                                </div>
                                <p className="text-[11px] text-slate-400 leading-snug">{c.relevant_excerpt}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Agent Response */}
                    <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        Synthesized Output
                      </span>
                      <div className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-line">
                        {agentResult.final_response}
                      </div>
                    </div>

                    {/* Recommendations & Human-in-the-Loop (HITL) Controls */}
                    {agentResult.recommendations.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                            Targeted Recommendations (Human-in-the-Loop Review)
                          </span>
                          {hitlFeedbackMsg && (
                            <span className="text-xs font-bold text-emerald-400 animate-fadeIn">
                              {hitlFeedbackMsg}
                            </span>
                          )}
                        </div>

                        <div className="space-y-3">
                          {agentResult.recommendations.map((rec, rIdx) => {
                            const recId = rec.id || String(rIdx);
                            return (
                              <div key={rIdx} className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-bold text-sm text-white">{rec.title}</span>
                                  <div className="flex items-center gap-2">
                                    {rec.potential_monthly_savings && rec.potential_monthly_savings > 0 && (
                                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                        +{formatINR(rec.potential_monthly_savings)}/mo
                                      </span>
                                    )}
                                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                                      rec.hitl_status === 'accepted' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
                                      rec.hitl_status === 'rejected' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                                      'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                    }`}>
                                      {rec.hitl_status || 'Pending Review'}
                                    </span>
                                  </div>
                                </div>
                                <p className="text-xs text-slate-300 leading-relaxed">{rec.description}</p>

                                {/* HITL Action Buttons */}
                                <div className="flex items-center justify-between pt-3 border-t border-slate-850">
                                  <span className="text-[11px] text-slate-500">
                                    Human Decision:
                                  </span>
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={() => handleHITLReview(recId, 'accepted')}
                                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-600/30 transition flex items-center gap-1.5"
                                    >
                                      <ThumbsUp className="w-3 h-3" /> Accept
                                    </button>
                                    <button
                                      onClick={() => handleHITLReview(recId, 'modified')}
                                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-600/20 text-amber-300 border border-amber-500/40 hover:bg-amber-600/30 transition flex items-center gap-1.5"
                                    >
                                      <Sparkles className="w-3 h-3" /> Modify
                                    </button>
                                    <button
                                      onClick={() => handleHITLReview(recId, 'rejected')}
                                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600/20 text-rose-300 border border-rose-500/40 hover:bg-rose-600/30 transition flex items-center gap-1.5"
                                    >
                                      <ThumbsDown className="w-3 h-3" /> Reject
                                    </button>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Execution Trace Viewer */}
                    {agentResult.execution_trace.length > 0 && (
                      <div className="pt-2">
                        <button
                          onClick={() => setExpandedTrace(!expandedTrace)}
                          className="text-xs text-slate-400 hover:text-indigo-400 transition flex items-center gap-1.5 font-mono"
                        >
                          <Activity className="w-3.5 h-3.5" />
                          {expandedTrace ? 'Hide' : 'View'} Execution Trace ({agentResult.execution_trace.length} steps)
                          {expandedTrace ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>

                        {expandedTrace && (
                          <div className="mt-2.5 p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2 font-mono text-xs text-slate-300">
                            {agentResult.execution_trace.map((st, i) => (
                              <div key={i} className="border-l-2 border-indigo-500 pl-3 py-1">
                                <div className="text-indigo-400 font-bold flex items-center justify-between">
                                  <span>Step {i + 1}: {st.step}</span>
                                  <span className="text-[10px] text-slate-500">{st.agent}</span>
                                </div>
                                <div className="text-slate-300 text-[11px] mt-0.5">{st.action}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 2: MULTI-AGENT COLLABORATION STUDIO              */}
      {/* ---------------------------------------------------- */}
      {activeTab === 'workflows' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-xl space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Workflow className="w-5 h-5 text-indigo-400" />
                Multi-Agent Autonomous Collaboration Chains
              </h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Execute demonstrable end-to-end multi-agent pipelines where specialized agents coordinate state handoffs.
              </p>
            </div>

            {/* Workflow Selection Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                onClick={() => {
                  setSelectedWorkflow('spending_decision_planning');
                  setWorkflowQuery('My discretionary spending increased by ₹8,000 this month. Will this delay my emergency reserve goal?');
                  setWorkflowResult(null);
                }}
                className={`cursor-pointer p-5 rounded-2xl border transition-all ${
                  selectedWorkflow === 'spending_decision_planning'
                    ? 'bg-indigo-950/60 border-indigo-500 ring-1 ring-indigo-500/40'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Workflow Chain 1</span>
                  {selectedWorkflow === 'spending_decision_planning' && (
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-indigo-500/20 text-indigo-300">Selected</span>
                  )}
                </div>
                <h3 className="font-bold text-white text-base">Spending Anomaly $\rightarrow$ Decision $\rightarrow$ Planning</h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                  Spending Analyst quantifies discretionary drift, Decision Agent evaluates goal delay impact, and Planning Agent formulates timeline recovery.
                </p>
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
                  <span className="text-indigo-400">Spending Analyst</span>
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-cyan-400">Decision Agent</span>
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-emerald-400">Planning Agent</span>
                </div>
              </div>

              <div
                onClick={() => {
                  setSelectedWorkflow('monitoring_replanning_planning');
                  setWorkflowQuery('My monthly rent increased by ₹5,000. How should my 50/30/20 allocation and savings goals adapt?');
                  setWorkflowResult(null);
                }}
                className={`cursor-pointer p-5 rounded-2xl border transition-all ${
                  selectedWorkflow === 'monitoring_replanning_planning'
                    ? 'bg-indigo-950/60 border-indigo-500 ring-1 ring-indigo-500/40'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">Workflow Chain 2</span>
                  {selectedWorkflow === 'monitoring_replanning_planning' && (
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-purple-500/20 text-purple-300">Selected</span>
                  )}
                </div>
                <h3 className="font-bold text-white text-base">Monitoring Shock $\rightarrow$ Replanning $\rightarrow$ Planning</h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                  Monitoring Agent flags variance thresholds, Replanning Agent creates Before vs. After plan comparisons, and Planning Agent updates monthly targets.
                </p>
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
                  <span className="text-purple-400">Monitoring Agent</span>
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-amber-400">Replanning Agent</span>
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-emerald-400">Planning Agent</span>
                </div>
              </div>
            </div>

            {/* Workflow Query Input & Execute */}
            <div className="space-y-3 pt-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Multi-Agent Test Scenario Query
              </label>
              <textarea
                value={workflowQuery}
                onChange={(e) => setWorkflowQuery(e.target.value)}
                rows={2}
                className="w-full bg-slate-950 border border-slate-700 rounded-2xl p-4 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleRunWorkflow}
                disabled={runningWorkflow || !workflowQuery.trim()}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-600/30 transition text-xs disabled:opacity-50"
              >
                {runningWorkflow ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
                {runningWorkflow ? 'Executing Multi-Agent Chain...' : 'Execute Multi-Agent Workflow'}
              </button>
            </div>

            {/* Workflow Execution Results */}
            {workflowResult && (
              <div className="mt-6 space-y-5 pt-6 border-t border-slate-800 animate-fadeIn">
                <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                      Collaborative Response Output
                    </span>
                    <span className="text-[11px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                      ✓ Validated by Reflection Layer
                    </span>
                  </div>
                  <div className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-line">
                    {workflowResult.final_response}
                  </div>
                </div>

                {/* Handover Trace */}
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2 font-mono text-xs">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Multi-Agent State Handover & Execution Trace
                  </span>
                  <div className="space-y-2 pt-1">
                    {workflowResult.execution_trace.map((st, idx) => (
                      <div key={idx} className="border-l-2 border-indigo-500 pl-3 py-1">
                        <div className="text-indigo-400 font-bold flex items-center justify-between">
                          <span>Step {idx + 1}: {st.step}</span>
                          <span className="text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded">{st.agent}</span>
                        </div>
                        <div className="text-slate-300 text-[11px] mt-0.5">{st.action}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 3: ORCHESTRATOR FLOW VISUAL STUDIO               */}
      {/* ---------------------------------------------------- */}
      {activeTab === 'orchestrator' && (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              LangGraph Orchestrator & State Flow Architecture
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Visual overview of the directed cyclic graph maintaining immutable financial state and zero hallucination boundaries.
            </p>
          </div>

          {/* Graphical Pipeline Layout */}
          <div className="p-6 rounded-3xl bg-slate-950 border border-slate-800 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900 border border-indigo-500/40 space-y-2">
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">1. Perception & Intent</span>
                <p className="text-xs font-bold text-white">Lead Orchestrator</p>
                <p className="text-[11px] text-slate-400">Classifies intent & coordinates multi-agent subgraph dispatch.</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 border border-cyan-500/40 space-y-2">
                <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block">2. Agentic RAG</span>
                <p className="text-xs font-bold text-white">pgvector Knowledge Base</p>
                <p className="text-[11px] text-slate-400">Evaluates knowledge need & retrieves RBI/SEBI guidelines.</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 border border-purple-500/40 space-y-2">
                <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider block">3. Decision Memory</span>
                <p className="text-xs font-bold text-white">PostgreSQL State</p>
                <p className="text-[11px] text-slate-400">Retrieves historical decision context and checks baseline drift.</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 border border-emerald-500/40 space-y-2">
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">4. Financial Engine</span>
                <p className="text-xs font-bold text-white">Deterministic Math</p>
                <p className="text-[11px] text-slate-400">Calculates Safe-to-Spend, 50/30/20 formulas, and goal timeline deltas.</p>
              </div>
            </div>

            <div className="flex items-center justify-center">
              <div className="h-6 w-0.5 bg-indigo-500" />
            </div>

            <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/50 space-y-3">
              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">
                5. Specialized Agent Execution Layer
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-semibold text-slate-200">
                <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">Spending Analyst</div>
                <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">Decision Agent</div>
                <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">Planning Agent</div>
                <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">Monitoring & Replan</div>
              </div>
            </div>

            <div className="flex items-center justify-center">
              <div className="h-6 w-0.5 bg-indigo-500" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900 border border-amber-500/40 space-y-2">
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">6. Validator Layer</span>
                <p className="text-xs font-bold text-white">Schema & Number Fact Check</p>
                <p className="text-[11px] text-slate-400">Rejects hallucinated values not produced by the deterministic engine.</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 border border-emerald-500/40 space-y-2">
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">7. Reflection & Self-Correction</span>
                <p className="text-xs font-bold text-white">Bounded Correction Loop</p>
                <p className="text-[11px] text-slate-400">Audits factual grounding and fixes formatting prior to presentation.</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 border border-pink-500/40 space-y-2">
                <span className="text-[10px] font-bold text-pink-400 uppercase tracking-wider block">8. Human-in-the-Loop</span>
                <p className="text-xs font-bold text-white">User Verification Review</p>
                <p className="text-[11px] text-slate-400">Explicit user confirmation (Accept / Modify / Reject) for recommendations.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 4: EVALUATION BENCHMARK & MULTI-LLM RESULTS      */}
      {/* ---------------------------------------------------- */}
      {activeTab === 'evaluation' && (
        <div className="space-y-6">
          {/* Header & Live Benchmark Button */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-400" />
                  Academic Agent Evaluation & Benchmark Dashboard
                </h2>
                <p className="text-xs sm:text-sm text-slate-400 mt-1">
                  Empirical metrics across RAG modes (No-RAG vs Basic RAG vs Agentic RAG) and LLM model comparisons on standardized dataset questions.
                </p>
              </div>
              <button
                onClick={handleRunLiveBenchmark}
                disabled={loadingEval}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-lg transition text-xs disabled:opacity-50 self-start sm:self-auto"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingEval ? 'animate-spin' : ''}`} />
                {loadingEval ? 'Evaluating Datasets...' : 'Run Live Benchmark'}
              </button>
            </div>

            {/* RAG Mode Comparison Cards */}
            {ragComparison && (
              <div className="space-y-4 pt-2">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  RAG Mode Comparative Benchmark (rag_questions.jsonl)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Mode A: No RAG */}
                  <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-400 uppercase">Mode A: No RAG</span>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-slate-400">Baseline</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Groundedness:</span>
                        <span className="font-mono font-bold text-amber-400">{intPercent(ragComparison.no_rag.groundedness_score)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Retrieval Relevance:</span>
                        <span className="font-mono font-bold text-slate-500">N/A (0%)</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Reflection Success:</span>
                        <span className="font-mono font-bold text-white">{intPercent(ragComparison.no_rag.reflection_success_rate)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Average Latency:</span>
                        <span className="font-mono font-bold text-white">{ragComparison.no_rag.average_latency_ms} ms</span>
                      </div>
                    </div>
                  </div>

                  {/* Mode B: Basic RAG */}
                  <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-400 uppercase">Mode B: Basic RAG</span>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-cyan-500/10 text-cyan-300">Direct Lookup</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Groundedness:</span>
                        <span className="font-mono font-bold text-cyan-300">{intPercent(ragComparison.basic_rag.groundedness_score)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Retrieval Relevance:</span>
                        <span className="font-mono font-bold text-white">{intPercent(ragComparison.basic_rag.retrieval_relevance)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Reflection Success:</span>
                        <span className="font-mono font-bold text-white">{intPercent(ragComparison.basic_rag.reflection_success_rate)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Average Latency:</span>
                        <span className="font-mono font-bold text-white">{ragComparison.basic_rag.average_latency_ms} ms</span>
                      </div>
                    </div>
                  </div>

                  {/* Mode C: Agentic RAG */}
                  <div className="p-5 rounded-2xl bg-indigo-950/40 border border-indigo-500/50 space-y-3 shadow-lg ring-1 ring-indigo-500/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-indigo-300 uppercase">Mode C: Agentic RAG</span>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                        ⭐ Optimal
                      </span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-300">Groundedness:</span>
                        <span className="font-mono font-bold text-emerald-400">{intPercent(ragComparison.agentic_rag.groundedness_score)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-300">Retrieval Relevance:</span>
                        <span className="font-mono font-bold text-emerald-400">{intPercent(ragComparison.agentic_rag.retrieval_relevance)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-300">Reflection Success:</span>
                        <span className="font-mono font-bold text-emerald-400">{intPercent(ragComparison.agentic_rag.reflection_success_rate)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-300">Average Latency:</span>
                        <span className="font-mono font-bold text-white">{ragComparison.agentic_rag.average_latency_ms} ms</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Qualitative Insights */}
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Comparative Findings
                  </span>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {ragComparison.comparative_insights.map((ins, iIdx) => (
                      <li key={iIdx} className="flex items-start gap-2">
                        <span className="text-indigo-400 font-bold">•</span>
                        <span>{ins}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Multi-LLM Benchmark Comparison Table */}
            {llmBenchmark && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Multi-LLM Comparative Benchmark Matrix
                </h3>
                <div className="overflow-x-auto rounded-2xl border border-slate-800">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-950 text-slate-400 border-b border-slate-800">
                        <th className="py-3 px-4 font-semibold uppercase">Model Name</th>
                        <th className="py-3 px-4 font-semibold uppercase">Provider</th>
                        <th className="py-3 px-4 font-semibold uppercase">Factual Accuracy</th>
                        <th className="py-3 px-4 font-semibold uppercase">Groundedness</th>
                        <th className="py-3 px-4 font-semibold uppercase">Output Validity</th>
                        <th className="py-3 px-4 font-semibold uppercase">Avg Latency</th>
                        <th className="py-3 px-4 font-semibold uppercase">Cost Tier</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {llmBenchmark.models.map((m, mIdx) => (
                        <tr key={mIdx} className="hover:bg-slate-850/50 transition">
                          <td className="py-3 px-4 font-bold text-white font-sans">{m.model_name}</td>
                          <td className="py-3 px-4 text-slate-400 font-sans">{m.provider}</td>
                          <td className="py-3 px-4 text-emerald-400">{intPercent(m.factual_accuracy)}</td>
                          <td className="py-3 px-4 text-cyan-300">{intPercent(m.groundedness_score)}</td>
                          <td className="py-3 px-4 text-slate-200">{intPercent(m.structured_output_validity)}</td>
                          <td className="py-3 px-4 text-white">{m.average_latency_ms} ms</td>
                          <td className="py-3 px-4 font-sans text-xs text-slate-300">{m.cost_tier}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

function intPercent(val: number): string {
  return `${Math.round(val * 100)}%`;
}
