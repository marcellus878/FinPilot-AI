import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Sparkles,
  Send,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Activity,
  Zap,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  BookOpen,
} from 'lucide-react';
import { sendAdvisorChatMessage, getAdvisorRecommendations, reviewRecommendation } from '../services/api';
import { formatINR } from '../utils/formatters';
import type {
  AdvisorChatResponse,
  AdvisorRecommendationItem,
  FinancialFactItem,
  AgentTraceItem,
  RAGCitationItem,
  ReflectionAudit,
} from '../types';

interface ChatMessage {
  id: string;
  sender: 'user' | 'advisor';
  content: string;
  timestamp: string;
  intent?: string;
  facts?: FinancialFactItem[];
  recommendations?: AdvisorRecommendationItem[];
  rag_citations?: RAGCitationItem[];
  reflection_audit?: ReflectionAudit | null;
  trace?: AgentTraceItem[];
  healthScore?: number | null;
}

interface AdvisorViewProps {
  initialPrompt?: string | null;
  onClearInitialPrompt?: () => void;
}

const SUGGESTED_QUERIES = [
  {
    icon: '🧠',
    label: 'Decision Memory Review',
    prompt: 'What major financial decisions did I make previously and how did they turn out?',
  },
  {
    icon: '📉',
    label: 'Decision Drift Analysis',
    prompt: 'Has my financial situation changed since my last big purchase decision?',
  },
  {
    icon: '💡',
    label: 'Proactive Opportunities',
    prompt: 'What proactive financial optimizations or opportunities should I look into right now?',
  },
  {
    icon: '📡',
    label: 'Monitoring: Plan Health Review',
    prompt: 'Review my current financial health and check if my budget or goals have drifted.',
  },
  {
    icon: '🔄',
    label: 'Adaptive Replanning',
    prompt: 'Evaluate if I need to adapt my financial plan and propose recovery strategies.',
  },
  {
    icon: '⚖️',
    label: 'Decision: Laptop Purchase',
    prompt: 'Can I afford to buy a ₹60,000 laptop?',
  },
  {
    icon: '🚗',
    label: 'Decision: Car Loan EMI',
    prompt: 'Can I take on a ₹15,000 per month car loan for 36 months?',
  },
  {
    icon: '🧩',
    label: 'Planning: Salary Allocation',
    prompt: 'How should I allocate my monthly salary across essentials, savings, and discretionary spending?',
  },
  {
    icon: '🎯',
    label: 'Planning: Goal Conflict',
    prompt: 'I have competing goals for Emergency Fund and House Downpayment, how do I resolve the conflict?',
  },
  {
    icon: '💡',
    label: 'Expense Reduction',
    prompt: 'How can I cut expenses, plug miscellaneous leaks, and reduce subscriptions?',
  },
];

