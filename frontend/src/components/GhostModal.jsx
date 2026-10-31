import { useEffect } from "react";
import { Close } from "./Icons";
import { fmtDate, fmtNum, ageLabel } from "../format";

function Row({ label, children }) {
  return (
    <div className="grid grid-cols-[92px_1fr] gap-4 border-b hairline py-3 sm:grid-cols-[130px_1fr]">
      <dt className="label pt-0.5">{label}</dt>
      <dd className="font-mono text-[11px] leading-relaxed text-bone/80">{children}</dd>
    </div>
  );
}

export default function GhostModal({ ghost, lore, onClose }) {
  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  if (!ghost) return null;
  const lines = (ghost.last_lines || "").split("\n").filter(Boolean);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center overflow-y-auto bg-void/80 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-label={`Record for ${ghost.path}`}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="relative w-full max-w-2xl animate-rise border border-white/10 bg-crypt shadow-[0_40px_120px_-40px_rgba(0,0,0,1)]">
        <div className="flex items-start justify-between gap-6 border-b hairline px-6 py-5 sm:px-8">
          <div className="min-w-0">
            <p className="label mb-2">
              {ghost.kind === "forgotten" ? "Still in the tree" : "Certificate of removal"}
            </p>
            <h3 className="break-words font-mono text-[13px] leading-relaxed text-bone">
              {ghost.path}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 p-1 text-dust transition-colors hover:text-bone"
          >
            <Close className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-6 py-6 sm:px-8">
          {lore ? (
            <p className="mb-7 border-l border-candle/40 pl-4 font-display text-2xl italic leading-snug text-candle/90">
              “{lore}”
            </p>
          ) : null}

          {ghost.kind === "forgotten" ? (
            <p className="mb-7 font-display text-lg leading-relaxed text-ash">
              This file never died. It is still built, still read, and no one has changed it
              in {ageLabel(ghost.age_days)}. Being forgotten and being deleted are different deaths.
            </p>
          ) : (
            <p className="mb-7 font-display text-lg leading-relaxed text-ash">
              {ghost.kind === "revenant"
                ? "This file was removed, and then it was not. Something brought it back."
                : `This file lived for ${ageLabel(ghost.age_days)} and then stopped existing in the
                   branch it was born in.`}
            </p>
          )}

          <dl className="border-t hairline">
            <Row label="Born">{ghost.born ? fmtDate(ghost.born) : "unknown"}</Row>
            <Row label={ghost.kind === "forgotten" ? "Last touched" : "Died"}>
              {ghost.died ? fmtDate(ghost.died) : "unknown"}
            </Row>
            <Row label={ghost.kind === "forgotten" ? "Untouched for" : "Lifespan"}>
              {ageLabel(ghost.age_days)}
              {ghost.age_days >= 60 ? (
                <span className="text-dust"> · {fmtNum(ghost.age_days)} days</span>
              ) : null}
            </Row>
            <Row label="Commits">{fmtNum(ghost.commits)}</Row>
            <Row label="Churn">
              +{fmtNum(ghost.added)} / −{fmtNum(ghost.deleted)}
            </Row>
            <Row label={ghost.kind === "forgotten" ? "Last hand" : "Killed by"}>{ghost.killed_by}</Row>
            <Row label="Commit">
              <span className="text-candle/90">{ghost.commit}</span> · {ghost.last_subject}
            </Row>
            {ghost.buried_note ? <Row label="Left behind">{ghost.buried_note}</Row> : null}
          </dl>

          {lines.length ? (
            <div className="mt-7">
              <p className="label mb-3">Its last known lines</p>
              <pre className="overflow-x-auto border border-white/10 bg-void/60 p-4 font-mono text-[11px] leading-relaxed text-bone/70">
                {lines.map((line, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="select-none text-dust/50">{String(i + 1).padStart(2, "0")}</span>
                    <span className="whitespace-pre-wrap break-all">{line}</span>
                  </div>
                ))}
              </pre>
            </div>
          ) : (
            <p className="mt-7 font-mono text-[10px] uppercase tracking-[0.18em] text-dust">
              No readable remains were recovered.
            </p>
          )}
        </div>

        <div className="flex items-center justify-between border-t hairline px-6 py-4 sm:px-8">
          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-dust">
            {ghost.language || "unknown language"} · {fmtNum(ghost.lines)} lines at death
          </span>
          <button
            type="button"
            onClick={onClose}
            className="font-mono text-[10px] uppercase tracking-[0.2em] text-ash transition-colors hover:text-candle"
          >
            Close the record
          </button>
        </div>
      </div>
    </div>
  );
}
