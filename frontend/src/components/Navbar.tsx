import React from 'react';
import { Sun, Moon, Sparkles, MapPin, Activity } from 'lucide-react';

interface NavbarProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ darkMode, setDarkMode }) => {
  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text tracking-tight">
              Farmhouse AI <span className="text-slate-900 dark:text-white font-medium text-base">Revenue Manager</span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Commercial Slot Engine v2.0</p>
          </div>
        </div>

        {/* Right Info Controls */}
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-600 dark:text-slate-300">
            <MapPin className="w-3.5 h-3.5 text-emerald-500" />
            <span>Lonavala Farmhouse Cluster</span>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 text-xs font-semibold border border-emerald-200 dark:border-emerald-800">
            <Activity className="w-3.5 h-3.5 animate-spin" />
            <span>AI Model Active</span>
          </div>

          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-all"
            title="Toggle Dark/Light Mode"
          >
            {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
          </button>
        </div>

      </div>
    </header>
  );
};
