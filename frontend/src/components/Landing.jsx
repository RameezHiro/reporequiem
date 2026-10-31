import { useEffect, useState } from "react";
import { ArrowRight, Candle, Branch } from "./Icons";

const LOCAL_EXAMPLES = ["C:\\Users\\you\\projects\\lumen-mail", "~/code/old-side-project"];
const URL_EXAMPLES = ["github.com/pallets/flask", "github.com/expressjs/express"];

function isLocalHost() {
  if (typeof window === "undefined") return true;
  return ["localhost", "127.0.0.1"].includes(window.location.hostname);
}

export default function Landing({ onScan, onDemo, busy, error, voice, localPaths = true }) {
  const [mode, setMode] = useState(localPaths && isLocalHost() ? "local" : "url");
  const [value, setValue] = useState("");

  useEffect(() => {
    if (!localPaths && mode === "local") setMode("url");
  }, [localPaths, mode]);

  const examples = mode === "local" ? LOCAL_EXAMPLES : URL_EXAMPLES;
  const tabs = [
    { id: "local", label: "Local path" },
    { id: "url", label: "Public repository" },
  ].filter((tab) => tab.id !== "local" || localPaths);

  const submit = (event) => {
    event.preventDefault();
    const source = value.trim();
    if (source) onScan(source);
  };

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div className="absolute -top-40 left-1/2 h-[560px] w-[900px] -translate-x-1/2 rounded-full bg-ember/[0.06] blur-3xl animate-fog" />
        <div className="absolute bottom-0 right-0 h-[420px] w-[520px] rounded-full bg-candle/[0.04] blur-3xl" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      </div>

      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 pt-7 sm:px-10">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-full border border-white/15">
            <Candle className="h-4 w-4 text-candle" />
          </span>
          <span className="font-mono text-[11px] uppercase tracking-[0.32em] text-bone">
            Repo<span className="text-dust">/</span>Requiem
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden font-mono text-[10px] uppercase tracking-[0.24em] text-dust sm:block">
            HF26 · Week 4 · Ghost in the Machine
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-ember animate-flicker" />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center px-6 py-20 sm:px-10 sm:py-24">
        <div className="max-w-4xl">
          <p className="label mb-7 animate-rise" style={{ animationDelay: "40ms" }}>
            Git archaeology · an open-weight séance
          </p>
          <h1
            className="font-display text-[13.5vw] font-light leading-[0.86] tracking-[-0.03em] text-bone sm:text-[86px] lg:text-[104px] animate-rise"
            style={{ animationDelay: "120ms" }}
          >
            Every repository
            <br />
            <span className="italic text-candle">has ghosts.</span>
          </h1>
          <p
            className="mt-9 max-w-2xl text-pretty text-[15px] leading-relaxed text-ash sm:text-base animate-rise"
            style={{ animationDelay: "220ms" }}
          >
            Deleted files. Reverted commits. A language it stopped speaking. RepoRequiem
            exhumes the real history of a repository and gives a local open-weight model
            the facts to speak for the dead.
          </p>

          <form
            onSubmit={submit}
            className="mt-12 animate-rise"
            style={{ animationDelay: "300ms" }}
          >
            <div className="mb-4 flex items-center gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setMode(tab.id)}
                  className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.22em] transition-colors ${
                    mode === tab.id
                      ? "text-bone"
                      : "text-dust hover:text-ash"
                  }`}
                >
                  {tab.label}
                  {mode === tab.id ? (
                    <span className="mt-1 block h-px w-full bg-ember" />
                  ) : null}
                </button>
              ))}
            </div>

            <div className="group flex items-center gap-3 border-b border-white/20 pb-3 transition-colors focus-within:border-candle/70 sm:gap-4">
              <span className="font-mono text-sm text-ember">›</span>
              <input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                disabled={busy}
                spellCheck={false}
                autoComplete="off"
                aria-label={mode === "local" ? "Local repository path" : "Public repository URL"}
                placeholder={mode === "local" ? LOCAL_EXAMPLES[0] : URL_EXAMPLES[0]}
                className="min-w-0 flex-1 bg-transparent font-mono text-[13px] text-bone placeholder:text-dust/70 focus:outline-none disabled:opacity-50 sm:text-sm"
              />
              <button
                type="submit"
                disabled={busy || !value.trim()}
                className="group/btn flex shrink-0 items-center gap-2 bg-ember/10 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-candle transition-colors hover:bg-ember/20 disabled:cursor-not-allowed disabled:opacity-40 sm:px-5"
              >
                Disturb the soil
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover/btn:translate-x-0.5" />
              </button>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
              <button
                type="button"
                onClick={onDemo}
                disabled={busy}
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-ash transition-colors hover:text-candle disabled:opacity-40"
              >
                Or open the demo repository →
              </button>
              {examples.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setValue(example)}
                  className="hidden font-mono text-[10px] text-dust transition-colors hover:text-ash sm:block"
                >
                  {example}
                </button>
              ))}
            </div>

            {error ? (
              <p className="mt-6 max-w-2xl border-l border-blood/80 bg-blood/10 px-4 py-3 font-mono text-[11px] leading-relaxed text-bone/80">
                {error}
              </p>
            ) : (
              <p className="mt-6 max-w-2xl font-mono text-[10px] leading-relaxed text-dust">
                {localPaths
                  ? "Local paths are read in place, never uploaded. Public repositories are cloned read-only and deleted after the reading."
                  : "Public repositories are cloned read-only and deleted after the reading. This deployment does not read server paths."}
              </p>
            )}
          </form>
        </div>

        <div
          className="mt-24 grid grid-cols-2 gap-px border-y hairline bg-white/[0.06] animate-rise sm:grid-cols-4"
          style={{ animationDelay: "420ms" }}
        >
          {[
            ["Reads", "git objects only"],
            ["Voice", voice || "offline archivist"],
            ["Cost", "nothing per reading"],
            ["Privacy", "no accounts, no telemetry"],
          ].map(([key, val]) => (
            <div key={key} className="bg-void px-5 py-5">
              <div className="label mb-2">{key}</div>
              <div className="font-mono text-[11px] text-bone/85">
                <span className="block truncate">{val}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-20 grid gap-10 sm:grid-cols-3">
          {[
            [
              "01",
              "Mined, not imagined",
              "Every name, date and commit comes from the repository's own objects. The model is never allowed to invent a fact.",
            ],
            [
              "02",
              "A voice you can hold",
              "Any Ollama model works. Swap it, fine-tune it, or pull the network cable: the Archivist still reads the record.",
            ],
            [
              "03",
              "Nothing leaves the room",
              "No sign-in, no upload, no API key. Your code and your history stay on the machine that already had them.",
            ],
          ].map(([n, title, body]) => (
            <div key={n} className="border-t hairline pt-5">
              <div className="mb-3 flex items-center justify-between">
                <span className="font-mono text-[10px] tracking-[0.28em] text-ember/80">{n}</span>
                {n === "02" ? <Branch className="h-4 w-4 text-dust" /> : null}
              </div>
              <h3 className="font-display text-xl text-bone">{title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-ash">{body}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className="mx-auto flex w-full max-w-6xl flex-col gap-3 border-t hairline px-6 py-7 font-mono text-[10px] uppercase tracking-[0.2em] text-dust sm:flex-row sm:items-center sm:justify-between sm:px-10">
        <span>Built for Hacktoberfest 2026 · #hf26challenge</span>
        <span className="text-dust/70">The archive does not forget. It only stops being read.</span>
      </footer>
    </div>
  );
}
