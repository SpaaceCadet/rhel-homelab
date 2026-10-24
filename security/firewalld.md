# Firewalld, Docker and nftables on RHEL

## Context

A read-only RHEL homelab audit found `firewalld` enabled, with a physical NIC in the `public` zone and Docker bridges in a Docker-specific zone. The standalone `nftables.service` was inactive, **but nftables rules were populated** by firewalld and Docker. This is normal: an inactive nftables service does not imply an empty firewall.

The source also had broad service allowances and a geography-based allow rule. **Those are intentionally not reproduced:** broad `accept` rules can weaken intended port-level restrictions. Public examples should be minimal.

## Inspect before changing

```bash
sudo firewall-cmd --state
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --zone=public --list-all
sudo firewall-cmd --permanent --zone=public --list-all
sudo firewall-cmd --list-all-policies
sudo nft -a list ruleset
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

Compare runtime and permanent configurations. Runtime-only rich rules can disappear on reload; permanent changes require a reload to become active. Do not assume a declared allowed service is Internet-accessible—or a missing service is blocked—without checking Docker port publishing, NAT and upstream filtering.

## Minimal example: SSH and HTTPS

**Do not run these blindly** on a remote server. Keep an established admin SSH session and console access; confirm the intended interface and zone first.

```bash
sudo firewall-cmd --permanent --zone=public --add-service=ssh
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --check-config
sudo firewall-cmd --reload
sudo firewall-cmd --zone=public --list-all
```

Remove obsolete services/ports only after confirming dependencies (for example an NFS share, Cockpit, application health check, or ACME HTTP-01 challenge). For temporary HTTP-01, plan and verify port 80 exposure intentionally.

## Docker-specific networking

- A Docker bridge or published port may be governed by Docker-managed nft/iptables chains such as `DOCKER-USER` and NAT DNAT chains.
- A Docker-owned `docker-forwarding` policy may permit forwarding to Docker interfaces even when the host public zone does not explicitly name a published port.
- Prefer a loopback-only mapping (for a host-local reverse proxy): `127.0.0.1:8083:8080` instead of `8083:8080`.
- Do not replay `nft -a list ruleset` or Docker-managed chains to a rebuilt system. Recreate Compose networks/ports and let Docker generate runtime rules.
- Test from LAN **and** an authorized external client for any intended WAN-facing service.

## Migration checklist

1. Back up `/etc/firewalld/` securely, including custom zones, policies and ipsets; exclude sensitive ipset contents from public docs.
2. List runtime and permanent rules separately.
3. Configure a staging host with the correct NIC zone, minimal needed services and reviewed custom restrictions.
4. Recreate Docker workloads and compare the effective forwarding/NAT policy.
5. Validate SSH connectivity before applying tighter restrictions.
6. Verify Nginx HTTPS, internal container ports, mTLS and ACME challenges as applicable.
7. Keep a backup and console access for rollback.

## Troubleshooting

```bash
sudo journalctl -u firewalld -n 100 --no-pager
sudo firewall-cmd --zone=public --list-rich-rules
sudo nft list ruleset
sudo ss -lntp
docker network ls
```

Do not attribute every connectivity issue to firewalld alone: check DNS, application binding, proxy vhosts, router/NAT and SELinux too.
