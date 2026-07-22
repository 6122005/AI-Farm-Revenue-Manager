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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboard();
      setData(res);
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
                  <th className="py-2 px-3">Couple Day</th>
                  <th className="py-2 px-3">Couple Night</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {data.demand_heatmap.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-semibold text-slate-700 dark:text-slate-300">{row.day}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        {row['12H_DAY'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        {row['12H_NIGHT'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                        {row['24H_DAY'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                        {row['24H_NIGHT'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-300">
                        {row['COUPLE_DAY'] || row['COUPLE_SLOT'] || 0}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-1 rounded bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300">
                        {row['COUPLE_NIGHT'] || 0}
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

    </div>
  );
};
