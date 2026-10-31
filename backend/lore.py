"""
RepoRequiem - the voice.

The archaeology is factual; this module gives it a mouth. It talks to a local
open-weight model through Ollama (or any OpenAI-compatible endpoint) and falls
back to a deterministic archivist when no model is awake. The fallback is not a
crash path: it is a feature, so the demo works with the internet off.
"""

from __future__ import annotations

import json
import os
import random
import re
import textwrap
from datetime import datetime

import requests

from archaeology import record_facts

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL_OVERRIDE = os.getenv("OLLAMA_MODEL", "").strip()
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() not in {"0", "false", "no"}
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))

# OpenAI-compatible escape hatch (still for open-weight models only).
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

SYSTEM = textwrap.dedent("""
    You are the Archivist of RepoRequiem. You read the history of a software
    repository and speak for the files that are no longer there.

    Voice: patient, literary, restrained. Gothic without theatre. Short
    sentences. Concrete nouns. No exclamation marks, no emoji, no jokes, no
    "as an AI". You are not a haunted house; you are a person with a lamp in
    an archive at night.

    HARD RULE: use only the FACTS provided. Never invent file names, people,
    dates, numbers, commits or events. If a fact is not given, leave it out.
    Do not mention that you were given facts. Never claim knowledge beyond them.
""").strip()

LORE_SCHEMA = textwrap.dedent("""
    Reply with ONLY a JSON object, no markdown fences, in this exact shape:
    {
      "epitaph": "one line carved on the repository's headstone, max 90 characters",
      "inscription": "2-3 sentences for the stone, max 65 words, use real dates and names from the facts",
      "haunting": [
        {"title": "3-5 words", "text": "70-110 words about one true detail from the facts"},
        {"title": "3-5 words", "text": "70-110 words"},
        {"title": "3-5 words", "text": "70-110 words"},
        {"title": "3-5 words", "text": "70-110 words"}
      ],
      "laments": [
        {"path": "exact/path/from/THE BURIED", "text": "one first-person sentence spoken by that deleted file, max 30 words"}
      ]
    }
    Include one lament for each path listed under THE BURIED (up to 8). Use the
    exact path strings. The four chapters should cover different parts of the
    record: the buried files, the cursed commits, the forgotten survivors or
    extinct language, and the repository's last words. Do not repeat facts
    between chapters. No headings inside the text.

    Each chapter must be a full paragraph of 70-110 words. A chapter shorter
    than 60 words is discarded. Do not summarise in a single sentence; let the
    detail breathe.
""").strip()


class ModelUnavailable(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------

def _ollama_models() -> list[str]:
    try:
        res = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=4)
        res.raise_for_status()
        return [m.get("name", "") for m in res.json().get("models", []) if m.get("name")]
    except Exception:
        return []


def _pick_model(available: list[str]) -> str | None:
    if MODEL_OVERRIDE and (not available or MODEL_OVERRIDE in available):
        return MODEL_OVERRIDE
    if not available:
        return MODEL_OVERRIDE or None

    def score(name: str) -> int:
        n = name.lower()
        s = 0
        for family in ("qwen3", "qwen2.5", "qwen2", "gemma3", "gemma2", "llama3.1",
                       "llama3", "mistral", "phi4", "phi3", "deepseek", "granite"):
            if family in n:
                s += 6
                break
        if "instruct" in n:
            s += 3
        if "vl" in n or "vision" in n:
            # Vision models write weaker prose and often spend the budget thinking.
            s -= 3
        if "coder" in n:
            s -= 8
        if "embed" in n:
            s -= 20
        if "70b" in n or "72b" in n:
            s -= 4
        return s

    best = max(available, key=score)
    # A vision or code model can spend the whole timeout before admitting it
    # cannot write this. If nothing suitable is installed, fall back at once
    # instead of making the visitor wait. OLLAMA_MODEL still forces a choice.
    if score(best) <= 3:
        return None
    return best


