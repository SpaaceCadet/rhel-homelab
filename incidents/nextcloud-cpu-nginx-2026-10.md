# Case study: Nextcloud CPU saturation and automated Nginx reconnaissance

**Recorded:** 12 October 2026. **Source:** Obsidian read-only incident investigation. This report summarizes the investigation; it is **not** a claim of confirmed exploit or proven PHP bug.

## Symptoms and impact

A Nextcloud Apache/PHP Docker container was observed at approximately **597% CPU** (~6 logical CPUs) while reporting only **213 MiB** of memory usage in the observed sample. Several Apache prefork workers each consumed near one CPU core. Host load rose and fans ran loudly. The workload later appeared to subside without container restart, but CPU wasn't measured at the exact moment the fan quieted.

Separately, Nginx logged repeated automated requests for common configuration and secret-file paths. In the reviewed subset of **178 requests from one external source**, **176 returned 404** and **2 returned 400**; no 2xx responses appeared for that source. This is not proof of universal compromise absence.

## Investigation

- `docker stats --no-stream` and per-process views isolated the busy workload to Apache workers.
- Short `strace` samples yielded no captured syscalls from inspected workers, consistent with sustained user-space CPU consumption.
- `perf` attributed many sampled cycles to JIT-related execution.
- PHP CLI inspection showed OPcache JIT enabled with a small JIT buffer, but CLI configuration is not conclusive evidence of the Apache execution context.
- A few TCP sockets were in `CLOSE_WAIT`; their causal relationship to CPU use was not established.
- Access-log review distinguished local Nginx exporter monitoring traffic from an external source probing paths such as `/.env` and `/.git/config`.
- Nginx client-certificate verification appeared in configuration; actual virtual-host scope and public reachability still required independent checks.

## Conclusions

**CPU root cause: unresolved.** JIT activity is not proof of a JIT defect or infinite loop. The observed reduction in fan noise cannot alone verify a sustained CPU recovery. No confirmed intrusion was found in the reviewed responses; security assessment cannot rely on this alone.

## Safer follow-up actions

1. Correlate CPU with request rate, PHP worker states, cron/background jobs and database queries during a future recurrence.
2. Gather bounded `perf`, `strace`, PHP-FPM/Apache, application and database metrics under controlled conditions.
3. Validate TLS client authentication separately and review reverse-proxy and Docker-published port exposure.
4. Review web access logs for successes, authentication events and unusual client behavior; retain only necessary logs securely.
5. Ensure Docker image updates and application patching do not depend solely on client mTLS.
6. Add alerting on sustained CPU, high load, unusual request bursts and exporter health.

## Redaction

Real host identifiers, addresses, usernames, certificate paths and attacker infrastructure have been omitted. The raw source logs remain private.

## Mitigation added on 26 October 2026

An [hourly CPU watchdog](../nextcloud/cpu-watchdog.md) was deployed after the operator reported rare recurring saturation and requested automatic recovery. It requires host and running-container uptime above one hour, host CPU above 80%, and Nextcloud above 50% of total host CPU capacity in three samples before restarting only the app container. The first observed check recorded host CPU 3.8% and Nextcloud 0.0%, correctly exiting without restart. The saturation/restart path was not tested under load. This is symptom mitigation; the original root cause remains unresolved.
