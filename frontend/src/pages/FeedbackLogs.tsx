import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { OwnerFeedbackItem } from '../types';
import { History, CheckCircle, Edit3, XCircle } from 'lucide-react';

export const FeedbackLogs: React.FC = () => {
  const [logs, setLogs] = useState<OwnerFeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getFeedbackHistory();
      setLogs(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Owner Decision Audit Trail</h2>
        <p className="text-xs text-slate-500">Historical feedback loop storing owner acceptances, overrides, and rejections.</p>
      </div>

      <div className="glass-card p-5">
        {loading ? (
          <div className="text-center py-8 text-xs text-slate-500">Loading audit history...</div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-slate-400 space-y-2">
            <History className="w-10 h-10 mx-auto text-slate-300" />
            <p className="text-xs">No owner pricing actions logged yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Slot</th>
                  <th className="py-2.5 px-3">Guests</th>
                  <th className="py-2.5 px-3">Suggested Price</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Override Price</th>
                  <th className="py-2.5 px-3">Reason / Context</th>
                  <th className="py-2.5 px-3">Logged At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/40">
                {logs.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-3 font-medium">{item.booking_date}</td>
                    <td className="py-3 px-3 font-semibold">{item.commercial_slot}</td>
                    <td className="py-3 px-3">{item.person_count}</td>
                    <td className="py-3 px-3 font-bold text-slate-800 dark:text-slate-200">₹{item.suggested_price.toLocaleString('en-IN')}</td>
                    <td className="py-3 px-3">
                      {item.action === 'ACCEPT' && (
                        <span className="px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-bold flex items-center space-x-1 w-max">
                          <CheckCircle className="w-3 h-3" />
                          <span>ACCEPT</span>
                        </span>
                      )}
                      {item.action === 'OVERRIDE' && (
                        <span className="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-bold flex items-center space-x-1 w-max">
                          <Edit3 className="w-3 h-3" />
                          <span>OVERRIDE</span>
                        </span>
                      )}
                      {item.action === 'REJECT' && (
                        <span className="px-2.5 py-1 rounded-full bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 font-bold flex items-center space-x-1 w-max">
                          <XCircle className="w-3 h-3" />
                          <span>REJECT</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-bold text-emerald-600 dark:text-emerald-400">
                      {item.override_price ? `₹${item.override_price.toLocaleString('en-IN')}` : '-'}
                    </td>
                    <td className="py-3 px-3 text-slate-500 max-w-xs truncate">{item.reason || '-'}</td>
                    <td className="py-3 px-3 text-slate-400">{new Date(item.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};
