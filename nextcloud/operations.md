# Nextcloud and MariaDB operations / recovery runbook

This adapts a real RHEL Docker deployment audit into safe, reusable procedures. Substitute your own compose directory and containers. Database operations are potentially disruptive: stage and test first.

## Reference configuration: evidence vs improvements

| Aspect | Historical observation | Published example |
|---|---|---|
| Nextcloud image | Unpinned `nextcloud` | `nextcloud:apache` illustration; pin tested release |
| DB image | `mariadb:10.6` | Preserved as **historical**, not a current recommendation |
| Data | Host bind mounts on secondary disk | Local `./data/` paths with `:Z` |
| Networking | App host port exposed, DB internal | App bound to loopback, DB internal |
| Secrets | Same plaintext root/app password in source Compose | Two distinct placeholders in ignored `.env` |
| DB command | READ-COMMITTED, binary logging ROW | Recorded for reproduction; capacity/retention require review |

## Inspect

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 app db
docker compose exec -u www-data app php occ status
docker compose exec db mariadb-admin ping -u root -p
curl -I http://127.0.0.1:8080/status.php
```

`mariadb-admin` availability varies by image. Avoid typing secrets in shell commands where they may enter history or process lists.

## Application reverse-proxy considerations

Use TLS at host Nginx, forward `Host` and `X-Forwarded-Proto`, and configure application trusted domains/proxies accordingly. For installations using mTLS, a client needs the trusted certificate before the HTTP request reaches Nextcloud. mTLS is **not** a reason to skip updates.

## Backup

**Do not back up a running MariaDB merely by copying its `/var/lib/mysql` tree.** Use a consistent database dump or supported physical backup with tested restore. Separately preserve Nextcloud's data/configuration/app state; keep backup files outside the served webroot.

Illustrative flow:

```bash
# Plan a maintenance window and consistent backup method
docker compose exec -u www-data app php occ maintenance:mode --on
# Run a tested logical/physical DB backup to access-restricted storage
# Back up the Nextcloud bind-mounted data/config/apps with ownership + SELinux context strategy
docker compose exec -u www-data app php occ maintenance:mode --off
```

Do not use the above as an unattended backup script: exceptions must restore service and backup/restore must be verified. A `docker compose down` without a consistent database backup is insufficient for application disaster recovery.

## Restore/migration checklist

1. Record installed image digests, Nextcloud and MariaDB versions, extensions, hostname and application settings in a **private** inventory.
2. Provision storage with correct ownership and SELinux labels; confirm disk capacity.
3. Restore a *tested* DB backup and the matching Nextcloud data/config/apps from the same logical recovery point.
4. Supply existing application DB credentials from a password manager; setting init variables does not rotate existing users.
5. Bring containers up, inspect logs and `occ status`, validate login, file listings, upload/download and scheduled jobs.
6. Restore TLS/CA separately via secure backup; test mTLS if enabled and ensure certificate renewal reloads Nginx.
7. Perform a real restore drill, document recovery time and rollback.

## Credential remediation

The historical configuration contained the **same plaintext password** for DB root and app user. Rotate using a coordinated MariaDB account update and Nextcloud configuration update during a controlled maintenance window, then verify app/database connectivity. Simply editing Compose environment is **not** sufficient for an initialized database.
