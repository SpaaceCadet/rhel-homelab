# Sanitized RHEL homelab infrastructure architecture

**Evidence basis:** Obsidian deployment inventory, reverse-proxy, Pi-hole, monitoring, MCP and migration notes recorded in October 2026. This is a **logical diagram**, not an up-to-the-minute scan. Hostnames, physical addressing, credentials and real network restrictions have been deliberately removed.

## Network, application and trust boundaries

```mermaid
flowchart TB
 External["Authorized remote client"] --> Router["Home router / NAT"]
 Router -->|"HTTPS to approved sites"| Nginx["RHEL host Nginx / TLS / optional client mTLS"]
 Router -->|"SSH, limited"| SSH["Host SSH service + Fail2ban"]
 Nginx --> Next["Nextcloud / Apache Docker"]
 Next --> DB["MariaDB private Docker network"]
 Nginx -. "Collabora routes configured; backend not verified" .-> Code["Collabora CODE"]
 LAN["Trusted LAN clients"] -->|"DNS if configured"| Pi["Pi-hole macvlan: separate LAN address"]
 Pi --> Upstream["Configured upstream resolvers"]
 Laptop["Remote management laptop"] -->|"SSH port-forward"| SSH
 SSH -->|"Magic packet / RDP connection"| Windows["Windows PC on LAN"]
 SubgraphNote["Logical service groups - not literal Docker subnets"] --- Metrics["Prometheus / Grafana / Exporters"]
 Metrics --> Nginx
 Tunnel["Outbound managed MCP tunnels"] --> LinuxMCP["Linux MCP / restricted SSH"]
 Tunnel --> ObsMCP["Obsidian MCP / vault access"]
 LinuxMCP --> SSH
 ObsMCP --> Vault["Markdown vault"]
 GUI["Obsidian GUI container"] --> Vault
```

The drawing shows **possible or observed paths**, not proof of public exposure or actual DHCP DNS distribution. Collabora reverse proxy routes existed but a running backend was not verified in the source snapshot.

## Docker / data dependencies

```mermaid
flowchart LR
 Host["RHEL host + Docker"] --> Bridge["Compose bridge networks"]
 Host --> Mac["External Docker macvlan"]
 Bridge --> NC["Nextcloud"] --> Maria["MariaDB"]
 Bridge --> PM["Prometheus"] --> Graf["Grafana"]
 PM --> Export["cAdvisor / Nginx exporter"]
 Mac --> Pi["Pi-hole LAN IP"]
 Host --> Obsi["Obsidian GUI + MCP"]
 Obsi --> Vault["Host vault volume"]
 NC --> NCData["App data bind mount"]
 Maria --> DBData["Consistent DB backup needed"]
 Graf --> GVol["Persistent Grafana volume"]
 PM --> PVol["Persistent TSDB volume"]
```

## Operational trust boundaries

| Boundary | Verification / concern |
| --- | --- |
| Internet to Nginx | TLS/mTLS varies by virtual host; verify actual enforcement and router reachability |
| Internet to SSH | Prefer public-key auth, restricted allowed users and monitored source traffic |
| Host to Docker | Docker forwarding/NAT can differ from firewalld public-zone listings |
| Container to host | Container localhost is not host localhost; use intentional gateway and SSH policy |
| LAN to macvlan | Container gets its own LAN IP; host-to-macvlan reachability is special |
| MCP to vault | Write-capable tool needs authenticated access, POSIX permission and SELinux review |
| Monitoring to runtime | cAdvisor mounts and sockets widen read/control capability; isolate accordingly |

## Evidence gaps

The inspected notes did not establish every client DNS assignment, Pi-hole physical macvlan parent, Collabora runtime status, or end-to-end renewal / reboot recovery. An architecture diagram must not be treated as a security scan or as proof of those services' health.

**Related:** [Nextcloud](../nextcloud/README.md), [DNS](../dns/README.md), [Monitoring](../monitoring/README.md), [MCP](../mcp/README.md), [Remote access](../remote-access/README.md), [Security](../security/README.md).
