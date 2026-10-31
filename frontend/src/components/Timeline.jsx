import { useMemo, useState } from "react";
import { fmtNum } from "../format";

function monthLabel(month) {
  const [y, m] = month.split("-");
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${names[Number(m) - 1]} ${y}`;
}

export default function Timeline({ timeline = [], first, last }) {
  const [hover, setHover] = useState(null);

  const points = useMemo(() => {
    if (!timeline.length) return [];
    if (timeline.length <= 72) return timeline;
    // Too many months: group by quarter so the shape survives.
    const groups = new Map();
    for (const point of timeline) {
      const [y, m] = point.month.split("-").map(Number);
      const key = `${y}-Q${Math.floor((m - 1) / 3) + 1}`;
      groups.set(key, (groups.get(key) || 0) + point.commits);
    }
    return [...groups.entries()].map(([month, commits]) => ({ month, commits }));
  }, [timeline]);

  if (!points.length) return null;

  const max = Math.max(...points.map((p) => p.commits), 1);
  const total = points.reduce((sum, p) => sum + p.commits, 0);
  const active = hover !== null ? points[hover] : null;

  return (
    <div className="border-y hairline py-8">
      <div className="mb-6 flex items-end justify-between gap-6">
        <div>
          <p className="label mb-2">The pulse</p>
          <p className="font-display text-2xl font-light text-bone">
            {fmtNum(total)} commits <span className="text-dust">over</span> {points.length}{" "}
            <span className="text-dust">{points.length > 60 ? "quarters" : "months"}</span>
          </p>
        </div>
        <div className="text-right font-mono text-[10px] uppercase tracking-[0.18em] text-dust">
          {active ? (
            <>
              <span className="text-candle">{monthLabel(active.month)}</span>
              <br />
              {fmtNum(active.commits)} commit{active.commits === 1 ? "" : "s"}
            </>
          ) : (
            <>
              {String(first || "").slice(0, 7)}
              <br />
              {String(last || "").slice(0, 7)}
            </>
          )}
        </div>
      </div>

      <div className="flex h-24 items-end gap-[2px]" role="img" aria-label="Commit activity over time">
        {points.map((point, i) => {
          const height = Math.max(2, Math.pow(point.commits / max, 0.62) * 96);
          const hot = point.commits === max;
          return (
            <button
              key={point.month}
              type="button"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(i)}
              onBlur={() => setHover(null)}
              aria-label={`${monthLabel(point.month)}: ${point.commits} commits`}
              className="group relative flex-1 focus:outline-none"
              style={{ height: `${height}px`, minWidth: points.length > 50 ? 2 : 4 }}
            >
              <span
                className={`absolute inset-0 transition-colors duration-200 ${
                  i === hover
                    ? "bg-candle"
                    : hot
                    ? "bg-ember/80"
                    : "bg-bone/25 group-hover:bg-bone/50"
                }`}
              />
            </button>
          );
        })}
      </div>
      <div className="mt-3 flex justify-between font-mono text-[9px] uppercase tracking-[0.2em] text-dust/70">
        <span>{String(first || "").slice(0, 7)}</span>
        <span>the record ends here</span>
        <span>{String(last || "").slice(0, 7)}</span>
      </div>
    </div>
  );
}
