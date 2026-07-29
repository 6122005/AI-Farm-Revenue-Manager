import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SlotRule, ModelMetric } from '../types';
import { Layers, Award, Clock, Save, Users } from 'lucide-react';

export const Settings: React.FC = () => {
  const [slots, setSlots] = useState<SlotRule[]>([]);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [leadRules, setLeadRules] = useState<any[]>([]);
  const [surcharge, setSurcharge] = useState<number>(150);
  const [threshold, setThreshold] = useState<number>(4);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isSavingSettings, setIsSavingSettings] = useState<boolean>(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [sRes, mRes, lrRes, settingsRes] = await Promise.all([
        api.getSlots(),
        api.getModelMetrics(),
        api.getLeadRules(),
        api.getSettings()
      ]);
      setSlots(sRes);
      setMetrics(mRes);
      setLeadRules(lrRes.sort((a, b) => a.min_days - b.min_days));
      
      const surSetting = settingsRes.find(s => s.key === 'guest_surcharge_per_person');
      const threshSetting = settingsRes.find(s => s.key === 'guest_surcharge_threshold');
      if (surSetting) setSurcharge(parseFloat(surSetting.value) || 0);
      if (threshSetting) setThreshold(parseInt(threshSetting.value) || 0);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRuleChange = (index: number, field: string, value: any) => {
    const updated = [...leadRules];
    updated[index] = { ...updated[index], [field]: value };
    setLeadRules(updated);
  };

  const handleSaveLeadRules = async () => {
    setIsSaving(true);
    try {
      await api.updateLeadRules(leadRules);
      alert('Lead Days pricing rules saved successfully!');
      fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to save Lead Days pricing rules.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSettings = async () => {
    setIsSavingSettings(true);
    try {
      await api.updateSettings([
        { key: 'guest_surcharge_per_person', value: surcharge.toString(), description: 'Surcharge amount in ₹ per extra person exceeding baseline capacity.' },
        { key: 'guest_surcharge_threshold', value: threshold.toString(), description: 'Baseline guest count capacity. Surcharges apply to guest counts above this.' }
      ]);
      alert('Guest pricing settings saved successfully!');
      fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to save guest pricing settings.');
    } finally {
      setIsSavingSettings(false);
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

      {/* Lead Days Pricing Adjustment Rules */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-indigo-500" />
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Lead Days Pricing Adjustment Rules</h3>
          </div>
          <button
            onClick={handleSaveLeadRules}
            disabled={isSaving}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{isSaving ? 'Saving...' : 'Save Rules'}</span>
          </button>
        </div>
        <p className="text-xs text-slate-500">Configure business rules to apply markup/discount offsets based on booking lead time (days before stay).</p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                <th className="py-2.5 px-3 w-24">Min Days</th>
                <th className="py-2.5 px-3 w-28">Max Days</th>
                <th className="py-2.5 px-3 w-28">Adjustment (%)</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3 text-center w-24">Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/40">
              {leadRules.map((rule, idx) => (
                <tr key={rule.id || idx}>
                  <td className="py-2.5 px-3">
                    <input
                      type="number"
                      value={rule.min_days}
                      onChange={(e) => handleRuleChange(idx, 'min_days', parseInt(e.target.value) || 0)}
                      className="w-16 px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs text-center"
                    />
                  </td>
                  <td className="py-2.5 px-3">
                    <input
                      type="number"
                      value={rule.max_days}
                      onChange={(e) => handleRuleChange(idx, 'max_days', parseInt(e.target.value) || 0)}
                      className="w-20 px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs text-center"
                    />
                  </td>
                  <td className="py-2.5 px-3">
                    <input
                      type="number"
                      step="0.5"
                      value={rule.adjustment_pct}
                      onChange={(e) => handleRuleChange(idx, 'adjustment_pct', parseFloat(e.target.value) || 0)}
                      className="w-20 px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs text-center font-bold text-indigo-600 dark:text-indigo-400"
                    />
                  </td>
                  <td className="py-2.5 px-3">
                    <input
                      type="text"
                      value={rule.description || ''}
                      onChange={(e) => handleRuleChange(idx, 'description', e.target.value)}
                      placeholder="e.g. Early bird discount"
                      className="w-full max-w-md px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs"
                    />
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <input
                      type="checkbox"
                      checked={rule.is_active}
                      onChange={(e) => handleRuleChange(idx, 'is_active', e.target.checked)}
                      className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Guest Pricing Settings */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-sky-500" />
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Guest Pricing Settings</h3>
          </div>
          <button
            onClick={handleSaveSettings}
            disabled={isSavingSettings}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{isSavingSettings ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
        <p className="text-xs text-slate-500">Configure additional guest charges to prevent price decreases on higher occupancy bookings.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Extra Guest Surcharge (₹ per person)
            </label>
            <input
              type="number"
              value={surcharge}
              onChange={(e) => setSurcharge(parseFloat(e.target.value) || 0)}
              className="w-full max-w-xs px-3 py-1.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-medium"
            />
            <p className="text-[10px] text-slate-400">The surcharge amount charged for each additional guest exceeding the baseline capacity.</p>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Baseline Capacity Threshold (guests count)
            </label>
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(parseInt(e.target.value) || 0)}
              className="w-full max-w-xs px-3 py-1.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-medium"
            />
            <p className="text-[10px] text-slate-400">Surcharge starts accumulating for guest counts exceeding this baseline value.</p>
          </div>
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
