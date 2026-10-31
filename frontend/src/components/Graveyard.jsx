import { useState } from "react";
import { fmtNum, span, ageLabel, fmtYear } from "../format";

const KINDS = {
  buried: { label: "Buried", dot: "bg-ember", text: "text-ember" },
  revenant: { label: "Revenant", dot: "bg-moss", text: "text-moss" },
  forgotten: { label: "Still here", dot: "bg-dust", text: "text-dust" },
};

function fallbackLament(ghost) {
  if (ghost.kind === "forgotten") {
    return `I am still here. Nobody has opened me in ${ageLabel(ghost.age_days)}.`;
  }
  return `I was ${ghost.path}. ${ghost.killed_by} closed me in “${ghost.last_subject}”.`;
}

function Headstone({ ghost, lament, onSelect }) {
  const kind = KINDS[ghost.kind] || KINDS.buried;
  const arched = ghost.kind !== "forgotten";

  return (
    <button
      type="button"
      onClick={() => onSelect(ghost)}
      className={`headstone group relative flex h-full flex-col px-5 pb-5 pt-7 text-left sm:px-6 sm:pt-8 ${
        arched ? "rounded-t-[96px] rounded-b-sm" : "rounded-t-xl rounded-b-sm"
      }`}
    >
      <span
        className={`mx-auto mb-3 flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.24em] ${kind.text}`}
      >
        <span className={`h-1 w-1 rounded-full ${kind.dot}`} />
        {kind.label}
      </span>

      <span className="mx-auto mb-3 block h-5 w-px bg-gradient-to-b from-transparent via-white/20 to-transparent" />

      <span className="block break-words text-center font-mono text-[11px] leading-relaxed text-bone/90">
        {ghost.path}
      </span>

      <span className="mt-2 block text-center font-mono text-[9px] uppercase tracking-[0.2em] text-dust">
        {ghost.kind === "forgotten"
          ? `last touched ${fmtYear(ghost.died)}`
          : `${span(ghost.born, ghost.died)} · ${ageLabel(ghost.age_days)}`}
      </span>

      <span className="my-4 block h-px w-10 self-center bg-white/15" />

      <span className="block text-center font-display text-[17px] italic leading-snug text-ash">
        {lament ? (
          <span className="line-clamp-3">“{lament}”</span>
        ) : (
          <span className="mx-auto block h-3 w-4/5 skeleton" />
        )}
      </span>

      <span className="mt-auto block pt-5 text-center">
        <span className="block font-mono text-[9px] uppercase tracking-[0.18em] text-dust/80">
          {ghost.kind === "forgotten" ? "last hand" : "killed by"} · {ghost.killed_by}
        </span>
        <span className="mt-1.5 block truncate font-mono text-[9px] text-dust/60">
          {ghost.commit} · {ghost.last_subject}
        </span>
      </span>

      <span className="pointer-events-none absolute inset-x-0 -bottom-px flex justify-center pb-1 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <span className="font-mono text-[8px] uppercase tracking-[0.28em] text-candle/80">
          open the record
        </span>
      </span>
    </button>
  );
}

const CLOSED = { buried: 6, revenant: 2, forgotten: 3 };
const OPEN = { buried: 12, revenant: 6, forgotten: 12 };

export default function Graveyard({ ghosts = [], revenants = [], forgotten = [], laments = {}, lorePending, onSelect }) {
  const [showAll, setShowAll] = useState(false);
  const limits = showAll ? OPEN : CLOSED;

  const buried = ghosts.slice(0, limits.buried);
  const risen = revenants.slice(0, limits.revenant);
  const left = forgotten.slice(0, limits.forgotten);
  const all = [...buried, ...risen, ...left];
  const total = ghosts.length + revenants.length + forgotten.length;

  const hidden =
    Math.max(0, Math.min(ghosts.length, OPEN.buried) - buried.length) +
    Math.max(0, Math.min(revenants.length, OPEN.revenant) - risen.length) +
    Math.max(0, Math.min(forgotten.length, OPEN.forgotten) - left.length);

  if (!all.length) {
    return (
      <p className="border-l border-white/10 pl-5 font-display text-xl italic text-ash">
        Nothing is buried here. The archive is complete, which is its own kind of strangeness.
      </p>
    );
  }

  return (
    <div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {all.map((ghost, i) => (
          <div
            key={`${ghost.kind}-${ghost.path}`}
            className="animate-rise"
            style={{ animationDelay: `${Math.min(i * 45, 400)}ms` }}
          >
            <Headstone
              ghost={ghost}
              lament={laments[ghost.path] || (lorePending ? "" : fallbackLament(ghost))}
              onSelect={onSelect}
            />
          </div>
        ))}
      </div>

      {hidden > 0 || (showAll && all.length > CLOSED.buried + CLOSED.revenant + CLOSED.forgotten) ? (
        <div className="mt-8 flex items-center justify-center gap-3">
          <span className="h-px w-8 bg-white/10" />
          <button
            type="button"
            onClick={() => setShowAll((open) => !open)}
            aria-expanded={showAll}
            className="font-mono text-[10px] uppercase tracking-[0.22em] text-dust transition-colors hover:text-candle"
          >
            {showAll ? "close the graves" : `open ${fmtNum(hidden)} more grave${hidden === 1 ? "" : "s"}`}
          </button>
          <span className="h-px w-8 bg-white/10" />
        </div>
      ) : null}

      {total > all.length ? (
        <p className="mt-4 text-center font-mono text-[9px] uppercase tracking-[0.18em] text-dust/60">
          showing {fmtNum(all.length)} of {fmtNum(total)} names
        </p>
      ) : null}
    </div>
  );
}
