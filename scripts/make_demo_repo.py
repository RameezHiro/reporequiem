"""
Builds a small, deliberately haunted git repository for demos and tests.

    python scripts/make_demo_repo.py ../lumen-mail

The history is scripted: a CoffeeScript era that goes extinct, files that die,
one that comes back, a 3 a.m. commit, a revert spiral, a Friday the 13th ship,
and a quiet abandonment. Every date is real to git, so the archaeology engine
reads it like any other repository.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else "lumen-mail").resolve()
if REPO.exists():
    shutil.rmtree(REPO)
REPO.mkdir(parents=True)

files: dict[str, str] = {}


def write(path: str, content: str) -> None:
    full = REPO / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    files[path] = content


def remove(path: str) -> None:
    full = REPO / path
    if full.exists():
        full.unlink()
    files.pop(path, None)


def git(*args: str, date: str, author: str, email: str) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": author,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_NAME": author,
        "GIT_COMMITTER_EMAIL": email,
    }
    subprocess.run(["git", "-C", str(REPO), *args], check=True, env=env,
                   capture_output=True)


subprocess.run(["git", "init", "-q", "-b", "main", str(REPO)], check=True)
subprocess.run(["git", "-C", str(REPO), "config", "user.name", "Ana Ruiz"], check=True)
subprocess.run(["git", "-C", str(REPO), "config", "user.email", "ana@lumen.example"], check=True)

ANA = ("Ana Ruiz", "ana@lumen.example")
TOMAS = ("Tomás Vega", "tomas@lumen.example")
MIRA = ("Mira Chen", "mira@lumen.example")


def commit(message: str, date: str, who=ANA) -> None:
    git("add", "-A", date=date, author=who[0], email=who[1])
    git("commit", "-q", "-m", message, date=date, author=who[0], email=who[1])


# 2019 - the CoffeeScript years ------------------------------------------------
write("README.md", "# lumen-mail\n\nA quiet mail client for people who miss the desktop.\n")
write("package.json", '{\n  "name": "lumen-mail",\n  "version": "0.1.0",\n  "main": "index.js"\n}\n')
write("app.coffee", "App = require './src/inbox'\nApp.start()\n")
write("src/parser.coffee", """# Parses RFC822 headers. Written at 2am. Do not touch.
parse = (raw) ->
  headers = {}
  for line in raw.split '\\n'
    [key, value] = line.split ': '
    headers[key] = value if value
  headers

module.exports = parse
""")
write("src/inbox.coffee", """# The inbox is a list. That is the whole idea.
render = (messages) ->
  for message in messages
    console.log message.subject
""")
commit("Initial commit: lumen-mail", "2019-02-14T09:12:00-05:00")

write("src/parser_test.coffee", """assert = require 'assert'
parse = require './parser'
# TODO: test folded headers before shipping
assert.equal parse('Subject: hi').Subject, 'hi'
""")
commit("Add message parser", "2019-03-02T14:40:00-05:00")

write("src/sync.coffee", """# IMAP sync. Temporary. This will be rewritten before launch.
sync = (account) ->
  console.log 'connecting', account.host
  # FIXME: no reconnect logic, no backoff, no mercy
""")
write("src/theme.coffee", """# Colors for the inbox. Chosen on a laptop screen at night.
theme =
  background: '#f7f4ee'
  ink: '#1e1e1e'
""")
commit("Add mailbox sync and theme", "2019-04-18T11:05:00-05:00")

write("src/sync.coffee", """# IMAP sync. Temporary. This will be rewritten before launch.
sync = (account) ->
  console.log 'connecting', account.host
  # FIXME: no reconnect logic, no backoff, no mercy
  # FIXME: this fires twice on reconnect
""")
commit("wip: sync retries", "2019-05-30T02:47:00-05:00", TOMAS)

write("src/sync.coffee", files["src/sync.coffee"] + "  # FIXME: still fires twice\n")
commit("fix sync", "2019-06-01T15:20:00-05:00", TOMAS)
write("src/sync.coffee", files["src/sync.coffee"] + "  # FIXME: now it never stops\n")
commit("fix the sync fix", "2019-06-02T01:10:00-05:00", TOMAS)
write("src/sync.coffee", """# IMAP sync. Temporary. This will be rewritten before launch.
sync = (account) ->
  console.log 'connecting', account.host
  # TODO: give up gracefully
""")
commit("fix: sync no longer loops", "2019-06-03T23:52:00-05:00", TOMAS)

write("src/sync.coffee", """# IMAP sync. Temporary. This will be rewritten before launch.
sync = (account) ->
  console.log 'connecting', account.host
  # FIXME: no reconnect logic, no backoff, no mercy
  # FIXME: this fires twice on reconnect
