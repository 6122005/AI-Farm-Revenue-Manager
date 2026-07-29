import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { DashboardSummary } from '../types';
import {
  IndianRupee,
  CalendarCheck,
  Percent,
  TrendingUp,
  Award,
  Sparkles,
  Flame,
  Clock,
  Users,
  UploadCloud,
  FileSpreadsheet
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [valData, setValData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboard();
      setData(res);
      const valRes = await api.getValidationDashboard();
      setValData(valRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-medium text-slate-500">Loading Revenue Engine Analytics...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  // Empty State when user has not uploaded any dataset file yet
  if (data.has_data === false) {
    return (
      <div className="space-y-6">
        
        {/* Banner */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 text-white relative overflow-hidden shadow-xl">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-xs tracking-wider uppercase mb-1">
                <Sparkles className="w-4 h-4" />
                <span>Commercial Revenue Optimization Engine</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold">Farmhouse Revenue Command Center</h2>
              <p className="text-slate-300 text-sm mt-1 max-w-xl">
                Awaiting historical Excel dataset upload to calculate custom revenue yield analytics.
              </p>
            </div>
          </div>
        </div>

        {/* Empty State Action Card */}
        <div className="glass-card p-12 text-center max-w-2xl mx-auto space-y-5 my-8">
          <div className="w-20 h-20 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto shadow-inner">
            <UploadCloud className="w-10 h-10" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">No Dataset Uploaded Yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mt-2">
              Upload your historical farmhouse booking Excel or CSV dataset. The AI engine will train models exclusively on your uploaded data and generate custom revenue analytics here.
            </p>
          </div>

          <div className="pt-3">
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('switch-tab', { detail: 'upload' }));
              }}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold shadow-lg shadow-emerald-500/25 transition-all text-sm cursor-pointer"
            >
              <FileSpreadsheet className="w-5 h-5" />
              <span>Upload Booking Dataset (Excel/CSV)</span>
            </button>
          </div>
        </div>

      </div>
    );
  }

  const PIE_COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4', '#14b8a6'];

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 text-white relative overflow-hidden shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-xs tracking-wider uppercase mb-1">
              <Sparkles className="w-4 h-4" />
              <span>Commercial Revenue Optimization Engine</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold">Farmhouse Revenue Command Center</h2>
            <p className="text-slate-300 text-sm mt-1 max-w-xl">
              Predicting maximum yield per commercial slot with machine learning champion models trained on your uploaded dataset.
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex items-center space-x-3 bg-white/10 backdrop-blur-md px-4 py-2.5 rounded-xl border border-white/10">
            <Award className="w-6 h-6 text-amber-400" />
            <div>
              <div className="text-xs text-slate-300">Champion Model</div>
              <div className="text-sm font-bold text-white">{data.champion_model} (R² = {(data.champion_r2 * 100).toFixed(1)}%)</div>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: Revenue */}
        <div className="glass-card p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <IndianRupee className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Revenue</span>
            <div className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">
              ₹{data.total_revenue.toLocaleString('en-IN')}
            </div>
          </div>
        </div>

        {/* Card 2: Bookings */}
        <div className="glass-card p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <CalendarCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Bookings</span>
            <div className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">
              {data.total_bookings} Slots
            </div>
          </div>
        </div>

        {/* Card 3: Average Price */}
        <div className="glass-card p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-violet-100 dark:bg-violet-950/60 text-violet-600 dark:text-violet-400 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Selling Price</span>
            <div className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">
              ₹{Math.round(data.average_price).toLocaleString('en-IN')}
            </div>
          </div>
        </div>

        {/* Card 4: Occupancy & Peak */}
        <div className="glass-card p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <Percent className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Occupancy Rate</span>
            <div className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">
              {data.occupancy_rate}%
            </div>
          </div>
        </div>

      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Monthly Revenue Chart */}
        <div className="glass-card p-5 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Monthly Revenue Breakdown</h3>
              <p className="text-xs text-slate-500">Historical performance by month</p>
            </div>
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-2.5 py-1 rounded-md">
              Peak: {data.peak_month}
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.monthly_revenue}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `₹${v / 1000}k`} />
                <Tooltip
                  formatter={(value: any) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']}
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }}
                />
                <Bar dataKey="revenue" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Slot Utilization Pie */}
        <div className="glass-card p-5 space-y-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Commercial Slot Distribution</h3>
            <p className="text-xs text-slate-500">Revenue contribution per inventory slot</p>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.slot_utilization}
                  dataKey="revenue"
                  nameKey="slot"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {data.slot_utilization.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']}
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Demand Heatmap & Top Revenue Days */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Heatmap */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center space-x-2">
            <Flame className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Demand Heatmap (Day vs Slot)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                  <th className="py-2 px-3">Day</th>
                  <th className="py-2 px-3">12H Day</th>
                  <th className="py-2 px-3">12H Night</th>
                  <th className="py-2 px-3">24H Day</th>
                  <th className="py-2 px-3">24H Night</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {data.demand_heatmap.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-semibold text-slate-700 dark:text-slate-300">{row.day}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        {row['12H Day'] || row['12H_DAY'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        {row['12H Night'] || row['12H_NIGHT'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                        {row['24H Day'] || row['24H_DAY'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                        {row['24H Night'] || row['24H_NIGHT'] || 0}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Revenue Days */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-emerald-500" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Top Historical Yield Bookings</h3>
          </div>
          <div className="space-y-3">
            {data.top_revenue_days.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800">
                <div>
                  <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{item.date}</div>
                  <div className="text-xs text-slate-500 flex items-center space-x-2 mt-0.5">
                    <span>{item.slot}</span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <Users className="w-3 h-3 text-slate-400" />
                      <span>{item.guests} Guests</span>
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-base font-extrabold text-emerald-600 dark:text-emerald-400">
                    ₹{item.price.toLocaleString('en-IN')}
                  </div>
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Commercial Slot</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* 🚀 Production Validation Command Center */}
      {valData && (
        <div className="space-y-6 pt-6 border-t border-slate-200 dark:border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
            <div>
              <h3 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-emerald-500" />
                <span>Production Validation & Usage Analytics</span>
              </h3>
              <p className="text-xs text-slate-500">Live operational metrics measured against real owner decisions</p>
            </div>
            
            {/* Retraining Recommendation Badge */}
            <div className={`px-4 py-2 rounded-xl border flex items-center space-x-2 text-xs font-bold ${
              valData.retraining_recommendation 
                ? 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/40 dark:border-rose-900 dark:text-rose-400' 
                : 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-400'
            }`}>
              <span className={`w-2.5 h-2.5 rounded-full ${valData.retraining_recommendation ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'}`}></span>
              <span>{valData.retraining_recommendation ? "Retraining Recommended" : "Model Status Stable"}</span>
            </div>
          </div>

          {/* Retraining Info Banner */}
          <div className={`p-4 rounded-xl text-xs ${
            valData.retraining_recommendation 
              ? 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20' 
              : 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20'
          }`}>
            <strong>Status Check:</strong> {valData.retraining_reason}
          </div>

          {/* Validation KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* KPI 1: AI vs Owner Avg Price */}
            <div className="glass-card p-4 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">AI vs Owner Avg Price</span>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl font-extrabold text-slate-900 dark:text-white">₹{Math.round(valData.ai_avg_price).toLocaleString('en-IN')}</span>
                <span className="text-xs text-slate-400">/</span>
                <span className="text-base font-bold text-emerald-600 dark:text-emerald-400">₹{Math.round(valData.owner_avg_price).toLocaleString('en-IN')}</span>
              </div>
              <p className="text-[10px] text-slate-400">AI price recommendations compared with owner final bookings</p>
            </div>

            {/* KPI 2: Revenue Delta */}
            <div className="glass-card p-4 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Yield Revenue Difference</span>
              <div className="flex items-center space-x-1.5 text-xl font-extrabold text-emerald-600 dark:text-emerald-400">
                <TrendingUp className="w-5 h-5" />
                <span>₹{valData.revenue_diff.toLocaleString('en-IN')}</span>
              </div>
              <p className="text-[10px] text-slate-400">Revenue difference due to manual pricing overrides</p>
            </div>

            {/* KPI 3: Acceptance & Override Rates */}
            <div className="glass-card p-4 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Acceptance vs Override</span>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl font-extrabold text-blue-600 dark:text-blue-400">{valData.acceptance_rate.toFixed(1)}%</span>
                <span className="text-xs text-slate-400">/</span>
                <span className="text-base font-bold text-amber-600 dark:text-amber-400">{valData.override_rate.toFixed(1)}%</span>
              </div>
              <p className="text-[10px] text-slate-400">Rate of owner acceptance vs. custom manual price overrides</p>
            </div>

            {/* KPI 4: Prediction Confidence Accuracy */}
            <div className="glass-card p-4 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Decision Match Accuracy</span>
              <div className="text-xl font-extrabold text-purple-600 dark:text-purple-400">
                {valData.confidence_accuracy.toFixed(1)}%
              </div>
              <p className="text-[10px] text-slate-400">Mean directional match score between AI and owner prices</p>
            </div>

          </div>

          {/* Error Performance & Drift Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* MAE Performance */}
            <div className="glass-card p-5 space-y-3 lg:col-span-2">
              <div>
                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Real-world Prediction Errors (MAE)</h4>
                <p className="text-[10px] text-slate-500">Live mean absolute error across daily, weekly, and monthly scopes</p>
              </div>
              
              <div className="grid grid-cols-3 gap-4 pt-2">
                <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                  <div className="text-xs text-slate-400 font-mono">Daily MAE</div>
                  <div className="text-base font-bold text-slate-800 dark:text-slate-200 mt-1">₹{Math.round(valData.daily_mae).toLocaleString('en-IN')}</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                  <div className="text-xs text-slate-400 font-mono">Weekly MAE</div>
                  <div className="text-base font-bold text-slate-800 dark:text-slate-200 mt-1">₹{Math.round(valData.weekly_mae).toLocaleString('en-IN')}</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                  <div className="text-xs text-slate-400 font-mono">Monthly MAE</div>
                  <div className="text-base font-bold text-slate-800 dark:text-slate-200 mt-1">₹{Math.round(valData.monthly_mae).toLocaleString('en-IN')}</div>
                </div>
              </div>
            </div>

            {/* Drift Detector Card */}
            <div className="glass-card p-5 space-y-3">
              <div>
                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Model Drift Detection</h4>
                <p className="text-[10px] text-slate-500">Statistical check comparing AI recommendations and actual pricing</p>
              </div>
              
              <div className="pt-2 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-mono">Deviation Score:</span>
                  <span className={`text-xs font-bold ${valData.drift_detected ? 'text-rose-500' : 'text-emerald-500'}`}>
                    {valData.drift_score.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-mono">Drift Status:</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    valData.drift_detected 
                      ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' 
                      : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                  }`}>
                    {valData.drift_detected ? "DRIFT_DETECTED" : "DATASET_STABLE"}
                  </span>
                </div>
              </div>
            </div>

          </div>

          {/* Validation Feedback List */}
          <div className="glass-card p-5 space-y-4">
            <div>
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Owner Decision Audit Trail</h4>
              <p className="text-[10px] text-slate-500">List of latest decisions logged for validation and retraining</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <th className="py-2 px-3">Date</th>
                    <th className="py-2 px-3">Slot</th>
                    <th className="py-2 px-3 text-right">AI Suggested Price</th>
                    <th className="py-2 px-3 text-right">Owner Price</th>
                    <th className="py-2 px-3 text-center">Action</th>
                    <th className="py-2 px-3">Explanation Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                  {valData.overrides.slice(0, 5).map((fb: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="py-3 px-3 text-slate-700 dark:text-slate-300 font-semibold">{fb.date}</td>
                      <td className="py-3 px-3 text-slate-500">{fb.slot}</td>
                      <td className="py-3 px-3 text-right text-slate-500 font-mono">₹{fb.suggested.toLocaleString('en-IN')}</td>
                      <td className="py-3 px-3 text-right font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        ₹{fb.final.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wider ${
                          fb.action === 'ACCEPT' 
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                            : fb.action === 'OVERRIDE'
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                            : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                        }`}>
                          {fb.action}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-500 italic max-w-xs truncate">{fb.reason}</td>
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
