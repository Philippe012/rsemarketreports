import { useEffect, useRef } from 'react';

import type { BondTrade } from '../../types/report';
import { formatCompactNumber, formatSignedNumber } from '../../utils/formatters';

export function SessionActivityStrip({ trades }: { trades: BondTrade[] }) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(false);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return undefined;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    if (el.scrollWidth <= el.clientWidth) return undefined;

    let frameId: number;
    const step = () => {
      if (!pausedRef.current) {
        const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 1;
        el.scrollLeft = atEnd ? 0 : el.scrollLeft + 0.4;
      }
      frameId = requestAnimationFrame(step);
    };
    frameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameId);
  }, [trades.length]);

  if (trades.length === 0) return null;

  const pause = () => {
    pausedRef.current = true;
  };
  const resume = () => {
    pausedRef.current = false;
  };

  return (
    <section>
      <div className="mb-3">
        <h2 className="text-[15px] font-semibold tracking-tight" style={{ color: 'var(--text)' }}>
          Session activity
        </h2>
        <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
          Transactions recorded in this report
        </p>
      </div>
      <div
        ref={scrollerRef}
        onMouseEnter={pause}
        onMouseLeave={resume}
        onFocus={pause}
        onBlur={resume}
        onTouchStart={pause}
        onTouchEnd={resume}
        className="flex gap-3 overflow-x-auto scroll-smooth pb-1"
      >
        {trades.map((trade, i) => {
          const tone =
            trade.change === null || trade.change === 0
              ? 'var(--text-muted)'
              : trade.change > 0
                ? 'var(--positive)'
                : 'var(--negative)';
          return (
            <div
              key={`${trade.bond}-${i}`}
              className="flex w-52.5 shrink-0 flex-col gap-1.5 rounded-lg border px-3.5 py-3"
              style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
            >
              <p className="truncate text-[13px] font-medium" style={{ color: 'var(--text)' }} title={trade.bond}>
                {trade.bond}
              </p>
              {trade.category && (
                <p className="text-[10.5px] font-medium uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                  {trade.category}
                </p>
              )}
              <div className="mt-0.5 flex items-baseline justify-between">
                <span className="text-[13px] tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                  {formatCompactNumber(trade.volume)}
                </span>
                <span className="text-[13px] font-semibold tabular-nums" style={{ color: tone }}>
                  {formatSignedNumber(trade.change, 3)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
