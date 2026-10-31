import { fmtDate, fmtTime } from "../format";

const SEVERITY = {
  grave: "bg-ember",
  major: "bg-candle/80",
  minor: "bg-dust/70",
};

export default function Curses({ cursed = [] }) {
  if (!cursed.length) return null;

  return (
    <div className="divide-y hairline border-y hairline">
      {cursed.map((curse, i) => (
        <div
          key={curse.commit + curse.title}
          className="group grid gap-3 py-5 transition-colors hover:bg-white/[0.015] sm:grid-cols-[38px_1fr_auto] sm:gap-6"
        >
          <span className="font-mono text-[10px] tracking-[0.2em] text-dust/70">
            {String(i + 1).padStart(2, "0")}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${SEVERITY[curse.severity] || SEVERITY.minor}`} />
              <h3 className="font-display text-xl font-light text-bone">{curse.title}</h3>
            </div>
            <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-ash">{curse.detail}</p>
            <p className="mt-2 truncate font-mono text-[10px] text-dust">
              “{curse.subject}”
            </p>
          </div>
          <div className="shrink-0 font-mono text-[10px] leading-relaxed text-dust sm:text-right">
            <div className="text-candle/80">{curse.commit}</div>
            <div>{curse.author}</div>
            <div>
              {fmtDate(curse.date, "short")} · {fmtTime(curse.date)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
