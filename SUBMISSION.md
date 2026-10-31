# Submission checklist

Target: **DEV Hacktoberfest 2026 — Week 4: Ghost in the Machine**
Challenge: <https://dev.to/challenges/hacktoberfest-week4-2026-10-26>
Required tag: `#hf26challenge`
Deadline: **31 October 2026**

## Before publishing

- [x] Put the code on a public repository: <https://github.com/RameezHiro/reporequiem>.
- [x] Add the repository URL to `DEV_POST.md`. There is no hosted demo; the post
      explains that the history stays local.
- [ ] Upload `docs/screenshots/*.png` to DEV and replace the relative image paths.
      The current screenshots show the **offline Archivist**. That is the honest
      state of this machine: the installed models are a vision model and a code
      model, both of which the picker now skips. Do not relabel them as model output.
- [ ] Record a 20–40 second screen capture (optional but strong): open demo →
      graveyard → open a headstone → ask the séance one question.
- [ ] Read `DEV_POST.md` out loud and rewrite anything that does not sound like you.
- [ ] Confirm the tags: `hf26challenge`, plus up to three others.

## What the judges are scoring

| Criterion | Where it is answered |
| --- | --- |
| Writing quality (heaviest) | `DEV_POST.md` — one concrete idea, a real build story, no launch-post filler. |
| Relevance to the theme | The ghost is the repository's own deleted history, not a chatbot persona. |
| Creativity | Git archaeology as a haunted archive; certificates of removal; revenants; cursed commits; a séance grounded in the record. |
| Technical execution | Deterministic mining, grounded prompting, schema validation, path allowlist, deterministic fallback, tests, Docker/Render config. |
| Open-source AI at the core | Local open-weight model via Ollama, with an OpenAI-compatible escape hatch; the app is fully useful when the model is absent. |

## Verify locally

```bash
# backend tests (no model, no network)
cd backend
python -m unittest discover -s tests -v

# frontend production build
cd ../frontend
npm run build

# run the app
cd ../backend
uvicorn main:app --port 8000
# open http://127.0.0.1:8000/?demo=1
```

Quick API smoke test:

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s -X POST http://127.0.0.1:8000/api/demo
```

## Deploy (Render)

1. Push the repository to GitHub.
2. In Render: **New → Blueprint**, select the repository. `render.yaml` is picked
   up automatically.
3. Wait for the Docker build; the health check is `/api/health`.
4. On the free instance there is no Ollama, so `LLM_ENABLED=false` and the demo
   uses the deterministic Archivist. That is intentional and disclosed in the
   post. Do not claim the hosted demo uses a model.
5. Optional: set `LLM_ENABLED=true` plus `OPENAI_BASE_URL`, `OPENAI_MODEL` and
   `OPENAI_API_KEY` for an open-weight hosted endpoint, and say so in the post.

## Publish on DEV

1. New post → paste `DEV_POST.md` (front matter is optional on DEV; set the title,
   description, tags and cover image in the editor instead).
2. Add the `#hf26challenge` tag. The editor may suggest `#hacktoberfest`; DEV allows
   four tags total.
3. Preview the images and the code blocks on mobile.
4. Publish, then add the post URL to the challenge submission field if one is
   present.

## Honest limitations to keep in the post

- Deletion detection is heuristic (`--no-renames`, non-binary, removes lines and
  adds none).
- Large histories are capped by `MAX_COMMITS`; the UI says when a scan is partial.
- The hosted demo uses the offline Archivist unless a model endpoint is configured.
- The model writes the prose; git supplies every fact. The post should not claim
  the model "analyzes" the repository.
