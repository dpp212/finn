'use client';

import { useState, useEffect } from 'react';
import { BottomNav } from '@/components/BottomNav';
import { PushView } from '@/components/PushView';
import { PullView } from '@/components/PullView';
import { PortfolioView } from '@/components/PortfolioView';
import { SettingsView } from '@/components/SettingsView';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'push' | 'portfolio' | 'pull' | 'settings'>('push');

  return (
    <div className="flex flex-col h-screen max-w-md mx-auto bg-finn-bg">
      {/* Header */}
      <header className="flex items-center justify-between px-4 pt-4 pb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-finn-accent to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">F</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white">FINN</h1>
            <p className="text-xxs text-finn-muted -mt-0.5">Financial Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-finn-green animate-pulse-slow" />
          <span className="text-xxs text-finn-muted">Live</span>
        </div>
      </header>

      {/* Tab labels */}
      <div className="flex px-4 gap-1 mt-1">
        {(['push', 'portfolio', 'pull', 'settings'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === tab
                ? 'bg-finn-accent/20 text-finn-accent'
                : 'text-finn-muted hover:text-finn-text'
            }`}
          >
            {tab === 'push' ? '📡 Push' : tab === 'portfolio' ? '📊 Portfolio' : tab === 'pull' ? '🔍 Research' : '⚙️ Settings'}
          </button>
        ))}
      </div>

      {/* Content area — scrollable */}
      <main className="flex-1 overflow-y-auto px-4 pt-3 pb-20">
        {activeTab === 'push' && <PushView />}
        {activeTab === 'portfolio' && <PortfolioView />}
        {activeTab === 'pull' && <PullView />}
        {activeTab === 'settings' && <SettingsView />}
      </main>

      {/* Bottom nav (mobile) */}
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}
