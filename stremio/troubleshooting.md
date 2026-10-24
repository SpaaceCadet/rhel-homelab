# Incident: HLSv2 probe 500 and missing E-AC3 audio

**Date:** 2026-10-24 · **Environment:** RHEL 10.1, Stremio Server 4.20.16, FFmpeg/FFprobe 4.4.1-Jellyfin, Brave/Chromium, Nginx and Docker.

## Symptoms and evidence

- A stream played without sound in the browser but played with sound in VLC.
- Affected media included HEVC video and E-AC3 audio; other investigated video used H.264 with E-AC3 audio.
- Browser test `MediaSource.isTypeSupported('audio/mp4; codecs="ec-3"')` reported `false`.
- Torrent `stats.json` returned 200; direct media requests returned 206.
- The web player requested `/hlsv2/probe?mediaURL=https%3A%2F%2Fstremio.home.test%2F...`, returning HTTP **500**.
- Container log: `Error: Probe process exited with code: 1`.
- No active FFmpeg process was observed at the times inspected (not a continuous capture).

## Root cause isolated

A direct FFprobe invocation **inside the container** returned:

```text
Failed to resolve hostname stremio.home.test: Name does not resolve
```

Yet the same stream was successfully inspected over the container's internal HTTP proxy:

```bash
docker exec stremio ffprobe -v error \
  -show_entries stream=codec_name,codec_type -of json \
  "http://127.0.0.1:8080/<torrent-hash>/<file-index>"
```

This established that FFprobe could read the media and that the custom HTTPS hostname, not the codec library itself, was preventing the original probe. Container Nginx forwards `/hlsv2` to the server on `127.0.0.1:11470`.

## Fix

For a host Nginx reverse proxy reached through `192.168.1.10:443`, add to the Compose service:

```yaml
extra_hosts:
  - "stremio.home.test:192.168.1.10"
```

Here `192.168.1.10` and `stremio.home.test` are **examples**. Do **not** use `127.0.0.1`: it refers to the container, whereas the advertised URL uses HTTPS port 443 on the host reverse proxy.

In the actual incident, a temporary `/etc/hosts` mapping was tested successfully; FFprobe then returned codec metadata from the HTTPS URL, and browser transcoding/playback with sound worked. The permanent Compose mapping was prepared but was not independently confirmed after recreation.

## Safe verification

```bash
# Host-side: verifies correct TLS hostname routing (diagnostic -k only)
curl -k -I --resolve stremio.home.test:443:192.168.1.10 https://stremio.home.test/

# Container DNS mapping
docker exec stremio getent hosts stremio.home.test

# FFprobe to the SAME external-facing hostname used by Stremio Web
docker exec stremio ffprobe -v error \
  -show_entries stream=codec_name,codec_type -of json \
  "https://stremio.home.test/<torrent-hash>/<file-index>"

# Check for probe errors during playback
docker logs --since 5m stremio 2>&1 | grep -Ei 'hlsv2|probe|ffmpeg|error'
```

Use only content you are permitted to access. Keep certificates valid and trusted; do not disable TLS validation permanently. `/hlsv2/status` returning HTTP 200 does not prove a transcode is active. Confirm playback, probe success, and runtime FFmpeg/output codecs if you need to determine exactly what changed.

## Prevent recurrence

Keep DNS and the static IP mapping current, preserve Docker volumes and Guest browser storage, and monitor transcoding CPU/RAM. An FFprobe exit code alone hides the important stderr DNS detail; capturing it first can avoid unnecessary proxy and codec changes.