export const AdvisorView: React.FC<AdvisorViewProps> = ({ initialPrompt, onClearInitialPrompt }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'recommendations'>('chat');
  const [savedRecommendations, setSavedRecommendations] = useState<AdvisorRecommendationItem[]>([]);
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const [hitlStatusMap, setHitlStatusMap] = useState<Record<string, 'accepted' | 'modified' | 'rejected'>>({});
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleHITLAction = async (recId: string, action: 'accepted' | 'modified' | 'rejected') => {
    try {
      await reviewRecommendation(recId, { action });
      setHitlStatusMap((prev) => ({ ...prev, [recId]: action }));
    } catch (err: any) {
      console.error('Failed to submit HITL review', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    // Initial welcome message
    const welcomeMsg: ChatMessage = {
      id: 'welcome-1',
      sender: 'advisor',
      content:
        `### 👋 Hello, I am your FinPilot AI Financial Advisor!\n\n` +
        `I am orchestrated by **LangGraph** and reason strictly over your **verified financial calculations and persistent decision memory**.\n\n` +
        `I analyze your income, essential vs. discretionary spending, recurring commitments, budgets, savings goals, and past purchase decisions to give you mathematically sound financial guidance.\n\n` +
        `Ask me a question below, check your past decisions, or choose one of the suggested topics to get started!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages([welcomeMsg]);

    // Load existing recommendations
    getAdvisorRecommendations()
      .then((recs) => setSavedRecommendations(recs))
      .catch((err) => console.error('Failed to load recommendations', err));
  }, []);

  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      handleSendMessage(initialPrompt);
      if (onClearInitialPrompt) {
        onClearInitialPrompt();
      }
    }
  }, [initialPrompt]);

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = (queryText || inputQuery).trim();
    if (!textToSend || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setIsLoading(true);

    try {
      const response: AdvisorChatResponse = await sendAdvisorChatMessage({ message: textToSend });

      const advisorMsg: ChatMessage = {
        id: response.request_id || `adv-${Date.now()}`,
        sender: 'advisor',
        content: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: response.intent,
        facts: response.financial_facts,
        recommendations: response.recommendations,
        rag_citations: (response as any).rag_citations || [],
        reflection_audit: (response as any).reflection_audit || null,
        trace: response.execution_trace,
        healthScore: response.financial_health_score,
      };

      setMessages((prev) => [...prev, advisorMsg]);

      // Update saved recommendations list
      if (response.recommendations && response.recommendations.length > 0) {
        setSavedRecommendations((prev) => [...response.recommendations, ...prev]);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'advisor',
        content: `⚠️ **Advisory Error:** ${err.message || 'Unable to communicate with the AI reasoning engine. Please try again.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMarkdownFormattedText = (text: string) => {
    const lines = text.split('\n');
    return (
      <div className="space-y-2 text-slate-200 text-sm leading-relaxed">
        {lines.map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={idx} className="h-1" />;

          // Heading 3
          if (trimmed.startsWith('### ')) {
            return (
              <h3 key={idx} className="text-base font-semibold text-cyan-300 mt-3 mb-1 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                {trimmed.replace('### ', '')}
              </h3>
            );
          }

          // Heading 4
          if (trimmed.startsWith('#### ')) {
            return (
              <h4 key={idx} className="text-sm font-semibold text-slate-100 mt-2 mb-1">
                {trimmed.replace('#### ', '')}
              </h4>
            );
          }

          // Bullet list items
          if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const content = trimmed.substring(2);
            return (
              <div key={idx} className="flex items-start gap-2 ml-2">
                <span className="text-cyan-400 mt-1">•</span>
                <span>{renderInlineFormatting(content)}</span>
              </div>
            );
          }

          return <p key={idx}>{renderInlineFormatting(trimmed)}</p>;
        })}
      </div>
    );
  };

  const renderInlineFormatting = (content: string) => {
    // Process **bold** and *italic* tags
    const parts = content.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return (
          <em key={i} className="text-slate-300 italic">
            {part.slice(1, -1)}
          </em>
        );
      }
      return part;
    });
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-cyan-950 border border-slate-700/60 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-white tracking-tight">FinPilot AI Advisor</h1>
                <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  LangGraph Orchestrated
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-0.5">
                Deterministic Financial Reasoning Engine & Multi-Agent Advisory
              </p>
            </div>
          </div>

          {/* Navigation Toggle */}
          <div className="flex items-center bg-slate-950/60 p-1 rounded-xl border border-slate-700/60">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                activeTab === 'chat'
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Bot className="w-3.5 h-3.5" />
              Advisor Chat
            </button>
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                activeTab === 'recommendations'
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Recommendations
              {savedRecommendations.length > 0 && (
                <span className="px-1.5 py-0.2 text-[10px] bg-slate-800 text-cyan-300 rounded-full border border-cyan-500/30">
                  {savedRecommendations.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'chat' ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Chat Feed */}
          <div className="lg:col-span-3 flex flex-col h-[700px] bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'advisor' && (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shrink-0 border border-cyan-400/30 mt-1">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-4.5 border transition-all ${
                      msg.sender === 'user'
                        ? 'bg-cyan-600/90 text-white border-cyan-500/40 shadow-lg shadow-cyan-600/10 rounded-tr-none'
                        : 'bg-slate-950/80 text-slate-200 border-slate-800 shadow-md rounded-tl-none'
                    }`}
                  >
                    {/* Header info for Advisor Messages */}
                    {msg.sender === 'advisor' && msg.intent && (
                      <div className="flex items-center justify-between gap-2 pb-2 mb-3 border-b border-slate-800/80 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1.5 font-medium text-cyan-400">
                          <Zap className="w-3 h-3 text-cyan-400" />
                          Intent: {msg.intent.replace('_', ' ').toUpperCase()}
                        </span>
                        <span>{msg.timestamp}</span>
                      </div>
                    )}

                    {/* Main Content */}
                    {msg.sender === 'user' ? (
                      <p className="text-sm text-white leading-relaxed">{msg.content}</p>
                    ) : (
                      renderMarkdownFormattedText(msg.content)
                    )}

                    {/* Structured Financial Facts Badges */}
                    {msg.facts && msg.facts.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-800/80">
                        <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                          <Activity className="w-3.5 h-3.5 text-cyan-400" />
                          Grounded Financial Facts
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {msg.facts.map((fact, fIdx) => (
                            <div
                              key={fIdx}
                              className="bg-slate-900/90 border border-slate-800 rounded-xl p-2.5 flex flex-col justify-between"
                            >
                              <span className="text-[11px] text-slate-400 font-medium truncate">{fact.metric}</span>
                              <span className="text-sm font-bold text-cyan-300 mt-0.5">{fact.value}</span>
                              {fact.interpretation && (
                                <span className="text-[10px] text-slate-500 mt-1 truncate">{fact.interpretation}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* RAG Sources Cited */}
                    {msg.rag_citations && msg.rag_citations.length > 0 && (
                      <div className="mt-3.5 pt-2.5 border-t border-slate-800/80">
                        <div className="text-[11px] font-semibold text-slate-400 mb-1.5 flex items-center gap-1.5">
                          <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                          Sources used:
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.rag_citations.map((c, cIdx) => (
                            <div
                              key={cIdx}
                              className="px-2 py-1 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-[11px] text-indigo-200 flex items-center gap-1 shadow-sm"
                            >
                              <span className="font-semibold">{c.title}</span>
                              <span className="text-[9px] text-indigo-400 bg-indigo-900/60 px-1 py-0.5 rounded font-mono">
                                {c.publisher}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reflection & Groundedness Banner */}
                    {msg.reflection_audit && (
                      <div className="mt-3 py-1.5 px-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-300 flex items-center justify-between">
                        <span className="flex items-center gap-1.5 font-medium">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                          Reflected & Grounded in Verified Financial Context
                        </span>
                        <span className="font-mono text-[10px] text-emerald-400 font-bold">
                          {Math.round(msg.reflection_audit.groundedness_score * 100)}% Match
                        </span>
                      </div>
                    )}

                    {/* Recommendations Cards with HITL */}
                    {msg.recommendations && msg.recommendations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-800/80">
                        <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                          Targeted Actionable Recommendations (Human-in-the-Loop)
                        </div>
                        <div className="space-y-2.5">
                          {msg.recommendations.map((rec, rIdx) => {
                            const recKey = rec.id || `msg-${msg.id}-rec-${rIdx}`;
                            const hitlStatus = hitlStatusMap[recKey];
                            return (
                              <div
                                key={rIdx}
                                className="bg-gradient-to-r from-slate-900 to-slate-850 border border-slate-700/80 rounded-xl p-3 flex flex-col gap-2 hover:border-cyan-500/40 transition-colors shadow-sm"
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <span className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                    {rec.title}
                                  </span>
                                  <div className="flex items-center gap-2">
                                    {rec.potential_monthly_savings && rec.potential_monthly_savings > 0 && (
                                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                        +{formatINR(rec.potential_monthly_savings)}/mo
                                      </span>
                                    )}
                                    <span
                                      className={`px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${
                                        rec.priority === 'high'
                                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                      }`}
                                    >
                                      {rec.priority}
                                    </span>
                                  </div>
                                </div>
                                <p className="text-xs text-slate-300 leading-normal">{rec.description}</p>

                                {/* HITL Review Decision */}
                                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                                  <span className="text-[10px] text-slate-500">
                                    {hitlStatus ? `Decision: ${hitlStatus.toUpperCase()}` : 'Review Recommendation:'}
                                  </span>
                                  <div className="flex items-center gap-1.5">
                                    <button
                                      onClick={() => handleHITLAction(recKey, 'accepted')}
                                      className={`px-2 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ${
                                        hitlStatus === 'accepted'
                                          ? 'bg-emerald-500 text-white'
                                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20'
                                      }`}
                                    >
                                      <ThumbsUp className="w-2.5 h-2.5" /> Accept
                                    </button>
                                    <button
                                      onClick={() => handleHITLAction(recKey, 'modified')}
                                      className={`px-2 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ${
                                        hitlStatus === 'modified'
                                          ? 'bg-amber-500 text-white'
                                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20'
                                      }`}
                                    >
                                      <Sparkles className="w-2.5 h-2.5" /> Modify
                                    </button>
                                    <button
                                      onClick={() => handleHITLAction(recKey, 'rejected')}
                                      className={`px-2 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ${
                                        hitlStatus === 'rejected'
                                          ? 'bg-rose-500 text-white'
                                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20'
                                      }`}
                                    >
                                      <ThumbsDown className="w-2.5 h-2.5" /> Reject
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
                    {msg.trace && msg.trace.length > 0 && (
                      <div className="mt-3 pt-2">
                        <button
                          onClick={() =>
                            setExpandedTraceId(expandedTraceId === msg.id ? null : msg.id)
                          }
                          className="text-[11px] text-slate-500 hover:text-cyan-400 transition-colors flex items-center gap-1 font-mono"
                        >
                          <Activity className="w-3 h-3" />
                          {expandedTraceId === msg.id ? 'Hide' : 'View'} LangGraph Agent Execution Trace ({msg.trace.length} steps)
                          {expandedTraceId === msg.id ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                        </button>

                        {expandedTraceId === msg.id && (
                          <div className="mt-2 bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-[11px] space-y-2 text-slate-400">
                            {msg.trace.map((step, sIdx) => (
                              <div key={sIdx} className="border-l-2 border-cyan-500/50 pl-2.5 py-0.5">
                                <div className="text-cyan-400 font-semibold flex items-center justify-between">
                                  <span>Step {sIdx + 1}: {step.step}</span>
                                  <span className="text-[10px] text-slate-500">{step.agent}</span>
                                </div>
                                <div className="text-slate-300 text-[10px]">{step.action}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {msg.sender === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center shrink-0 mt-1 border border-slate-600">
                      <span className="text-xs font-bold text-white">ME</span>
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 items-center text-slate-400 text-sm">
                  <div className="w-8 h-8 rounded-lg bg-cyan-600/30 border border-cyan-400/40 flex items-center justify-center animate-pulse">
                    <Bot className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3 flex items-center gap-2.5">
                    <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                    <span>Orchestrator reasoning over financial metrics...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask FinPilot AI about spending leaks, budget limits, salary planning, goals..."
                  disabled={isLoading}
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || isLoading}
                  className="bg-gradient-to-r from-cyan-500 to-indigo-600 text-white px-5 py-3 rounded-xl font-medium text-sm flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-40 shadow-lg shadow-cyan-500/20"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  <span>Ask</span>
                </button>
              </form>
            </div>
          </div>

          {/* Sidebar with Suggested Prompts & Quick Insights */}
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-cyan-400" />
                Suggested Queries
              </h3>
              <div className="space-y-2">
                {SUGGESTED_QUERIES.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q.prompt)}
                    disabled={isLoading}
                    className="w-full text-left p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-850 transition-all text-xs text-slate-300 flex items-start gap-2.5 group disabled:opacity-50"
                  >
                    <span className="text-base shrink-0">{q.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-white group-hover:text-cyan-300 transition-colors">
                        {q.label}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate mt-0.5">{q.prompt}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-emerald-400" />
                Zero Hallucination Guarantee
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                FinPilot AI agents are strictly grounded in deterministic financial engine equations. All cash balances, safe-to-spend targets, and runway metrics are computed by verified algorithms before reasoning.
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Recommendations Tab */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-400" />
                AI Financial Recommendations Hub
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Actionable advice generated from your recent spending analysis and budget optimization runs.
              </p>
            </div>
          </div>

          {savedRecommendations.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Sparkles className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-sm font-medium">No recommendations recorded yet.</p>
              <p className="text-xs text-slate-500 mt-1">
                Ask the AI Advisor in the chat tab to analyze your spending and suggest expense reductions.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedRecommendations.map((rec, rIdx) => (
                <div
                  key={rec.id || rIdx}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-cyan-500/40 transition-colors shadow-md"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-sm font-semibold text-white flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        {rec.title}
                      </span>
                      <div className="flex items-center gap-2">
                        {rec.potential_monthly_savings && rec.potential_monthly_savings > 0 && (
                          <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            +{formatINR(rec.potential_monthly_savings)}/mo
                          </span>
                        )}
                        <span
                          className={`px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${
                            rec.priority === 'high'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {rec.priority}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">{rec.description}</p>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center justify-between pt-2 border-t border-slate-800/60">
                    <span>Type: {rec.type}</span>
                    {rec.category && <span>Category: {rec.category}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
