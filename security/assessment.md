# RHEL homelab security assessment — sanitized October 2026 audit

**Scope:** Historical configuration evidence from Obsidian, not a current vulnerability scan, penetration test, or guarantee of security. Priority estimates below are recommendations, not confirmed exploitable findings.

| Priority | Area | Observed condition / concern | Recommended action |
| --- | --- | --- | --- |
| High | SSH and MCP policy | Restricted SSH account existed; lab MCP authorization policy used broad `all_users: true` matching | Confirm true end-user identity authorization before sharing; restrict allowed tools and destinations |
| High | Public service exposure | Source Firewalld permitted services not necessarily needed by the web homelab; Docker dynamic forwarding may bypass naïve host-zone assumptions | Inventory listeners, Docker publish bindings, router NAT, Firewalld runtime/permanent and effective nftables |
| High | Secret lifecycle | Historical Nextcloud Compose used same inline password for DB root and app; Pi-hole password appeared inline; tunnel/SSH identities exist | Rotate with application-aware process; use protected secret files / manager, not Git |
| High | Container interfaces | Some historical Docker services bound host ports on all interfaces | Prefer intentional loopback bindings or authenticated reverse proxy, test compatibility before changing production |
| Medium | cAdvisor mounts | Runtime/socket mounts increase privilege and information exposure, even read-only | Limit network access and isolate privileged collector; assess necessity |
| Medium | SELinux | Targeted enforcing observed, plus custom booleans, port labels and a historically unlabeled mount point | Keep enforcing; inspect AVCs, minimum required customizations and path labels |
| Medium | TLS/renewal | Nginx and Certbot timer were observed; successful certificate renewal and reload were not always independently confirmed | Validate certificate expiry, controlled renewal dry-run, deploy reload and mTLS endpoints |
| Medium | Backups | Persistent monitoring volumes verified; no automatic full backup schedule was confirmed | Create encrypted off-host backups and perform isolated restore drills |
| Medium | Pi-hole / DNS | Pi-hole listening mode `all`; actual DHCP client use was not verified | Verify LAN-only DNS exposure, upstream resolution and clients' actual resolvers |
| Medium | Observability | Exporter coverage is not comprehensive across all host filesystems and HTTP status/latency | Validate metrics and configure failure/CPU/disk alerts |

## Read-only audit checklist

```bash
sudo ss -lntup
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --list-all
sudo firewall-cmd --list-all-policies
sudo nft list ruleset
docker ps --format 'table {{.Names}}\t{{.Ports}}'
getenforce
sudo semanage boolean -l -C
sudo semanage port -l -C
sudo ausearch -m AVC -ts recent
sudo fail2ban-client status sshd
sudo nginx -t
sudo certbot certificates
```

**Safety:** These commands may output IP addresses, hostnames, process names or policy details. Inspect privately; never push unredacted output. Do not run automatic firewall cleanup, password rotation or SELinux relabeling on a live server without a rollback plan.

## Important interpretation

The October snapshots included temporary Fail2ban bans and a broadly matching source ipset rule. Those are **not published verbatim** or advocated as standard configuration. A listening or firewall-allowed port is not proof of WAN reachability; a missing firewall port listing does not prove a Docker-published service is unreachable. Confirm network paths through legitimate outside-network tests.

See detailed runbooks: [Firewalld](firewalld.md), [Fail2ban](fail2ban.md), [SELinux](selinux.md), [Nginx](../nginx/README.md), [MCP](../mcp/README.md).
