#!/usr/bin/env python3
"""Check YAML parseability and existing relative links, without accessing the network."""
from pathlib import Path
import re
import sys

import yaml

root = Path(__file__).resolve().parents[1]
errors = []
for file in root.rglob("*"):
    if not file.is_file() or ".git" in file.parts:
        continue
    if file.suffix in {".yaml", ".yml"}:
        try:
            yaml.safe_load(file.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeError) as exc:
            errors.append(f"{file.relative_to(root)}: invalid YAML: {exc}")
    if file.suffix == ".md":
        data = file.read_text(encoding="utf-8")
        # Only conventional inline links to local files; external URLs and anchors skipped.
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', data):
            target = target.strip().split("#", 1)[0].split("?", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "/", "#")):
                continue
            if "%" in target or " " in target:
                continue  # Complex/encoded link syntax is outside this simple check.
            candidate = file.parent / target
            if not candidate.exists():
                errors.append(f"{file.relative_to(root)}: missing relative link {target}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("YAML parsing and simple relative Markdown links: OK")
