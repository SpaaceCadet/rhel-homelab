# RHEL Homelab

Self-hosted infrastructure on Red Hat Enterprise Linux — Docker, Nginx, DNS, monitoring, security, and troubleshooting runbooks.

This repository documents reproducible deployment patterns and real troubleshooting exercises from a personal homelab. Published examples use **sanitized IPs/hostnames**. No secrets, certificate private keys or persistent application data are included.

## Documented projects

| Project | Focus |
| --- | --- |
| [Stremio Docker](stremio/README.md) | Container networking, HLSv2/FFprobe troubleshooting and E-AC3 browser playback |
| [RHEL security baseline](security/README.md) | Firewalld, Docker/nftables, SSH/Fail2ban and enforcing SELinux |
| [Nginx, Certbot & mTLS](nginx/README.md) | Reverse proxy, HTTPS issuance/renewal, optional mutual TLS, safe backup and rollback |
| [Wake-on-LAN + SSH RDP](remote-access/README.md) | Remote wake, secure localhost RDP tunnel through Linux, and troubleshooting |
| [Nextcloud + MariaDB + Collabora](nextcloud/README.md) | Docker persistence, database restore, TLS/mTLS reverse proxy and documented Collabora integration |
| [Pi-hole + LAN DNS](dns/README.md) | External Docker macvlan, local DNS, client resolution, troubleshooting and recovery |
| [Linux MCP + Obsidian MCP](mcp/README.md) | Restricted SSH-based Linux diagnostics, secure tunnels and writable Obsidian vault integration |
| [Prometheus + Grafana monitoring](monitoring/README.md) | Node Exporter, cAdvisor, Nginx Exporter, PromQL, persistence and recovery |

### Incident highlight: browser video played without audio

The stream had audio in VLC but not in Stremio Web. HLSv2 probing returned HTTP 500 because Docker could not resolve the advertised local HTTPS hostname. A mapping to the host HTTPS reverse proxy restored probing and the user observed working browser playback.

See the [2026-10-24 DNS/audio incident](stremio/troubleshooting.md), [2026-10-25 Docker bridge playback postmortem](incidents/stremio-docker-bridge-playback-2026-10-25.md), and [updated sanitized Compose](stremio/compose.yaml).

## Infrastructure engineering

- [Architecture and trust boundaries](architecture/README.md) — logical Mermaid diagrams spanning LAN, proxy, containers, data and MCP
- [Disaster recovery and migration](disaster-recovery/README.md) — staged rebuild, consistent backups, acceptance and rollback
- [Security assessment](security/assessment.md) — evidence-based risk inventory and hardening priorities
- [Incident case studies](incidents/README.md) — documented investigations, supporting evidence and remaining unknowns
- [Continuous validation](ci/README.md) — Compose/YAML/link validation and secret scanning on GitHub Actions

## Documentation philosophy

- Distinguish **historically observed** settings from safe **example configurations**.
- Preserve SELinux enforcement and minimize firewall access; do not copy broad source allowlists.
- Treat GitHub documentation as a learning and recovery reference, **not** a production secrets backup.
- Verify each procedure in your target environment before applying it.

## Planned topics

Automated restore drills, monitoring alerting, and expanded incident coverage.

## Security

Never commit passwords, tokens, private keys, browser client certificates, actual network allow-lists, or application data.
