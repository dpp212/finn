'use client';

import { cn } from '@/lib/utils';

interface BottomNavProps {
  activeTab: 'push' | 'portfolio' | 'pull' | 'settings';
  onTabChange: (tab: 'push' | 'portfolio' | 'pull' | 'settings') => void;
}

const tabs = [
  { id: 'push' as const, icon: '📡', label: 'Push' },
  { id: 'portfolio' as const, icon: '📊', label: 'Portfolio' },
  { id: 'pull' as const, icon: '🔍', label: 'Research' },
  { id: 'settings' as const, icon: '⚙️', label: 'Settings' },
];

export function BottomNav({ activeTab, onTabChange }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-finn-surface/95 backdrop-blur-lg border-t border-finn-border">
      <div className="flex items-center justify-around py-2 px-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              'flex flex-col items-center gap-0.5 py-1 px-4 rounded-xl transition-all',
              activeTab === tab.id
                ? 'text-finn-accent'
                : 'text-finn-muted'
            )}
          >
            <span className="text-lg">{tab.icon}</span>
            <span className="text-xxs font-medium">{tab.label}</span>
            {activeTab === tab.id && (
              <div className="w-1 h-1 rounded-full bg-finn-accent mt-0.5" />
            )}
          </button>
        ))}
      </div>
    </nav>
  );
}
