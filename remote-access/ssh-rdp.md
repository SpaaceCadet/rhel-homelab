# Remote Windows Desktop over SSH local port forwarding

## Goal

Access Windows RDP from an external computer **without opening TCP/3389 on the home router**. The remote computer connects only to an SSH server on the home Linux host. SSH forwards local port `13389` to the Windows LAN address on port `3389`.

## Prerequisites

- Windows RDP hosting enabled and restricted by its local firewall; Windows edition supports hosting RDP.
- The Linux server can reach Windows over the LAN.
- You can SSH securely to Linux from the remote computer.
- Windows is awake; use [Wake-on-LAN](wake-on-lan.md) first if needed.

Illustrative endpoints:
- Linux SSH server: `ssh.example.net`
- Windows LAN IP: `192.168.1.100`
- Local desktop port: `127.0.0.1:13389`

## 1. Validate from Linux

```bash
nc -vz 192.168.1.100 3389
```

A TCP handshake shows reachability to the port, not successful Windows authentication. Keep the Windows firewall restricted to the necessary LAN sources.

## 2. Open tunnel on the **remote computer**

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:13389:192.168.1.100:3389 \
  linux_user@ssh.example.net
```

Include `-p YOUR_PORT` if SSH is listening on a non-default port. Keep the session open. `-N` means it does not request a remote shell. `ExitOnForwardFailure` checks setting up the local listener, not whether Windows RDP accepts connections.

## 3. Connect to Windows

On the *same remote computer* where SSH is running, launch Microsoft Remote Desktop (`mstsc` on Windows) and connect to:

```text
127.0.0.1:13389
```

Authenticate with the Windows account credentials; Windows PIN login is not equivalent to the RDP account password. SSH and RDP require distinct authentication steps.

## 4. End-to-end workflow

```text
Remote laptop → SSH into Linux → execute wake-on-lan script
Remote laptop → SSH local tunnel 127.0.0.1:13389
Linux host → Windows PC LAN IP:3389
Remote Desktop app → 127.0.0.1:13389
```

No port-forward rule for `13389` or `3389` is necessary on the router. Bind the local SSH listener to `127.0.0.1`, not to all interfaces.

## Security notes

- Verify SSH host keys, restrict SSH access and prefer keys.
- Do not expose RDP/3389 publicly; prefer RDP Network Level Authentication and patched Windows systems.
- `AllowTcpForwarding` must be permitted for the authorized SSH user; optionally restrict destinations through `PermitOpen` / `permitopen` if appropriate. Changes to sshd need a separate working session for rollback.
- Consider shutting down the RDP tunnel promptly when done; press Ctrl+C in its SSH terminal.

## Troubleshooting

| Symptom | Likely next check |
| --- | --- |
| `Address already in use` | Select another unused local port e.g. `13390` |
| `administratively prohibited` | SSH forwarding policy or destination restriction |
| `Connection refused` | RDP service running and listening on Windows |
| Tunnel connects but desktop times out | Linux→Windows address/firewall/routing |
| Windows rejects login | Windows credentials, account permissions, NLA |
| Wake succeeds but tunnel fails | Test TCP/3389 from Linux host |

> Evidence boundary: the original Obsidian RDP note contained an untested tunnel example, while prior lab conversations recorded successful WoL followed by SSH-forwarded RDP. Exact past SSH local port choices varied. This guide presents a reproducible, sanitized pattern rather than claiming a fresh end-to-end test.
