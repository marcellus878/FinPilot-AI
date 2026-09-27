import React, { useRef, useState } from 'react';
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Layers,
  Upload,
  UploadCloud,
  X,
} from 'lucide-react';

import { confirmStatementImport, previewStatementImport } from '../services/api';
import type {
  StatementImportConfirmItem,
  StatementImportPreviewResponse,
  StatementRowPreview,
} from '../types';
import { formatINR } from '../utils/formatters';

interface StatementImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (importedCount: number) => void;
}

export const StatementImportModal: React.FC<StatementImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<StatementImportPreviewResponse | null>(null);
  const [rows, setRows] = useState<StatementRowPreview[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setIsUploading(true);
    setErrorMessage(null);
    setPreviewData(null);
    setRows([]);
    setSelectedIndices(new Set());

    try {
      const res = await previewStatementImport(selectedFile);
      setPreviewData(res);
      setRows(res.transactions);

      // Select all valid and non-duplicate rows by default
      const validSet = new Set<number>();
      res.transactions.forEach((tx, idx) => {
        if (tx.is_valid && !tx.is_duplicate) {
          validSet.add(idx);
        }
      });
      setSelectedIndices(validSet);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to analyze statement file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleToggleRow = (index: number) => {
    const next = new Set(selectedIndices);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setSelectedIndices(next);
  };

  const handleCategoryChange = (index: number, newCategory: string) => {
    const updated = [...rows];
    updated[index] = { ...updated[index], category: newCategory };
    setRows(updated);
  };

  const handleConfirmImport = async () => {
    if (selectedIndices.size === 0) {
      alert('Please select at least one transaction to import.');
      return;
    }

    const itemsToImport: StatementImportConfirmItem[] = Array.from(selectedIndices).map((idx) => {
      const r = rows[idx];
      return {
        transaction_date: r.transaction_date,
        amount: r.amount,
        type: r.type,
        category: r.category,
        description: r.description,
        fingerprint: r.fingerprint,
      };
    });

    setIsImporting(true);
    setErrorMessage(null);
    try {
      const res = await confirmStatementImport(itemsToImport);
      onSuccess(res.imported_count);
      handleClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to complete import.');
    } finally {
      setIsImporting(false);
    }
  };

  const handleClose = () => {
    setPreviewData(null);
    setRows([]);
    setSelectedIndices(new Set());
    setErrorMessage(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full p-6 shadow-2xl space-y-5 text-xs text-slate-300 max-h-[90vh] flex flex-col relative">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 shrink-0">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Import Bank Statement</h3>
              <p className="text-[11px] text-slate-400">
                Upload CSV, XLSX, or PDF statements with automatic categorization and duplicate prevention
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg transition hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2 shrink-0">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Dropzone / Upload area */}
        {!previewData && (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 rounded-2xl p-10 text-center cursor-pointer transition bg-slate-950/50 hover:bg-slate-950 space-y-3"
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".csv,.xlsx,.xls,.pdf"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelect(e.target.files[0]);
                }
              }}
            />
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-emerald-400">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="font-semibold text-slate-200">
                {isUploading ? 'Analyzing Statement Columns & Rows...' : 'Click or Drag Statement File Here'}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Supports bank statements in <strong>.CSV</strong>, <strong>.XLSX</strong>, or <strong>.PDF</strong>
              </p>
            </div>
          </div>
        )}

        {/* Preview State */}
        {previewData && (
          <div className="space-y-4 flex-1 flex flex-col min-h-0">
            {/* Stats Summary Bar */}
            <div className="grid grid-cols-4 gap-3 shrink-0">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block">Total Rows</span>
                <span className="text-lg font-bold text-white">{previewData.total_rows}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-emerald-800/40">
                <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold block">Valid New</span>
                <span className="text-lg font-bold text-emerald-400">{previewData.valid_count}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-amber-800/40">
                <span className="text-[10px] uppercase tracking-wider text-amber-400 font-semibold block">Duplicates</span>
                <span className="text-lg font-bold text-amber-400">{previewData.duplicate_count}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block">Skipped / Errors</span>
                <span className="text-lg font-bold text-slate-400">{previewData.skipped_count}</span>
              </div>
            </div>

            {/* Column Mapping Badges */}
            <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-[11px] shrink-0">
              <div className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-semibold text-slate-300">Detected Mappings:</span>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(previewData.detected_columns).map(([role, col]) => (
                    <span key={role} className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                      <strong>{role}:</strong> {col}
                    </span>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setPreviewData(null);
                }}
                className="text-emerald-400 hover:text-emerald-300 underline text-xs"
              >
                Upload Different File
              </button>
            </div>

            {/* Preview Table */}
            <div className="flex-1 overflow-y-auto border border-slate-800 rounded-xl bg-slate-950/60">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 sticky top-0 border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="py-2.5 px-3 w-8">
                      <input
                        type="checkbox"
                        checked={selectedIndices.size === rows.filter((r) => r.is_valid).length && rows.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            const allValid = new Set<number>();
                            rows.forEach((r, idx) => {
                              if (r.is_valid) allValid.add(idx);
                            });
                            setSelectedIndices(allValid);
                          } else {
                            setSelectedIndices(new Set());
                          }
                        }}
                        className="rounded bg-slate-900 border-slate-700 text-emerald-600 focus:ring-0"
                      />
                    </th>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Description</th>
                    <th className="py-2.5 px-3 text-right">Amount</th>
                    <th className="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {rows.map((row, idx) => {
                    const isSelected = selectedIndices.has(idx);
                    return (
                      <tr
                        key={idx}
                        className={`transition ${
                          !row.is_valid
                            ? 'opacity-40 bg-slate-950'
                            : row.is_duplicate
                            ? 'bg-amber-950/10'
                            : 'hover:bg-slate-800/30'
                        }`}
                      >
                        <td className="py-2 px-3">
                          <input
                            type="checkbox"
                            disabled={!row.is_valid}
                            checked={isSelected}
                            onChange={() => handleToggleRow(idx)}
                            className="rounded bg-slate-900 border-slate-700 text-emerald-600 focus:ring-0 disabled:opacity-30"
                          />
                        </td>
                        <td className="py-2 px-3 font-mono text-[11px] text-slate-400">
                          {new Date(row.transaction_date).toLocaleDateString()}
                        </td>
                        <td className="py-2 px-3">
                          <span
                            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              row.type === 'income'
                                ? 'bg-emerald-950 text-emerald-300'
                                : 'bg-rose-950 text-rose-300'
                            }`}
                          >
                            {row.type === 'income' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                            {row.type}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          <select
                            value={row.category}
                            onChange={(e) => handleCategoryChange(idx, e.target.value)}
                            disabled={!row.is_valid}
                            className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-emerald-500 disabled:opacity-40"
                          >
                            <option value="Food">Food</option>
                            <option value="Groceries">Groceries</option>
                            <option value="Transport">Transport</option>
                            <option value="Shopping">Shopping</option>
                            <option value="Entertainment">Entertainment</option>
                            <option value="Bills & Utilities">Bills & Utilities</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Education">Education</option>
                            <option value="Rent/Housing">Rent/Housing</option>
                            <option value="EMI/Debt">EMI/Debt</option>
                            <option value="Salary/Income">Salary/Income</option>
                            <option value="Savings/Investment">Savings/Investment</option>
                            <option value="Cash Withdrawal">Cash Withdrawal</option>
                            <option value="Miscellaneous">Miscellaneous</option>
                          </select>
                        </td>
                        <td className="py-2 px-3 text-slate-300 max-w-xs truncate" title={row.description}>
                          {row.description}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-semibold">
                          {formatINR(row.amount, { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {!row.is_valid ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-950 text-rose-300 border border-rose-800/60">
                              Error
                            </span>
                          ) : row.is_duplicate ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-950 text-amber-300 border border-amber-800/60">
                              Duplicate
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800/60">
                              Ready
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Footer actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800 shrink-0">
              <span className="text-slate-400 text-xs">
                Selected: <strong className="text-white">{selectedIndices.size}</strong> transactions to import
              </span>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmImport}
                  disabled={isImporting || selectedIndices.size === 0}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {isImporting ? 'Importing Transactions...' : `Import ${selectedIndices.size} Transactions`}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
