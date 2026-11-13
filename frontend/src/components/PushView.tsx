'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { formatPct, timeAgo, CATEGORY_LABELS, CATEGORY_COLORS, cn } from '@/lib/utils';
import { FormattedContent } from '@/components/FormattedContent';

interface DigestData {
  window_hours: number;
  critical: any[];
  notable: any[];
  routine: any[];
  price_alerts: any[];
  counts: { critical: number; notable: number; routine: number; price_alerts: number };
}

export function PushView() {
  const [digest, setDigest] = useState<DigestData | null>(null);
  const [briefing, setBriefing] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [hours, setHours] = useState(24);
  const [showRoutine, setShowRoutine] = useState(false);
  const [activeSection, setActiveSection] = useState<'briefing' | 'digest' | 'alerts'>('briefing');

  useEffect(() => {
    loadData();
  }, [hours]);

  async function loadData() {
    setLoading(true);
    try {
      const [digestRes, briefingRes] = await Promise.all([
        api.getDigest(hours),
        api.getBriefing(hours),
      ]);
      setDigest(digestRes);
      setBriefing(briefingRes.briefing);
    } catch (err) {
      console.error('Failed to load push data:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-24 bg-finn-card rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Time window selector */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-finn-muted">Window:</span>
        {[6, 12, 24, 48, 168].map((h) => (
          <button
            key={h}
            onClick={() => setHours(h)}
            className={cn(
              'px-2.5 py-1 text-xs rounded-lg transition-all',
              hours === h
                ? 'bg-finn-accent/20 text-finn-accent font-medium'
                : 'text-finn-muted hover:text-finn-text'
            )}
          >
            {h <= 24 ? `${h}h` : `${h / 24}d`}
          </button>
        ))}
      </div>

      {/* Section tabs */}
      <div className="flex gap-1 bg-finn-surface rounded-xl p-1">
        {(['briefing', 'digest', 'alerts'] as const).map((section) => (
          <button
            key={section}
            onClick={() => setActiveSection(section)}
            className={cn(
              'flex-1 py-2 text-xs font-medium rounded-lg transition-all capitalize',
              activeSection === section
                ? 'bg-finn-card text-white shadow-sm'
                : 'text-finn-muted'
            )}
          >
            {section === 'briefing' ? '🧠 Briefing' : section === 'digest' ? '📋 Digest' : `🔔 Alerts (${digest?.counts.price_alerts || 0})`}
          </button>
        ))}
      </div>

      {/* AI Briefing */}
      {activeSection === 'briefing' && (
        <div className="bg-finn-card rounded-xl p-4 border border-finn-border">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-finn-accent to-purple-600 flex items-center justify-center">
              <span className="text-xs">F</span>
            </div>
            <span className="text-xs font-medium text-finn-text">FINN&apos;s Take</span>
            <span className="text-xxs text-finn-muted ml-auto">Last {hours}h</span>
          </div>
          <div className="pt-1">
            {briefing ? (
              <FormattedContent content={briefing} />
            ) : (
              <p className="text-xs text-finn-muted">No activity in this window. Your portfolio is quiet.</p>
            )}
          </div>
        </div>
      )}

      {/* Digest — announcements grouped by priority */}
      {activeSection === 'digest' && digest && (
        <div className="space-y-3">
          {/* Critical */}
          {digest.critical.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-finn-red mb-2 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-finn-red" />
                CRITICAL ({digest.critical.length})
              </h3>
              {digest.critical.map((a: any) => (
                <AnnouncementCard key={a.id} announcement={a} />
              ))}
            </div>
          )}

          {/* Notable */}
          {digest.notable.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-finn-amber mb-2 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-finn-amber" />
                NOTABLE ({digest.notable.length})
              </h3>
              {digest.notable.map((a: any) => (
                <AnnouncementCard key={a.id} announcement={a} />
              ))}
            </div>
          )}

          {/* Routine — collapsed by default */}
          {digest.routine.length > 0 && (
            <div>
              <button
                onClick={() => setShowRoutine(!showRoutine)}
                className="text-xs text-finn-muted flex items-center gap-1.5 mb-2 hover:text-finn-text transition-colors"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-finn-muted" />
                ROUTINE ({digest.routine.length}) — {showRoutine ? 'hide' : 'show'}
              </button>
              {showRoutine && digest.routine.map((a: any) => (
                <AnnouncementCard key={a.id} announcement={a} compact />
              ))}
            </div>
          )}

          {digest.critical.length === 0 && digest.notable.length === 0 && digest.routine.length === 0 && (
            <div className="text-center py-8 text-finn-muted text-sm">
              No announcements in the last {hours}h. Portfolio is quiet.
            </div>
          )}
        </div>
      )}

      {/* Alerts */}
      {activeSection === 'alerts' && digest && (
        <div className="space-y-2">
          {digest.price_alerts.length > 0 ? (
            digest.price_alerts.map((alert: any) => (
              <AlertCard key={alert.id} alert={alert} />
            ))
          ) : (
            <div className="text-center py-8 text-finn-muted text-sm">
              No price or volume alerts. All within normal ranges.
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function AnnouncementCard({ announcement: a, compact = false }: { announcement: any; compact?: boolean }) {
  const catColor = CATEGORY_COLORS[a.category] || CATEGORY_COLORS.default;
  const catLabel = CATEGORY_LABELS[a.category] || a.category;

  // Check for rich parsed enrichment
  let enrichmentData: any = null;
  if (a.enrichment) {
    try {
      enrichmentData = typeof a.enrichment === 'string' ? JSON.parse(a.enrichment) : a.enrichment;
    } catch (e) {
      enrichmentData = null;
    }
  }

  return (
    <div className={cn(
      'bg-finn-card rounded-xl border border-finn-border mb-2.5 transition-all hover:border-finn-accent/30',
      compact ? 'p-3' : 'p-4',
      a.priority === 'high' && 'border-finn-accent/30 shadow-sm shadow-indigo-950/20',
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="text-xs font-bold text-white tracking-wide">{a.company}</span>
            <span className={cn('px-1.5 py-0.5 text-xxs rounded-md font-semibold tracking-wide uppercase', catColor)}>
              {catLabel}
            </span>
            {a.sector && (
              <span className="text-xxs text-finn-muted">· {a.sector}</span>
            )}
          </div>
          <p className={cn('text-finn-text leading-snug font-medium', compact ? 'text-xs' : 'text-sm')}>
            {a.summary || a.headline}
          </p>
        </div>
        <span className="text-xxs text-finn-muted whitespace-nowrap pt-0.5">{timeAgo(a.filed_at)}</span>
      </div>

      {/* RICH ENRICHMENT 1: Quarterly Results Headline Numbers (Revenue, EBITDA, PBT, PAT QoQ & YoY) */}
      {enrichmentData && enrichmentData.type === 'results' && enrichmentData.metrics && (
        <div className="mt-3 pt-3 border-t border-finn-border/60 bg-finn-surface/60 rounded-lg p-2.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xxs font-semibold tracking-wider text-indigo-400 uppercase">
              Headline Results ({enrichmentData.quarter || 'Latest Quarter'})
            </span>
            <span className="text-xxs text-finn-muted">Audited Primary Filing</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            {/* Revenue */}
            <div className="bg-finn-card/80 p-2 rounded border border-finn-border/50">
              <span className="text-xxs text-finn-muted block">Revenue</span>
              <span className="font-bold text-white font-mono">{enrichmentData.metrics.revenue?.val}</span>
              <div className="flex gap-2 text-xxs mt-0.5 font-mono">
                <span className="text-emerald-400">QoQ {enrichmentData.metrics.revenue?.qoq}</span>
                <span className="text-emerald-400">YoY {enrichmentData.metrics.revenue?.yoy}</span>
              </div>
            </div>

            {/* EBITDA */}
            <div className="bg-finn-card/80 p-2 rounded border border-finn-border/50">
              <span className="text-xxs text-finn-muted block">EBITDA (Margin {enrichmentData.metrics.ebitda?.margin})</span>
              <span className="font-bold text-white font-mono">{enrichmentData.metrics.ebitda?.val}</span>
              <div className="flex gap-2 text-xxs mt-0.5 font-mono">
                <span className="text-emerald-400">QoQ {enrichmentData.metrics.ebitda?.qoq}</span>
                <span className="text-emerald-400">YoY {enrichmentData.metrics.ebitda?.yoy}</span>
              </div>
            </div>

            {/* PBT */}
            <div className="bg-finn-card/80 p-2 rounded border border-finn-border/50">
              <span className="text-xxs text-finn-muted block">PBT (Profit Before Tax)</span>
              <span className="font-bold text-white font-mono">{enrichmentData.metrics.pbt?.val}</span>
              <div className="flex gap-2 text-xxs mt-0.5 font-mono">
                <span className="text-emerald-400">QoQ {enrichmentData.metrics.pbt?.qoq}</span>
                <span className="text-emerald-400">YoY {enrichmentData.metrics.pbt?.yoy}</span>
              </div>
            </div>

            {/* PAT */}
            <div className="bg-finn-card/80 p-2 rounded border border-finn-border/50">
              <span className="text-xxs text-finn-muted block">PAT (Net Profit)</span>
              <span className="font-bold text-white font-mono">{enrichmentData.metrics.pat?.val}</span>
              <div className="flex gap-2 text-xxs mt-0.5 font-mono">
                <span className="text-emerald-400">QoQ {enrichmentData.metrics.pat?.qoq}</span>
                <span className="text-emerald-400">YoY {enrichmentData.metrics.pat?.yoy}</span>
              </div>
            </div>
          </div>

          {enrichmentData.verdict && (
            <div className="mt-2 text-xxs text-finn-text leading-relaxed bg-finn-card/50 p-2 rounded border-l-2 border-indigo-500">
              <span className="font-semibold text-indigo-300">Takeaway: </span>
              {enrichmentData.verdict}
            </div>
          )}
        </div>
      )}

      {/* RICH ENRICHMENT 2: Executive Management Change (Bio, Pedigree & Impact) */}
      {enrichmentData && enrichmentData.type === 'management_change' && (
        <div className="mt-3 pt-3 border-t border-finn-border/60 bg-finn-surface/60 rounded-lg p-2.5 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xxs font-semibold tracking-wider text-amber-400 uppercase">
              Leadership Background & Transition
            </span>
            <span className="text-xxs text-finn-muted">Primary Exchange Intimation</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-baseline gap-2">
              <span className="font-bold text-white text-sm">{enrichmentData.person}</span>
              <span className="text-xxs text-amber-300 font-medium px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                {enrichmentData.new_role}
              </span>
            </div>

            {enrichmentData.pedigree && (
              <p className="text-xxs text-finn-text-dim">
                <strong className="text-finn-text">Background:</strong> {enrichmentData.pedigree}
              </p>
            )}

            {enrichmentData.predecessor && (
              <p className="text-xxs text-finn-muted">
                <strong>Predecessor:</strong> {enrichmentData.predecessor}
              </p>
            )}

            {enrichmentData.verdict && (
              <div className="text-xxs text-finn-text bg-finn-card/60 p-2 rounded border-l-2 border-amber-500 mt-1">
                <span className="font-semibold text-amber-300">Assessment: </span>
                {enrichmentData.verdict}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Plain string enrichment fallback */}
      {a.enrichment && !enrichmentData && (
        <p className="text-xs text-finn-accent/80 mt-1.5 italic">{a.enrichment}</p>
      )}

      {/* Footer / Filing link */}
      {a.filing_url && (
        <div className="mt-2.5 flex items-center justify-between pt-1 border-t border-finn-border/30">
          <span className="text-xxs text-finn-muted font-mono">Source: {a.source || 'BSE'}</span>
          <a
            href={a.filing_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xxs text-finn-accent hover:underline flex items-center gap-1 font-medium"
          >
            Original Filing PDF ↗
          </a>
        </div>
      )}
    </div>
  );
}


function AlertCard({ alert }: { alert: any }) {
  const isPrice = alert.alert_type === 'price_spike';
  const change = alert.data?.change_pct;

  return (
    <div className={cn(
      'bg-finn-card rounded-xl border p-4 transition-all',
      alert.severity === 'critical'
        ? 'border-finn-red/30 glow-red'
        : 'border-finn-border',
    )}>
      <div className="flex items-start gap-3">
        <div className={cn(
          'w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0',
          isPrice
            ? (change > 0 ? 'bg-finn-green/10' : 'bg-finn-red/10')
            : 'bg-finn-amber/10'
        )}>
          {isPrice ? (change > 0 ? '📈' : '📉') : '📊'}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-white">{alert.title}</h4>
          <p className="text-xs text-finn-text-dim mt-1 leading-relaxed">{alert.body}</p>
          <span className="text-xxs text-finn-muted mt-1.5 block">{timeAgo(alert.triggered_at)}</span>
        </div>
        {isPrice && change != null && (
          <span className={cn(
            'text-sm font-mono font-bold tabular-nums',
            change > 0 ? 'text-finn-green' : 'text-finn-red'
          )}>
            {formatPct(change)}
          </span>
        )}
      </div>
    </div>
  );
}
