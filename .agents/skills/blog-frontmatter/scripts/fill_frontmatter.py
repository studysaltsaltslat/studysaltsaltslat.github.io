#!/usr/bin/env python3
"""
Fill missing blog post frontmatter for the Astro Theme Pure blog.

Workflow:
  1. Detect newly added posts under src/content/blog via git
     (untracked or staged-added files).
  2. For each post, fill missing/placeholder frontmatter fields:
     - title: first "# heading" or a humanized filename
     - description: agent-provided full-text summary (fallback: first paragraph)
     - publishDate: today (or git commit date when available)
     - tags: agent-provided tags (fallback: keyword extraction)
     - language: auto-detected (中文 / English)
     - heroImage: random image from the post folder (if any images exist)
  3. Print a summary so the user can review and edit the generated values.

Usage:
  python .agents/skills/blog-frontmatter/scripts/fill_frontmatter.py [--list]
  python .agents/skills/blog-frontmatter/scripts/fill_frontmatter.py [--all]
  python .agents/skills/blog-frontmatter/scripts/fill_frontmatter.py --file <path> [--description "..."] [--tags a,b,c]

Options:
  --list              Only print newly added posts, do not modify anything.
  --file PATH         Process a single post (path relative to repo root).
  --all               Process every post missing fields, not just newly added ones.
  --description TEXT  Agent-written full-text summary (overwrites description).
  --tags a,b,c        Agent-derived tags, comma separated (overwrites tags).
  --dry-run           Print what would change without writing files.
  --seed N            Seed the random hero image picker (for reproducibility).
"""

from __future__ import annotations

import argparse
import datetime
import random
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
BLOG_DIR = REPO_ROOT / "src" / "content" / "blog"
POST_GLOBS = ("*.md", "*.mdx")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".avif", ".webp"}

KEYWORDS = {
    "python",
    "typescript",
    "javascript",
    "go",
    "golang",
    "rust",
    "java",
    "cpp",
    "c++",
    "css",
    "html",
    "react",
    "vue",
    "svelte",
    "astro",
    "node",
    "docker",
    "kubernetes",
    "linux",
    "git",
    "sql",
    "redis",
    "mongodb",
    "教程",
    "笔记",
    "随笔",
    "写作",
}

PLACEHOLDER_TAGS = {"example", "technology"}


def git_status_new_files() -> list[Path]:
    """Return newly added post files under src/content/blog via git."""
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/content/blog"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"[warn] git status failed: {proc.stderr.strip()}", file=sys.stderr)
        return []
    new_paths: list[Path] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        flags, path = line[:2], line[3:].strip()
        is_new = flags.startswith("??") or flags[0] == "A"
        if not is_new:
            continue
        p = REPO_ROOT / path
        if p.is_dir():
            for glob in POST_GLOBS:
                new_paths.extend(sorted(p.rglob(glob)))
        elif p.is_file() and p.suffix in {".md", ".mdx"}:
            new_paths.append(p)
    return sorted(set(new_paths))


def all_posts() -> list[Path]:
    posts: list[Path] = []
    for glob in POST_GLOBS:
        posts.extend(sorted(BLOG_DIR.rglob(glob)))
    return posts


