#!/usr/bin/env python3
"""Refresh a first-party observability search index from pinned local checkouts."""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PATTERN = r"prometheus|promhttp|ServiceMonitor|PodMonitor|/metrics|DCGM_FI|dcu_.*(util|memory)|npu_smi|npu-smi|hami_.*(ratio|bytes)|OpenTelemetry|opentelemetry|Grafana"
EXCLUDED = re.compile(r"(^|/)(vendor|node_modules|third_party|\.git|dist|build)/|\.(sum|lock|svg|json|pb\.go)$")


def main():
    manifest = json.loads((HERE / "repositories.json").read_text())
    results = []
    for repo in manifest["repositories"]:
        checkout = ROOT / repo["name"]
        head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if head != repo["commit"]:
            raise RuntimeError(f"Snapshot changed: {repo['name']}")
        proc = subprocess.run(["git", "-C", str(checkout), "grep", "-n", "-I", "-i", "-E", PATTERN, "--", "."], capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr)
        hits = []
        for line in proc.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) != 3 or EXCLUDED.search(parts[0]):
                continue
            path, number, text = parts
            hits.append({"path": path, "line": int(number), "text": text[:500], "source": f"https://github.com/{repo['full_name']}/blob/{head}/{path}#L{number}"})
        results.append({"repository": repo["name"], "commit": head, "archived": repo["archived"], "hits": hits})
    output = HERE / "search-index.json"
    output.write_text(json.dumps({"pattern": PATTERN, "excluded": EXCLUDED.pattern, "scope": "Tracked text files only; generated/dependency exclusions. Keyword matches are discovery evidence, not proof of implementation or absence.", "repositories": results}, indent=2) + "\n")
    for repo in results:
        print(f"{repo['repository']}: {len(repo['hits'])} matches")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
