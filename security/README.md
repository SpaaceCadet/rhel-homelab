# RHEL security baseline — homelab runbooks

These guides are adapted from a private Obsidian RHEL 10.1 homelab audit (October 2026). **All examples are sanitized.** This is not a dump of effective firewall rules, identities, or private server configuration.

## Guides
- [Firewalld, Docker and nftables](firewalld.md)
- [Fail2ban and SSH](fail2ban.md)
- [SELinux in enforcing mode](selinux.md)
- [Nginx, Certbot and optional mTLS](../nginx/README.md)

## Baseline principles

1. Restrict host access according to **actual client and application requirements**. A zone with a service listed is not proof that a service is exposed on the Internet; router NAT, listeners, source rules and Docker chains also matter.
2. Keep **SELinux enforcing** and troubleshoot AVC denials rather than turning SELinux off.
3. Use SSH keys, restrict administrative access, and keep a console or second SSH session during rule changes to avoid lockouts.
4. Let **Docker** generate its dynamic NAT/filtering chains; do not copy a snapshot of `nft list ruleset` as if it were declarative persistent config.
5. Do not copy regional allow-list rules, banned IP snapshots, credentials, internal network topology, mTLS private keys, or certificate recovery archives into a public repository.
6. Review and validate on a staging system before rollout. None of these examples were automatically deployed to a running server.

## Audit checklist

```bash
hostnamectl
sudo systemctl status firewalld fail2ban sshd --no-pager
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --list-all
sudo firewall-cmd --list-all-policies
sudo nft list ruleset
getenforce
sudo semanage boolean -l -C
sudo semanage port -l -C
sudo ausearch -m AVC -ts recent
sudo fail2ban-client status sshd
```

Review output locally. Network addresses and security state should be redacted before sharing.
