"""Scan the repo for things that must not appear in a public repository.

    python tools/leak_scan.py

Generic patterns (always on): email addresses, phone numbers, price/quote/PO references, mail-thread markers, local user paths,
key-looking tokens. Project-specific terms (client, venue and people names) are NOT stored in the repo: put one per line in
SITARA_LEAK_TERMS (env var, newline or comma separated) or in a gitignored file `.leak-terms` at the repo root.
Allow a known-safe line with the marker `leak-ok` anywhere on it. Exit code 1 if anything is found.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".step", ".stp", ".wrl", ".zip", ".woff", ".woff2", ".ttf", ".otf"}
SKIP_FILES = {"LICENSE"}
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "users.noreply.github.com", "noreply.anthropic.com"}

PATTERNS = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")),
    ("phone", re.compile(r"(?<![\d.])(?:\(\d{3}\)\s?|\b\d{3}[.-])\d{3}[.-]\d{4}\b")),
    ("price", re.compile(r"(?:[$€£]\s?\d[\d,]*(?:\.\d\d)?\b|\b(?:USD|EUR|GBP)\s?\d[\d,]+)")),
    ("quote/PO ref", re.compile(r"\b(?:quote|QT|PO|invoice|proposal)\s*(?:no\.?|number|#)\s*[:#]?\s*[A-Z0-9-]{4,}", re.I)),
    ("mail thread", re.compile(r"^\s*(?:Re|Fwd?|From|Sent|Subject):\s", re.I)),
    ("local path", re.compile(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)[A-Za-z0-9._-]+")),
    ("token", re.compile(r"\b(?:ghp_|gho_|github_pat_|sk-|xox[bp]-|AKIA)[A-Za-z0-9_-]{12,}")),
]


def files():
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=REPO, capture_output=True)
    if out.returncode != 0:
        raise SystemExit("leak_scan needs a git checkout (git ls-files failed)")
    for rel in out.stdout.decode("utf-8", "replace").split("\0"):
        if not rel or rel in SKIP_FILES or os.path.splitext(rel)[1].lower() in SKIP_EXT:
            continue
        p = os.path.join(REPO, rel)
        if os.path.isfile(p):
            yield rel, p


def terms():
    raw = os.environ.get("SITARA_LEAK_TERMS", "")
    f = os.path.join(REPO, ".leak-terms")
    if os.path.exists(f):
        raw += "\n" + open(f, encoding="utf-8").read()
    return [t.strip() for t in re.split(r"[\n,]", raw) if t.strip() and not t.startswith("#")]


def scan():
    deny = [re.compile(re.escape(t), re.I) for t in terms()]
    hits = []
    for rel, p in files():
        try:
            text = open(p, encoding="utf-8", errors="strict").read()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if "leak-ok" in line:
                continue
            for label, rx in PATTERNS:
                m = rx.search(line)
                if not m:
                    continue
                if label == "local path" and m.group(0).endswith(("Developer", "user", "username", "you")):
                    continue  # vendor-generated or placeholder paths
                if label == "email" and m.group(1).lower() in ALLOWED_EMAIL_DOMAINS:
                    continue
                hits.append((rel, n, label, line.strip()[:100]))
            for rx in deny:
                if rx.search(line):
                    hits.append((rel, n, "denylist term", "(term hidden)"))
    return hits, len(deny)


def main():
    hits, nterms = scan()
    if not nterms:
        print("note: no project-specific terms configured (SITARA_LEAK_TERMS / .leak-terms); generic patterns only")
    for rel, n, label, snippet in hits:
        print(f"{rel}:{n}: {label}: {snippet}")
    print(f"leak scan: {len(hits)} finding(s)")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
