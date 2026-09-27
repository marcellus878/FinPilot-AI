import React, { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  DollarSign,
  Mic,
  MicOff,
  Plus,
  Sparkles,
  X,
} from 'lucide-react';

import { createTransaction, parseTransactionText } from '../services/api';
import type {
  NLParseResponse,
  Transaction,
  TransactionFormData,
} from '../types';

interface TransactionEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (tx: Transaction) => void;
}

type Mode = 'voice' | 'nl' | 'manual';

const SAMPLE_PROMPTS = [
  'Spent 450 rupees on Swiggy for dinner yesterday',
  'Spent 500 on petrol today',
  'Paid 1200 for broadband',
  'Got salary of 60000 yesterday',
  'Spent 350 on dinner last Saturday',
];

export const TransactionEntryModal: React.FC<TransactionEntryModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [activeMode, setActiveMode] = useState<Mode>('voice');
  const [nlText, setNlText] = useState<string>('');
  const [parsing, setParsing] = useState<boolean>(false);
  const [parseResult, setParseResult] = useState<NLParseResponse | null>(null);

  // Form Data (shared across modes for final confirmation)
  const [formData, setFormData] = useState<TransactionFormData>({
    amount: '',
    type: 'expense',
    category: 'Groceries',
    description: '',
    transaction_date: new Date().toISOString().slice(0, 16),
  });
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Speech Recognition state
  const [isListening, setIsListening] = useState<boolean>(false);
  const [speechSupported, setSpeechSupported] = useState<boolean>(true);
  const [transcript, setTranscript] = useState<string>('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check Web Speech API support
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setFormError(null);
      };

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);
        setNlText(currentTranscript);
      };

      recognition.onerror = (event: any) => {
        setIsListening(false);
        if (event.error !== 'no-speech') {
          setFormError(`Speech recognition error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } catch {
      setSpeechSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
    };
  }, []);

  // When speech transcript completes, trigger parse
  useEffect(() => {
    if (!isListening && transcript.trim()) {
      handleParse(transcript);
    }
  }, [isListening, transcript]);

  const toggleListening = () => {
    if (!speechSupported) return;
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setTranscript('');
      setParseResult(null);
      try {
        recognitionRef.current?.start();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleParse = async (text: string) => {
    if (!text.trim()) return;
    setParsing(true);
    setFormError(null);
    try {
      const res = await parseTransactionText(text);
      setParseResult(res);

      // Populate form data
      setFormData({
        amount: res.amount ? String(res.amount) : '',
        type: res.type,
        category: res.category,
        description: res.description || '',
        transaction_date: res.transaction_date.slice(0, 16),
      });
    } catch (err: any) {
      setFormError(err.message || 'Failed to parse natural language text.');
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.amount || Number(formData.amount) <= 0) {
      setFormError('Please enter a valid positive transaction amount.');
      return;
    }
    if (!formData.category.trim()) {
      setFormError('Please select or specify a category.');
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      const created = await createTransaction({
        ...formData,
        amount: Number(formData.amount).toFixed(2),
        transaction_date: new Date(formData.transaction_date).toISOString(),
      });
      onSuccess(created);
      handleClose();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save transaction.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (isListening && recognitionRef.current) {
      recognitionRef.current.abort();
    }
    setIsListening(false);
    setTranscript('');
    setNlText('');
    setParseResult(null);
    setFormData({
      amount: '',
      type: 'expense',
      category: 'Groceries',
      description: '',
      transaction_date: new Date().toISOString().slice(0, 16),
    });
    setFormError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 text-xs text-slate-300 relative">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Plus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Record Transaction</h3>
              <p className="text-[11px] text-slate-400">Add via Voice, Natural Language, or Manual entry</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg transition hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Mode Selector Tabs */}
        <div className="grid grid-cols-3 gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            type="button"
            onClick={() => {
              setActiveMode('voice');
              setFormError(null);
            }}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg font-semibold transition ${
              activeMode === 'voice'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            Voice Input
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveMode('nl');
              setFormError(null);
            }}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg font-semibold transition ${
              activeMode === 'nl'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Natural Text
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveMode('manual');
              setFormError(null);
            }}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg font-semibold transition ${
              activeMode === 'manual'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <DollarSign className="w-3.5 h-3.5" />
            Manual Form
          </button>
        </div>

        {formError && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        {/* ----------------- MODE 1: VOICE INPUT ----------------- */}
        {activeMode === 'voice' && (
          <div className="space-y-4">
            {!speechSupported ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-amber-800/40 text-amber-300 space-y-2 text-center">
                <p className="font-semibold text-xs">Browser Speech API Unavailable</p>
                <p className="text-[11px] text-slate-400">
                  Your browser does not support native speech recognition. You can type sentences in the Natural Text tab.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveMode('nl')}
                  className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold"
                >
                  Switch to Natural Text
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center p-6 bg-slate-950/80 rounded-2xl border border-slate-800/80 space-y-3">
                <button
                  type="button"
                  onClick={toggleListening}
                  className={`relative p-5 rounded-full transition-all duration-300 ${
                    isListening
                      ? 'bg-rose-600 text-white ring-8 ring-rose-500/20 animate-pulse'
                      : 'bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg'
                  }`}
                  title={isListening ? 'Click to stop listening' : 'Click to speak'}
                >
                  {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                </button>

                <div className="text-center">
                  <p className="font-semibold text-slate-200">
                    {isListening ? 'Listening... Speak your transaction' : 'Tap to start speaking'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    e.g. &ldquo;Spent 450 rupees on Swiggy for dinner yesterday&rdquo;
                  </p>
                </div>

                {transcript && (
                  <div className="w-full mt-2 p-3 bg-slate-900 rounded-xl border border-slate-800 text-slate-200 italic text-center">
                    &ldquo;{transcript}&rdquo;
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ----------------- MODE 2: NATURAL LANGUAGE ----------------- */}
        {activeMode === 'nl' && (
          <div className="space-y-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Describe transaction in plain English
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={nlText}
                  onChange={(e) => setNlText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleParse(nlText);
                    }
                  }}
                  placeholder="e.g. Paid 1200 for broadband today"
                  className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="button"
                  onClick={() => handleParse(nlText)}
                  disabled={parsing || !nlText.trim()}
                  className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition disabled:opacity-50 flex items-center gap-1 shrink-0"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {parsing ? 'Parsing...' : 'Parse'}
                </button>
              </div>
            </div>

            {/* Quick Prompts */}
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Try examples:</span>
              <div className="flex flex-wrap gap-1.5">
                {SAMPLE_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setNlText(prompt);
                      handleParse(prompt);
                    }}
                    className="px-2 py-1 bg-slate-950 hover:bg-slate-800 text-[11px] text-slate-400 hover:text-emerald-300 border border-slate-800/80 rounded-md transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Parse Preview Card (Visible when NL or Voice extracts values) */}
        {parseResult && (
          <div className="p-3 bg-emerald-950/20 border border-emerald-800/40 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-emerald-300 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Parsed & Categorized ({(parseResult.confidence * 100).toFixed(0)}% confidence)
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-slate-900 text-slate-300 border border-slate-800">
                {parseResult.essentiality.replace('_', ' ')}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 italic">{parseResult.essentiality_reason}</p>
          </div>
        )}

        {/* ----------------- EDITABLE STRUCTURED FORM ----------------- */}
        <form onSubmit={handleSubmit} className="space-y-3.5 border-t border-slate-800 pt-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              {activeMode !== 'manual' ? 'Review & Edit Before Saving' : 'Transaction Details'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 text-[11px] mb-1">Type</label>
              <div className="grid grid-cols-2 gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, type: 'expense' })}
                  className={`py-1 text-center rounded font-semibold transition ${
                    formData.type === 'expense'
                      ? 'bg-rose-950 text-rose-300 border border-rose-800/60'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Expense
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, type: 'income' })}
                  className={`py-1 text-center rounded font-semibold transition ${
                    formData.type === 'income'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Income
                </button>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 text-[11px] mb-1">Amount (₹)</label>
              <input
                type="number"
                step="1"
                min="0"
                required
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                placeholder="0"
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono font-semibold focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 text-[11px] mb-1">Category</label>
              <input
                type="text"
                required
                list="entry-categories-list"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
              />
              <datalist id="entry-categories-list">
                <option value="Food" />
                <option value="Groceries" />
                <option value="Transport" />
                <option value="Shopping" />
                <option value="Entertainment" />
                <option value="Bills & Utilities" />
                <option value="Healthcare" />
                <option value="Education" />
                <option value="Rent/Housing" />
                <option value="EMI/Debt" />
                <option value="Salary/Income" />
                <option value="Savings/Investment" />
                <option value="Cash Withdrawal" />
                <option value="Miscellaneous" />
              </datalist>
            </div>

            <div>
              <label className="block text-slate-400 text-[11px] mb-1">Date & Time</label>
              <input
                type="datetime-local"
                required
                value={formData.transaction_date}
                onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 text-[11px] mb-1">Description / Merchant</label>
            <input
              type="text"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="e.g. Swiggy - dinner"
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-slate-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {submitting ? 'Saving...' : 'Confirm & Save Transaction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
