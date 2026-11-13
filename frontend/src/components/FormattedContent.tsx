'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface FormattedContentProps {
  content: string;
  className?: string;
}

export function FormattedContent({ content, className }: FormattedContentProps) {
  if (!content) return null;

  // Split into lines and process paragraphs / bullet lists
  const lines = content.split('\n');

  function renderInline(text: string) {
    // Parses **bold**, _italic_, and `code`
    const tokens = text.split(/(\*\*.*?\*\*|_.*?_|`.*?`)/g);

    return tokens.map((token, i) => {
      if (token.startsWith('**') && token.endsWith('**') && token.length >= 4) {
        return (
          <span key={i} className="font-semibold text-white">
            {token.slice(2, -2)}
          </span>
        );
      }
      if (token.startsWith('_') && token.endsWith('_') && token.length >= 2) {
        return (
          <span key={i} className="text-finn-muted text-xs italic block mt-1">
            {token.slice(1, -1)}
          </span>
        );
      }
      if (token.startsWith('`') && token.endsWith('`') && token.length >= 2) {
        return (
          <code key={i} className="px-1 py-0.5 rounded bg-finn-surface border border-finn-border font-mono text-xs text-finn-accent">
            {token.slice(1, -1)}
          </code>
        );
      }
      return token;
    });
  }

  return (
    <div className={cn('space-y-2 text-sm leading-relaxed text-finn-text', className)}>
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={idx} className="h-1" />;
        }

        // Section Headers like "**High-Impact Filings (4):**" or "### Title"
        const isHeader =
          (trimmed.startsWith('**') && trimmed.endsWith('**') && !trimmed.startsWith('•')) ||
          trimmed.startsWith('###') ||
          (trimmed.startsWith('**') && trimmed.endsWith(':**'));

        if (isHeader) {
          const cleanHeader = trimmed
            .replace(/^###\s*/, '')
            .replace(/^\*\*/, '')
            .replace(/\*\*:?$/, '');

          const isCritical = /high-impact|critical|urgent/i.test(cleanHeader);
          const isSignals = /signal|price|volume/i.test(cleanHeader);
          const isNotable = /notable|action|corporate/i.test(cleanHeader);

          return (
            <div key={idx} className="pt-2 pb-1 flex items-center gap-2">
              <span
                className={cn(
                  'w-2 h-2 rounded-full',
                  isCritical
                    ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]'
                    : isSignals
                    ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]'
                    : isNotable
                    ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]'
                    : 'bg-finn-accent'
                )}
              />
              <span className="text-xs font-bold uppercase tracking-wider text-white">
                {cleanHeader}
              </span>
            </div>
          );
        }

        // Bullet point lines starting with • or - or *
        if (trimmed.startsWith('•') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          const bulletBody = trimmed.replace(/^[•\-\*]\s*/, '');

          // Check if bullet has a company ticker like "**TCS**:" or "**Tata Motors surged +4.8%**:"
          const colonMatch = bulletBody.match(/^(\*\*.*?\*\*)\s*:\s*(.*)$/);

          if (colonMatch) {
            const subject = colonMatch[1].replace(/\*\*/g, '');
            const rest = colonMatch[2];

            return (
              <div key={idx} className="flex items-start gap-2.5 py-1 text-xs">
                <span className="shrink-0 mt-0.5 px-1.5 py-0.5 rounded bg-finn-surface border border-finn-border font-mono font-medium text-finn-accent text-xxs">
                  {subject}
                </span>
                <span className="flex-1 text-finn-text leading-snug">
                  {renderInline(rest)}
                </span>
              </div>
            );
          }

          return (
            <div key={idx} className="flex items-start gap-2 py-0.5 text-xs text-finn-text">
              <span className="text-finn-accent/70 mt-0.5 select-none">•</span>
              <span className="flex-1 leading-snug">{renderInline(bulletBody)}</span>
            </div>
          );
        }

        // Numbered list: "1. text"
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 py-0.5 text-xs text-finn-text">
              <span className="font-mono text-finn-muted text-xxs mt-0.5">{numMatch[1]}.</span>
              <span className="flex-1 leading-snug">{renderInline(numMatch[2])}</span>
            </div>
          );
        }

        // Normal paragraph
        return (
          <p key={idx} className="text-xs leading-relaxed text-finn-text">
            {renderInline(trimmed)}
          </p>
        );
      })}
    </div>
  );
}
