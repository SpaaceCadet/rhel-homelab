# RHEL Homelab

Self-hosted infrastructure on Red Hat Enterprise Linux — Docker, Nginx, DNS, monitoring, security, and troubleshooting runbooks.

This repository documents reproducible deployment patterns and real troubleshooting exercises from a personal homelab. Published examples use **sanitized IPs/hostnames**. No secrets, certificate private keys or persistent application data are included.

## Documented projects

| Project | Focus |
| --- | --- |
| [Stremio Docker](stremio/README.md) | Container networking, HLSv2/FFprobe troubleshooting and E-AC3 browser playback |
| [RHEL security baseline](security/README.md) | Firewalld, Docker/nftables, SSH/Fail2ban and enforcing SELinux |
| [Nginx, Certbot & mTLS](nginx/README.md) | Reverse proxy, HTTPS issuance/renewal, optional mutual TLS, safe backup and rollback |

### Incident highlight: browser video played without audio

The stream had audio in VLC but not in Stremio Web. HLSv2 probing returned HTTP 500 because Docker could not resolve the advertised local HTTPS hostname. A mapping to the host HTTPS reverse proxy restored probing and the user observed working browser playback.

See the [Stremio incident report](stremio/troubleshooting.md) and [deployment example](stremio/compose.yaml).

## Documentation philosophy

- Distinguish **historically observed** settings from safe **example configurations**.
- Preserve SELinux enforcement and minimize firewall access; do not copy broad source allowlists.
- Treat GitHub documentation as a learning and recovery reference, **not** a production secrets backup.
- Verify each procedure in your target environment before applying it.

## Planned topics

Nextcloud, monitoring (Prometheus/Grafana), DNS services, SSH/Wake-on-LAN, and system architecture.

## Security

Never commit passwords, tokens, private keys, browser client certificates, actual network allow-lists, or application data.