""")
commit("Revert 'wip: sync retries'", "2019-06-14T10:00:00-05:00")

# The CoffeeScript extinction ------------------------------------------------
for path in ["app.coffee", "src/parser.coffee", "src/inbox.coffee",
             "src/sync.coffee", "src/theme.coffee", "src/parser_test.coffee"]:
    remove(path)
write("index.js", "const app = require('./src/inbox');\napp.start();\n")
write("src/parser.js", """// Parses RFC822 headers. Ported from CoffeeScript, logic kept.
module.exports = function parse(raw) {
  const headers = {};
  raw.split('\\n').forEach((line) => {
    const i = line.indexOf(': ');
    if (i > 0) headers[line.slice(0, i)] = line.slice(i + 2);
  });
  return headers;
};
""")
write("src/inbox.js", """const render = (messages) => messages.forEach((m) => console.log(m.subject));
module.exports = { render };
""")
commit("Retire CoffeeScript, port parser to JavaScript",
       "2019-07-09T16:30:00-05:00", MIRA)

write("src/attachments.js", """// Attachments were the most requested feature. They took two years.
const fs = require('fs');
module.exports = (message, dir) => fs.writeFileSync(dir + '/' + message.filename, message.body);
""")
write("assets/logo.svg", "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M3 5h18v14H3z' fill='none' stroke='#c8563a'/></svg>\n")
commit("Add attachments", "2019-09-21T12:15:00-05:00")

# Friday the 13th, 2020 -------------------------------------------------------
write("src/archive.js", """// Archive is a folder called 'old'. Do not rename it. Outlook depends on it.
module.exports = (message) => ({ ...message, archived: true });
""")
write("src/vendor.js", "// Vendored MIME tables. Copied by hand. Never regenerate.\n" +
      "module.exports = {\n" + "\n".join(f"  mime{i}: 'application/x-lumen-{i}'," for i in range(120)) + "\n};\n")
commit("Ship archive view and MIME tables", "2020-03-13T23:58:00-04:00")

write("src/attachments.js", """// Attachments were the most requested feature. They took two years.
const fs = require('fs');
module.exports = (message, dir) => fs.writeFileSync(dir + '/' + message.filename, message.body);
// TODO: this trusts the filename. Do not ship like this.
""")
commit("Add filename warning", "2020-03-14T00:12:00-04:00")

# A file dies, then comes back ------------------------------------------------
remove("src/attachments.js")
commit("Remove attachments pending rewrite", "2020-06-01T09:30:00-04:00")

write("src/parser.test.js", """const assert = require('assert');
const parse = require('./parser');
assert.equal(parse('Subject: hi').Subject, 'hi');
""")
write("docs/CHANGELOG.md", "# Changelog\n\n## 0.4.0\n- Attachments removed pending rewrite\n")
commit("Add tests and changelog", "2020-06-20T18:00:00-04:00", MIRA)

write("src/attachments.js", """// Attachments, second attempt. Streams now.
const fs = require('fs');
module.exports = (message, dir, stream) => {
  if (!stream) throw new Error('attachments require a stream');
  return fs.createWriteStream(dir + '/' + message.filename);
};
""")
commit("Restore attachments as streams", "2020-07-02T13:45:00-04:00")

write("package.json", '{\n  "name": "lumen-mail",\n  "version": "0.6.0",\n  "main": "index.js"\n}\n')
commit("chore: bump version", "2021-05-04T10:20:00-04:00")

write("README.md", """# lumen-mail

A quiet mail client for people who miss the desktop.

## Status

Unmaintained. The IMAP server we built this for shut down in 2021.
It still runs. It does not connect to anything.
""")
commit("update stuff", "2022-02-02T21:04:00-05:00")

remove("src/archive.js")
remove("src/vendor.js")
write("docs/CHANGELOG.md", "# Changelog\n\n## 0.6.0\n- Final release\n\nTODO: finish the migration notes before archiving\n")
git("add", "-A", date="2022-03-15T17:30:00-04:00", author=ANA[0], email=ANA[1])
git("commit", "-q", "-m", "Final cleanup. Thanks for everything.",
    date="2022-03-15T17:30:00-04:00", author=ANA[0], email=ANA[1])

# An unmerged timeline nobody finished ---------------------------------------
git("checkout", "-q", "-b", "feature/search", date="2022-01-20T22:10:00-05:00",
    author=TOMAS[0], email=TOMAS[1])
write("src/search.js", "// Full text search. Wanted it for years.\nmodule.exports = () => [];\n")
git("add", "-A", date="2022-01-20T22:10:00-05:00", author=TOMAS[0], email=TOMAS[1])
git("commit", "-q", "-m", "wip: search index", date="2022-01-20T22:10:00-05:00",
    author=TOMAS[0], email=TOMAS[1])
git("checkout", "-q", "main", date="2022-03-16T09:00:00-04:00", author=ANA[0], email=ANA[1])

print(f"built {REPO}")
print(subprocess.run(["git", "-C", str(REPO), "log", "--oneline", "-n", "8"],
                     capture_output=True, text=True).stdout)
