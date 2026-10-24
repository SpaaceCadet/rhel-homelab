# Incident response case studies

Sanitized historical homelab investigations from Obsidian. Reports preserve the distinction between a verified symptom, an interpretation and an unresolved root cause.

| Case | Evidence | Outcome |
| --- | --- | --- |
| [Nextcloud CPU and Nginx reconnaissance](nextcloud-cpu-nginx-2026-10.md) | Container/process/perf metrics, Nginx response patterns | CPU root cause not confirmed; scanning did not show successful HTTP 2xx in reviewed requests |
| [Stremio HLSv2 DNS and E-AC3](../stremio/troubleshooting.md) | Failed FFprobe of custom HTTPS hostname; working internal URL | Internal container name resolution fixed probe and playback |
| [Obsidian MCP vault EACCES](../mcp/obsidian.md) | UID, directory permissions, failed write | Writing restored after permissions troubleshooting; precise remediation not independently recorded |

## Reporting template

Use: **Impact → timeline → known evidence → hypotheses → fix/mitigation → validation → prevention → outstanding unknowns**. Redact attackers' IP addresses, real hostnames, internal networks, credentials and client data before publication.
