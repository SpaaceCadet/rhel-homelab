# Stremio Docker on RHEL: Reverse Proxy and Transcoding Troubleshooting

A reproducible homelab deployment guide and incident report for `tsaridas/stremio-docker` on RHEL, behind a hostname-based HTTPS reverse proxy.

## Symptoms and resolution

A stream with HEVC video and E-AC3 audio played silently in a Chromium-based browser but correctly in VLC. The browser requested `/hlsv2/probe`, which returned HTTP 500. Running FFprobe from inside the container showed that the hostname used by the browser was **not resolvable inside Docker**. The internal HTTP stream was accessible.

Providing an internal hostname mapping to the host's existing HTTPS reverse proxy allowed FFprobe to inspect the media, after which playback/transcoding worked.

See [the incident runbook](docs/transcoding-dns-incident.md).

## Example Docker Compose

```yaml
services:
  stremio:
    image: tsaridas/stremio-docker:latest
    container_name: stremio
    restart: unless-stopped
    environment:
      NO_CORS: "1"
      AUTO_SERVER_URL: "1"
      CASTING_DISABLED: "1"
    ports:
      - "127.0.0.1:8083:8080"
    volumes:
      - ./data:/root/.stremio-server:Z
    extra_hosts:
      - "stremio.home.test:192.168.1.10" # Replace with your hostname and proxy LAN IP
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

The host reverse proxy should route HTTPS for `stremio.home.test` to `http://127.0.0.1:8083`. The host's certificate must be valid for that name. Docker's `extra_hosts` mapping must point to an address reachable **from within the container** on TCP 443. Don't map to container `127.0.0.1` unless HTTPS actually listens there.

## Quick validation

```bash
docker compose config
docker compose up -d
curl -I http://127.0.0.1:8083/
docker exec stremio getent hosts stremio.home.test
docker exec stremio ffprobe -v error -show_entries stream=codec_name,codec_type -of json \
  'https://stremio.home.test/<hash>/<index>'
```

Replace sample names, IPs, and media path. Preserve browser Guest local storage and your persistent bind mount. Avoid publishing media hashes, account tokens, private certificates, or volumes.

## References

- [tsaridas/stremio-docker](https://github.com/tsaridas/stremio-docker)
