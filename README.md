# RepoRequiem

**Every repository has ghosts.**

RepoRequiem is git archaeology with a voice. It reads a repository's own
objects — deleted files, reverted commits, dead languages, the commit at 3 a.m.
— and lets a **local open-weight model** speak for what is no longer there.

The model never invents the record. Every name, date, path and commit in the
output is mined deterministically from git first; the model is only given those
facts and asked to narrate them. If no model is available, a deterministic
offline Archivist reads the same facts aloud. The demo works with the network
cable pulled.

Built for **DEV Hacktoberfest 2026, Week 4 — "Ghost in the Machine"** (`#hf26challenge`).

---

## What it finds

| What | How it is found |
| --- | --- |
| **The buried** | Paths that appear in history but not in `HEAD`. Each gets a birth date, a death date, a lifespan, churn, the commit that removed it, and its last surviving lines. |
| **Revenants** | Files deleted and later restored. |
| **The forgotten** | Files still in the tree that nobody has touched in years. |
| **Cursed commits** | 3 a.m. commits, Friday the 13th ships, revert spirals, fix-storms, the widest and heaviest commits, WIP messages. |
| **Extinct languages** | Languages present only among vanished files, with no living file left speaking them. |
| **Unmerged branches** | Branches whose tips never became ancestors of `HEAD`. |
| **Souls** | Authors, their commit counts, first and last appearance, lines added and removed. |
| **The record's life** | First commit, last commit, lifespan, days of silence, last words. |

The output is a **ghost record**: an epitaph, an inscription, four chapters of
haunting, a lament for each buried file, and a graveyard you can open file by
file. It can be exported as Markdown, and you can ask the archive questions in a
séance that answers only from the same facts.

## Why this is an open-source AI project

