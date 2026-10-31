import { useMemo, useState } from "react";
import { api } from "../api";
import { ageLabel, fmtDate, fmtNum, fmtYear, span } from "../format";
import Curses from "./Curses";
import GhostModal from "./GhostModal";
import Graveyard from "./Graveyard";
import Haunting from "./Haunting";
import { Branch, Download } from "./Icons";
import Reveal from "./Reveal";
import Seance from "./Seance";
import SectionHead from "./SectionHead";
import Souls from "./Souls";
import Timeline from "./Timeline";

function Stat({ label, value, sub }) {
  return (
    <div className="border-b border-r hairline bg-void px-4 py-5 sm:px-5">
      <p className="label mb-2">{label}</p>
      <p className="font-display text-3xl font-light leading-none text-bone sm:text-[34px]">
        {value}
      </p>
      {sub ? <p className="mt-1.5 font-mono text-[9px] text-dust">{sub}</p> : null}
    </div>
  );
}

export default function Record({ scan, lore, lorePending, onNew }) {
  const { record, scan_id: scanId } = scan;
  const { meta, life, totals } = record;
  const [selected, setSelected] = useState(null);

  const source = lore?.source;
  const voice = source?.model || (source ? "offline archivist" : "…");
  const engineOnline = Boolean(source?.model);

  const note = useMemo(() => {
    const bits = [];
    if (totals.files_vanished) bits.push(`${totals.files_vanished} buried`);
    if (record.revenants.length) bits.push(`${record.revenants.length} revenant${record.revenants.length === 1 ? "" : "s"}`);
    if (record.forgotten.length) bits.push(`${record.forgotten.length} still standing`);
    return bits.join(" · ");
  }, [record, totals]);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b hairline bg-void/85 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 py-3 sm:px-10">
          <div className="flex min-w-0 items-center gap-3">
            <span className="hidden font-mono text-[10px] uppercase tracking-[0.28em] text-dust sm:block">
              Repo<span className="text-ember">/</span>Requiem
            </span>
            <span className="hidden h-3 w-px bg-white/10 sm:block" />
            <div className="min-w-0">
              <p className="truncate font-display text-lg leading-none text-bone">{meta.name}</p>
              <p className="mt-1 truncate font-mono text-[9px] uppercase tracking-[0.16em] text-dust">
                {meta.branch} · {meta.head}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <span className="hidden items-center gap-2 border border-white/10 px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.14em] text-dust md:flex">
              <span
                className={`h-1 w-1 rounded-full ${engineOnline ? "bg-moss" : "bg-dust"}`}
              />
              {voice}
            </span>
            <a
              href={api.exportUrl(scanId)}
              className="flex items-center gap-2 border border-white/10 px-3 py-1.5 font-mono text-[9px] uppercase tracking-[0.16em] text-ash transition-colors hover:border-candle/40 hover:text-candle"
            >
              <Download className="h-3 w-3" />
              <span className="hidden sm:inline">Export</span>
            </a>
            <button
              type="button"
              onClick={onNew}
              className="border border-ember/30 bg-ember/10 px-3 py-1.5 font-mono text-[9px] uppercase tracking-[0.16em] text-candle transition-colors hover:bg-ember/20"
            >
              New reading
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-5 pb-24 sm:px-10">
        {/* Hero ------------------------------------------------------------ */}
        <section className="pb-12 pt-14 sm:pt-20">
          <div className="mb-6 flex flex-wrap items-center gap-x-3 gap-y-2 font-mono text-[9px] uppercase tracking-[0.22em] text-dust">
            <span className="text-ember/80">Ghost record</span>
            <span className="text-dust/40">/</span>
            <span>{fmtDate(life.first_commit)} → {fmtDate(life.last_commit)}</span>
            <span className="text-dust/40">/</span>
            <span>{ageLabel(life.lifespan_days)} of history</span>
            {life.abandoned ? (
              <span className="ml-1 border border-blood/50 bg-blood/15 px-2 py-0.5 text-bone/70">
                abandoned
              </span>
            ) : null}
          </div>

          {lore ? (
            <h1 className="max-w-5xl font-display text-[clamp(2.5rem,6.4vw,5.4rem)] font-light leading-[0.98] tracking-[-0.025em] text-bone animate-rise">
              {lore.epitaph}
            </h1>
          ) : (
            <div className="max-w-3xl space-y-4">
              <h1 className="font-display text-[clamp(2.5rem,6vw,4.6rem)] font-light leading-[0.98] tracking-tight text-bone">
                {meta.name}
              </h1>
              <div className="skeleton h-4 w-2/3" />
              <div className="skeleton h-4 w-1/2" />
            </div>
          )}

          <div className="mt-7 grid gap-8 md:grid-cols-[1fr_auto] md:items-end">
            {lore ? (
              <p className="max-w-2xl text-pretty text-[15px] leading-[1.85] text-ash animate-rise" style={{ animationDelay: "120ms" }}>
                {lore.inscription}
              </p>
            ) : (
              <p className="max-w-2xl font-display text-lg italic text-dust">
                The Archivist is still reading. The facts are already on the table.
              </p>
            )}
            <div className="font-mono text-[9px] uppercase leading-relaxed tracking-[0.18em] text-dust md:text-right">
              <div>Spoken by</div>
              <div className={engineOnline ? "text-candle/90" : "text-ash"}>
                {lore ? voice : "…"}
              </div>
              <div className="mt-2 text-dust/70">
                {source?.engine === "fallback" ? "facts only · no model" : "local inference"}
              </div>
            </div>
          </div>

          <div className="mt-12 grid grid-cols-2 border-l border-t hairline sm:grid-cols-3 lg:grid-cols-6">
            <Stat label="Commits" value={fmtNum(totals.commits)} sub={meta.truncated ? "capped" : "read in full"} />
            <Stat label="Souls" value={fmtNum(totals.souls)} sub="authors" />
            <Stat label="Buried" value={fmtNum(totals.files_vanished)} sub="files removed" />
            <Stat label="Living" value={fmtNum(totals.files_live)} sub="files still here" />
            <Stat label="Cursed" value={fmtNum(record.cursed.length)} sub="commits the log flinches at" />
            <Stat
              label="Silent for"
              value={fmtNum(life.silent_for_days)}
              sub={life.silent_for_days === 1 ? "day" : "days"}
            />
          </div>
        </section>

        <Timeline timeline={record.timeline} first={life.first_commit} last={life.last_commit} />

        {life.last_words ? (
          <Reveal className="grid gap-4 border-b hairline py-9 md:grid-cols-[180px_1fr] md:gap-10">
            <div>
              <p className="label">The last words</p>
              <p className="mt-2 font-mono text-[9px] text-dust">
                {life.last_author} · {fmtDate(life.last_date, "short")}
              </p>
            </div>
            <blockquote className="font-display text-2xl font-light italic leading-snug text-bone/90 sm:text-[28px]">
              “{life.last_words}”
            </blockquote>
          </Reveal>
        ) : null}

        {/* Haunting -------------------------------------------------------- */}
        <section className="pt-20">
          <Reveal>
            <SectionHead numeral="I" title="The haunting" note={engineOnline ? `spoken by ${voice}` : "read from the record"} />
          </Reveal>
          <Reveal delay={80}>
            <Haunting lore={lore} pending={lorePending} />
          </Reveal>
          {lore?.source?.engine === "fallback" ? (
            <Reveal delay={120} className="mt-8">
              <p className="border-l border-white/10 pl-4 font-mono text-[10px] leading-relaxed text-dust">
                The local model was not reachable, so the Archivist read the facts aloud
                without one. Every name, date and commit below is still from the repository.
              </p>
            </Reveal>
          ) : null}
        </section>

        {/* Graveyard ------------------------------------------------------- */}
        <section className="pt-20">
          <Reveal>
            <SectionHead numeral="II" title="The graveyard" note={note || "nothing buried"} />
          </Reveal>
          <Reveal delay={60}>
            <Graveyard
              ghosts={record.ghosts}
              revenants={record.revenants}
              forgotten={record.forgotten}
              laments={lore?.laments || {}}
              lorePending={lorePending}
              onSelect={setSelected}
            />
          </Reveal>
        </section>

        {/* Cursed commits --------------------------------------------------- */}
        {record.cursed.length ? (
          <section className="pt-20">
            <Reveal>
              <SectionHead numeral="III" title="Cursed commits" note="things the log still flinches at" />
            </Reveal>
            <Reveal delay={60}>
              <Curses cursed={record.cursed} />
            </Reveal>
          </section>
        ) : null}

        {/* Souls ------------------------------------------------------------ */}
        <section className="pt-20">
          <Reveal>
            <SectionHead
              numeral={record.cursed.length ? "IV" : "III"}
              title="The souls"
              note={`${fmtNum(totals.souls)} people, ${fmtNum(totals.added)} lines added`}
            />
          </Reveal>
          <Reveal delay={60}>
            <Souls authors={record.authors} />
          </Reveal>
        </section>

        {/* Other timelines -------------------------------------------------- */}
        {(record.extinct.length || record.branches.length) ? (
          <section className="pt-20">
            <Reveal>
              <SectionHead
                numeral={record.cursed.length ? "V" : "IV"}
                title="Other timelines"
                note="what the repository stopped being"
              />
            </Reveal>
            <div className="grid gap-10 md:grid-cols-2">
              {record.extinct.length ? (
                <Reveal delay={60}>
                  <p className="label mb-5">Languages it stopped speaking</p>
                  <div className="space-y-5">
                    {record.extinct.map((language) => (
                      <div key={language.language} className="flex items-baseline justify-between gap-4 border-b hairline pb-4">
                        <div>
                          <p className="font-display text-3xl font-light italic text-bone/90">
                            {language.language}
                          </p>
                          <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.16em] text-dust">
                            no living file answers in it
                          </p>
                        </div>
                        <p className="shrink-0 font-mono text-[10px] text-ember/80">
                          {language.files_lost} lost
                        </p>
                      </div>
                    ))}
                  </div>
                </Reveal>
              ) : null}

              {record.branches.length ? (
                <Reveal delay={120}>
                  <p className="label mb-5">Branches that never merged</p>
                  <div className="space-y-4">
                    {record.branches.map((branch) => (
                      <div key={branch.name} className="flex items-start gap-3 border-b hairline pb-4">
                        <Branch className="mt-1 h-3.5 w-3.5 shrink-0 text-dust" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-mono text-[11px] text-bone/80">{branch.name}</p>
                          <p className="mt-1 font-mono text-[9px] text-dust">
                            {branch.author} · {fmtDate(branch.date, "short")}
                          </p>
                        </div>
                        <span className="shrink-0 font-mono text-[8px] uppercase tracking-[0.16em] text-dust/70">
                          never merged
                        </span>
                      </div>
                    ))}
                  </div>
                </Reveal>
              ) : null}
            </div>
          </section>
        ) : null}

        {/* Séance ----------------------------------------------------------- */}
        <section className="pt-20">
          <Reveal>
            <SectionHead
              numeral={romanFor(record)}
              title="The séance"
              note="answers grounded in the record"
            />
          </Reveal>
          <Reveal delay={60}>
            <Seance
              scanId={scanId}
              ghosts={[...record.ghosts, ...record.forgotten]}
              authors={record.authors}
              engine={voice}
              engineOnline={engineOnline}
            />
          </Reveal>
        </section>

        {meta.truncated ? (
          <p className="mt-10 font-mono text-[9px] uppercase tracking-[0.16em] text-dust/70">
            Only the most recent {fmtNum(meta.max_commits)} commits were read.
          </p>
        ) : null}
      </main>

      <footer className="border-t hairline">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-5 py-7 font-mono text-[9px] uppercase tracking-[0.18em] text-dust sm:flex-row sm:items-center sm:justify-between sm:px-10">
          <span>
            Read with RepoRequiem · {fmtNum(meta.commit_count)} commits · {span(life.first_commit, life.last_commit)}
          </span>
          <div className="flex gap-5">
            <a href={api.exportUrl(scanId)} className="transition-colors hover:text-candle">
              Export the record
            </a>
            <button type="button" onClick={onNew} className="transition-colors hover:text-candle">
              New reading
            </button>
          </div>
        </div>
      </footer>

      <GhostModal
        ghost={selected}
        lore={selected ? lore?.laments?.[selected.path] : null}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

function romanFor(record) {
  let n = 3;
  if (record.cursed.length) n += 1;
  if (record.extinct.length || record.branches.length) n += 1;
  return ["I", "II", "III", "IV", "V", "VI"][n];
}
