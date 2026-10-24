# Fail2ban SSH protection on RHEL

## Reference setup

An October 2026 read-only homelab inspection found Fail2ban 1.1.0 active/enabled, with one `sshd` jail, a `systemd` journal backend and a `firewallcmd-rich-rules` action.

The following is a sanitized version of its `/etc/fail2ban/jail.local`, with no banned IPs or host identifiers:

```ini
[DEFAULT]
ignoreip = 127.0.0.1

[sshd]
enabled = true
port = ssh
backend = systemd
bantime = 1h
findtime = 10m
maxretry = 3
bantime.increment = true
bantime.factor = 4
bantime.max = 1w
```

A matching `firewallcmd-rich-rules` action was observed on the host. Check the **effective** action on your system; do not assume the same bundled action names or defaults for all Fail2ban versions.

## Deploy and validate

Install from an appropriate trusted package source for your RHEL version. Keep a console or second SSH connection while changing authentication protections.

```bash
sudo fail2ban-client -V
sudo systemctl enable --now fail2ban
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo fail2ban-client get sshd actions
sudo journalctl -u fail2ban -n 100 --no-pager
```

If creating `jail.local`, write it with root-only administrative control, then run `sudo fail2ban-client -t` (if available on the installed version) before restarting.

## Meaning of parameters

- `findtime = 10m`: sliding detection window.
- `maxretry = 3`: number of qualifying failures triggering a ban.
- `bantime = 1h`: baseline ban duration.
- `bantime.increment`, `factor`, `max`: increment the ban duration for repeated offenders, capped at one week.
- `backend = systemd`: match SSH logs in journald; actual journal match expressions may vary.

## Validation and recovery

1. Confirm valid SSH key-based logins work.
2. In a **controlled test only**, exercise failures from a disposable test client—**not** the primary administrator's IP.
3. Inspect `sudo fail2ban-client status sshd` and the relevant firewalld rich rules.
4. Confirm legitimate access remains available and ban expiry/unban behavior works.
5. Back up reviewed override files in `/etc/fail2ban` securely. Do not migrate transient banned-IP lists as permanent blocklists by default.

```bash
sudo fail2ban-client status sshd
sudo fail2ban-client get sshd banip
sudo firewall-cmd --zone=public --list-rich-rules
sudo grep -R -n 'ip.blocklist' /etc/fail2ban /etc/firewalld 2>/dev/null
```

The original audit included a separate local blocklist file; it was **not established whether any active jail consumed it**. Avoid claiming custom lists are enforced without checking filters and actions.
