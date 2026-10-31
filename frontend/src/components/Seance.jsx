import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Candle, Send } from "./Icons";

function suggestionFor(ghost) {
  const name = ghost.path.split("/").pop();
  return ghost.kind === "forgotten"
    ? `Why is ${name} still here?`
    : `Who killed ${name}?`;
}

export default function Seance({ scanId, ghosts = [], authors = [], engine, engineOnline }) {
  const [messages, setMessages] = useState([
    {
      role: "archivist",
      text:
        "The archive is open. Ask about a file, a person, or the quiet at the end. " +
        "I will only tell you what the record actually says.",
    },
  ]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const scroller = useRef(null);

  const suggestions = [
    ghosts[0] ? suggestionFor(ghosts[0]) : null,
    ghosts[1] ? suggestionFor(ghosts[1]) : null,
    "When did it go quiet?",
    authors[0] ? `Who is ${authors[0].name}?` : null,
  ].filter(Boolean).slice(0, 3);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, pending]);

  const ask = async (question) => {
    const text = (question ?? input).trim();
    if (!text || pending) return;
    const history = messages.map((m) => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.text,
    }));
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setPending(true);
    try {
      const result = await api.seance(scanId, text, history);
      setMessages((prev) => [
        ...prev,
        { role: "archivist", text: result.answer, engine: result.engine },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "archivist",
          text: `The archive did not answer. ${error.message}`,
          error: true,
        },
      ]);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="relative border border-white/10 bg-crypt/60">
      <div className="flex items-start justify-between gap-6 border-b hairline px-5 py-4 sm:px-7">
        <div className="flex items-center gap-3">
          <Candle className="h-4 w-4 text-candle animate-flicker" />
          <div>
            <p className="label">The séance</p>
            <p className="mt-1 font-display text-lg leading-none text-bone">
              Ask the repository what happened.
            </p>
          </div>
        </div>
        <span className="hidden shrink-0 items-center gap-2 font-mono text-[9px] uppercase tracking-[0.18em] text-dust sm:flex">
          <span
            className={`h-1 w-1 rounded-full ${engineOnline ? "bg-moss" : "bg-dust"}`}
          />
          {engineOnline ? engine : "offline archivist"}
        </span>
      </div>

      <div ref={scroller} className="max-h-[380px] space-y-5 overflow-y-auto px-5 py-6 sm:px-7">
        {messages.map((message, i) => (
          <div key={i} className={message.role === "user" ? "pl-8 sm:pl-16" : "pr-4"}>
            <p
              className={`mb-1.5 font-mono text-[8px] uppercase tracking-[0.24em] ${
                message.role === "user" ? "text-dust" : "text-ember/70"
              }`}
            >
              {message.role === "user" ? "you" : "the archive"}
            </p>
            <p
              className={
                message.role === "user"
                  ? "border-l border-white/15 pl-4 font-mono text-[12px] leading-relaxed text-bone/80"
                  : `font-display text-[19px] leading-[1.6] ${
                      message.error ? "text-ember/80" : "text-bone/90"
                    }`
              }
            >
              {message.text}
            </p>
          </div>
        ))}
        {pending ? (
          <div className="flex items-center gap-2 pl-1 font-mono text-[10px] uppercase tracking-[0.2em] text-dust">
            <span className="h-1 w-1 animate-breathe rounded-full bg-candle" />
            <span className="h-1 w-1 animate-breathe rounded-full bg-candle [animation-delay:200ms]" />
            <span className="h-1 w-1 animate-breathe rounded-full bg-candle [animation-delay:400ms]" />
            <span className="ml-2">reading the record</span>
          </div>
        ) : null}
      </div>

      {suggestions.length ? (
        <div className="flex flex-wrap gap-2 border-t hairline px-5 py-3 sm:px-7">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => ask(s)}
              disabled={pending}
              className="border border-white/10 px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.12em] text-dust transition-colors hover:border-candle/40 hover:text-candle disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
      ) : null}

      <form
        onSubmit={(event) => {
          event.preventDefault();
          ask();
        }}
        className="flex items-center gap-3 border-t hairline px-5 py-3 sm:px-7"
      >
        <span className="font-mono text-sm text-ember">›</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={pending}
          placeholder="Who deleted src/parser.coffee?"
          aria-label="Ask the archive a question"
          className="min-w-0 flex-1 bg-transparent font-mono text-[12px] text-bone placeholder:text-dust/60 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          aria-label="Send question"
          className="shrink-0 p-1.5 text-dust transition-colors hover:text-candle disabled:opacity-30"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
