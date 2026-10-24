# Pi-hole DNS operations, local records and recovery

## Query path

A client configured to use Pi-hole sends DNS queries to its LAN IP. Pi-hole may answer from local/custom records or blocklists, or forward to configured upstream resolvers. **Client DNS assignment (DHCP/router or manual) must be verified**, not inferred from the server's `/etc/resolv.conf`.

## Client configuration

1. Reserve Pi-hole's IP or use an appropriate static address outside DHCP allocation.
2. In your router's DHCP settings, advertise Pi-hole's LAN IP as DNS **if the router supports this**. Some routers enforce themselves as DNS or relay queries; validate client behavior.
3. On Windows: `ipconfig /all` then `nslookup example.com 192.168.1.53`. On Linux: `resolvectl status` (if available) and `dig @192.168.1.53 example.com`.
4. If using Android Private DNS (DNS-over-TLS), a configured external hostname can bypass a LAN Pi-hole; browser secure DNS/DoH can do likewise.
5. Create a test **local A record** (for example `app.home.arpa` → `192.168.1.20`) in Pi-hole's local DNS records. `home.arpa` is reserved for home-network naming. Verify via a direct query to Pi-hole, then with normal client resolution.

Example:

```bash
nslookup app.home.arpa 192.168.1.53
nslookup example.com 192.168.1.53
```

If the explicit Pi-hole query works but normal lookup does not, inspect actual DNS servers offered to the client, IPv6 DNS, browser DoH and cache. Avoid assigning an unreachable Pi-hole IP to every device without fallback or recovery access.

## Health and troubleshooting

```bash
docker compose ps
docker compose logs --tail 100 pihole
docker exec pihole pihole status
docker network inspect pihole_macvlan
```

| Symptom | Likely check |
| --- | --- |
| LAN clients cannot resolve | Pi-hole health, IP conflict, router DHCP, port 53 filtering, macvlan parent |
| Works with explicit `nslookup`, not normally | Client DNS configuration, IPv6 resolver, DoH, cache |
| Host cannot query Pi-hole | macvlan host/parent isolation |
| Some sites blocked unexpectedly | Query log / allowlist / upstream status |
| Pi-hole web admin inaccessible | Correct LAN IP and port, HTTP(S), web service, browser routing |
| Custom hostname missing | Local DNS record, DNS suffix, actual resolver in use |

The inspected source showed `FTLCONF_dns_listeningMode=all`; ensure the resolver is **LAN-limited** with firewalls and router policies. Do not allow open public DNS recursion.

## Backup/recovery

Preserve persistent `/etc/pihole` data, local DNS records and any active dnsmasq configurations, plus the Compose file and **securely held** administration credentials. On RHEL check file labels, ownership and mount behavior before restoring. Pi-hole image versions may migrate configuration formats; validate compatibility before moving versions. Keep a fallback DNS path while rebuilding Pi-hole.

## Verification boundaries

The October 2026 source audit verified a healthy Pi-hole container and its macvlan config, but **did not prove** that all LAN clients were actually receiving its IP from DHCP. It also did not capture the exact macvlan parent interface or a complete export of user DNS records, so none of those values are claimed as facts in this public runbook.
