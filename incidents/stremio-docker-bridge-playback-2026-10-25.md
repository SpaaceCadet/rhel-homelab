# Incident: Stremio playback outage — Docker bridge migration (2026-10-25)

**Status:** Restored, exact defect of original bridge unproven  
**Environment:** RHEL 10.1, Docker Compose, tsaridas/stremio-docker, host and bundled Nginx, Stremio Server 4.20.16, FFprobe/HLSv2 and BitTorrent.  
**Scope:** Homelab playback failed while frontend was responsive. No data loss observed.  
**Privacy:** Public report sanitizes actual local hostname, host IP, stream hashes, peer IPs, and certificate material.

## Executive summary

The browser could open Stremio, but selected video failed with HLSv2 504 responses and "Video is not supported". The bundled container Nginx, not the host Nginx, timed out waiting for the Stremio backend on container loopback port 11470. A separate self-signed HTTPS certificate trust issue was verified and corrected for Node.js, yet playback still failed. Stream statistics showed zero downloaded bytes, zero usable peers, and absent metadata despite more than 2,000 attempts to connect.

Host and default-Docker-bridge control torrents downloaded. The existing Stremio bridge and its network namespace stalled in repeated timed tests, while a new user-defined Docker bridge downloaded the same official Linux ISO torrent. After attaching the running Stremio container to the new bridge, Docker changed its default route and playback succeeded. Docker Compose was updated to exclusively use the new external bridge. Following recreation, route/network membership checks confirmed this configuration; the operator reported service working.

**Conclusion:** Replacing the outbound bridge path was an effective mitigation. The precise mechanism that made the original bridge stall was not proved. A distinct Node.js TLS trust defect was also found; an external add-on CORS error was not proved resolved.

## Service architecture

~~~text
Browser -> HTTPS local hostname :443
        -> host Nginx -> 127.0.0.1:8083 (host)
        -> Docker port -> bundled Nginx :8080
        -> backend 127.0.0.1:11470 (container)
             -> torrent engine/cache
             -> FFmpeg/FFprobe, HLSv2
Backend probes media URLs via advertised HTTPS local hostname.
Docker bridge determines the container's outbound route.
~~~

The host Nginx frontend was healthy; its long read timeout was not the relevant 504. Internal Nginx logged "upstream timed out ... reading response header" against the container's port 11470.

## Evidence / timeline, 2026-10-25

| Investigation step | Observed evidence | Meaning |
| --- | --- | --- |
| Browser | HLSv2 probe/playlist 504, player error 83, "Video is not supported" | Media unavailable; not proof of unsupported codec |
| UI sanity check | GET / on published loopback 8083 returned HTML 200 | Web UI reachable |
| Server logs | "Probe process exited with code: 1"; media GET 504 | Media pipeline failing |
| TLS self-request | Internal name resolved; Node failed DEPTH_ZERO_SELF_SIGNED_CERT | Container Node CA trust incomplete |
| Node trust test | NODE_EXTRA_CA_CERTS pointing to copied public certificate returned HTTPS 200 without bypass | Trusted CA mechanism works for Node; FFprobe trust is separate |
| Torrent stats | name=null, files=null, peers=0, downloaded=0, downloadSpeed=0; connection attempts increased beyond 2,000 | No usable torrent metadata/pieces during sampled session |
| Docker connectivity | Outbound TCP 443 worked; multiple peer-port sockets ESTAB | Basic egress/peer TCP exists; no evidence of successful BitTorrent handshakes for that stream |
| Firewalld/NAT | Docker zone permissive, forwarding enabled; original-bridge MASQUERADE counter nonzero | Missing NAT rule was not the cause |
| Official Linux torrent on RHEL host | Roughly 323 KiB/s | Host BitTorrent capability shown |
| Same torrent on default Docker bridge | ~133–164 KiB/s | General Docker bridge can download |
| Same torrent on original Stremio bridge | 0 B/s in repeated timed trials | Original path suspicious, subject to peer variability |
| Same torrent on fresh user-defined bridge | ~6.5 MiB obtained, ~110–154 KiB/s | Fresh bridge worked for control |
| Stremio attached to fresh bridge | Default route switched to the new gateway/interface | New outgoing traffic used new bridge |
| Functional test | Browser screenshot showed video actively playing | Playback restored |
| Compose redeploy | Only external working bridge attached; default route verified after recreation; user confirmed working | Persistent migration observed |

The test ISO was old and may have a sparse swarm. These sequential download samples are strong clues but not controlled proof that a particular nftables rule or network object was broken.

## Evidence excerpts (redacted)

~~~text
upstream timed out (110: Operation timed out)
while reading response header from upstream
upstream: http://127.0.0.1:11470/hlsv2/probe?mediaURL=...
Error: Probe process exited with code: 1
~~~

~~~json
{"name":null,"files":null,"peers":0,"downloaded":0,"downloadSpeed":0,"selections":[]}
~~~