def split_frontmatter(text: str) -> tuple[list[str], str] | None:
    """Return (frontmatter lines, body) or None if no frontmatter block."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :])
    return None


def parse_blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split frontmatter lines into top-level key -> raw block lines."""
    blocks: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][\w-]*):(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        block = [lines[i]]
        i += 1
        if rest.strip() == "":
            while i < len(lines) and lines[i][:1] in (" ", "\t"):
                block.append(lines[i])
                i += 1
        blocks.append((key, block))
    return blocks


def scalar_value(block: list[str]) -> str | None:
    if not block:
        return None
    val = block[0].split(":", 1)[1].strip()
    return val.strip("'\"") if val else None


def tags_from_block(block: list[str]) -> list[str]:
    tags: list[str] = []
    for line in block[1:]:
        m = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if m:
            tags.append(m.group(1).strip("'\""))
    if not tags and block:
        val = scalar_value(block)
        if val:
            tags = [t.strip(" '\"") for t in val.strip("[]").split(",") if t.strip()]
    return tags


def quote_yaml(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def detect_language(body: str) -> str:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    latin = len(re.findall(r"[A-Za-z]", body))
    return "中文" if cjk > 0 and cjk / max(cjk + latin, 1) > 0.3 else "English"


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)  # images -> alt
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> text
    text = re.sub(r"[`*_>#~]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_description(body: str) -> str:
    lines = body.splitlines()
    paragraphs: list[list[str]] = []
    current: list[str] = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            if current:
                paragraphs.append(current)
                current = []
            continue
        if in_code:
            continue
        if line.strip().startswith("#") or line.strip() == "":
            if current:
                paragraphs.append(current)
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(current)
    for para in paragraphs:
        text = strip_markdown(" ".join(para))
        if len(text) < 10:
            continue
        if len(text) <= 160:
            return text
        cut = text[:157].rsplit(" ", 1)[0]
        return cut + "..."
    return ""


def extract_title(body: str, path: Path) -> str:
    m = re.search(r"^#\s+(.+)$", body, re.M)
    if m:
        title = strip_markdown(m.group(1)).strip()
        if title:
            return title[:60]
    stem = path.parent.name if path.stem == "index" else path.stem
    words = re.sub(r"[-_]+", " ", stem).strip().title()
    return words[:60] or "Untitled"


def extract_tags(body: str) -> list[str]:
    lower = body.lower()
    found = [kw for kw in KEYWORDS if kw.lower() in lower]
    return sorted(set(found))[:5]


def images_in_folder(path: Path) -> list[Path]:
    return sorted(p for p in path.parent.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def build_frontmatter(
    blocks: list[tuple[str, list[str]]],
    path: Path,
    body: str,
    description_override: str | None = None,
    tags_override: list[str] | None = None,
) -> tuple[list[tuple[str, list[str]]], dict[str, str]]:
    existing = {key: block for key, block in blocks}
    changes: dict[str, str] = {}

    def ensure_scalar(key: str, value: str | None) -> None:
        if value is None:
            return
        block = existing.get(key)
        if block is None or not scalar_value(block):
            existing[key] = [f"{key}: {quote_yaml(value)}"]
            changes[key] = value

    ensure_scalar("title", extract_title(body, path))
    if description_override:
        description_override = description_override.strip()
        existing["description"] = [f"description: {quote_yaml(description_override)}"]
        changes["description"] = description_override
    else:
        ensure_scalar("description", extract_description(body))

    if "publishDate" not in existing:
        existing["publishDate"] = [
            "publishDate: " + quote_yaml(datetime.date.today().isoformat())
        ]
        changes["publishDate"] = datetime.date.today().isoformat()

    if tags_override is not None:
        tags = list(dict.fromkeys(t.strip() for t in tags_override if t.strip()))[:5]
        existing["tags"] = [f"tags: [{', '.join(quote_yaml(t) for t in tags)}]"]
        changes["tags"] = ", ".join(tags)
    else:
        tags = extract_tags(body)
        if "tags" not in existing:
            if tags:
                existing["tags"] = [f"tags: [{', '.join(quote_yaml(t) for t in tags)}]"]
                changes["tags"] = ", ".join(tags)
        else:
            current_tags = tags_from_block(existing["tags"])
            if not current_tags or all(t.lower() in PLACEHOLDER_TAGS for t in current_tags):
                existing["tags"] = [f"tags: [{', '.join(quote_yaml(t) for t in tags)}]"]
                changes["tags"] = ", ".join(tags) if tags else ""

    if "language" not in existing:
        lang = detect_language(body)
        existing["language"] = ["language: " + quote_yaml(lang)]
        changes["language"] = lang

    if "heroImage" not in existing:
        images = images_in_folder(path)
        if images:
            pick = random.choice(images)
            existing["heroImage"] = [
                "heroImage:",
                f"  src: {quote_yaml('./' + pick.name)}",
                "  alt: " + quote_yaml("封面图"),
            ]
            changes["heroImage"] = "./" + pick.name

    order = [
        "title",
        "description",
        "publishDate",
        "updatedDate",
        "tags",
        "language",
        "draft",
        "comment",
        "heroImage",
    ]
    ordered: list[tuple[str, list[str]]] = []
    used: set[str] = set()
    for key in order:
        if key in existing:
            ordered.append((key, existing[key]))
            used.add(key)
    for key, block in blocks:
        if key not in used:
            ordered.append((key, block))
    return ordered, changes


def process_file(
    path: Path,
    dry_run: bool,
    description_override: str | None = None,
    tags_override: list[str] | None = None,
) -> None:
    text = path.read_text(encoding="utf-8")
    parsed = split_frontmatter(text)
    if parsed is None:
        print(f"[skip] {path.relative_to(REPO_ROOT)}: no frontmatter block")
        return
    fm_lines, body = parsed
    blocks = parse_blocks(fm_lines)
    new_blocks, changes = build_frontmatter(
        blocks, path, body, description_override, tags_override
    )
    if not changes:
        print(f"[ok]   {path.relative_to(REPO_ROOT)}: frontmatter complete")
        return
    rel = path.relative_to(REPO_ROOT)
    print(f"[edit] {rel}")
    for key, value in changes.items():
        print(f"  {key}: {value}")
    print("  (generated values — 可自行修改)")
    if dry_run:
        return
    new_fm = "\n".join(line for _, block in new_blocks for line in block)
    path.write_text("---\n" + new_fm + "\n---\n" + body, encoding="utf-8")


def main() -> int:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Fill missing blog frontmatter")
    parser.add_argument("--list", action="store_true", help="only list newly added posts")
    parser.add_argument("--file", default=None, help="process a single post (relative path)")
    parser.add_argument(
        "--all", action="store_true", help="process every post, not just newly added"
    )
    parser.add_argument("--dry-run", action="store_true", help="print changes without writing")
    parser.add_argument("--seed", type=int, default=None, help="random seed for hero image pick")
    parser.add_argument("--description", default=None, help="full-text summary for description")
    parser.add_argument("--tags", default=None, help="comma separated tags")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    tags_override = None
    if args.tags:
        tags_override = [t.strip() for t in args.tags.split(",") if t.strip()]

    if args.list:
        posts = git_status_new_files()
        if not posts:
            print("No new blog posts detected under src/content/blog.")
            return 0
        for post in posts:
            print(post.relative_to(REPO_ROOT))
        return 0

    if args.file:
        target = REPO_ROOT / args.file
        if not target.is_file():
            print(f"[error] file not found: {args.file}", file=sys.stderr)
            return 1
        if not target.resolve().is_relative_to(BLOG_DIR.resolve()):
            print(f"[error] file is outside src/content/blog: {args.file}", file=sys.stderr)
            return 1
        posts = [target]
    else:
        posts = all_posts() if args.all else git_status_new_files()
    if not posts:
        print("No new blog posts detected under src/content/blog.")
        return 0
    print(f"Processing {len(posts)} post(s)...")
    for post in posts:
        process_file(post, args.dry_run, args.description, tags_override)
    if not args.dry_run:
        print("\nDone. Review the generated values above; you can edit any of them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
