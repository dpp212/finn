'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { formatCurrency, formatPct, formatNumber, cn } from '@/lib/utils';

interface Stock {
  ticker: string;
  name: string;
  sector: string;
  close: number | null;
  change_pct: number | null;
  volume: number | null;
  volume_ratio: number | null;
  date: string | null;
}

export function PortfolioView() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'name' | 'change' | 'volume'>('change');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPortfolio();
  }, []);

  async function loadPortfolio() {
    try {
      const res = await api.getPortfolio();
      setStocks(res.portfolio);
    } catch (err) {
      console.error('Failed to load portfolio:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await api.refreshPrices();
      await loadPortfolio();
    } catch (err) {
      console.error('Refresh failed:', err);
    } finally {
      setRefreshing(false);
    }
  }

  const sorted = [...stocks].sort((a, b) => {
    if (sortBy === 'change') return Math.abs(b.change_pct || 0) - Math.abs(a.change_pct || 0);
    if (sortBy === 'volume') return (b.volume_ratio || 0) - (a.volume_ratio || 0);
    return a.name.localeCompare(b.name);
  });

  // Summary stats
  const gainers = stocks.filter(s => (s.change_pct || 0) > 0).length;
  const losers = stocks.filter(s => (s.change_pct || 0) < 0).length;
  const bigMover = [...stocks].sort((a, b) => Math.abs(b.change_pct || 0) - Math.abs(a.change_pct || 0))[0];

  if (loading) {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-16 bg-finn-card rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-finn-card rounded-xl p-3 text-center border border-finn-border">
          <p className="text-lg font-bold text-finn-green tabular-nums">{gainers}</p>
          <p className="text-xxs text-finn-muted">Gainers</p>
        </div>
        <div className="bg-finn-card rounded-xl p-3 text-center border border-finn-border">
          <p className="text-lg font-bold text-finn-red tabular-nums">{losers}</p>
          <p className="text-xxs text-finn-muted">Losers</p>
        </div>
        <div className="bg-finn-card rounded-xl p-3 text-center border border-finn-border">
          <p className="text-sm font-bold text-white truncate">{bigMover?.name || '—'}</p>
          <p className={cn('text-xxs font-mono tabular-nums',
            (bigMover?.change_pct || 0) > 0 ? 'text-finn-green' : 'text-finn-red'
          )}>
            {formatPct(bigMover?.change_pct)} top move
          </p>
        </div>
      </div>

      {/* Sort + Refresh */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {(['change', 'volume', 'name'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={cn(
                'px-2.5 py-1 text-xs rounded-lg transition-all capitalize',
                sortBy === s ? 'bg-finn-accent/20 text-finn-accent' : 'text-finn-muted'
              )}
            >
              {s === 'change' ? '% Move' : s === 'volume' ? 'Vol' : 'A-Z'}
            </button>
          ))}
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="text-xs text-finn-accent hover:text-finn-accent-dim disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      {/* Stock list */}
      <div className="space-y-1.5">
        {sorted.map((stock) => (
          <StockRow key={stock.ticker} stock={stock} />
        ))}
      </div>
    </div>
  );
}


function StockRow({ stock }: { stock: Stock }) {
  const change = stock.change_pct || 0;
  const isUp = change >= 0;
  const volumeHigh = (stock.volume_ratio || 0) >= 2;

  return (
    <div className={cn(
      'bg-finn-card rounded-xl border border-finn-border p-3 flex items-center gap-3 transition-all hover:border-finn-accent/20',
      volumeHigh && 'border-finn-amber/20',
    )}>
      {/* Company info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">{stock.name}</span>
          {volumeHigh && (
            <span className="px-1 py-0.5 text-xxs rounded bg-finn-amber/15 text-finn-amber font-medium">
              {stock.volume_ratio?.toFixed(1)}× vol
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xxs text-finn-muted font-mono">{stock.ticker.replace('.NS', '')}</span>
          <span className="text-xxs text-finn-muted">·</span>
          <span className="text-xxs text-finn-muted">{stock.sector}</span>
        </div>
      </div>

      {/* Price + Change */}
      <div className="text-right">
        <p className="text-sm font-mono font-medium text-white tabular-nums">
          {stock.close ? `₹${stock.close.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
        </p>
        <p className={cn(
          'text-xs font-mono font-semibold tabular-nums',
          isUp ? 'text-finn-green' : 'text-finn-red'
        )}>
          {formatPct(change)}
        </p>
      </div>
    </div>
  );
}
