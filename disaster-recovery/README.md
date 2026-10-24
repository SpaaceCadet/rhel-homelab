# RHEL homelab disaster recovery and controlled migration

**Status:** Sanitized operator runbook derived from Obsidian migration audits; **not evidence that a complete restore was performed**. The historic October 17 master note preceded the October 19 Grafana persistence repair. This guide incorporates the later state and does not repeat the earlier assumption that Grafana may be discarded.

## Recovery goals / stopping rules

1. **Inventory** versions, image digests, Compose project paths, mounted data, Docker networks, custom systemd units, crontabs, certificates and actual NIC configuration.
2. **Verify backups**: consistent MariaDB dump or supported physical backup, Nextcloud files/config, Obsidian vault, Pi-hole state, Grafana/Prometheus volumes, encrypted Nginx/Certbot/SSH/tunnel secrets.
3. **Stage replacement host** under a distinct LAN IP. Keep old host and old data intact.
4. **Rebuild base services**: storage mounts, Docker, SELinux enforcing, reviewed Firewalld, SSH and Nginx. Recreate Docker networks including external macvlan with the correct physical parent.
5. **Restore applications** with version compatibility checked, before changing external DNS or router forwards.
6. **Accept/cut over** only after application reads/writes, TLS/mTLS, DNS, monitoring and authorized remote-access tests succeed.
7. **Rollback** by restoring original addressing and network forwarding to the old host if acceptance fails; never let two active services claim the same reserved LAN IP.

## Inventory commands (read-only; sanitize outputs)

```bash
hostnamectl
lsblk -f
findmnt
df -hT
ip -br addr
ip -4 route
nmcli connection show
docker compose ls --all
docker ps -a
docker volume ls
docker network ls
docker image ls --digests
sudo firewall-cmd --permanent --list-all-zones
sudo semanage boolean -l -C
sudo semanage port -l -C
systemctl list-timers --all
```

Do not publish `docker inspect` dumps, NetworkManager profiles, active source allowlists, tunnel environment files or credential recovery packages.

## Backup matrix

| Asset | Required recovery material | Restore rule |
| --- | --- | --- |
| MariaDB | Consistent point-in-time dump or supported physical backup | Match with Nextcloud files/config; do not simply copy a running datadir |
| Nextcloud | Data, config, custom apps, compatible image | Maintenance window; ownership/SELinux and trusted proxy verification |
| Grafana | Persistent data volume plus datasource/dashboard exports | Preserve dashboard UIDs, users and compatible database schema |
| Prometheus | TSDB (including WAL if full restore) and scrape config | Stop for file-level copy or use supported snapshot process |
| Pi-hole | Persisted config/local DNS/dnsmasq state + network definition | Create external macvlan before Compose, avoid IP collision |
| Obsidian | Vault and MCP build source/lockfile + permissions | Test write permissions/SELinux and vault-path mapping |
| Nginx / Certbot | Encrypted configs, ACME accounts, live/archive symlinks, client CA private keys | Never put private key material into Git |
| MCP tunnel / SSH | Protected policy, SSH identity, tunnel environment and systemd units | Keep authentication restrictions and regenerate credentials as required |

**Do not run** `docker compose down -v`, `docker volume prune`, raw nftables restores or disk formatting as part of an exploratory recovery attempt.

## Target validation

```bash
getenforce
sudo nginx -t
sudo certbot certificates
docker compose ps
curl -fsS http://127.0.0.1:9091/-/ready
curl -fsS http://127.0.0.1:3000/api/health
```

The curl ports are examples from the documented reference topology, **not guaranteed target mappings**. Also verify authenticated Nextcloud login/upload/download, MariaDB integrity, local Pi-hole queries from a separate LAN client, Obsidian test write, monitored exporters, and tunnel authorization. For certificate renewal, perform a controlled dry run and verify reload behavior separately.

## Backup validation and rollback

Maintain versioned encrypted **off-host** copies and periodically restore them to an isolated test system. A persistent Docker volume is not an off-host backup. Keep recovery credentials outside the public repo. Document last successful backup, last restore drill, expected recovery point and recovery time; these are currently **not verified by the cited notes**.

See also: [monitoring recovery](../monitoring/backup-recovery.md), [Nextcloud operations](../nextcloud/operations.md), [Nginx TLS recovery](../nginx/README.md), [SELinux](../security/selinux.md).
