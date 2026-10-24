# Wake-on-LAN / Wake-on-WAN via Linux SSH

## Overview

The always-on Linux server sends an Ethernet magic packet within the LAN. From outside the house, use **SSH to Linux** to trigger it. No Internet-facing UDP 9 forwarding is required.

Example parameters (replace with your own, do not commit real ones):

| Setting | Example |
| --- | --- |
| Windows Ethernet MAC | `AA:BB:CC:DD:EE:FF` |
| Windows LAN IP | `192.168.1.100` |
| Network | `192.168.1.0/24` |
| Broadcast | `192.168.1.255` |
| SSH host | `ssh.example.net` (placeholder) |

## 1. Enable firmware/NIC WoL

In BIOS/UEFI look for `Wake on LAN`, `Power on by PCI-E` or equivalent. If ErP/Deep Sleep removes power from Ethernet during shutdown, review those settings carefully. Availability depends on hardware/firmware.

On Windows 11 open Device Manager → Ethernet adapter → Properties:
- Advanced: enable Wake on Magic Packet (and Shutdown Wake-On-Lan if supported).
- Power Management: allow wake and, if available, limit wake to magic packets.

Check from an elevated PowerShell:

```powershell
powercfg /a
powercfg /devicequery wake_programmable
powercfg /devicequery wake_armed
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, MacAddress
Get-NetAdapterAdvancedProperty | Where-Object { $_.DisplayName -match 'Wake|Magic|WOL|Shutdown' }
```

If wake from sleep works but full shutdown does not, inspect Windows Fast Startup and whether S5 wake is supported; disabling Fast Startup can help on some systems but cannot create missing hardware support.

## 2. On the Linux server

Install an available WoL client from your configured distribution repositories (RHEL packages vary):

```bash
sudo dnf search wakeonlan
# If available from a trusted repository:
sudo dnf install wakeonlan
command -v wakeonlan
```

Check correct subnet/broadcast with `ip -4 addr` and `ip -4 route`. For a `192.168.1.0/24` LAN, broadcast is usually `192.168.1.255`:

```bash
wakeonlan -i 192.168.1.255 -p 9 AA:BB:CC:DD:EE:FF
```

`Packet sent` means a packet was transmitted, **not** that the Windows machine booted.

## 3. Reusable script

Example `~/bin/wake-windows`:

```bash
#!/usr/bin/env bash
set -euo pipefail
MAC='AA:BB:CC:DD:EE:FF'
BROADCAST='192.168.1.255'
exec /usr/bin/wakeonlan -i "$BROADCAST" -p 9 "$MAC"
```

```bash
mkdir -p ~/bin
chmod 700 ~/bin
chmod 700 ~/bin/wake-windows
~/bin/wake-windows
```

Replace the executable path if `command -v wakeonlan` differs. The command should run without sudo if your chosen client supports unprivileged UDP broadcast.

## 4. Trigger wake from outside the LAN

Use an authorized SSH connection to the Linux server:

```bash
ssh -p 22 linux_user@ssh.example.net '~/bin/wake-windows'
```

Use the actual public hostname and SSH port; `ssh.example.net` is just an example.

Verify from a different network such as a mobile hotspot. If troubleshooting packet transmission, capture on the Linux server (requires sudo):

```bash
sudo tcpdump -ni any 'udp port 9'
```

A packet capture proves the Linux host emitted a packet, not that the Windows NIC received it. Ping can be blocked by the Windows firewall and is not conclusive. Verify wake by actual Windows activity or successful RDP/TCP connectivity.

## Troubleshooting

| Symptom | Investigate |
| --- | --- |
| Cannot SSH from outside | DDNS, router SSH mapping, firewalld, key, reachability |
| SSH works but no wake | MAC, broadcast, NIC driver, firmware, Ethernet power |
| Wakes from sleep only | S5 support, ErP, Fast Startup |
| Works locally but not remotely | SSH command execution, permissions, different subnets/VLANs |
| Wake packet seen but PC remains off | NIC standby power, firmware settings, wrong network segment |

## Security

Do not expose UDP/9 to WAN. Keep host SSH patched, authenticated, rate-limited and limited to permitted identities. A dedicated SSH key with a forced wake command can further reduce risk, but must not be confused with an account used for RDP forwarding.
