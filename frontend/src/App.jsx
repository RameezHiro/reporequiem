import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import Landing from "./components/Landing";
import Reading from "./components/Reading";
import Record from "./components/Record";
import { fmtYear, fmtNum } from "./format";

function minimalLore(record) {
  const { meta, life, totals } = record;
  return {
    epitaph: `${meta.name}: ${fmtYear(life.first_commit)} — ${fmtYear(life.last_commit)}`,
    inscription: `${fmtNum(totals.commits)} commits by ${fmtNum(totals.souls)} people. ${fmtNum(
      totals.files_vanished
    )} files were removed. The last words were “${life.last_words}”.`,
    haunting: [
      {
        title: "The record",
        text: `The repository was opened on ${fmtYear(life.first_commit)} and last touched on ${fmtYear(
          life.last_commit
        )}. It has been silent for ${fmtNum(life.silent_for_days)} days. The model could not be reached, so this is the bare record: names, dates, and the count of what is missing.`,
      },
    ],
    laments: {},
    source: { engine: "fallback", model: "", ok: true, reason: "The voice could not be reached." },
  };
}

export default function App() {
  const [stage, setStage] = useState("idle");
  const [scan, setScan] = useState(null);
  const [lore, setLore] = useState(null);
  const [lorePending, setLorePending] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState("");
  const [health, setHealth] = useState({ model: "", ok: false, local_paths: true });
  const token = useRef(0);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ model: "", ok: false, local_paths: true }));
  }, []);

  const begin = useCallback(async (fetcher, label) => {
    const current = ++token.current;
    setError("");
    setSource(label);
    setStage("reading");
    setScan(null);
    setLore(null);
    setLorePending(false);

    try {
      const data = await fetcher();
      if (current !== token.current) return;
      setScan(data);
      setStage("record");
      setLorePending(true);
      window.scrollTo(0, 0);

      api
        .haunt(data.scan_id)
        .then((result) => {
          if (current !== token.current) return;
          setLore(result.lore);
          setLorePending(false);
        })
        .catch((err) => {
          if (current !== token.current) return;
          setLore(minimalLore(data.record));
          setLorePending(false);
          setError(err.message);
        });
    } catch (err) {
      if (current !== token.current) return;
      setStage("idle");
      setError(err.message);
    }
  }, []);

  const onScan = useCallback((value) => begin(() => api.scan(value), value), [begin]);

  const onDemo = useCallback(
    () => begin(() => api.demo(), "the demo repository · lumen-mail"),
    [begin]
  );

  // ?demo=1 opens the fixture directly, so links in the write-up land on a full record.
  const demoOpened = useRef(false);
  useEffect(() => {
    if (demoOpened.current) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") !== "1") return;
    demoOpened.current = true;
    onDemo();
  }, [onDemo]);

  const onNew = useCallback(() => {
    token.current += 1;
    if (scan?.scan_id) api.discard(scan.scan_id);
    setStage("idle");
    setScan(null);
    setLore(null);
    setError("");
    setSource("");
    window.scrollTo(0, 0);
  }, [scan]);

  const onCancel = useCallback(() => {
    token.current += 1;
    setStage("idle");
    setSource("");
    setError("");
  }, []);

  return (
    <div className="grain relative">
      {stage === "idle" ? (
        <Landing
          onScan={onScan}
          onDemo={onDemo}
          busy={false}
          error={error}
          voice={health.model}
          localPaths={health.local_paths !== false}
        />
      ) : null}

      {stage === "reading" ? <Reading source={source} onCancel={onCancel} /> : null}

      {stage === "record" && scan ? (
        <Record
          scan={scan}
          lore={lore}
          lorePending={lorePending}
          onNew={onNew}
        />
      ) : null}
    </div>
  );
}
