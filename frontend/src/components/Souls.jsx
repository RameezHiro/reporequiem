import { fmtDate, fmtNum } from "../format";

export default function Souls({ authors = [] }) {
  if (!authors.length) return null;
  const max = Math.max(...authors.map((a) => a.commits), 1);
  const founder = [...authors].sort((a, b) =>
    String(a.first_seen).localeCompare(String(b.first_seen))
  )[0];
  const visitor = [...authors].sort((a, b) =>
    String(b.last_seen).localeCompare(String(a.last_seen))
  )[0];

  return (
    <div className="grid gap-x-12 gap-y-7 sm:grid-cols-2">
      {authors.map((author) => {
        const role =
          author.name === founder?.name
            ? "founder"
            : author.name === visitor?.name
            ? "last visitor"
            : null;
        return (
          <div key={author.name} className="group">
            <div className="mb-2 flex items-baseline justify-between gap-4">
              <div className="flex min-w-0 items-baseline gap-2">
                <span className="truncate font-display text-xl text-bone">{author.name}</span>
                {role ? (
                  <span className="shrink-0 font-mono text-[8px] uppercase tracking-[0.2em] text-ember/80">
                    {role}
                  </span>
                ) : null}
              </div>
              <span className="shrink-0 font-mono text-[10px] text-dust">
                {fmtNum(author.commits)} commits
              </span>
            </div>
            <div className="h-px w-full bg-white/[0.07]">
              <div
                className="h-px bg-bone/40 transition-all duration-700 group-hover:bg-candle/70"
                style={{ width: `${Math.max(4, (author.commits / max) * 100)}%` }}
              />
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[9px] uppercase tracking-[0.14em] text-dust/80">
              <span className="text-moss/80">+{fmtNum(author.added)}</span>
              <span className="text-ember/70">−{fmtNum(author.deleted)}</span>
              <span>
                {fmtDate(author.first_seen, "short")} → {fmtDate(author.last_seen, "short")}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
