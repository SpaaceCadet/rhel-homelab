# Collabora CODE behind Nginx — documented integration

## Verification boundary

An Obsidian snapshot of the host's Nginx configuration (October 2026) contained Collabora CODE path rewrites to a **host-loopback upstream on port 9980**, including the WebSocket route for document editing. The contemporaneous port snapshot did **not** establish a running listener on that port, and no verified Collabora Compose definition was available. **Do not present this as a fully confirmed Collabora deployment.**

## Observed route mapping (sanitized)

| Reverse-proxy path | Internal destination (example) |
|---|---|
| `/collabora/hosting/discovery` | `/hosting/discovery` |
| `/collabora/hosting/capabilities` | `/hosting/capabilities` |
| `/collabora/cool/*/ws` | `/cool/*/ws` (WebSocket) |
| `/collabora/cool` | `/cool` |
| `/collabora/browser` | `/browser` |
| `/collabora/loleaflet` | `/loleaflet` (legacy path) |

The original host served these under a client-certificate-protected HTTPS vhost. Route behavior depends on Nginx location selection and rewriting; validate the final upstream request path, Host header, WebSocket upgrade and Collabora's own configuration rather than assuming these patterns work for every version.

## Representative Nginx excerpt (not standalone config)

```nginx
# Inside an appropriately configured HTTPS server block:
location ^~ /collabora/hosting/discovery {
    proxy_pass http://127.0.0.1:9980/hosting/discovery;
    proxy_set_header Host $http_host;
}

location ~ ^/collabora/cool/(.*)/ws$ {
    proxy_pass http://127.0.0.1:9980/cool/$1/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $http_host;
    proxy_read_timeout 3600s;
}
```

This is a partial mapping, **not a complete vhost or deployment recipe**. Add and verify the rest of the routes for the chosen CODE release and your actual Nextcloud integration. If browser and server use different subdomains or mTLS, ensure every required request and WebSocket handshake meets access control.

## Validate before claiming operational status

```bash
sudo ss -lntp | grep ':9980'
curl -i --max-time 5 http://127.0.0.1:9980/hosting/discovery
sudo nginx -t
sudo journalctl -u nginx -n 100 --no-pager
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
```

Check Nextcloud Office's configured document server URL and perform a real document-editing test, including WebSocket traffic in browser devtools. A successful `nginx -t` checks syntax, not backend health.

## Security and reliability

Do not expose CODE's admin/API endpoints indiscriminately; restrict the reverse proxy and permitted document hosts as appropriate. Keep TLS trusted and client-certificate controls consistent. Pin a supported CODE image, persist only required application data, and monitor CPU/memory consumption during document editing.
