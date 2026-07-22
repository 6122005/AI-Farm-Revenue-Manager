import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SlotRule, ModelMetric } from '../types';
import { Layers, Award } from 'lucide-react';

export const Settings: React.FC = () => {
  const [slots, setSlots] = useState<SlotRule[]>([]);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [sRes, mRes] = await Promise.all([
        api.getSlots(),
        api.getModelMetrics()
      ]);
      setSlots(sRes);
      setMetrics(mRes);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Commercial Slot & Model Configurator</h2>
        <p className="text-xs text-slate-500">Configure commercial inventory slots and inspect machine learning model performance.</p>
      </div>

      {/* Commercial Slots Config */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center space-x-2">
          <Layers className="w-5 h-5 text-emerald-500" />
          <h3 className="font-bold text-slate-900 dark:text-white text-base">Configured Commercial Inventory Slots</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {slots.map((slot) => (
            <div key={slot.code} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-sm text-slate-900 dark:text-white">{slot.code}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
                  Active
                </span>
              </div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">{slot.name}</div>
              <p className="text-xs text-slate-500">{slot.description}</p>
              <div className="text-xs text-slate-400 pt-1 border-t border-slate-200 dark:border-slate-800">
                Hours: <span className="font-medium text-slate-600 dark:text-slate-300">{slot.min_hours} - {slot.max_hours} Hrs</span> • Max Guests: <span className="font-medium text-slate-600 dark:text-slate-300">{slot.max_guests}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ML Model Performance Benchmark */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center space-x-2">
          <Award className="w-5 h-5 text-amber-500" />
          <h3 className="font-bold text-slate-900 dark:text-white text-base">Machine Learning Model Validation Benchmark</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                <th className="py-2.5 px-3">Algorithm</th>
                <th className="py-2.5 px-3">R² Score</th>
                <th className="py-2.5 px-3">MAE (₹)</th>
                <th className="py-2.5 px-3">RMSE (₹)</th>
                <th className="py-2.5 px-3">MAPE (%)</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/40">
              {metrics.map((m, idx) => (
                <tr key={idx} className={m.is_champion ? 'bg-emerald-50/50 dark:bg-emerald-950/20 font-semibold' : ''}>
                  <td className="py-3 px-3 font-bold text-slate-800 dark:text-slate-200 flex items-center space-x-2">
                    {m.is_champion && <Award className="w-4 h-4 text-amber-500" />}
                    <span>{m.model_name}</span>
                  </td>
                  <td className="py-3 px-3 font-bold text-emerald-600 dark:text-emerald-400">{(m.r2_score * 100).toFixed(2)}%</td>
                  <td className="py-3 px-3">₹{Math.round(m.mae).toLocaleString()}</td>
                  <td className="py-3 px-3">₹{Math.round(m.rmse).toLocaleString()}</td>
                  <td className="py-3 px-3">{m.mape.toFixed(2)}%</td>
                  <td className="py-3 px-3">
                    {m.is_champion ? (
                      <span className="px-2.5 py-1 rounded-full bg-emerald-500 text-white font-bold text-[10px]">CHAMPION</span>
                    ) : (
                      <span className="text-slate-400">Candidate</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