def _ollama_chat(messages: list[dict], json_mode: bool) -> str:
    model = _pick_model(_ollama_models())
    if not model:
        raise ModelUnavailable("No suitable local model found")
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.85, "num_predict": 1600, "top_p": 0.92},
    }
    # Thinking models would spend the token budget before writing the record.
    # Only send the flag to families that understand it.
    if re.search(r"qwen3|deepseek-r1|gpt-oss|magistral", model, re.IGNORECASE):
        payload["think"] = False
    if json_mode:
        payload["format"] = "json"
    try:
        res = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=LLM_TIMEOUT)
        res.raise_for_status()
        data = res.json()
        content = (data.get("message") or {}).get("content", "")
        if not content.strip():
            raise ModelUnavailable("Empty response")
        return content
    except requests.RequestException as exc:
        raise ModelUnavailable(f"Ollama unreachable: {exc.__class__.__name__}") from exc


def _openai_chat(messages: list[dict], json_mode: bool) -> str:
    if not (OPENAI_BASE and OPENAI_MODEL):
        raise ModelUnavailable("No OpenAI-compatible endpoint configured")
    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": 0.85,
        "max_tokens": 1600,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        res = requests.post(
            f"{OPENAI_BASE}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {OPENAI_KEY}"} if OPENAI_KEY else {},
            timeout=LLM_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        raise ModelUnavailable(f"Endpoint failed: {exc.__class__.__name__}") from exc


def chat(messages: list[dict], json_mode: bool = False) -> str:
    if not LLM_ENABLED:
        raise ModelUnavailable("LLM disabled")
    if OPENAI_BASE and OPENAI_MODEL:
        return _openai_chat(messages, json_mode)
    return _ollama_chat(messages, json_mode)


def engine_name() -> str:
    if OPENAI_BASE and OPENAI_MODEL:
        return OPENAI_MODEL
    return _pick_model(_ollama_models()) or ""


# --------------------------------------------------------------------------
# JSON helpers
# --------------------------------------------------------------------------

def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ModelUnavailable("Model did not return valid JSON")


