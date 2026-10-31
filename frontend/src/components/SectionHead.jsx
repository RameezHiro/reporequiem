export default function SectionHead({ numeral, title, note, id }) {
  return (
    <div id={id} className="mb-10 scroll-mt-24">
      <div className="flex items-end justify-between gap-6 border-b hairline pb-5">
        <div className="flex items-start gap-4 sm:gap-6">
          <span className="shrink-0 pt-2 font-mono text-[11px] tracking-[0.3em] text-ember/90">{numeral}</span>
          <h2 className="font-display text-3xl font-light leading-none tracking-tight text-bone sm:text-4xl">
            {title}
          </h2>
        </div>
        {note ? (
          <span className="hidden shrink-0 font-mono text-[10px] uppercase tracking-[0.22em] text-dust sm:block">
            {note}
          </span>
        ) : null}
      </div>
    </div>
  );
}
