# Linux Lightspeed MCP — RHEL, Docker and restricted SSH

## Verified reference architecture

The October 2026 lab ran `linux-mcp-server 0.1.0a` in Docker on RHEL 10.1. The image was built from [rhel-lightspeed/linux-mcp-server](https://github.com/rhel-lightspeed/linux-mcp-server), using `BUILD_FROM_SOURCE=0` to work around a Rust/uv build-tool mismatch. The backend used streamable HTTP at host loopback `127.0.0.1:8000/mcp`. A distinct systemd tunnel service connected outbound to the managed control plane. No public inbound MCP port or public Nginx vhost was needed.

```text
ChatGPT → managed MCP tunnel ← outbound systemd tunnel on RHEL
                                         ↓
                             127.0.0.1:8000/mcp
                                         ↓
                            Docker Linux MCP service
                                         ↓ policy + SSH public-key auth
                            Restricted host SSH account
                                         ↓
                       CPU, RAM, disks, services and logs
```

## Build (reference pattern)

```bash
git clone https://github.com/rhel-lightspeed/linux-mcp-server.git
cd linux-mcp-server
git rev-parse HEAD
docker build --build-arg BUILD_FROM_SOURCE=0 \
  -t lightspeed-mcp:local -f Containerfile .
```

Record the upstream commit and image digest for reproducibility. Revalidate image arguments against the checked-out upstream version; the historic build used a release-specific CLI.

## Separation of privilege

- Run the container as non-root (historically UID/GID 1001).
- Use a **dedicated host SSH identity** with no sudo and no Docker-group membership.
- Mount only its SSH private key, trusted `known_hosts` and approved application policy read-only.
- Restrict which Linux targets and MCP tools are accessible.
- Pin SSH host keys using trusted host metadata, not unverified first-contact acceptance.
- A read-only diagnostic tool can still reveal confidential host data. End-user identity verification and policy enforcement remain necessary.

Check the real Docker bridge gateway in each installation; the container's `127.0.0.1` is **not** the RHEL host.

```bash
docker network inspect bridge \
  --format '{{(index .IPAM.Config 0).Gateway}}'
sudo systemctl status sshd --no-pager
docker logs --tail 100 lightspeed-mcp
```

## Historical container command (adapt before use)

The recorded image had no ENTRYPOINT and required the `linux-mcp-server` executable explicitly:

```bash
docker run -d --name lightspeed-mcp --restart unless-stopped \
  --user 1001:1001 \
  -p 127.0.0.1:8000:8000 \
  --mount type=bind,src=/srv/mcp/ssh,dst=/run/mcp-ssh,readonly \
  --mount type=bind,src=/srv/mcp/config,dst=/run/mcp-config,readonly \
  lightspeed-mcp:local linux-mcp-server \
  --transport streamable_http --host 0.0.0.0 --port 8000 \
  --path /mcp --toolset FIXED --host-mode REMOTE_ONLY \
  --user mcp-reader \
  --ssh-key-path /run/mcp-ssh/id_ed25519 \
  --known-hosts-path /run/mcp-ssh/known_hosts \
  --verify-host-keys --no-search-for-ssh-key \
  --policy-path /run/mcp-config/policy.yaml
```

This is **not standalone copy-paste deployment**: create least-privilege SSH identity/keys, known_hosts and an authenticated tool policy first; review the host-side SSH allow rules. Do not use an unrestricted `all_users: true` policy as a substitute for OAuth or connector-level access control.

## Protocol and health validation

A plain GET against `/mcp` may return HTTP 406 because the endpoint expects MCP headers and JSON-RPC requests. A sample initiation request:

```bash
curl -i -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"diagnostic-client","version":"1.0"}}}'
```

The actual client may need session negotiation and subsequent initialized notifications. Check tunnel service status separately:

```bash
sudo systemctl status lightspeed-tunnel.service --no-pager
sudo journalctl -u lightspeed-tunnel.service -n 100 --no-pager
ss -lntp | grep -E ':(8000|19090)[[:space:]]'
```

Tunnel credentials belong in a root-owned environment file with `0600` permissions, never in Git. The historic tunnel client version was 0.0.16; compatibility and onboarding may change. Successful local MCP initialization does not prove tunnel authentication, authorized tool calls or reboot persistence.

## Troubleshooting

| Symptom | Investigation |
|---|---|
| MCP HTTP 406 | Use proper Accept, JSON-RPC and session headers |
| Tool authorization denied | Check host/tool policy **and** identity claims |
| SSH login refused | Inspect AllowUsers, authorized_keys, host key, network and journald |
| MCP responds but tool fails | Confirm gateway address, restricted account capabilities and selected toolset |
| Tunnel disconnected | Check network, systemd unit and protected environment configuration |
| Breaks after host poweroff | Inspect Docker restart policy, systemd startup dependencies and external tunnel reconnection |

Do not grant broad sudo access or relax sshd globally merely to silence MCP errors.
