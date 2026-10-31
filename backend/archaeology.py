"""
RepoRequiem - git archaeology.

Everything in this module is deterministic. No model, no network, no guessing:
we read the repository the way a coroner reads a body. The language model in
`lore.py` is only allowed to speak about the facts produced here.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

# Files that are noise in a graveyard.
NOISE_PATTERNS = re.compile(
    r"(^|/)(node_modules|dist|build|\.next|vendor|__pycache__|\.venv|venv|"
    r"target|coverage|\.nyc_output|\.pytest_cache)(/|$)"
)
NOISE_NAMES = re.compile(
    r"(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|"
    r"composer\.lock|Gemfile\.lock|\.DS_Store|\.gitignore)$",
    re.IGNORECASE,
)
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf", ".zip",
    ".gz", ".tar", ".mp3", ".mp4", ".wav", ".woff", ".woff2", ".ttf", ".otf",
    ".eot", ".so", ".dll", ".exe", ".dylib", ".class", ".jar", ".pyc", ".wasm",
    ".psd", ".ai", ".sketch", ".fig",
}

LANG_BY_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".vue": "Vue", ".svelte": "Svelte",
    ".rb": "Ruby", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".swift": "Swift", ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++",
    ".cs": "C#", ".php": "PHP", ".pl": "Perl", ".pm": "Perl", ".lua": "Lua",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".ps1": "PowerShell",
    ".sql": "SQL", ".r": "R", ".jl": "Julia", ".scala": "Scala", ".clj": "Clojure",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".hs": "Haskell",
    ".dart": "Dart", ".coffee": "CoffeeScript", ".elm": "Elm", ".nim": "Nim",
    ".zig": "Zig", ".asm": "Assembly", ".s": "Assembly", ".f": "Fortran",
    ".f90": "Fortran", ".cob": "COBOL", ".pas": "Pascal", ".vb": "Visual Basic",
    ".groovy": "Groovy", ".ml": "OCaml", ".fs": "F#", ".sol": "Solidity",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".md": "Markdown",
}

GONE_MARKERS = re.compile(
    r"(TODO|FIXME|HACK|XXX|DEPRECATED|deprecated|do not use|DO NOT USE|"
    r"legacy|temporary|temp fix|for now|remove me|abandon|goodbye|farewell)",
)

MAX_CONTENT_BYTES = 8000


class GitError(RuntimeError):
    pass


def _git(repo: str, *args: str, timeout: int = 60) -> str:
    """Run a read-only git command and return stdout."""
    # -c core.quotepath=false keeps non-ASCII paths readable.
    cmd = ["git", "-C", repo, "-c", "core.quotepath=false", *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            env={
                **os.environ,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_PAGER": "cat",
                "LC_ALL": "C.UTF-8",
            },
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git timed out after {timeout}s: {' '.join(args[:3])}") from exc
    except FileNotFoundError as exc:
        raise GitError("git is not installed or not on PATH") from exc

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        raise GitError(err[-1] if err else f"git exited with {proc.returncode}")
    return proc.stdout.decode("utf-8", "replace")


def _parse_dt(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Keep the author's original offset: 21:00 in New York is 21:00, not 02:00.
    return dt


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _days_between(a: datetime | None, b: datetime | None) -> int:
    if not a or not b:
        return 0
    return max(0, (b - a).days)


def _human_lang(path: str) -> str | None:
    ext = os.path.splitext(path)[1].lower()
    return LANG_BY_EXT.get(ext)


def _is_noise(path: str) -> bool:
    return bool(NOISE_PATTERNS.search(path) or NOISE_NAMES.search(path))


def _is_binary_path(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in BINARY_EXT


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:160]
    return ""


def _interesting_line(text: str) -> str:
    """The most human line we can find in a dead file."""
    candidates = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) > 200:
            continue
        if GONE_MARKERS.search(line):
            return line[:200]
        if line.startswith(("#", "//", "/*", "*", "--", ";")) and len(line) > 12:
            candidates.append(line)
    return (candidates[-1] if candidates else "")[:200]


# --------------------------------------------------------------------------
# Repository targets
# --------------------------------------------------------------------------

def resolve_local_path(raw: str) -> str:
    path = os.path.abspath(os.path.expanduser((raw or "").strip().strip('"')))
    if not os.path.isdir(path):
        raise GitError(f"No directory at {path}")
    return path


PUBLIC_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}


def _normalize_public_url(url: str) -> str:
    """Accept `owner/repo` and `github.com/owner/repo`, return an https URL."""
    url = (url or "").strip()
    if re.fullmatch(r"[\w.-]+/[\w.-]+", url):
        return f"https://github.com/{url}"
    if re.match(r"^(www\.)?(github|gitlab|bitbucket|codeberg)\.(com|org)/", url, re.IGNORECASE):
        return f"https://{url}"
    return url


def clone_public_repo(url: str, timeout: int = 180) -> tuple[str, str]:
    """Clone a public repository (history included) into a temp dir.

    Returns (temp_dir, remote_label). The caller is responsible for cleanup.
    Returns a path that must be removed with `cleanup_clone`.
    """
    url = _normalize_public_url(url)
    parsed = urlparse(url)
    allowed = PUBLIC_HOSTS
    if parsed.scheme != "https" or parsed.hostname not in allowed:
        raise GitError("Only public https repositories on github.com, gitlab.com, "
                       "bitbucket.org or codeberg.org can be cloned. "
                       "Use a local path for anything private.")
    if not re.fullmatch(r"/[\w.\-/]+", parsed.path or ""):
        raise GitError("That does not look like a repository URL.")

    tmp = tempfile.mkdtemp(prefix="requiem-")
    repo = os.path.join(tmp, "repo")
    proc = subprocess.run(
        ["git", "clone", "--single-branch", "--no-checkout", "--quiet", url, repo],
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if proc.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        err = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        raise GitError(err[-1] if err else "clone failed")
    return repo, url


def cleanup_clone(repo: str) -> None:
    parent = os.path.dirname(os.path.abspath(repo))
    if os.path.basename(parent).startswith("requiem-") or os.path.basename(repo) == "repo":
        shutil.rmtree(parent, ignore_errors=True)


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

def analyze(repo_path: str, max_commits: int = 15000) -> dict:
    repo_path = os.path.abspath(repo_path)
    try:
        root = _git(repo_path, "rev-parse", "--show-toplevel").strip()
    except GitError:
        root = repo_path
    if not os.path.isdir(root):
        raise GitError("Not a git repository.")

    head = _git(root, "rev-parse", "HEAD").strip()
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() or "HEAD"
    remote = ""
    try:
        remote = _git(root, "config", "--get", "remote.origin.url").strip()
    except GitError:
        remote = ""

    # ---- commit stream -------------------------------------------------
    log_out = _git(
        root,
        "log",
        "--no-renames",
        "--pretty=format:%x01%H%x02%an%x02%ae%x02%aI%x02%s",
        "--numstat",
        f"--max-count={max_commits}",
        timeout=180,
    )

    commits: list[dict] = []
    file_events: dict[str, list[dict]] = defaultdict(list)
    for line in log_out.splitlines():
        if not line:
            continue
        if line.startswith("\x01"):
            parts = line[1:].split("\x02", 4)
            if len(parts) < 5:
                continue
            commits.append(
                {
                    "sha": parts[0],
                    "author": parts[1] or "unknown",
                    "email": parts[2],
                    "date": parts[3],
                    "subject": parts[4][:300],
                    "files": [],
                    "added": 0,
                    "deleted": 0,
                }
            )
            continue
        if not commits:
            continue
        fields = line.split("\t", 2)
        if len(fields) != 3:
            continue
        adds, dels, path = fields
        is_binary = adds == "-" or dels == "-"
        a = 0 if is_binary else int(adds or 0)
        d = 0 if is_binary else int(dels or 0)
        path = path.strip()
        if not path or path.startswith('"'):
            continue
        cur = commits[-1]
        cur["files"].append({"path": path, "added": a, "deleted": d, "binary": is_binary})
        cur["added"] += a
        cur["deleted"] += d
        file_events[path].append(
            {
                "sha": cur["sha"],
                "date": cur["date"],
                "author": cur["author"],
                "subject": cur["subject"],
                "added": a,
                "deleted": d,
                "deleted_file": d > 0 and a == 0 and not is_binary,
            }
        )

    truncated = len(commits) >= max_commits
    commits.sort(key=lambda c: c["date"], reverse=True)

    # ---- per-file ledger (commits arrive newest first) ------------------
    ledger: dict[str, dict] = {}
    for commit in commits:
        for change in commit["files"]:
            path = change["path"]
            entry = ledger.get(path)
            if entry is None:
                entry = {
                    "path": path,
                    "first_date": commit["date"],
                    "last_date": commit["date"],
                    "last_sha": commit["sha"],
                    "last_subject": commit["subject"],
                    "last_author": commit["author"],
                    "commits": 0,
                    "added": 0,
                    "deleted": 0,
                    "authors": Counter(),
                }
                ledger[path] = entry
            entry["first_date"] = commit["date"]  # always the oldest we have seen
            entry["commits"] += 1
            entry["added"] += change["added"]
            entry["deleted"] += change["deleted"]
            if commit["author"]:
                entry["authors"][commit["author"]] += 1

    live_paths = set()
    try:
        tree = _git(root, "ls-tree", "-r", "--name-only", "-z", "HEAD", timeout=120)
        live_paths = {p for p in tree.split("\0") if p}
    except GitError:
        live_paths = set()

    vanished_paths = [p for p in ledger if p not in live_paths]

    # ---- root commit / lifespan ----------------------------------------
    try:
        root_out = _git(root, "log", "--max-parents=0", "--reverse",
                        "--format=%H%x02%aI%x02%an", timeout=60).strip()
        root_parts = root_out.split("\x02") if root_out else []
    except GitError:
        root_parts = []

    dates = [c["date"] for c in commits if c["date"]]
    first_date = _parse_dt(root_parts[1]) if len(root_parts) > 1 else (
        _parse_dt(min(dates)) if dates else None
    )
    last_date = _parse_dt(max(dates)) if dates else None
    now = datetime.now(timezone.utc)

    # ---- authors --------------------------------------------------------
    authors: dict[str, dict] = {}
    for commit in commits:
        dt = _parse_dt(commit["date"])
        a = authors.setdefault(
            commit["author"],
            {
                "name": commit["author"],
                "commits": 0,
                "added": 0,
                "deleted": 0,
                "first_seen": commit["date"],
                "last_seen": commit["date"],
                "email": commit["email"],
            },
        )
        a["commits"] += 1
        a["added"] += commit["added"]
        a["deleted"] += commit["deleted"]
        if commit["date"] < a["first_seen"]:
            a["first_seen"] = commit["date"]
        if commit["date"] > a["last_seen"]:
            a["last_seen"] = commit["date"]
        del dt

    author_list = sorted(authors.values(), key=lambda x: x["commits"], reverse=True)
    for a in author_list:
        a["share"] = round(100 * a["commits"] / max(1, len(commits)))
        a["alive"] = bool(a["last_seen"] == last_date.isoformat()) if last_date else False

    # ---- vanished ghosts ------------------------------------------------
    def ghost_rank(path: str) -> float:
        e = ledger[path]
        return e["commits"] * 2 + min(e["added"] + e["deleted"], 5000) / 50

    vanished_candidates = [
        p for p in vanished_paths
        if not _is_noise(p) and not _is_binary_path(p)
    ]
    vanished_candidates.sort(key=ghost_rank, reverse=True)
    top_vanished = vanished_candidates[:14]

    ghosts = []
    for path in top_vanished:
        e = ledger[path]
        events = sorted(file_events.get(path, []), key=lambda x: x["date"])
        death = next((ev for ev in reversed(events) if ev["deleted_file"]), None)
        death_date = _parse_dt(death["date"]) if death else None
        born_date = _parse_dt(e["first_date"])
        dominant_author = e["authors"].most_common(1)[0][0] if e["authors"] else e["last_author"]

        snippet, lines, buried_note = "", 0, ""
        if death:
            try:
                parent = _git(root, "rev-parse", f"{death['sha']}^").strip()
                blob = _git(root, "show", f"{parent}:{path}", timeout=30)[:MAX_CONTENT_BYTES]
                lines = blob.count("\n") + (1 if blob and not blob.endswith("\n") else 0)
                raw_lines = [ln for ln in blob.splitlines() if ln.strip()]
                snippet = "\n".join(raw_lines[:3])[:400]
                buried_note = _interesting_line(blob)
            except GitError:
                pass

        ghosts.append(
            {
                "path": path,
                "kind": "buried",
                "language": _human_lang(path),
                "born": _iso(born_date),
                "died": _iso(death_date),
                "age_days": _days_between(born_date, death_date),
                "commits": e["commits"],
                "churn": e["added"] + e["deleted"],
                "added": e["added"],
                "deleted": e["deleted"],
                "author": dominant_author,
                "killed_by": death["author"] if death else e["last_author"],
                "last_subject": death["subject"] if death else e["last_subject"],
                "commit": death["sha"][:10] if death else e["last_sha"][:10],
                "lines": lines,
                "last_lines": snippet,
                "buried_note": buried_note,
            }
        )

    # ---- revenants: died, then rose ------------------------------------
    revenants = []
    for path in vanished_paths + list(live_paths):
        if _is_noise(path) or _is_binary_path(path):
            continue
        events = sorted(file_events.get(path, []), key=lambda x: x["date"])
        died = None
        for ev in events:
            if ev["deleted_file"]:
                died = ev
            elif died and (ev["added"] > 0 or ev["deleted"] > 0):
                revenants.append(
                    {
                        "path": path,
                        "kind": "revenant",
                        "language": _human_lang(path),
                        "born": died["date"],
                        "died": ev["date"],
                        "age_days": _days_between(_parse_dt(died["date"]), _parse_dt(ev["date"])),
                        "commits": ledger[path]["commits"],
                        "churn": ledger[path]["added"] + ledger[path]["deleted"],
                        "added": ledger[path]["added"],
                        "deleted": ledger[path]["deleted"],
                        "author": ev["author"],
                        "killed_by": ev["author"],
                        "last_subject": ev["subject"],
                        "commit": ev["sha"][:10],
                        "lines": 0,
                        "last_lines": "",
                        "buried_note": "",
                    }
                )
                died = None
        if len(revenants) >= 6:
            break

    # ---- forgotten survivors -------------------------------------------
    orphans = []
    for path in live_paths:
        if path not in ledger or _is_noise(path) or _is_binary_path(path):
            continue
        e = ledger[path]
        last = _parse_dt(e["last_date"])
        orphans.append(
            {
                "path": path,
                "kind": "forgotten",
                "language": _human_lang(path),
                "born": e["first_date"],
                "died": e["last_date"],
                "age_days": _days_between(last, now),
                "commits": e["commits"],
                "churn": e["added"] + e["deleted"],
                "added": e["added"],
                "deleted": e["deleted"],
                "author": e["last_author"],
                "killed_by": e["last_author"],
                "last_subject": e["last_subject"],
                "commit": e["last_sha"][:10],
                "lines": 0,
                "last_lines": "",
                "buried_note": "",
            }
        )
    # The longer a living file has gone untouched, the more forgotten it is.
    orphans.sort(key=lambda x: (x["age_days"], -x["commits"]), reverse=True)
    forgotten = orphans[:8]

    # ---- extinct languages ---------------------------------------------
    live_langs = Counter()
    dead_langs = Counter()
    for p in live_paths:
        lang = _human_lang(p)
        if lang and not _is_noise(p):
            live_langs[lang] += 1
    for p in vanished_paths:
        lang = _human_lang(p)
        if lang and not _is_noise(p):
            dead_langs[lang] += 1
    extinct = [
        {"language": lang, "files_lost": n, "files_left": live_langs.get(lang, 0)}
        for lang, n in dead_langs.most_common()
        if live_langs.get(lang, 0) == 0 and n >= 1
    ][:6]

    # ---- cursed commits -------------------------------------------------
    cursed: list[dict] = []
    used_commits: set[str] = set()

    def add_curse(title: str, detail: str, commit: dict | None, severity: str = "minor"):
        if not commit or commit["sha"] in used_commits:
            return
        used_commits.add(commit["sha"])
        cursed.append(
            {
                "title": title,
                "detail": detail,
                "severity": severity,
                "commit": commit["sha"][:10],
                "subject": commit["subject"],
                "author": commit["author"],
                "date": commit["date"],
            }
        )

    if commits:
        churn_king = max(commits, key=lambda c: c["added"] + c["deleted"])
        add_curse(
            "The Heaviest Stone",
            f"{churn_king['added'] + churn_king['deleted']:,} lines moved in a single commit.",
            churn_king,
            "grave",
        )
        widest = max(commits, key=lambda c: len(c["files"]))
        add_curse(
            "The Widest Grave",
            f"{len(widest['files'])} files touched at once.",
            widest,
            "grave",
        )

        night = [c for c in commits if _parse_dt(c["date"]) and _parse_dt(c["date"]).hour < 5]
        if night:
            add_curse(
                "The 3 A.M. Visitor",
                "Committed while the house was asleep.",
                night[0],
                "major",
            )

        reverts = [c for c in commits if re.match(r"(?i)revert", c["subject"])]
        if reverts:
            add_curse(
                "The Unburial",
                f"{len(reverts)} commit{'s' if len(reverts) != 1 else ''} spent undoing other commits.",
                reverts[0],
                "major",
            )

        fixes = sum(1 for c in commits if re.search(r"(?i)\b(fix|hotfix|oops|whoops)\b", c["subject"]))
        if fixes >= 3:
            add_curse(
                "The Fixer",
                f"{fixes} commits describe themselves as a fix. The wound kept opening.",
                next((c for c in commits if re.search(r"(?i)\bfix\b", c["subject"])), None),
                "major",
            )

        wips = [c for c in commits if re.search(r"(?i)\b(wip|tmp|temp|asdf|test)\b", c["subject"])]
        if wips:
            add_curse(
                "The Unfinished Sentence",
                f"{len(wips)} commit{'s' if len(wips) != 1 else ''} left a thought unfinished.",
                wips[0],
                "minor",
            )

        deleted_most = max(
            (c for c in commits if c["files"]),
            key=lambda c: sum(1 for f in c["files"] if f["deleted"] > 0 and f["added"] == 0),
            default=None,
        )
        if deleted_most:
            killed = sum(1 for f in deleted_most["files"] if f["deleted"] > 0 and f["added"] == 0)
            if killed:
                add_curse(
                    "The Harvester",
                    f"{killed} file{'s' if killed != 1 else ''} deleted in one stroke.",
                    deleted_most,
                    "grave",
                )

        fridays = [
            c for c in commits
            if _parse_dt(c["date"]) and _parse_dt(c["date"]).weekday() == 4
            and _parse_dt(c["date"]).day == 13
        ]
        if fridays:
            add_curse("Friday the 13th", "Someone shipped on the unluckiest day of the year.", fridays[0], "grave")

    # ---- rhythm ---------------------------------------------------------
    months = Counter()
    for c in commits:
        dt = _parse_dt(c["date"])
        if dt:
            months[dt.strftime("%Y-%m")] += 1
    timeline = [{"month": m, "commits": n} for m, n in sorted(months.items())]

    # ---- branches -------------------------------------------------------
    branches = []
    try:
        ref_out = _git(root, "for-each-ref",
                       "--format=%(refname:short)|%(committerdate:iso-strict)|%(authorname)",
                       "refs/heads/", timeout=30)
        for line in ref_out.splitlines():
            parts = line.split("|")
            if len(parts) < 3:
                continue
            name, date, author = parts[0], parts[1], parts[2]
            merged = True
            if name != branch:
                try:
                    _git(root, "merge-base", "--is-ancestor", name, "HEAD", timeout=20)
                except GitError:
                    merged = False
            branches.append(
                {"name": name, "date": date, "author": author, "merged": merged,
                 "current": name == branch}
            )
    except GitError:
        branches = []
    branches.sort(key=lambda b: b["date"], reverse=True)

    # ---- assembly -------------------------------------------------------
    name = os.path.basename(root.rstrip("\\/")) or "repository"
    if remote:
        remote_name = re.sub(r"\.git$", "", remote.rstrip("/")).split("/")[-1]
        if remote_name:
            name = remote_name

    abandoned_for = _days_between(last_date, now)
    total_added = sum(c["added"] for c in commits)
    total_deleted = sum(c["deleted"] for c in commits)

    record = {
        "meta": {
            "name": name,
            "root": root,
            "remote": remote,
            "branch": branch,
            "head": head[:10],
            "scanned_at": now.isoformat(),
            "commit_count": len(commits),
            "truncated": truncated,
            "max_commits": max_commits,
        },
        "life": {
            "first_commit": _iso(first_date),
            "last_commit": _iso(last_date),
            "lifespan_days": _days_between(first_date, last_date),
            "silent_for_days": abandoned_for,
            "abandoned": abandoned_for > 730,
            "last_words": commits[0]["subject"] if commits else "",
            "last_author": commits[0]["author"] if commits else "",
            "last_date": _iso(last_date),
        },
        "totals": {
            "commits": len(commits),
            "souls": len(author_list),
            "files_live": len([p for p in live_paths if not _is_noise(p)]),
            "files_vanished": len([p for p in vanished_paths if not _is_noise(p) and not _is_binary_path(p)]),
            "added": total_added,
            "deleted": total_deleted,
            "branches": len(branches),
            "unmerged_branches": len([b for b in branches if not b["merged"]]),
        },
        "authors": author_list[:14],
        "ghosts": ghosts,
        "revenants": revenants,
        "forgotten": forgotten,
        "extinct": extinct,
        "cursed": cursed[:7],
        "timeline": timeline,
        "branches": [b for b in branches if not b["merged"]][:10],
        "languages": [{"language": k, "files": v} for k, v in live_langs.most_common(8)],
    }
    return record


def record_facts(record: dict) -> str:
    """A compact, model-readable dossier. The model may only use these facts."""
    meta, life, totals = record["meta"], record["life"], record["totals"]
    lines = [
        f"REPOSITORY: {meta['name']}",
        f"BRANCH: {meta['branch']}  HEAD: {meta['head']}",
        f"COMMITS: {totals['commits']}  SOULS: {totals['souls']}  "
        f"LIVING FILES: {totals['files_live']}  VANISHED FILES: {totals['files_vanished']}",
        f"LIFESPAN: {life['first_commit']} to {life['last_commit']} "
        f"({life['lifespan_days']} days)",
        f"SILENT FOR: {life['silent_for_days']} days"
        + ("  (ABANDONED)" if life["abandoned"] else ""),
        f"LAST WORDS (last commit message): \"{life['last_words']}\" by {life['last_author']}",
        f"UNMERGED BRANCHES: {totals['unmerged_branches']}",
        "",
        "SOULS (authors):",
    ]
    for a in record["authors"][:8]:
        lines.append(
            f"- {a['name']}: {a['commits']} commits, first {a['first_seen'][:10]}, "
            f"last {a['last_seen'][:10]}, +{a['added']}/-{a['deleted']}"
        )
    lines.append("")
    lines.append("THE BURIED (deleted files):")
    for g in record["ghosts"][:10]:
        lines.append(
            f"- {g['path']} ({g['language'] or 'unknown'}), lived {str(g['born'])[:10]} to "
            f"{str(g['died'])[:10]}, {g['churn']} lines churned, killed by {g['killed_by']} "
            f"in \"{g['last_subject']}\" [{g['commit']}]"
            + (f"; its last words: \"{g['buried_note']}\"" if g.get("buried_note") else "")
        )
    if record["revenants"]:
        lines.append("")
        lines.append("THE REVENANTS (deleted, then restored):")
        for r in record["revenants"]:
            lines.append(f"- {r['path']}, died {str(r['died'])[:10]}, rose again")
    if record["forgotten"]:
        lines.append("")
        lines.append("THE FORGOTTEN (alive but untouched):")
        for f in record["forgotten"][:6]:
            lines.append(
                f"- {f['path']}, untouched for {f['age_days']} days, last touched by "
                f"{f['killed_by']} in \"{f['last_subject']}\""
            )
    if record["extinct"]:
        lines.append("")
        lines.append("EXTINCT LANGUAGES: " + ", ".join(
            f"{e['language']} ({e['files_lost']} files lost)" for e in record["extinct"]
        ))
    if record["cursed"]:
        lines.append("")
        lines.append("CURSED COMMITS:")
        for c in record["cursed"]:
            lines.append(f"- {c['title']}: {c['subject']} by {c['author']} on "
                         f"{str(c['date'])[:10]} ({c['detail']})")
    if record["branches"]:
        lines.append("")
        lines.append("UNMERGED BRANCHES (ghosts of other timelines):")
        for b in record["branches"]:
            lines.append(f"- {b['name']}, last touched {str(b['date'])[:10]} by {b['author']}")
    return "\n".join(lines)
