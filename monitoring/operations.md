# Monitoring operations and troubleshooting

## Inspect

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 prometheus grafana node-exporter cadvisor nginx-exporter
curl -fsS http://127.0.0.1:9091/-/ready
curl -fsS http://127.0.0.1:3000/api/health
curl -fsS http://127.0.0.1:9091/api/v1/targets
curl -fsS http://127.0.0.1:9091/api/v1/status/flags
```

The historic host's Prometheus configuration scraped Node Exporter through the host gateway, cAdvisor and Nginx Exporter by Compose DNS name, and Prometheus at localhost. From inside Grafana, the datasource URL was **`http://prometheus:9090`**, not the browser's host published port 9091. This distinction prevents common datasource connectivity errors.

## PromQL examples

```promql
up
```

```promql
nginx_up{job="nginx"}
```

```promql
100 * (1 - avg(rate(node_cpu_seconds_total{job="node",mode="idle"}[1m])))
```

```promql
100 * avg(rate(node_cpu_seconds_total{job="node",mode="iowait"}[1m]))
```

I/O wait is **not** Linux PSI pressure; don't label the panel as PSI if `node_pressure_*` metrics are missing.

For cAdvisor, investigate `container_last_seen` and container CPU/memory series, checking label availability for the particular version. An `up=1` result demonstrates scrape success, not completeness of the collected host/container metrics.

## Source-specific lessons

1. Grafana was originally configured without a persistent volume; container recreation could have lost the database. A later verified fix moved it to a persistent external volume.
2. cAdvisor initially lacked host runtime mounts. Later adjustments provided sufficient access to observe metrics for 11 containers, but Docker/containerd socket mounts expand exposure significantly. The **published sample intentionally leaves these mounts out** rather than implicitly granting high privilege.
3. The host lacked `/proc/pressure` in the observed context; dashboards relying on PSI did not work. A separate CPU I/O wait panel was created.
4. Node Exporter used host networking and PID namespace; not all host filesystem coverage was verified without mounting the root filesystem.
5. Nginx Exporter reads `stub_status`: active connections and request counts, not detailed request status distribution or response latency.

## Security and verification

- Restrict metrics listeners to trusted networks or bind to loopback, as appropriate to the collector path.
- Keep `stub_status` restricted, accessible to the exporter but not the public Internet. SELinux and host firewall policy still apply.
- Treat Grafana dashboards, users, datasource credentials and exports as potential sensitive configuration.
- Ensure automatic retention limits fit disk capacity; `/prometheus` is persistent but metrics history still expires.
- No automatic monitoring backup was documented in the October audit.
