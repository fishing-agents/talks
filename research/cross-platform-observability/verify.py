#!/usr/bin/env python3
"""Check deck artifacts, repository coverage, and commit-pinned source references."""
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
TALKS = HERE.parents[1]
REPOS = TALKS / "references"


def main():
    manifest = json.loads((HERE / "repositories.json").read_text())
    repositories = {r["name"]: r for r in manifest["repositories"]}
    inventory = (HERE / "inventory.md").read_text()
    missing = [name for name in repositories if f"### {name}\n" not in inventory]
    assert not missing, f"Missing repository entries: {missing}"
    checked = set()
    for file in sorted(HERE.glob("*.md")) + [TALKS / "hami_cross_platform_observability.md"]:
        for match in re.finditer(r"https://github.com/Project-HAMi/([^/]+)/blob/([0-9a-f]{40})/([^\s)]+)", file.read_text()):
            repo, commit, path = match.groups()
            path, _, anchor = path.partition("#")
            path = unquote(path)
            key = (repo, commit, path, anchor)
            if key in checked:
                continue
            assert repo in repositories, f"Unknown repo: {repo}"
            assert commit == repositories[repo]["commit"], f"Unpinned source: {repo}"
            proc = subprocess.run(["git", "-C", str(REPOS / repo), "show", f"{commit}:{path}"], capture_output=True)
            assert proc.returncode == 0, f"Source missing: {repo}/{path}"
            lines = len(proc.stdout.splitlines())
            for line in re.findall(r"L(\d+)", anchor):
                assert 1 <= int(line) <= lines, f"Bad anchor: {repo}/{path}#{anchor} ({lines} lines)"
            checked.add(key)
    from slidr.parser.markdown import parse
    from slidr.parser.ast import Heading
    from pypdf import PdfReader
    deck = parse((TALKS / "hami_cross_platform_observability.md").read_text())
    headings = [n for s in deck.slides for n in s.children if isinstance(n, Heading) and n.level in (1, 2)]
    assert len(headings) == len(deck.slides), "Every slide needs exactly one main heading"
    dist = TALKS / "dist"
    html = (dist / "hami_cross_platform_observability.html").read_text()
    audience_html = html.split('<div id="presenter-panel">', 1)[0]
    assert audience_html.count('<section ') == len(deck.slides), "Audience HTML slide count mismatch"
    pdf = PdfReader(dist / "hami_cross_platform_observability.pdf")
    assert len(pdf.pages) == len(deck.slides), "PDF page count mismatch"
    for i, page in enumerate(pdf.pages):
        assert page.extract_text().strip(), f"Blank PDF page {i+1}"
    result = {"repository_entries": len(repositories), "checked_source_references": len(checked), "slides": len(deck.slides), "pdf_pages": len(pdf.pages), "scope": "Static source/citation and rendered artifact checks, not a live GPU observability test."}
    (HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
