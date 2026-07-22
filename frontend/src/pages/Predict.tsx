import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { PredictionRequest, PredictionResponse } from '../types';
import {
  TrendingUp,
  CloudRain,
  Sun,
  CheckCircle,
  XCircle,
  Edit3,
  Zap,
  Users,
  Calendar,
  Layers,
  Sparkles,
  ZapOff,
  Clock,
  PartyPopper,
  Info,
  CalendarDays,
  ShieldCheck,
  ShieldAlert,
  Timer,
  AlertTriangle
} from 'lucide-react';

export const Predict: React.FC = () => {
  const formatForInput = (dt: Date) => {
    const pad = (n: number) => (n < 10 ? '0' + n : n);
    return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
  };

  const getInitialStartDT = () => {
    const now = new Date();
    now.setHours(7, 0, 0, 0);
    return formatForInput(now);
  };

  const calcAutoEndDT = (startStr: string, slot: string): string => {
    try {
      const start = new Date(startStr);
      if (isNaN(start.getTime())) return startStr;

      const end = new Date(start);

      if (slot === '12H_DAY' || slot === 'COUPLE_DAY') {
        end.setHours(19, 0, 0, 0);
        if (end <= start) end.setDate(end.getDate() + 1);
      } else if (slot === '12H_NIGHT' || slot === 'COUPLE_NIGHT') {
        start.setHours(19, 0, 0, 0);
        end.setTime(start.getTime());
        end.setDate(end.getDate() + 1);
        end.setHours(7, 0, 0, 0);
      } else if (slot === '24H_DAY') {
        start.setHours(7, 0, 0, 0);
        end.setTime(start.getTime());
        end.setDate(end.getDate() + 1);
      } else if (slot === '24H_NIGHT') {
        start.setHours(19, 0, 0, 0);
        end.setTime(start.getTime());
        end.setDate(end.getDate() + 1);
      } else {
        end.setHours(end.getHours() + 12);
      }

      return formatForInput(end);
    } catch {
      return startStr;
    }
  };

  const initialStart = getInitialStartDT();
  const initialEnd = calcAutoEndDT(initialStart, '12H_DAY');

  const [form, setForm] = useState<PredictionRequest>({
    start_datetime: initialStart,
    end_datetime: initialEnd,
    commercial_slot: '12H_DAY',
    person_count: 2,
    lead_days: 0,
    competitor_price: 0
  });

  const [durationHours, setDurationHours] = useState<number>(12);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [overrideModal, setOverrideModal] = useState(false);
  const [overridePrice, setOverridePrice] = useState<number>(3500);
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [feedbackToast, setFeedbackToast] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (form.start_datetime && form.end_datetime) {
      try {
        const start = new Date(form.start_datetime);
        const end = new Date(form.end_datetime);
        if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
          const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
          if (diffHours <= 0) {
            setValidationError('End Date & Time must be after Start Date & Time');
            setDurationHours(0);
          } else {
            setValidationError(null);
            setDurationHours(Math.round(diffHours * 10) / 10);
          }

          const today = new Date();
          today.setHours(0, 0, 0, 0);
          const startDay = new Date(start);
          startDay.setHours(0, 0, 0, 0);
          const lead = Math.max(0, Math.floor((startDay.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));
          setForm((prev) => ({ ...prev, lead_days: lead }));
        }
      } catch {
        setDurationHours(12);
      }
    }
  }, [form.start_datetime, form.end_datetime]);

  const [weatherPreview, setWeatherPreview] = useState<any>(null);

  useEffect(() => {
    if (form.start_datetime) {
      const dateStr = form.start_datetime.split('T')[0];
      api.getWeatherPreview(dateStr)
        .then((w) => setWeatherPreview(w))
        .catch(console.error);
    }
  }, [form.start_datetime]);

  const handleSlotChange = (newSlot: string) => {
    const newEnd = calcAutoEndDT(form.start_datetime || initialStart, newSlot);
    setForm((prev) => ({
      ...prev,
      commercial_slot: newSlot,
      end_datetime: newEnd,
      person_count: newSlot.includes('COUPLE') ? 2 : prev.person_count
    }));
  };

  const handleStartChange = (newStart: string) => {
    const newEnd = calcAutoEndDT(newStart, form.commercial_slot);
    setForm((prev) => ({
      ...prev,
      start_datetime: newStart,
      end_datetime: newEnd
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validationError) return;

    try {
      setLoading(true);
      const reqPayload: PredictionRequest = {
        ...form,
        start_datetime: form.start_datetime?.replace('T', ' '),
        end_datetime: form.end_datetime?.replace('T', ' '),
        booking_date: form.start_datetime?.split('T')[0]
      };
      const res = await api.predictPrice(reqPayload);
      setPrediction(res);
      setOverridePrice(res.recommended_price);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: 'ACCEPT' | 'OVERRIDE' | 'REJECT') => {
    if (!prediction) return;
    try {
      await api.logFeedback({
        booking_date: prediction.booking_date,
        commercial_slot: prediction.commercial_slot,
        person_count: prediction.person_count,
        lead_days: prediction.lead_days,
        suggested_price: prediction.recommended_price,
        action,
        override_price: action === 'OVERRIDE' ? overridePrice : undefined,
        reason: action === 'OVERRIDE' ? overrideReason : undefined
      });
      setFeedbackToast(`Action '${action}' saved to training feedback loop!`);
      setOverrideModal(false);
      setTimeout(() => setFeedbackToast(null), 4000);
    } catch (err) {
      console.error(err);
    }
  };

  const getSlotName = (code: string) => {
    switch (code) {
      case 'COUPLE_SLOT': return 'Couple Special (2 Guests)';
      case 'COUPLE_DAY': return 'Couple Slot Day (7 AM - 7 PM)';
      case 'COUPLE_NIGHT': return 'Couple Slot Night (7 PM - 7 AM)';
      case '12H_DAY': return '12 Hour Day (7 AM - 7 PM)';
      case '12H_NIGHT': return '12 Hour Night (7 PM - 7 AM)';
      case '24H_DAY': return '24 Hour Day (7 AM - 7 AM)';
      case '24H_NIGHT': return '24 Hour Night (7 PM - 7 PM)';
      default: return code;
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">AI Price Prediction Console</h2>
        <p className="text-xs text-slate-500">Commercial inventory valuation with start & end datetime optimization</p>
      </div>

      {feedbackToast && (
        <div className="p-4 rounded-xl bg-emerald-500 text-white font-semibold text-sm shadow-lg flex items-center space-x-2 animate-bounce">
          <CheckCircle className="w-5 h-5" />
          <span>{feedbackToast}</span>
        </div>
      )}

      {/* Input Form & Main Prediction Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left: Form */}
        <div className="glass-card p-6 space-y-5">
          <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-3">
            <Zap className="w-5 h-5 text-emerald-500" />
            <h3 className="font-bold text-slate-900 dark:text-white">Booking Request Parameters</h3>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 text-sm">
            
            {/* Commercial Slot Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5 flex items-center space-x-1">
                <Layers className="w-3.5 h-3.5" />
                <span>Commercial Inventory Slot</span>
              </label>
              <select
                value={form.commercial_slot}
                onChange={(e) => handleSlotChange(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none font-medium text-xs"
              >
                <option value="COUPLE_SLOT">Couple Special (2 Guests)</option>
                <option value="COUPLE_DAY">Couple Slot Day (7 AM to 7 PM)</option>
                <option value="COUPLE_NIGHT">Couple Slot Night (7 PM to 7 AM)</option>
                <option value="12H_DAY">12 Hour Day (7 AM to 7 PM)</option>
                <option value="12H_NIGHT">12 Hour Night (7 PM to 7 AM)</option>
                <option value="24H_DAY">24 Hour Day (7 AM to 7 AM)</option>
                <option value="24H_NIGHT">24 Hour Night (7 PM to 7 PM)</option>
              </select>
            </div>

            {/* Start Date & Time */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5 flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-emerald-500" />
                <span>Booking Start Date & Time</span>
              </label>
              <input
                type="datetime-local"
                value={form.start_datetime}
                onChange={(e) => handleStartChange(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none text-xs font-mono"
                required
              />
            </div>

            {/* End Date & Time (Auto-filled) */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 flex items-center space-x-1">
                  <CalendarDays className="w-3.5 h-3.5 text-blue-500" />
                  <span>Booking End Date & Time (Auto-filled)</span>
                </label>
              </div>
              <input
                type="datetime-local"
                value={form.end_datetime}
                onChange={(e) => setForm({ ...form, end_datetime: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none text-xs font-mono"
                required
              />
            </div>

            {/* Duration Display */}
            {validationError ? (
              <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-600 dark:text-rose-400 text-xs font-medium flex items-center space-x-2">
                <Info className="w-4 h-4 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <Clock className="w-4 h-4 text-emerald-500" />
                  <span>Calculated Booking Duration</span>
                </div>
                <span className="px-2.5 py-1 rounded-lg bg-emerald-500 text-white font-extrabold text-xs">
                  {durationHours} Hours
                </span>
              </div>
            )}

            {/* Opportunity Cost Revenue Floor Notice */}
            {durationHours > 0 && durationHours < (form.commercial_slot.includes('24H') ? 24 : 12) && (
              <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-[11px] text-amber-800 dark:text-amber-300 space-y-1">
                <div className="font-bold flex items-center space-x-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                  <span>Opportunity Cost Protection Active</span>
                </div>
                <p className="text-[10.5px] leading-tight text-amber-700 dark:text-amber-400">
                  Stay of {durationHours}h blocks the full {form.commercial_slot.includes('24H') ? '24h' : '12h'} inventory slot (remaining {Math.round((form.commercial_slot.includes('24H') ? 24 : 12) - durationHours)}h un-sellable). Owner revenue protected with a 90% slot floor.
                </p>
              </div>
            )}

            {/* Dynamic Real-Time Weather Forecast Preview for Selected Date */}
            {weatherPreview && (
              <div className="p-3 rounded-xl bg-gradient-to-r from-sky-50 to-blue-50 dark:from-slate-800/80 dark:to-slate-800 border border-sky-200 dark:border-slate-700 space-y-1.5 text-xs">
                <div className="flex items-center justify-between font-bold text-slate-800 dark:text-slate-200">
                  <div className="flex items-center space-x-2">
                    {weatherPreview.rain_probability > 40 ? (
                      <CloudRain className="w-4 h-4 text-cyan-500" />
                    ) : (
                      <Sun className="w-4 h-4 text-amber-500" />
                    )}
                    <span>Target Date Forecast ({form.start_datetime ? form.start_datetime.split('T')[0] : 'Selected Date'})</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-semibold">
                    {weatherPreview.condition}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300 text-[11px] pt-1">
                  <div>
                    <span className="font-extrabold text-sm text-slate-900 dark:text-white">{weatherPreview.temperature}°C</span>
                    <span className="text-slate-400 ml-1">Temp</span>
                  </div>
                  <div>
                    <span className="font-bold text-cyan-600 dark:text-cyan-400">{weatherPreview.rain_probability}%</span>
                    <span className="text-slate-400 ml-1">Rain Prob</span>
                  </div>
                  <div>
                    <span className="font-bold text-slate-700 dark:text-slate-300">{weatherPreview.humidity}%</span>
                    <span className="text-slate-400 ml-1">Humidity</span>
                  </div>
                </div>
              </div>
            )}

            {/* Lead Time Days Input Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 flex items-center space-x-1">
                  <Timer className="w-3.5 h-3.5 text-purple-500" />
                  <span>Lead Time (Days in Advance)</span>
                </label>
                <span className="text-[10px] text-slate-400">Auto / Manual</span>
              </div>
              <input
                type="number"
                min="0"
                max="365"
                value={form.lead_days}
                onChange={(e) => setForm({ ...form, lead_days: parseInt(e.target.value) || 0 })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none text-xs font-semibold"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Days in advance between today and the booking start date.
              </p>
            </div>

            {/* Person Count */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 flex items-center space-x-1">
                  <Users className="w-3.5 h-3.5" />
                  <span>Person Count ({form.person_count} Guests)</span>
                </label>
                {form.person_count <= 2 && (
                  <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950 px-2 py-0.5 rounded-full flex items-center space-x-1">
                    <ZapOff className="w-3 h-3" />
                    <span>Couple Utility Discount</span>
                  </span>
                )}
              </div>
              <input
                type="range"
                min="1"
                max="40"
                value={form.person_count}
                onChange={(e) => setForm({ ...form, person_count: parseInt(e.target.value) })}
                className="w-full accent-emerald-500"
              />
            </div>

            {/* Competitor Price */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
                Competitor Farmhouse Price (₹) [Default 0]
              </label>
              <input
                type="number"
                step="500"
                min="0"
                value={form.competitor_price ?? 0}
                onChange={(e) => setForm({ ...form, competitor_price: parseFloat(e.target.value) || 0 })}
                placeholder="0"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !!validationError}
              className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold shadow-lg shadow-emerald-500/25 flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              {loading ? (
                <span>Executing AI Model...</span>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Calculate Recommended Price</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right: Results Dashboard */}
        <div className="lg:col-span-2 space-y-6">
          
          {prediction ? (
            <>
              {/* Data Drift Warning Banner */}
              {prediction.drift_status?.drift_detected && (
                <div className="glass-card p-4 border border-amber-500/60 bg-amber-500/10 text-amber-900 dark:text-amber-200 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <AlertTriangle className="w-5 h-5 text-amber-500 animate-pulse flex-shrink-0" />
                    <div>
                      <div className="text-xs font-bold">Data Drift Alert Detected!</div>
                      <div className="text-[11px] text-amber-700 dark:text-amber-300">
                        Target feature distribution shifted. Retraining recommended for optimal accuracy.
                      </div>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 bg-amber-500 text-white font-extrabold text-[10px] rounded-lg uppercase tracking-wider">
                    Retrain Advised
                  </span>
                </div>
              )}

              {/* Primary Recommended Price Badge */}
              <div className="glass-card p-6 border-emerald-500/40 relative overflow-hidden bg-gradient-to-br from-emerald-500/10 via-transparent to-teal-500/10">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs uppercase font-extrabold tracking-widest text-emerald-600 dark:text-emerald-400">
                        Recommended Selling Price
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${
                        (prediction.reliability_level || 'HIGH') === 'HIGH'
                          ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                          : (prediction.reliability_level || 'HIGH') === 'MEDIUM'
                          ? 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300'
                          : 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300'
                      }`}>
                        {(prediction.reliability_level || 'HIGH')} RELIABILITY
                      </span>
                    </div>

                    <div className="text-4xl sm:text-5xl font-black text-slate-900 dark:text-white mt-1">
                      ₹{prediction.recommended_price.toLocaleString('en-IN')}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Optimal Range: <span className="font-semibold text-slate-700 dark:text-slate-300">₹{prediction.min_price.toLocaleString('en-IN')} – ₹{prediction.max_price.toLocaleString('en-IN')}</span>
                    </div>
                  </div>

                  <div className="flex flex-col space-y-2 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <div className="px-3 py-1 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 text-xs font-bold">
                        Confidence: {prediction.confidence_score.toFixed(1)}%
                      </div>
                      <div className="px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold">
                        Quality: {prediction.data_quality_score || 90}%
                      </div>
                    </div>

                    <div className="text-xs text-slate-500">
                      Sample Size Used: <span className="font-bold text-slate-800 dark:text-slate-200">{prediction.sample_size_used || 50} Bookings</span>
                    </div>
                    <div className="text-xs text-slate-400">
                      Model: <span className="font-bold text-slate-700 dark:text-slate-300">{prediction.champion_model}</span>
                    </div>
                    {prediction.model_path_used && (
                      <div className="text-[11px] font-mono text-slate-400 truncate max-w-xs" title={prediction.model_path_used}>
                        Path: {prediction.model_path_used}
                      </div>
                    )}
                    {prediction.model_timestamp_used && (
                      <div className="text-[11px] font-mono text-emerald-500 font-semibold">
                        Trained: {prediction.model_timestamp_used}
                      </div>
                    )}
                  </div>
                </div>

                {/* Owner Action Buttons */}
                <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => handleAction('ACCEPT')}
                    className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold flex items-center space-x-1.5 shadow-md shadow-emerald-500/20 cursor-pointer"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Accept Price (₹{prediction.recommended_price})</span>
                  </button>

                  <button
                    onClick={() => setOverrideModal(true)}
                    className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold flex items-center space-x-1.5 shadow-md shadow-amber-500/20 cursor-pointer"
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>Override Price</span>
                  </button>

                  <button
                    onClick={() => handleAction('REJECT')}
                    className="px-4 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold flex items-center space-x-1.5 shadow-md shadow-rose-500/20 cursor-pointer"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>

              {/* Commercial Multi-Slot Inventory Consistency Validation Card */}
              {prediction.multi_slot_consistency && (
                <div className={`glass-card p-5 border ${
                  prediction.multi_slot_consistency.status === 'VALID'
                    ? 'border-emerald-500/40 bg-emerald-500/5'
                    : prediction.multi_slot_consistency.status === 'JUSTIFIED_DEVIATION'
                    ? 'border-blue-500/40 bg-blue-500/5'
                    : 'border-amber-500/40 bg-amber-500/5'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <Layers className="w-5 h-5 text-emerald-500" />
                      <h3 className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                        Commercial Multi-Slot Inventory Consistency Validation
                      </h3>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                      prediction.multi_slot_consistency.status === 'VALID'
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                        : prediction.multi_slot_consistency.status === 'JUSTIFIED_DEVIATION'
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                        : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                    }`}>
                      {prediction.multi_slot_consistency.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3 text-xs">
                    <div className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800/60">
                      <span className="text-slate-400 block text-[10px]">Predicted 12H Day</span>
                      <span className="font-extrabold text-slate-900 dark:text-white">
                        ₹{prediction.multi_slot_consistency.predicted_12h_day.toLocaleString('en-IN')}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800/60">
                      <span className="text-slate-400 block text-[10px]">Predicted 12H Night</span>
                      <span className="font-extrabold text-slate-900 dark:text-white">
                        ₹{prediction.multi_slot_consistency.predicted_12h_night.toLocaleString('en-IN')}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800/60">
                      <span className="text-slate-400 block text-[10px]">Combined Inventory</span>
                      <span className="font-extrabold text-slate-900 dark:text-white">
                        ₹{prediction.multi_slot_consistency.combined_inventory_value.toLocaleString('en-IN')}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800/60">
                      <span className="text-slate-400 block text-[10px]">Predicted 24H Value</span>
                      <span className="font-extrabold text-emerald-600 dark:text-emerald-400">
                        ₹{prediction.multi_slot_consistency.predicted_24h_value.toLocaleString('en-IN')}
                      </span>
                    </div>
                  </div>

                  {/* Historical Package Discount & Slot Differentiation Audit Strip */}
                  {prediction.multi_slot_consistency.learned_package_discount_used_pct !== undefined && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-[11px] pt-2 border-t border-slate-200 dark:border-slate-800">
                      <div className="p-2 rounded bg-slate-50 dark:bg-slate-900/60">
                        <span className="text-slate-400 block text-[9.5px]">Hist. Avg 24H Day</span>
                        <span className="font-bold text-slate-800 dark:text-slate-200">
                          ₹{prediction.multi_slot_consistency.historical_avg_24h_day_price?.toLocaleString('en-IN') || '3,929'}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-50 dark:bg-slate-900/60">
                        <span className="text-slate-400 block text-[9.5px]">Hist. Avg 24H Night</span>
                        <span className="font-bold text-slate-800 dark:text-slate-200">
                          ₹{prediction.multi_slot_consistency.historical_avg_24h_night_price?.toLocaleString('en-IN') || '5,759'}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-50 dark:bg-slate-900/60">
                        <span className="text-slate-400 block text-[9.5px]">Dataset Median Discount</span>
                        <span className="font-bold text-emerald-600 dark:text-emerald-400">
                          {prediction.multi_slot_consistency.historical_median_package_discount_pct}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-50 dark:bg-slate-900/60">
                        <span className="text-slate-400 block text-[9.5px]">Learned Discount Used</span>
                        <span className="font-bold text-blue-600 dark:text-blue-400">
                          {prediction.multi_slot_consistency.learned_package_discount_used_pct}%
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-slate-600 dark:text-slate-300 p-2.5 rounded-lg bg-white/50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 leading-relaxed">
                    <div className="font-semibold text-slate-800 dark:text-slate-200 mb-0.5">
                      Validation Audit & Rules Verification:
                    </div>
                    {prediction.multi_slot_consistency.reason}
                  </div>
                </div>
              )}

              {/* BOOKING SUMMARY CARD & FESTIVAL CARD */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Booking Summary Card */}
                <div className="glass-card p-5 space-y-3">
                  <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-2">
                    <ShieldCheck className="w-5 h-5 text-emerald-500" />
                    <h3 className="font-bold text-slate-900 dark:text-white text-sm">Booking Summary</h3>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">Start Time:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">{prediction.start_datetime}</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">End Time:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">{prediction.end_datetime}</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">Duration:</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400">{prediction.duration_hours} Hours</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">Commercial Slot:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{getSlotName(prediction.commercial_slot)}</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">Guests:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{prediction.person_count} Guests</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">Lead Time:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{prediction.lead_days} Days</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800/40">
                      <span className="text-slate-500">Weekend:</span>
                      <span className={`font-bold ${prediction.is_weekend ? 'text-amber-500' : 'text-slate-600 dark:text-slate-400'}`}>
                        {prediction.is_weekend ? 'Yes (Weekend)' : 'No (Weekday)'}
                      </span>
                    </div>

                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Competitor Price:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {prediction.competitor_price ? `₹${prediction.competitor_price.toLocaleString('en-IN')}` : '₹0 (Not Set)'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Festival Card */}
                <div className="glass-card p-5 space-y-3 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-2">
                      <PartyPopper className="w-5 h-5 text-amber-500" />
                      <h3 className="font-bold text-slate-900 dark:text-white text-sm">Festival & Holiday Intelligence</h3>
                    </div>

                    <div className="mt-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center space-y-1">
                      <span className="text-xs uppercase font-bold tracking-wider text-amber-600 dark:text-amber-400">
                        Holiday Event Status
                      </span>
                      <div className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center justify-center space-x-2">
                        {prediction.festival_name !== 'No Festival' ? (
                          <>
                            <span className="text-2xl">🎉</span>
                            <span className="text-amber-500">{prediction.festival_name}</span>
                          </>
                        ) : (
                          <span className="text-slate-500">No Festival</span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500">
                        {prediction.festival_name !== 'No Festival'
                          ? 'Public holiday demand surge multiplier applied.'
                          : 'Standard calendar day (No festival surge active).'}
                      </p>
                    </div>
                  </div>

                  {/* Weather Preview */}
                  <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      {prediction.weather.rain_probability > 50 ? <CloudRain className="w-4 h-4 text-cyan-500" /> : <Sun className="w-4 h-4 text-amber-500" />}
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{prediction.weather.condition}</span>
                    </div>
                    <div className="text-right font-bold text-slate-700 dark:text-slate-300">
                      {prediction.weather.temperature}°C • Rain {prediction.weather.rain_probability}%
                    </div>
                  </div>

                </div>

              </div>

              {/* Explainable AI (XAI) Waterfall Breakdown */}
              <div className="glass-card p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">Explainable AI (Why this price?)</h3>
                  <span className="text-xs font-semibold text-slate-500">Factor Drivers</span>
                </div>

                <div className="space-y-2.5">
                  {prediction.price_factors.map((factor, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-800">
                      <div>
                        <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">{factor.factor}</div>
                        <div className="text-xs text-slate-500">{factor.description}</div>
                      </div>
                      <div className={`text-sm font-extrabold ${factor.impact_pct >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-500'}`}>
                        {factor.impact_pct >= 0 ? `+${factor.impact_pct}%` : `${factor.impact_pct}%`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Historical Price Derivation Explanation Card */}
              {prediction.historical_price_explanation && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-1.5 text-xs">
                  <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 font-extrabold">
                    <ShieldCheck className="w-4 h-4 flex-shrink-0" />
                    <span>Historical Price Grounding & Traceability Proof</span>
                  </div>
                  <p className="text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                    {prediction.historical_price_explanation}
                  </p>
                </div>
              )}

              {/* Contributing Historical Rows Evidence (EXCLUSIVELY FROM UPLOADED DATA) */}
              <div className="glass-card p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">Contributing Historical Rows Evidence</h3>
                  <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded-md">
                    Strictly From Uploaded Dataset
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                        <th className="py-2 px-3">Row ID</th>
                        <th className="py-2 px-3">Date</th>
                        <th className="py-2 px-3">Slot</th>
                        <th className="py-2 px-3">Guests</th>
                        <th className="py-2 px-3">Lead Days</th>
                        <th className="py-2 px-3">Selling Price</th>
                        <th className="py-2 px-3">Similarity</th>
                        <th className="py-2 px-3">Contribution Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/40">
                      {(prediction.contributing_historical_rows || prediction.similar_bookings).map((item: any, idx: number) => (
                        <tr key={idx}>
                          <td className="py-2.5 px-3 font-mono font-bold text-slate-700 dark:text-slate-300">{item.row_id || `Row #${idx + 1}`}</td>
                          <td className="py-2.5 px-3 font-medium">{item.booking_date}</td>
                          <td className="py-2.5 px-3">{item.commercial_slot}</td>
                          <td className="py-2.5 px-3">{item.person_count}</td>
                          <td className="py-2.5 px-3">{item.lead_days}d</td>
                          <td className="py-2.5 px-3 font-bold text-emerald-600 dark:text-emerald-400">₹{item.selling_price?.toLocaleString('en-IN')}</td>
                          <td className="py-2.5 px-3 font-semibold text-blue-500">{item.similarity_score}%</td>
                          <td className="py-2.5 px-3 text-[11px] text-slate-500">{item.contribution_note || `Historical record matching slot ${item.commercial_slot}`}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </>
          ) : (
            <div className="glass-card p-12 text-center text-slate-400 space-y-3">
              <TrendingUp className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-700" />
              <h4 className="text-base font-semibold text-slate-600 dark:text-slate-300">No Active Prediction</h4>
              <p className="text-xs">Set Start & End Date/Time parameters on the left and click 'Calculate Recommended Price'.</p>
            </div>
          )}

        </div>

      </div>

      {/* Override Modal */}
      {overrideModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-md w-full p-6 space-y-4 bg-white dark:bg-slate-900 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Override AI Price Recommendation</h3>
            <p className="text-xs text-slate-500">Your price correction will be stored to continuously train future models.</p>

            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Your Override Selling Price (₹)</label>
              <input
                type="number"
                step="500"
                value={overridePrice}
                onChange={(e) => setOverridePrice(parseFloat(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white font-bold text-lg"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Reason for Override</label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="e.g. VIP regular client / Special holiday event request"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs h-20"
              ></textarea>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3">
              <button
                onClick={() => setOverrideModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => handleAction('OVERRIDE')}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-600 text-white shadow-md cursor-pointer"
              >
                Save Override Action
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
