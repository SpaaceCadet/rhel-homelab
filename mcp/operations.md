# MCP operations, availability, security and recovery

## Distinct components

The Linux and Obsidian MCP services are separate applications and may each have a separate persistent tunnel process. An active Docker container alone does not prove that the service is usable from ChatGPT. Validate backend health, tunnel connectivity, access policy, and a real authorized tool operation.

| Service | Primary purpose | Authority |
|---|---|---|
| Linux MCP | Inspect Linux system state over restricted SSH | Read-only OS tools, but output may be sensitive |
| Obsidian MCP | Read/search/write Markdown vault | Changes files inside an approved vault |

## Routine diagnostics

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker logs --tail 100 lightspeed-mcp
docker logs --tail 100 obsidian-mcp
sudo systemctl status lightspeed-tunnel.service --no-pager
sudo systemctl status obsidian-tunnel.service --no-pager
sudo journalctl -u lightspeed-tunnel.service -n 60 --no-pager
sudo journalctl -u obsidian-tunnel.service -n 60 --no-pager
ss -lntp
```

Unit names and health URLs are examples derived from one installation; check target system units before concluding the services exist. Avoid dumping full Docker inspect environment objects in tickets because they may contain credentials.

## Hardening checklist

- [ ] No unauthenticated public MCP listener; prefer loopback and authenticated managed access
- [ ] End-user auth is separate from tunnel/client auth; evaluate least-privilege, per-tool authorization
- [ ] Tunnel API keys and IDs stored in protected systemd environment files, not source control
- [ ] No Docker socket mount and no unnecessary host sudo/group privileges for Linux MCP
- [ ] SSH host key verified, restricted identity and destination policy reviewed
- [ ] Writable Obsidian vault access intentionally scoped; use separate test vault where practical
- [ ] SELinux enforcing, with reviewed container labels and POSIX ACLs
- [ ] Docker restart and systemd dependencies validated by an actual reboot drill
- [ ] Audit logs retained without publishing private file paths or content

## Recovery

1. Securely back up Obsidian vault content, application source and lockfiles, Compose, and any custom tool policy.
2. Back up credentials and SSH private keys **separately and encrypted** in an authorized secret store.
3. Rebuild containers with pinned source/image revisions and restored ownership/SELinux labels.
4. Restore the appropriate SSH trust policy, end-user authorization policy and tunnel configuration; do not clone expired or broadly shared secrets.
5. Verify local backend health, tunnel startup, read-only Linux query and Obsidian read/write in a disposable path.
6. Test restart/reboot resilience, record failure modes, and maintain a rollback plan.

## Lessons learned

- A Docker `rw` mount does not override filesystem permissions.
- Docker loopback is not the physical host; determine the actual gateway and SSH reachability.
- HTTP MCP protocol errors may reflect missing Accept/session headers rather than a crashed service.
- OAuth/tunnel credentials and MCP tool authorization are different layers.
- A working one-off test is not evidence of validated unattended restart after a power failure.
