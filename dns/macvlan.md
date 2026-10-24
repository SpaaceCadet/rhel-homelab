# Docker macvlan network for Pi-hole

## Why macvlan?

The inspected homelab configured an **external Docker macvlan** so Pi-hole had a separate LAN address. No `ports:` were published on the host. Docker Compose references the existing network; it does **not** create it.

## Prerequisites

- A wired Linux host and LAN infrastructure permitting multiple source MAC addresses on one port.
- A free LAN address reserved outside DHCP dynamic allocation or reserved appropriately.
- An identified physical parent interface and correct subnet/gateway.
- Administrative access to the host outside of the DNS service itself.

**The original parent NIC was not confirmed** in the source snapshot. Always inspect your actual system instead of guessing the interface.

## Example creation

These values are **examples only**; do not execute before checking your network:

```bash
ip -br link
ip -4 route
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=enp1s0 \
  pihole_macvlan
docker network inspect pihole_macvlan
```

Use your actual physical parent NIC instead of `enp1s0`. Verify that `192.168.1.53` is free before starting Compose. Never create a duplicate IP on the existing live LAN.

## Typical macvlan limitation

By design, a macvlan container may not be able to communicate directly with the Docker host through its parent interface. Therefore `dig @192.168.1.53` *from the host* can fail even while queries **from another LAN client work**. Test from a different PC or a correctly designed macvlan shim if host access is required; do not assume you need to open DNS to the Internet.

## Verify the network

```bash
docker network inspect pihole_macvlan
docker compose config --quiet
docker compose up -d
docker compose ps
docker inspect pihole --format '{{json .NetworkSettings.Networks}}'
```

Host-to-container DNS ping/HTTP failure alone is not proof of outage. From another LAN device:

```bash
nslookup example.com 192.168.1.53
```

## Migration

Back up the Pi-hole config and local DNS/dnsmasq files. On a **separate staging address**, inspect the original external network's driver, subnet, gateway and parent options. Recreate the macvlan before restoring Compose. Avoid two machines or containers claiming the same production LAN IP; cut over deliberately, with rollback plans and a temporary independent DNS resolver.
