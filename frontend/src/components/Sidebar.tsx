import React from 'react';
import { LayoutDashboard, TrendingUp, UploadCloud, History, Settings, ShieldCheck } from 'lucide-react';

export type NavTab = 'dashboard' | 'predict' | 'upload' | 'feedback' | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const items = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'predict' as NavTab, label: 'Price Predictor', icon: TrendingUp },
    { id: 'upload' as NavTab, label: 'Data & Retraining', icon: UploadCloud },
    { id: 'feedback' as NavTab, label: 'Override Audit Logs', icon: History },
    { id: 'settings' as NavTab, label: 'Slot Config & Models', icon: Settings },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-4 min-h-[calc(100vh-4rem)]">
      <nav className="space-y-1.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-xl font-medium text-sm transition-all duration-150 ${
                isActive
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/25 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400 dark:text-slate-500'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Commercial Inventory Reminder */}
      <div className="mt-8 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400">
        <div className="flex items-center space-x-2 font-semibold text-slate-700 dark:text-slate-200 mb-1">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Slot Revenue Logic</span>
        </div>
        <p>Models true commercial inventory slot value. Price/Hour logic is strictly disabled.</p>
      </div>
    </aside>
  );
};
