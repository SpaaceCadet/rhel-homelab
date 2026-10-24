# Repository checks

GitHub Actions workflow: [documentation-validation.yml](../.github/workflows/documentation-validation.yml).

Every push and pull request is configured to run:
- Python YAML parse checks and local relative Markdown link checks
- Docker Compose `config --quiet` for `stremio/`, `nextcloud/`, `dns/`, and `monitoring/`
- Gitleaks secret scanning

The workflow uses **example environment variables**, not real credentials. It never connects to the homelab or deploys anything. Gitleaks is a heuristic scan, not a substitute for a manual privacy/security review; Git history must also be checked if a secret was ever accidentally committed.

## Run locally

```bash
python3 -m pip install PyYAML
python3 scripts/validate_docs.py
for dir in stremio nextcloud dns monitoring; do
  if [ -f "$dir/.env.example" ]; then cp "$dir/.env.example" "$dir/.env"; fi
  docker compose --project-directory "$dir" -f "$dir/compose.yaml" config --quiet
  rm -f "$dir/.env"
done
```

The `latest` image tags in illustrative Compose files are **not production version pinning**. Test the stack against supported releases before deployment. A passing Compose config check validates syntax and variable resolution, **not live runtime health, container privileges or security**.

## Known limitations

The Markdown link checker intentionally skips complex link encodings and external links. It checks only ordinary relative paths. YAML parsing does not establish that a service schema is correct; Compose validation covers example stack syntax but does not launch containers. The CI workflow itself must be allowed by repository branch settings and the connected GitHub integration before GitHub can execute it.
