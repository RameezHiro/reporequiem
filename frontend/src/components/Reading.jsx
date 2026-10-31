import { useEffect, useState } from "react";
import { Candle } from "./Icons";
import { useElapsed } from "../hooks";

const LINES = [
  "resolving HEAD",
  "walking the commit graph",
  "opening deleted blobs",
  "counting the graves",
  "listening for revenants",
  "checking which languages stopped speaking",
  "reading the last commit message",
  "the archivist is taking notes",
];

const PHRASES = [
  "Every repository keeps the shape of what was removed.",
  "A deleted file is still a decision someone made.",
  "The quiet at the end is part of the record.",
];

export default function Reading({ source, onCancel }) {
  const elapsed = useElapsed(true);
  const [visible, setVisible] = useState(1);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible((n) => Math.min(n + 1, LINES.length));
    }, 1700);
    return () => clearInterval(id);
  }, []);

  const phrase = PHRASES[Math.min(Math.floor(elapsed / 7), PHRASES.length - 1)];

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div className="absolute left-1/2 top-1/3 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-candle/[0.05] blur-3xl animate-fog" />
      </div>

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-6 py-24 sm:px-10">
        <div className="mb-10 flex items-center gap-4">
          <span className="relative flex h-12 w-12 items-center justify-center rounded-full border border-candle/20">
            <span className="absolute inset-0 rounded-full bg-candle/10 blur-md animate-flicker" />
            <Candle className="relative h-6 w-6 text-candle animate-flicker" />
          </span>
          <div>
            <p className="label">Reading the archive</p>
            <p className="mt-1 font-mono text-[12px] text-bone/80">{source}</p>
          </div>
        </div>

        <div className="h-px w-full overflow-hidden bg-white/10">
          <div className="h-full w-1/3 bg-candle/70 animate-shimmer" />
        </div>

        <div className="mt-10 min-h-[260px] space-y-3">
          {LINES.slice(0, visible).map((line, i) => (
            <div
              key={line}
              className="flex items-baseline gap-3 font-mono text-[11px] tracking-wide animate-rise"
              style={{ animationDelay: `${i === visible - 1 ? 0 : 0}ms` }}
            >
              <span className={i === visible - 1 ? "text-ember" : "text-dust"}>›</span>
              <span className={i === visible - 1 ? "text-bone/85" : "text-dust"}>{line}</span>
              {i === visible - 1 ? (
                <span className="ml-1 inline-block h-3 w-1.5 bg-candle/70 animate-breathe" />
              ) : null}
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col gap-5 border-t hairline pt-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="font-display text-xl italic leading-snug text-ash">{phrase}</p>
            <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.22em] text-dust">
              {elapsed}s elapsed · no files are uploaded
            </p>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="self-start font-mono text-[10px] uppercase tracking-[0.2em] text-dust transition-colors hover:text-ash sm:self-auto"
          >
            Leave the archive
          </button>
        </div>
      </div>
    </div>
  );
}
