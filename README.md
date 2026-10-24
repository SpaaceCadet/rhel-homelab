# RHEL Homelab

Self-hosted infrastructure on Red Hat Enterprise Linux — Docker, Nginx, DNS, monitoring, security, and troubleshooting runbooks.

This repository documents reproducible deployment patterns and real troubleshooting exercises from a personal homelab. Published configuration uses **sanitized example IPs and hostnames**; secrets, certificates and persistent application data are excluded.

## Documented projects

| Project | Focus |
| --- | --- |
| [Stremio Docker](stremio/README.md) | Reverse proxy, container networking, HLSv2 probing, FFprobe/FFmpeg, and E-AC3 audio troubleshooting |

### Stremio incident: browser video played without audio

The media played in VLC, but Stremio Web in Brave had no sound. HLSv2 media probing returned HTTP 500 because the container could not resolve the hostname in its advertised HTTPS stream URL. A container-side hostname mapping to the host HTTPS reverse proxy restored media probing and working browser playback.

Read the [incident report](stremio/troubleshooting.md) and [deployment Compose example](stremio/compose.yaml).

## Planned topics

Nextcloud, monitoring (Prometheus/Grafana), network services, SSH/Wake-on-LAN, and host security. These are not documented here yet.

## Security note

Do not copy example settings without adapting DNS, TLS, port exposure and access control to your environment. Never commit passwords, tokens, private keys or application data.
