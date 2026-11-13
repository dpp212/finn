import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '—';
  if (Math.abs(value) >= 10_000_000) return `${(value / 10_000_000).toFixed(1)}Cr`;
  if (Math.abs(value) >= 100_000) return `${(value / 100_000).toFixed(1)}L`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString('en-IN');
}

export function formatPct(value: number | null | undefined): string {
  if (value == null) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '';
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

export const CATEGORY_LABELS: Record<string, string> = {
  results: 'Results',
  m_and_a: 'M&A',
  fund_raise: 'Fund Raise',
  management_change: 'Mgmt Change',
  litigation: 'Litigation',
  insider_trading: 'Insider',
  earnings_call: 'Earnings Call',
  investor_meetings: 'Investor Meet',
  credit_rating: 'Credit Rating',
  dividend: 'Dividend',
  bonus_split: 'Bonus/Split',
  capex: 'Capex',
  press_release: 'Press Release',
  postal_ballot: 'Postal Ballot',
  agm_egm: 'AGM/EGM',
  pledging: 'Pledging',
  unclassified: 'Other',
};

export const CATEGORY_COLORS: Record<string, string> = {
  results: 'bg-blue-500/20 text-blue-400',
  m_and_a: 'bg-purple-500/20 text-purple-400',
  fund_raise: 'bg-emerald-500/20 text-emerald-400',
  management_change: 'bg-amber-500/20 text-amber-400',
  litigation: 'bg-red-500/20 text-red-400',
  insider_trading: 'bg-orange-500/20 text-orange-400',
  earnings_call: 'bg-cyan-500/20 text-cyan-400',
  dividend: 'bg-green-500/20 text-green-400',
  capex: 'bg-indigo-500/20 text-indigo-400',
  default: 'bg-gray-500/20 text-gray-400',
};