- **Open-weight models** through [Ollama](https://ollama.com): any local model
  works. The app picks a sensible one automatically and respects `OLLAMA_MODEL`.
- **An open escape hatch**: any OpenAI-compatible endpoint serving an open-weight
  model can be used instead (`OPENAI_BASE_URL`, `OPENAI_MODEL`).
- **No cloud dependency in the core loop.** Inference, archaeology and rendering
  all happen on your machine.
- **Grounded prompting as a design constraint**, not a prompt suggestion: the
  model only receives `record_facts()` output, the reply is schema-validated, and
  every lament is checked against the set of paths that actually died.
- **Graceful degradation**: a deterministic archivist keeps the product useful
  when the model is missing, slow or broken.

## Quick start

Requirements: **Python 3.11+**, **Node 20+**, **git**, and optionally **Ollama**.

```bash
git clone <this-repo> reporequiem
cd reporequiem

# 1. Frontend
cd frontend
npm install
npm run build

# 2. Backend
cd ../backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>. The backend serves the built frontend and the API
from one port. Add `?demo=1` to open the bundled haunted repository directly.

### The local model

```bash
ollama pull qwen3-vl:4b     # or any instruct model you like
ollama serve
```

The app discovers models from `/api/tags`. To force one:

```bash
# Windows PowerShell
$env:OLLAMA_MODEL = "gemma3:4b"
# macOS/Linux
export OLLAMA_MODEL="gemma3:4b"
```

The picker prefers text instruct models. A thinking model can spend the whole
token budget before it writes the record, so if you see the offline Archivist
with a thinking model installed, force a non-thinking instruct model (for
example `gemma3:4b`) with `OLLAMA_MODEL`.

If generation fails for any reason, the reading still completes and the record
says **"facts only · no model"** rather than pretending.

### Frontend development

```bash
cd frontend
npm run dev
```

Vite runs on `:5173` and proxies `/api` to `:8000` (see `vite.config.js`).

## The demo repository

`scripts/make_demo_repo.py` builds `lumen-mail`, a small repository with a
scripted history: a CoffeeScript era that goes extinct, files that die, one that
returns, a 3 a.m. commit, a revert spiral, a Friday the 13th ship, an unmerged
branch, and a quiet abandonment. The history is real to git, so the scanner
reads it exactly like a normal repository. It is generated at runtime into
`backend/.demo/` (gitignored) the first time you press **Open the demo**.

## How grounded prompting works

1. `analyze()` walks `git log --numstat --no-renames` and `git ls-tree`, builds a
   per-file ledger, and assembles the `record` dict.
2. `record_facts()` renders that dict as plain text — no prose, no speculation.
3. The system prompt forbids inventing facts and forbids mentioning that facts
   were provided. The schema asks for JSON only.
4. `_extract_json()` tolerates fences and stray prose; `_validate_lore()` enforces
   limits, drops chapters that are too thin, and discards any lament whose path
   is not in the set of buried files.
5. If anything fails validation, `fallback_lore()` speaks the same facts without
   a model.

That last step is the important one: **the fallback is a feature, not an error
screen.** It makes the project demonstrable anywhere, and it keeps the archive
honest when the machine is not.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Version, detected voice, server time. |
| `POST` | `/api/scan` | `{ "source": "/path" \| "github.com/owner/repo" }` → record. |
| `POST` | `/api/demo` | Build and read the bundled haunted repository. |
| `POST` | `/api/scan/{id}/haunt` | Generate (and cache) the ghost record. |
| `POST` | `/api/scan/{id}/seance` | `{ "question": "...", "history": [] }` → grounded answer. |
| `GET` | `/api/scan/{id}` | Cached record and lore. |
| `GET` | `/api/scan/{id}/export` | Markdown download. |
| `DELETE` | `/api/scan/{id}` | Forget a reading and clean up clones. |

Scans live in memory (`MAX_SCANS`, default 16) and expire after six hours
(`SCAN_TTL_SECONDS`). Public clones are deleted with the scan.

### Public repositories

Only HTTPS clones from `github.com`, `gitlab.com`, `bitbucket.org` and
`codeberg.org` are allowed; the URL is validated before `git clone` runs. The
clone is `--single-branch --no-checkout` and read-only. Private repositories
should be read through the local-path mode on your own machine.

## Configuration

Copy `.env.example` to `.env` or set the variables in your shell.

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint. |
| `OLLAMA_MODEL` | *(auto)* | Force a specific model. |
| `LLM_ENABLED` | `true` | Set `false` to use the offline Archivist only. |
| `LLM_TIMEOUT` | `300` | Seconds allowed for one generation. |
| `OPENAI_BASE_URL` / `OPENAI_MODEL` / `OPENAI_API_KEY` | *(empty)* | OpenAI-compatible fallback (open-weight models only). |
| `MAX_COMMITS` | `15000` | History cap per reading. |
| `MAX_SCANS` | `16` | In-memory scan slots. |
| `SCAN_TTL_SECONDS` | `21600` | Scan lifetime. |
| `ALLOW_LOCAL_PATHS` | `true` | Allow reading paths on the server. Set `false` on a public deployment. |

## Tests

```bash
cd backend
python -m unittest discover -s tests -v
```

The suite covers the archaeology engine against the generated fixture, the JSON
extraction and validation boundary, and the deterministic fallback — no model or
network required.

## Deployment

The included `Dockerfile` builds the frontend and serves it from FastAPI. A
`render.yaml` blueprint is included for Render's Docker runtime.

The hosted deployment is deliberately configured with `LLM_ENABLED=false`: there
is no Ollama on that machine, so it demonstrates the offline Archivist path.
Point it at an open-weight OpenAI-compatible endpoint if you want a hosted voice.

```bash
docker build -t reporequiem .
docker run --rm -p 8000:8000 reporequiem
```

## Limitations

- Files are detected as deleted when a commit removes all their lines
  (`--no-renames`, non-binary). This is a heuristic, not a semantic truth.
- History is capped; a very large repository can be read only in part, and the
  record says so.
- Git timestamps are author/committer dates as recorded; rewritten history is
  taken at face value.
- The séance retrieves by path, author and facts. It is not a general code
  search engine.
- Similes are the model's; facts are git's. The app is careful to keep the line
  between them visible.

## License

MIT. See [LICENSE](LICENSE).