def _clean_text(value, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"\s+", " ", value).strip().strip('"')
    value = value.replace("—", " - ")
    if len(value) > limit:
        value = value[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:") + "."
    return value


def _validate_lore(data: dict, record: dict) -> dict:
    known = {g["path"] for g in record["ghosts"]}
    epitaph = _clean_text(data.get("epitaph"), 110)
    inscription = _clean_text(data.get("inscription"), 420)

    chapters = []
    for item in data.get("haunting") or []:
        if not isinstance(item, dict):
            continue
        title = _clean_text(item.get("title"), 48)
        text = _clean_text(item.get("text"), 760)
        if text and len(text) > 120:
            chapters.append({"title": title or "Untitled", "text": text})
    chapters = chapters[:5]

    laments = {}
    for item in data.get("laments") or []:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if path in known:
            text = _clean_text(item.get("text"), 240)
            if text:
                laments[path] = text

    if not epitaph or not inscription or len(chapters) < 3:
        raise ModelUnavailable("Model response was too thin")
    return {"epitaph": epitaph, "inscription": inscription,
            "haunting": chapters, "laments": laments}


# --------------------------------------------------------------------------
# Deterministic archivist (works offline, no model)
# --------------------------------------------------------------------------

def _year(value: str | None) -> str:
    return (value or "")[:4] or "unknown"


def _nice_date(value: str | None) -> str:
    if not value:
        return "an unrecorded night"
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d %B %Y").lstrip("0")
    except ValueError:
        return value[:10]


LAMENT_OPENERS = [
    "I was {path}.",
    "My name was {path}.",
    "They called me {path}.",
    "I lived at {path}.",
]
LAMENT_CLOSERS = [
    "{killer} closed me in a commit called \u201c{subject}\u201d.",
    "{killer} took me out with \u201c{subject}\u201d and did not look back.",
    "The last hand on me belonged to {killer}, in \u201c{subject}\u201d.",
    "I ended on {killer}\u2019s commit, \u201c{subject}\u201d.",
]


def fallback_lore(record: dict) -> dict:
    meta, life, totals = record["meta"], record["life"], record["totals"]
    name = meta["name"]
    rng = random.Random(name + str(totals["commits"]))

    epitaph = f"{name}: {_year(life['first_commit'])} - {_year(life['last_commit'])}"
    if life["abandoned"]:
        epitaph = f"{name}: left the lights on for {life['silent_for_days'] // 365} years"
    elif totals["files_vanished"]:
        epitaph = f"{name}: {totals['commits']} commits, {totals['files_vanished']} files it could not keep"
    else:
        epitaph = f"{name}: {totals['commits']} commits, nothing buried, everything older"

    inscription = (
        f"Opened on {_nice_date(life['first_commit'])} and last touched on "
        f"{_nice_date(life['last_commit'])}, {life['lifespan_days']} days later. "
        f"{totals['souls']} people wrote here. {totals['files_vanished']} files were removed "
        f"and never returned."
    )
    if life["abandoned"]:
        inscription += f" Nothing has moved in {life['silent_for_days']} days."

    chapters = []
    ghosts = record["ghosts"]
    if ghosts:
        g = ghosts[0]
        chapters.append({
            "title": "The First Burial",
            "text": (
                f"{g['path']} was alive for {g['age_days']} days and changed {g['commits']} times. "
                f"Its last lines were written by {g['author']}. {g['killed_by']} removed it in "
                f"\u201c{g['last_subject']}\u201d. The file was {g['churn']} lines of work, and then it "
                f"was a name in a log. Nobody wrote it a note. The repository kept the shape of the "
                f"space where it used to be."
            ),
        })
    if record["cursed"]:
        c = record["cursed"][0]
        chapters.append({
            "title": c["title"],
            "text": (
                f"On {_nice_date(c['date'])}, {c['author']} made a commit called "
                f"\u201c{c['subject']}\u201d. {c['detail']} The record does not say whether anyone "
                f"reviewed it. The record only says it happened, and that the repository carried "
                f"it forward like a stone in a pocket."
            ),
        })
    if record["revenants"]:
        r = record["revenants"][0]
        chapters.append({
            "title": "It Came Back",
            "text": (
                f"{r['path']} was deleted, and then it was not. It returned on "
                f"{_nice_date(r['died'])} in \u201c{r['last_subject']}\u201d, as if the repository "
                f"had changed its mind. Most files do not get that. Most files stay gone, and the "
                f"build learns to work around the hole."
            ),
        })
    elif record["forgotten"]:
        f = record["forgotten"][0]
        chapters.append({
            "title": "Still Here",
            "text": (
                f"{f['path']} is still in the tree. It has not changed in {f['age_days']} days. "
                f"Every build reads it and every reader skips it. {f['killed_by']} was the last "
                f"person to touch it, in \u201c{f['last_subject']}\u201d. Being forgotten and being "
                f"deleted are different deaths."
            ),
        })
    if record["extinct"]:
        e = record["extinct"][0]
        chapters.append({
            "title": "A Dead Language",
            "text": (
                f"The repository once spoke {e['language']}. {e['files_lost']} of those files are "
                f"gone now, and no living file answers in that language. The syntax is still "
                f"documented somewhere. Nothing here needs it anymore."
            ),
        })
    if life["last_words"]:
        chapters.append({
            "title": "Last Words",
            "text": (
                f"The last thing anyone wrote here was \u201c{life['last_words']}\u201d, by "
                f"{life['last_author']}, on {_nice_date(life['last_date'])}. It is not a goodbye. "
                f"People rarely know which commit is the last one. The repository simply stopped "
                f"receiving, and the quiet became part of the record."
            ),
        })
    if len(chapters) < 2:
        chapters.append({
            "title": "An Orderly House",
            "text": (
                f"{name} has {totals['commits']} commits and {totals['souls']} authors. It has "
                f"kept almost everything it was given. There is little buried here, which is its "
                f"own kind of strangeness. The archive is quiet because nothing was lost, not "
                f"because nothing happened."
            ),
        })
        chapters.append({
            "title": "What Remains",
            "text": (
                f"Every file in the tree is a decision someone made and did not undo. "
                f"{totals['added']:,} lines were added; {totals['deleted']:,} were taken away. "
                f"The difference is what you are reading now."
            ),
        })

    laments = {}
    for g in ghosts[:8]:
        opener = rng.choice(LAMENT_OPENERS).format(path=g["path"])
        closer = rng.choice(LAMENT_CLOSERS).format(
            killer=g["killed_by"], subject=g["last_subject"]
        )
        middle = f" I held {g['lines'] or g['churn']} lines for {g['age_days']} days."
        laments[g["path"]] = f"{opener}{middle} {closer}"

    return {
        "epitaph": epitaph,
        "inscription": inscription,
        "haunting": chapters[:5],
        "laments": laments,
        "source": {"engine": "fallback", "model": "", "ok": True,
                   "reason": "No local model was awake, so the Archivist read the record aloud."},
    }


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def generate_lore(record: dict) -> dict:
    facts = record_facts(record)
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                "FACTS:\n" + facts + "\n\n"
                "Write the ghost record for this repository.\n\n" + LORE_SCHEMA
            ),
        },
    ]
    try:
        raw = chat(messages, json_mode=True)
        lore = _validate_lore(_extract_json(raw), record)
        lore["source"] = {"engine": "ollama", "model": engine_name(), "ok": True, "reason": ""}
        return lore
    except ModelUnavailable as exc:
        lore = fallback_lore(record)
        lore["source"]["reason"] = str(exc)
        return lore


