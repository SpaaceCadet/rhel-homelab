# Stremio on RHEL — Docker deployment

A documented homelab deployment of [tsaridas/stremio-docker](https://github.com/tsaridas/stremio-docker) behind an HTTPS Nginx reverse proxy, including diagnosis of **silent E-AC3 playback and HLSv2 probe HTTP 500**.

> **Privacy:** Hostnames, LAN IP addresses, and data paths below are examples. No real certificates, keys, tokens, or browser Guest data are included.

## 2026-10-25 playback outage: Docker bridge migration

A later incident produced **HLSv2 504 Gateway Timeout**, backend media probe exits, and "Video is not supported", even though the frontend and /stats.json returned HTTP 200. Torrent statistics had zero bytes/peers and missing metadata. Tests found that the original Stremio bridge repeatedly stalled while the host, Docker default bridge, and a freshly created user-defined bridge downloaded an official control torrent. Moving Stremio's default route to the replacement bridge restored browser playback. The precise root cause in the original bridge was **not established**.

Read the [full postmortem](../incidents/stremio-docker-bridge-playback-2026-10-25.md). This is separate from the earlier 2026-10-24 DNS/E-AC3 incident.

### Current sanitized Compose and prerequisites

The checked-in [compose.yaml](compose.yaml) documents the restored topology: a **single named external network**, a read-only local public CA certificate mount + NODE_EXTRA_CA_CERTS, an extra_hosts mapping to the reachable host HTTPS proxy, the persistent data bind mount, and the localhost-only 8083 port mapping.

Before deployment, prepare the network and public certificate:

~~~bash
docker network inspect stremio-diag >/dev/null 2>&1 ||
  docker network create --driver bridge stremio-diag
mkdir -p data certs
# Put only a valid PUBLIC local trust certificate at ./certs/local-ca.crt.
# Update stremio.home.test and 192.168.1.10 to your own values in compose.yaml.
test -f certs/local-ca.crt
docker compose config -q
docker compose up -d stremio
~~~

Never commit the certificate's **private key**, secrets, stream info hashes, or persistent media/cache data. Do not put a hostname mapping to container 127.0.0.1. Using a self-signed server certificate with CA:TRUE as a trust anchor was a tested Node.js workaround; a properly managed local CA with valid SAN/usage is preferable. NODE_EXTRA_CA_CERTS does not necessarily configure FFmpeg's trust independently.

The network is declared external, so **Compose will not create it** on a new host. Keep it across redeployments and include network creation in disaster-recovery steps.

### Quick health check after recreation

~~~bash
docker inspect stremio --format '{{json .NetworkSettings.Networks}}'
PID=$(docker inspect -f '{{.State.Pid}}' stremio)
sudo nsenter -t "$PID" -n ip route
curl -I http://127.0.0.1:8083/
docker exec stremio getent hosts stremio.home.test
~~~

Inspect real torrent download progress and successful video/audio playback, not just the UI. A read-only HTTP 200 is not a media health check. Preserve the bind mount and browser Guest state; do not use docker compose down -v. Also review NO_CORS: it is inherited from the working environment and relaxes origin restrictions.

## Architecture

```text
Brave / Stremio Web
    │ HTTPS stremio.home.test:443
    ▼
RHEL host Nginx reverse proxy
    │ 127.0.0.1:8083
    ▼
Docker Nginx (:8080)
    │ reverse proxy
    ▼
Stremio Server (:11470 inside the container)
    ├── FFprobe / FFmpeg (inspection and transcoding)
    └── torrent download/cache
```

The **backend must also reach the externally advertised HTTPS hostname** when probing a stream. Docker DNS resolution may differ from the browser's or host's DNS.

## Deployment

1. Set up a host HTTPS reverse proxy mapping `stremio.home.test:443` to `http://127.0.0.1:8083` and verify DNS on your client.
2. Update [compose.yaml](compose.yaml) to your real hostname, reverse-proxy host IP and persistent data directory.
3. From this directory run:

```bash
docker compose config
docker compose up -d
docker compose ps
docker exec stremio getent hosts stremio.home.test
curl -I http://127.0.0.1:8083/
```

4. Open the HTTPS hostname in your browser, check Streaming Server status and test playback.
5. Do not expose internal port 11470 on the host. The host mapping above binds 8083 only to 127.0.0.1.

## Diagnosing silent audio

Read [the incident report](troubleshooting.md) for the exact symptom, evidence, cause, workaround, and validation commands. In the tested case:
- Video stream and torrent statistics worked.
- The stream used E-AC3 audio; VLC had sound while Brave did not.
- `/hlsv2/probe` returned HTTP 500, and FFprobe inside Docker couldn't resolve the advertised HTTPS hostname.
- An internal HTTP probe worked.
- Mapping the hostname to the reachable host HTTPS reverse proxy restored probing and the user observed working transcoding/playback.

**Scope:** The permanent Compose mapping should be reverified after container recreation. This is a networking-specific workaround, not evidence of a general Stremio defect or a guarantee of AAC transcoding for every file.

## Operations

```bash
docker logs --tail 100 stremio
docker exec stremio ffmpeg -version
docker exec stremio ffprobe -version
docker exec stremio getent hosts stremio.home.test
docker top stremio -eo pid,comm,args
docker compose up -d --no-deps --force-recreate stremio
```

Keep the bind-mounted `data` directory backed up and never publish it; Guest state may also live in browser storage. Avoid `docker compose down -v` when preserving state. A static `extra_hosts` IP must be updated if the reverse proxy changes address.

**Related project:** [tsaridas/stremio-docker](https://github.com/tsaridas/stremio-docker).
