# Grafana and Prometheus persistence, backup and recovery

## Verified October 2026 repair

A read-only snapshot initially showed Grafana without an explicitly declared volume. Later maintenance installed an **external Grafana data volume** mounted at `/var/lib/grafana` and explicitly attached the pre-existing Prometheus volume at `/prometheus`. Grafana login survived container recreation; a Prometheus historical query worked. Both data volumes were intentionally declared external in the repaired deployment. Their real volume IDs are intentionally excluded.

A reproducible **new installation** can use the named volumes in [compose.yaml](compose.yaml). **Do not replace the external volumes of an existing installation with empty ones**: that would hide or abandon existing data.

## Preserve these components

| Item | Content |
| --- | --- |
| Grafana data (`/var/lib/grafana`) | SQLite/database, dashboards, users, plugins, datasource settings |
| Prometheus data (`/prometheus`) | TSDB blocks, WAL and historical samples |
| `compose.yaml` | Service names, image versions, port mapping and volume names |
| `prometheus.yml` | Jobs, targets and scrape intervals |
| Image digests | Exact tested versions for restore |
| Dashboard exports | Portable JSONs, not a substitute for complete Grafana database |

## Backup procedure (planned, not executed here)

1. Identify the **actual** Docker volumes using `docker inspect grafana prometheus` and `docker volume inspect` on the source host.
2. Make a configuration/dashboard export (Grafana UI or authenticated API) and separately back up its complete database/state.
3. During a maintenance window, stop Grafana and Prometheus gracefully before taking a complete file-level copy of the volumes, including Prometheus WAL. Alternatively use a documented, supported snapshot/backup strategy.
4. Securely archive with ownership/permissions preserved, generate checksums and copy to encrypted **off-server** storage. Do not publish exports or backups without reviewing sensitive fields.
5. Restart the containers, validate `/api/health`, `/-/ready` and scrape-target status, then test the backup by restoring on an isolated host.

A Docker volume is **persistence**, not a backup. The source audit found earlier rollback archives, but they were older than some dashboard changes and therefore were not sufficient as a guaranteed complete current migration backup.

## Restore/migration

- Restore into **fresh, empty** volumes on the target, not into a running database or nonempty volume.
- Use saved matching image versions for the initial restoration. Newer Grafana may upgrade its database, making rollback with an older image unsafe.
- Keep the original host untouched until acceptance checks succeed. Avoid simultaneous ownership of service IPs/hostnames or copying two live databases together.
- Recreate host Nginx `stub_status` and ensure exporter reachability; it is a dependency outside the Compose monitoring stack.
- Verify Grafana login, datasource connectivity (`http://prometheus:9090`), all dashboards, actual container series, Nginx `nginx_up=1`, and historic samples if history was migrated.
- Roll back using the **pre-upgrade backup** and the matching image, rather than trying to downgrade a modified Grafana database.

No scheduled backups were verified for the monitoring stack. Periodic tested restorations and capacity/retention planning remain follow-ups.
