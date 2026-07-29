import React, { useState } from 'react';
import { api } from '../services/api';
import {
  ShieldAlert,
  Search
} from 'lucide-react';

export const Audit: React.FC = () => {
  const [rowIndex, setRowIndex] = useState<number>(0);
  const [auditData, setAuditData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await api.auditPrediction(rowIndex);
      setAuditData(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to fetch forensic audit.');
      setAuditData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col space-y-2">
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center space-x-2">
          <ShieldAlert className="w-6 h-6 text-emerald-500" />
          <span>Forensic Prediction Audit Log</span>
        </h2>
        <p className="text-sm text-slate-500">
          Inspect, evaluate, and trace the step-by-step decision rules and SHAP attributions for any booking.
        </p>
      </div>

      {/* Row Selector Input */}
      <div className="glass-card p-5 max-w-md">
        <form onSubmit={handleAudit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Select Booking Row Index (0 to 726)
            </label>
            <div className="relative">
              <input
                type="number"
                min={0}
                max={726}
                value={rowIndex}
                onChange={(e) => setRowIndex(parseInt(e.target.value) || 0)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-sm"
                placeholder="Enter booking row index (e.g. 552)"
              />
              <Search className="absolute left-3.5 top-3.5 w-4.5 h-4.5 text-slate-400" />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-500/50 text-white font-bold transition-all text-sm cursor-pointer shadow-lg shadow-emerald-500/20 flex items-center justify-center space-x-2"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <span>Run Forensic Analysis</span>
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-medium">
          ⚠️ {error}
        </div>
      )}

      {/* Forensic Report Display */}
      {auditData && (
        <div className="space-y-6">
          {/* Header Summary */}
          <div className="glass-card p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-l-4 border-emerald-500">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                  Row #{auditData.row_index} Audit Log
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs font-bold text-slate-600 dark:text-slate-300">{auditData.input_features.booking_date}</span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs font-bold text-slate-600 dark:text-slate-300">{auditData.input_features.commercial_slot}</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                Booking Classification: <span className="text-emerald-500">{auditData.classification}</span>
              </h3>
            </div>
            
            {/* Error Classification Badge */}
            <div className={`px-4 py-2 rounded-xl text-xs font-extrabold tracking-wider border ${
              auditData.classification === 'Outlier'
                ? 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/40 dark:border-rose-900 dark:text-rose-400'
                : auditData.classification === 'Business Rule Missing'
                ? 'bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/40 dark:border-amber-900 dark:text-amber-400'
                : 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-400'
            }`}>
              {auditData.classification.toUpperCase()}
            </div>
          </div>

          {/* Pricing KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-card p-4 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Actual Price</span>
              <div className="text-xl font-extrabold text-slate-900 dark:text-white">₹{auditData.actual_price.toLocaleString('en-IN')}</div>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Predicted Price</span>
              <div className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400">₹{auditData.predicted_price.toLocaleString('en-IN')}</div>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Absolute Error</span>
              <div className="text-xl font-extrabold text-rose-500">₹{auditData.abs_error.toLocaleString('en-IN')}</div>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Percentage Error</span>
              <div className="text-xl font-extrabold text-rose-500">{auditData.pct_error.toFixed(1)}%</div>
            </div>
          </div>

          {/* Features and SHAP split */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Feature Values */}
            <div className="glass-card p-5 space-y-4">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Feature values audit</h4>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-500 block">Guests (person_count):</span>
                  <strong className="text-slate-700 dark:text-slate-300">{auditData.input_features.person_count}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Lead Days (lead_days):</span>
                  <strong className="text-slate-700 dark:text-slate-300">{auditData.lead_days} days</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Weekend Status (is_weekend):</span>
                  <strong className="text-slate-700 dark:text-slate-300">{auditData.engineered_features.is_weekend ? 'Weekend' : 'Weekday'}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Festival (festival_name):</span>
                  <strong className="text-slate-700 dark:text-slate-300">{auditData.festival}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Weather (temperature/rain):</span>
                  <strong className="text-slate-700 dark:text-slate-300">
                    {auditData.weather.temperature || 26.0}°C / {auditData.weather.rain_probability || 0}% rain
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Estimated Occupancy:</span>
                  <strong className="text-slate-700 dark:text-slate-300">{auditData.occupancy}%</strong>
                </div>
              </div>
            </div>

            {/* SHAP Contributions */}
            <div className="glass-card p-5 space-y-4">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">SHAP feature contributions</h4>
              <div className="space-y-2">
                {auditData.shap_contributions.map((item: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                    <span className="font-mono text-slate-500">{item.feature}:</span>
                    <span className={`font-bold ${item.impact_amount >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                      ₹{item.impact_amount >= 0 ? '+' : ''}{Math.round(item.impact_amount).toLocaleString('en-IN')}
                    </span>
                  </div>
                ))}
                {auditData.shap_contributions.length === 0 && (
                  <p className="text-xs text-slate-500 italic">No significant SHAP contributions computed for this segment.</p>
                )}
              </div>
            </div>
          </div>

          {/* Historical averages */}
          <div className="glass-card p-5 space-y-4">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Historical pricing segment averages</h4>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 text-center space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Same slot avg</span>
                <strong className="text-sm text-slate-700 dark:text-slate-300">₹{Math.round(auditData.historical_average_slot).toLocaleString('en-IN')}</strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 text-center space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Same month avg</span>
                <strong className="text-sm text-slate-700 dark:text-slate-300">₹{Math.round(auditData.historical_average_month).toLocaleString('en-IN')}</strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 text-center space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Weekend status avg</span>
                <strong className="text-sm text-slate-700 dark:text-slate-300">₹{Math.round(auditData.historical_average_weekend).toLocaleString('en-IN')}</strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 text-center space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Guests count avg</span>
                <strong className="text-sm text-slate-700 dark:text-slate-300">₹{Math.round(auditData.historical_average_guests).toLocaleString('en-IN')}</strong>
              </div>
            </div>
          </div>

          {/* Top 5 Mismatch Reasons */}
          <div className="glass-card p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Top 5 forensic reasons for actual vs. predicted deviation</h4>
            <ul className="list-decimal pl-5 text-xs text-slate-600 dark:text-slate-400 space-y-2">
              {auditData.reasons.map((r: string, idx: number) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          </div>

          {/* Similar bookings */}
          <div className="glass-card p-5 space-y-4">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 font-semibold">Similar bookings match data</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <th className="py-2 px-3">Date</th>
                    <th className="py-2 px-3">Slot</th>
                    <th className="py-2 px-3 text-right">Guests</th>
                    <th className="py-2 px-3 text-right">Lead Days</th>
                    <th className="py-2 px-3 text-right">Selling Price</th>
                    <th className="py-2 px-3 text-center">Similarity Match Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                  {auditData.similar_bookings.map((item: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="py-3 px-3 text-slate-700 dark:text-slate-300 font-semibold">{item.booking_date}</td>
                      <td className="py-3 px-3 text-slate-500">{item.commercial_slot}</td>
                      <td className="py-3 px-3 text-right">{item.person_count}</td>
                      <td className="py-3 px-3 text-right">{item.lead_days}</td>
                      <td className="py-3 px-3 text-right font-extrabold text-slate-800 dark:text-slate-200">
                        ₹{item.selling_price.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="px-2 py-0.5 rounded font-mono font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                          {item.similarity_score}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
