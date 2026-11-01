# Nextcloud — MariaDB migration from HDD to NVMe SSD

Public case study: paths, hostname and container names are sanitized. Verify that the example SSD directory is actually on SSD storage before using it.

Recorded: 2026-11-01, Africa/Casablanca. Work performed during the 31 October / 1 November session.

## Outcome and scope

The active MariaDB data directory was moved from the 1 TB HDD to the existing NVMe SSD. Nextcloud application files, configuration, and uploaded media stayed on the HDD. This was a storage relocation, not a database upgrade.

| Component | Before | After |
|---|---|---|
| MariaDB host directory | `/mnt/hdd/db` on ext4 HDD | `/srv/ssd/nextcloud-db` on XFS NVMe |
| MariaDB container mount | `/var/lib/mysql` | Unchanged |
| Nextcloud host directory | `/mnt/hdd/nextcloud` | Unchanged, on HDD |
| Nextcloud container mount | `/var/www/html` | Unchanged |
| Uploaded files | Under Nextcloud's HDD data directory | Unchanged |

Host: `example-host`, RHEL 10.1. Containers: `example-db-1`, `example-app-1`. Observed database image: `mariadb:10.6`; Nextcloud reported 33.0.1 (internal version 33.0.1.2). These are historical observations, not version recommendations.

## Why separate the database from media storage?

Database tables, indexes and transaction logs involve small random I/O and latency-sensitive operations. NVMe storage reduces storage latency and separates database I/O from large media transfers on the HDD. Photos and videos retain the HDD's larger capacity.

Expected benefits include faster database access during directory browsing, metadata operations and synchronization. No controlled before/after benchmark was performed: no percentage improvement or upload-speed increase is claimed.

Before migration, the SSD root filesystem had about 191.8 GiB available (15% used). This was a point-in-time pre-migration reading.

## Evidence

Live inspection before migration showed MariaDB's running process mounted HDD `/db` at `/var/lib/mysql` on `/dev/sda1`.

After migration, the running MariaDB process mount table showed:

```text
259:3 /srv/ssd/nextcloud-db /var/lib/mysql rw,relatime - xfs /dev/nvme0n1p3
```

This confirms the active database uses the SSD, rather than merely confirming that a copied directory exists.

The administrator supplied these successful application checks:

```text
installed: true
versionstring: 33.0.1
maintenance: true
needsDbUpgrade: false
```

`occ user:list --limit=1` returned an existing user, confirming database access. The maintenance-mode message about apps not being loaded was expected.

The transcript does not contain every intermediate command's output. The copy/checksum procedure below records the migration method supplied; checksum success, saved backup location, exact deployed YAML suffix and image-ID equality were not independently captured. Browser upload/download acceptance was requested but its result was not supplied.

## Procedure used as the migration runbook

Do not rerun blindly against the now-active SSD database.

1. Identify Compose project, service and source files through container labels. Historical source: `/opt/example-nextcloud/compose.yaml`; verify current labels before reuse.
2. Save the current Compose file securely and record the running database image ID. Preserve that exact image during relocation; check the image ID before starting the copied database, not only afterward.
3. Check database size, SSD capacity, and `findmnt -T /srv`. Destination must be new and empty.
4. Pause synchronization and database-writing background jobs. Pause the Nextcloud CPU watchdog for maintenance.
5. Enable Nextcloud maintenance mode; stop the application, then cleanly stop MariaDB. Check shutdown logs and exit status.
6. Copy the entire stopped database directory, preserving ownership and metadata:

```bash
sudo mkdir /srv/ssd/nextcloud-db
sudo rsync -aHAXS --numeric-ids --info=progress2 \
  /mnt/hdd/db/ /srv/ssd/nextcloud-db/
sudo rsync -aHAXScni --numeric-ids --delete \
  /mnt/hdd/db/ /srv/ssd/nextcloud-db/
```

The second command is a checksum dry run; `-n` prevents changes, including deletion. Expected result: no differences and no errors. Never remove `-n` casually. Both services must stay stopped throughout the copy and comparison.

7. Change only MariaDB's bind source:

```yaml
# Before
- /mnt/hdd/db:/var/lib/mysql
# After — private SELinux labeling example
- /srv/ssd/nextcloud-db:/var/lib/mysql:Z
```

Keep SELinux enforcing and preserve appropriate existing options. `:Z` is appropriate for a directory private to one container; exact deployed labeling was not independently verified. Leave Nextcloud's HDD mount, credentials, network and database version unchanged.

8. Validate Compose. Recreate only the database service with the existing project/file flags, `--no-deps --force-recreate --pull never`. Ensure the locally selected image is the original image; `--pull never` alone does not guarantee identity if a tag changed locally. A restart alone does not apply a new bind mount.
9. Confirm the mount, image identity and MariaDB readiness. Start Nextcloud while still in maintenance mode and run:

```bash
sudo docker exec -u www-data example-app-1 php /var/www/html/occ status
sudo docker exec -u www-data example-app-1 php /var/www/html/occ user:list --limit=1
```

10. Disable maintenance mode, verify login/browsing and download/upload, then restore paused jobs and clients. Keep the original HDD directory until the change is accepted and independent backups are verified.

## Rollback

### Before reopening application writes

Stop Nextcloud and MariaDB. Restore the saved original Compose file so the database points to the untouched HDD directory. Start the same MariaDB image, verify readiness and database access, then disable maintenance mode and restore jobs.

This assumes the original directory is intact and application files have not diverged. Never run two database instances against the same data directory.

### After application writes have resumed

The old HDD database is stale. Switching directly to it can lose metadata and disagree with current Nextcloud files.

Pause clients/jobs, enable maintenance mode, stop Nextcloud and cleanly stop MariaDB. Copy the current SSD database into a new empty HDD directory, verify checksums, and point MariaDB there. Start and validate before reopening writes. Check capacity first and preserve the original rollback copy.

If the SSD database is corrupted/unreadable, use a tested, consistent backup recovery plan covering both database and application data; relocation alone cannot repair corruption.

## Follow-up audit: separate from migration acceptance

- APCu local cache enabled; CLI enabled; cache allocation 32 MiB.
- PHP CLI memory limit 2048 MiB; OPcache enabled, 128 MiB, 32 MiB interned strings, 10,000 scripts. Web-runtime cache utilization was not measured.
- Redis distributed caching and locking were not configured in effective settings.
- MariaDB buffer pool 128 MiB; flush-at-commit 1; maximum connections 151, peak observed 4.
- Measurements were taken shortly after restart and largely idle. They do not justify a specific database cache increase.
- Nextcloud background mode was changed to cron and root's crontab was edited for five-minute execution. Two cron.php processes were later observed. Completion and unattended scheduling still need validation; do not record this as fully resolved.
- The original HDD directory is a rollback snapshot, not a continuously updated backup.

## Related documentation

- [Nextcloud overview](README.md)
- [Operations and recovery](operations.md)
- [CPU watchdog](cpu-watchdog.md)

## References

- https://docs.docker.com/engine/storage/bind-mounts/
- https://docs.docker.com/reference/cli/docker/compose/up/
- https://mariadb.com/docs/server/server-usage/backup-and-restore/backup-and-restore-overview