def _retrieve(record: dict, question: str, limit: int = 4) -> tuple[list[dict], list[str]]:
    q = question.lower()
    tokens = {t for t in re.findall(r"[a-z0-9_./-]{3,}", q) if t not in
              {"the", "and", "who", "what", "when", "why", "did", "was", "were", "are",
               "you", "your", "tell", "about", "this", "that", "repo", "repository", "file"}}
    ghosts, names = [], []
    for g in record["ghosts"] + record["revenants"] + record["forgotten"]:
        path = g["path"].lower()
        if path in q or any(t in path for t in tokens):
            ghosts.append(g)
        if len(ghosts) >= limit:
            break
    for a in record["authors"]:
        if a["name"].lower() in q or any(t in a["name"].lower() for t in tokens):
            names.append(
                f"{a['name']}: {a['commits']} commits, first {str(a['first_seen'])[:10]}, "
                f"last {str(a['last_seen'])[:10]}, +{a['added']}/-{a['deleted']}"
            )
    return ghosts, names


def answer_seance(record: dict, question: str, history: list[dict] | None = None) -> dict:
    question = (question or "").strip()[:500]
    if not question:
        return {"answer": "Ask the archive something. It is listening.", "engine": "none"}

    ghosts, names = _retrieve(record, question)
    context_lines = [record_facts(record)]
    if ghosts:
        context_lines.append("\nMATCHING FILES:")
        for g in ghosts:
            context_lines.append(
                f"- {g['path']} ({g['kind']}): born {str(g.get('born'))[:10]}, "
                f"died/last touched {str(g.get('died'))[:10]}, {g['commits']} commits, "
                f"last by {g['killed_by']} in \"{g['last_subject']}\" [{g['commit']}]"
                + (f", last words: \"{g['buried_note']}\"" if g.get("buried_note") else "")
            )
    if names:
        context_lines.append("\nMATCHING SOULS: " + " | ".join(names))

    messages = [
        {"role": "system", "content": SYSTEM + "\n\nAnswer in 1-3 sentences, in the Archivist's voice."},
        {
            "role": "user",
            "content": "FACTS:\n" + "\n".join(context_lines)
            + "\n\nQUESTION: " + question
            + "\n\nAnswer only from the facts. If the record does not say, say that plainly.",
        },
    ]
    try:
        raw = chat(messages, json_mode=False)
        answer = _clean_text(raw, 700)
        if not answer:
            raise ModelUnavailable("empty")
        return {"answer": answer, "engine": "ollama", "model": engine_name(),
                "matched": [g["path"] for g in ghosts]}
    except ModelUnavailable as exc:
        return {"answer": _fallback_answer(record, question, ghosts, names, str(exc)),
                "engine": "fallback", "model": "", "matched": [g["path"] for g in ghosts]}


def _fallback_answer(record, question, ghosts, names, reason) -> str:
    if ghosts:
        g = ghosts[0]
        if g["kind"] == "forgotten":
            return (f"{g['path']} is still here. It has not changed in {g['age_days']} days; "
                    f"the last hand on it was {g['killed_by']}, in \u201c{g['last_subject']}\u201d.")
        return (f"{g['path']} was removed by {g['killed_by']} in \u201c{g['last_subject']}\u201d "
                f"on {_nice_date(g['died'])}. It had {g['commits']} commits behind it. "
                f"The record does not say why.")
    if names:
        return names[0] + ". The archive keeps no opinion of them, only the count."
    if record["ghosts"]:
        g = record["ghosts"][0]
        return (f"The loudest grave is {g['path']}, removed by {g['killed_by']} on "
                f"{_nice_date(g['died'])}. There are {record['totals']['files_vanished']} "
                f"others. I can name any of them.")
    return ("Nothing was buried here. The archive is complete, which is rare, and "
            "therefore suspicious.")
