# Incident: HLSv2 probe HTTP 500 and silent E-AC3 playback

**Environment:** RHEL 10.1, Docker Compose, `tsaridas/stremio-docker`, Stremio Server 4.20.16, FFmpeg 4.4.1-Jellyfin, host Nginx TLS reverse proxy, Brave browser.

## Failure

- Direct media streaming returned `206 Partial Content`; `stats.json` returned `200`.
- VLC successfully played the same stream with audio.
- The stream had `hevc` video and `eac3` audio (plus ASS subtitle tracks).
- Brave reported `false` for `MediaSource.isTypeSupported('audio/mp4; codecs="ec-3"')`.
- The Stremio endpoint `/hlsv2/probe?mediaURL=https%3A%2F%2Fstremio.home.test%2F...` returned HTTP 500.
- Server logs stated: `Error: Probe process exited with code: 1`.

Running `ffprobe` inside Docker against the HTTPS URL initially failed with `Failed to resolve hostname ...: Name does not resolve`.

The following *internal* test worked:

```bash
docker exec stremio ffprobe -v error -show_entries stream=codec_name,codec_type -of json \
  'http://127.0.0.1:8080/<hash>/<index>'
```

This proved that the input stream and probing binary worked when reached via internal Nginx.

## Root cause and correction

The browser-resolvable private hostname was unavailable to the container's resolver. The media URL passed to FFprobe used that hostname, so probing failed even though direct streaming from the browser succeeded.

A temporary mapping inside the container showed the fix:

```bash
# Diagnostic only. Does not persist across container recreation.
docker exec -u 0 stremio sh -c 'echo "192.168.1.10 stremio.home.test" >> /etc/hosts'
```

After adding a suitable entry pointing to the **host HTTPS proxy**, FFprobe successfully inspected the original HTTPS media URL and the user confirmed audio/transcoding playback worked. For persistence, use `extra_hosts` in Compose as shown in the README and recreate only the service after checking persistent volumes.

## Important limitations

- The precise conversion profile and codec of the *transcoded output* were not recorded. Successful playback does not prove that each video is copied or that each audio stream is always converted to AAC.
- The permanent Compose change needs a post-recreation verification in the deployment where the incident occurred.
- This workaround is appropriate for an environment using a static host LAN IP; if it changes, update the mapping or provide resolvable internal DNS.
- Never disable TLS certificate validation as a general workaround.
- Container `127.0.0.1` is not the Docker host. In the example, internal Nginx listens on HTTP port 8080 and not HTTPS port 443.

## Useful checks

```bash
docker logs --since 10m stremio 2>&1 | grep -Ei 'hlsv2|probe|ffmpeg|error'
docker exec stremio getent hosts stremio.home.test
docker top stremio -eo pid,comm,args
docker exec stremio cat /etc/nginx/http.d/default.conf
```
