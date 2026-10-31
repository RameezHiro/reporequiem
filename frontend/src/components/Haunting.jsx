export default function Haunting({ lore, pending }) {
  if (pending) {
    return (
      <div className="grid gap-8 md:grid-cols-2">
        <p className="md:col-span-2 flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.22em] text-dust">
          <span className="h-1.5 w-1.5 rounded-full bg-candle animate-flicker" />
          The Archivist is speaking
        </p>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="space-y-3">
            <div className="skeleton h-4 w-2/5" />
            <div className="skeleton h-3 w-full" />
            <div className="skeleton h-3 w-11/12" />
            <div className="skeleton h-3 w-4/5" />
          </div>
        ))}
      </div>
    );
  }

  if (!lore?.haunting?.length) return null;

  return (
    <div className="grid gap-x-14 gap-y-12 md:grid-cols-2">
      {lore.haunting.map((chapter, i) => (
        <article key={chapter.title + i} className="relative">
          <div className="mb-3 flex items-baseline gap-3">
            <span className="font-mono text-[9px] tracking-[0.24em] text-ember/70">
              {String(i + 1).padStart(2, "0")}
            </span>
            <h3 className="font-display text-2xl font-normal tracking-tight text-bone">
              {chapter.title}
            </h3>
          </div>
          <p
            className={`text-pretty text-[15px] leading-[1.85] text-ash ${
              i === 0 ? "first-letter:font-display first-letter:text-candle" : ""
            }`}
          >
            {chapter.text}
          </p>
        </article>
      ))}
    </div>
  );
}
