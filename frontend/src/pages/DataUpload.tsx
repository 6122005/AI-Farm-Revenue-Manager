import React, { useState } from 'react';
import { api } from '../services/api';
import { UploadCloud, FileSpreadsheet, Download, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export const DataUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setUploading(true);
      setError(null);
      const res = await api.uploadDataset(file);
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and process file.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Dataset Upload & Model Retraining</h2>
        <p className="text-xs text-slate-500">Upload historical farmhouse booking Excel file to auto-train champion ML models.</p>
      </div>

      {/* Download Sample Excel Template */}
      <div className="glass-card p-5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <FileSpreadsheet className="w-8 h-8 text-emerald-500" />
          <div>
            <h4 className="font-bold text-sm text-slate-900 dark:text-white">Download Farm Booking Data Excel Sample</h4>
            <p className="text-xs text-slate-500">Includes mandatory fields: Booking Date, Commercial Slot, Guest Count, Selling Price.</p>
          </div>
        </div>
        <a
          href={api.getSampleExcelUrl()}
          download
          className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs flex items-center space-x-2 transition-all"
        >
          <Download className="w-4 h-4" />
          <span>Download Sample</span>
        </a>
      </div>

      {/* Upload Zone */}
      <div className="glass-card p-8 text-center border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-emerald-500 transition-all space-y-4">
        <UploadCloud className="w-12 h-12 mx-auto text-emerald-500" />
        <div>
          <h3 className="font-bold text-slate-900 dark:text-white text-base">Drag and Drop Excel Dataset Here</h3>
          <p className="text-xs text-slate-500 mt-1">Supports .xlsx, .xls, and .csv files.</p>
        </div>

        <div className="flex items-center justify-center space-x-3">
          <label className="cursor-pointer px-4 py-2 rounded-xl bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs font-bold hover:opacity-90 transition-all">
            Browse File
            <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileChange} className="hidden" />
          </label>
          {file && (
            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
              Selected: {file.name}
            </span>
          )}
        </div>

        {file && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full max-w-xs mx-auto py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm shadow-md shadow-emerald-500/20 flex items-center justify-center space-x-2"
          >
            {uploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Cleaning & Training ML Models...</span>
              </>
            ) : (
              <span>Process & Train Champion Model</span>
            )}
          </button>
        )}
      </div>

      {/* Result Status */}
      {result && (
        <div className="glass-card p-6 border-emerald-500/50 space-y-3 bg-emerald-50/50 dark:bg-emerald-950/20">
          <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 font-bold">
            <CheckCircle2 className="w-5 h-5" />
            <span>Automated Dataset Pipeline & Training Complete!</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">{result.message}</p>
          <div className="grid grid-cols-3 gap-3 pt-2 text-center text-xs">
            <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-slate-400 block">Records Processed</span>
              <span className="font-bold text-slate-800 dark:text-white text-base">{result.record_count}</span>
            </div>
            <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-slate-400 block">Selected Champion</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400 text-base">{result.champion_model}</span>
            </div>
            <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-slate-400 block">R² Score</span>
              <span className="font-bold text-slate-800 dark:text-white text-base">{(result.r2_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

    </div>
  );
};
