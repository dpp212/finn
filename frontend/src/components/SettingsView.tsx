'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

export function SettingsView() {
  const [settings, setSettings] = useState({
    volume_threshold: 2.0,
    price_change_threshold: 3.0,
    digest_window_hours: 24,
    alert_categories: ['results', 'm_and_a', 'management_change', 'litigation', 'fund_raise'],
  });
  const [saving, setSaving] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const res = await api.getSettings();
      setSettings(res);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  }

  async function saveSettings() {
    setSaving(true);
    try {
      await api.updateSettings(settings);
    } catch (err) {
      console.error('Failed to save:', err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDataRefresh() {
    setRefreshStatus('Fetching prices...');
    try {
      await api.refreshPrices();
      setRefreshStatus('Scraping announcements...');
      await api.refreshAnnouncements(7);
      setRefreshStatus('Classifying announcements...');
      await api.classifyAnnouncements();
      setRefreshStatus('Done ✓');
      setTimeout(() => setRefreshStatus(''), 3000);
    } catch (err) {
      setRefreshStatus('Error — check backend logs');
    }
  }

  const allCategories = [
    'results', 'm_and_a', 'fund_raise', 'management_change', 'litigation',
    'insider_trading', 'earnings_call', 'credit_rating', 'dividend',
    'capex', 'press_release', 'bonus_split',
  ];

  return (
    <div className="space-y-6">
      {/* Alert thresholds */}
      <section>
        <h3 className="text-sm font-semibold text-white mb-3">Alert Thresholds</h3>
        <div className="space-y-4 bg-finn-card rounded-xl border border-finn-border p-4">
          <div>
            <label className="text-xs text-finn-muted mb-1 block">
              Price change alert (±%)
            </label>
            <input
              type="range"
              min="1" max="10" step="0.5"
              value={settings.price_change_threshold}
              onChange={(e) => setSettings(s => ({ ...s, price_change_threshold: parseFloat(e.target.value) }))}
              className="w-full accent-finn-accent"
            />
            <span className="text-xs text-finn-accent font-mono">±{settings.price_change_threshold}%</span>
          </div>
          <div>
            <label className="text-xs text-finn-muted mb-1 block">
              Volume spike alert (× above 20-day avg)
            </label>
            <input
              type="range"
              min="1.5" max="5" step="0.5"
              value={settings.volume_threshold}
              onChange={(e) => setSettings(s => ({ ...s, volume_threshold: parseFloat(e.target.value) }))}
              className="w-full accent-finn-accent"
            />
            <span className="text-xs text-finn-accent font-mono">{settings.volume_threshold}×</span>
          </div>
        </div>
      </section>

      {/* Alert categories */}
      <section>
        <h3 className="text-sm font-semibold text-white mb-3">Alert Categories</h3>
        <div className="bg-finn-card rounded-xl border border-finn-border p-4">
          <div className="flex flex-wrap gap-2">
            {allCategories.map((cat) => {
              const active = settings.alert_categories.includes(cat);
              return (
                <button
                  key={cat}
                  onClick={() => {
                    setSettings(s => ({
                      ...s,
                      alert_categories: active
                        ? s.alert_categories.filter(c => c !== cat)
                        : [...s.alert_categories, cat],
                    }));
                  }}
                  className={cn(
                    'px-2.5 py-1 text-xs rounded-lg border transition-all capitalize',
                    active
                      ? 'bg-finn-accent/15 border-finn-accent/30 text-finn-accent'
                      : 'border-finn-border text-finn-muted hover:text-finn-text'
                  )}
                >
                  {cat.replace(/_/g, ' ')}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Save */}
      <button
        onClick={saveSettings}
        disabled={saving}
        className="w-full py-3 bg-finn-accent rounded-xl text-white text-sm font-medium disabled:opacity-50 transition-all hover:bg-finn-accent-dim"
      >
        {saving ? 'Saving...' : 'Save Settings'}
      </button>

      {/* Data management */}
      <section>
        <h3 className="text-sm font-semibold text-white mb-3">Data Management</h3>
        <div className="bg-finn-card rounded-xl border border-finn-border p-4 space-y-3">
          <button
            onClick={handleDataRefresh}
            className="w-full py-2.5 bg-finn-surface border border-finn-border rounded-lg text-xs text-finn-text hover:border-finn-accent/30 transition-all"
          >
            🔄 Full Data Refresh (prices + announcements + classify)
          </button>
          {refreshStatus && (
            <p className="text-xs text-finn-accent text-center">{refreshStatus}</p>
          )}
        </div>
      </section>

      {/* About */}
      <div className="text-center py-4">
        <p className="text-xxs text-finn-muted">FINN v0.1.0 — Built for ENAM</p>
        <p className="text-xxs text-finn-muted mt-1">Gemini Flash (bulk) + Pro (reasoning)</p>
      </div>
    </div>
  );
}