## Cause assessment

**Verified:**
- The Node.js process did not initially trust the local self-signed/CA-capable HTTPS certificate. Adding that public trust certificate through NODE_EXTRA_CA_CERTS allowed an authenticated HTTPS self-request.
- Internal Nginx forwarded requests to port 11470 but the backend did not produce timely media responses.
- The affected torrent session transferred no data during repeated observations.
- Routing Stremio through the fresh Docker bridge coincided with observed playback restoration.

**Not verified:** The original bridge's exact failure mode: kernel filtering, conntrack, Docker bridge state, tracker/peer behavior, or another interaction. Some TCP sessions and masqueraded packets succeeded. Do not call the original bridge permanently broken without additional instrumentation.

**Separate issue:** A CORS error from an external add-on was observed. The origin's response controls those CORS headers; changing the local Nginx or migrating a bridge does not by itself fix it.

**Do not conflate with 2026-10-24:** That earlier incident concerned a container failing to resolve the advertised HTTPS hostname when probing E-AC3 media. See [the earlier HLSv2/DNS report](../stremio/troubleshooting.md).

## Remediation sequence

1. Preserve persistent Stremio data and the host-only published web port.
2. Test the local HTTPS trust chain; mount **only the public certificate** as read-only and add NODE_EXTRA_CA_CERTS. Never set TLS verification off globally.
3. Use read-only logs, torrent statistics, socket inspection, Docker routes, Firewalld/nftables counters and control torrent experiments rather than opening firewall ports blindly.
4. Create a new user-defined diagnostic bridge; verify it can download the official control torrent.
5. Attach Stremio to the new bridge; verify its default route changes to that bridge; retry playback and observe success.
6. Update Compose to attach **only** to the working named external bridge, while retaining the volume, loopback-only port, extra_hosts local name resolution and certificate trust settings.
7. Recreate only Stremio and inspect its sole network/default route. Validate playback.

Sanitized durable configuration: [stremio/compose.yaml](../stremio/compose.yaml). The actual external bridge's name in the example is stremio-diag. On a rebuilt host, provision this network before Compose:

~~~bash
docker network inspect stremio-diag >/dev/null 2>&1 ||
  docker network create --driver bridge stremio-diag
cd /path/to/stremio-deployment
docker compose config -q
docker compose up -d --no-deps stremio
~~~

If a new deployment selects a conflicting subnet or route, examine the effective network/gateway; Docker-assigned network addresses are not portable.

## Verification and operations

~~~bash
# Confirm running container's network membership and routing
docker inspect stremio --format '{{json .NetworkSettings.Networks}}'
PID=$(docker inspect -f '{{.State.Pid}}' stremio)
sudo nsenter -t "$PID" -n ip route
sudo nsenter -t "$PID" -n ip route get 1.1.1.1

# Frontend health
curl -I http://127.0.0.1:8083/

# HTTPS must validate; no insecure skip-verification switches
docker exec stremio node -e '
require("https").get("https://stremio.home.test/", res => {
 console.log(res.statusCode); res.resume();
}).on("error", console.error)'

# Streaming backend/logs
docker logs --since 10m stremio 2>&1 |
  grep -Ei 'hlsv2|probe|upstream timed out|error'
~~~

During authorized test playback also observe: live download bytes and peer counts, playlist HTTP result, image **and sound**, and subsequent behavior after a planned service recreation. A UI 200 or stats 200 alone does not prove media functionality.

## Risk, recurrence prevention, and follow-up

- Preserve a named external Docker network in deployment docs and disaster-recovery procedures. Do not remove it while Compose references it.
- Monitor HLSv2 5xx, probe exits, torrent transfer progress, and route/network membership, not merely container "Up" state.
- If the problem returns, capture conntrack state and packet traces on both bridge and physical egress; repeat *simultaneous* control tests on several healthy licensed swarms.
- Avoid changing host-wide firewall/security restrictions without matching drop counters or packet traces.
- Keep host web port bound to 127.0.0.1; restrict public reachability at the HTTPS proxy. Review the security implications of NO_CORS before broader exposure.
- Trust a suitable CA certificate with correct hostname/SAN and usage; rotate/local-CA-manage it. NODE_EXTRA_CA_CERTS applies to Node, not necessarily FFprobe.
- Back up Compose and persistent data. Avoid docker compose down -v and avoid deleting browser Guest state. Pin a tested image digest rather than floating latest when reproducibility matters.
- Remaining uncertainty: why the original Stremio bridge stalled. Treat the new bridge as a successful *mitigation*, not a complete underlying root-cause fix.

## Related documents

- [Stremio deployment](../stremio/README.md)
- [Sanitized Compose](../stremio/compose.yaml)
- [Previous HLS/FFprobe/DNS incident](../stremio/troubleshooting.md)
- [Incident index](README.md)
