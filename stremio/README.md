# Stremio on RHEL — Docker deployment

A documented homelab deployment of [tsaridas/stremio-docker](https://github.com/tsaridas/stremio-docker) behind an HTTPS Nginx reverse proxy, including diagnosis of **silent E-AC3 playback and HLSv2 probe HTTP 500**.

> **Privacy:** Hostnames, LAN IP addresses, and data paths below are examples. No real certificates, keys, tokens, or browser Guest data are included.

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
