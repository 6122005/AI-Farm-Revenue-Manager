import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import type { NavTab } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Predict } from './pages/Predict';
import { DataUpload } from './pages/DataUpload';
import { FeedbackLogs } from './pages/FeedbackLogs';
import { Settings } from './pages/Settings';

export function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  useEffect(() => {
    const handleSwitchTab = (e: Event) => {
      const customEvent = e as CustomEvent<NavTab>;
      if (customEvent.detail) {
        setActiveTab(customEvent.detail);
      }
    };
    window.addEventListener('switch-tab', handleSwitchTab);
    return () => window.removeEventListener('switch-tab', handleSwitchTab);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      <Navbar darkMode={darkMode} setDarkMode={setDarkMode} />

      <div className="flex flex-1">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'predict' && <Predict />}
          {activeTab === 'upload' && <DataUpload />}
          {activeTab === 'feedback' && <FeedbackLogs />}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}

export default App;
