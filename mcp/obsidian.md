# Obsidian MCP — Docker, TypeScript and vault permissions

## Verified design

The source environment contained a custom `obsidian-mcp` Node.js/TypeScript application in Docker. The inspected application used a two-stage Node 20 Alpine Dockerfile, `npm ci`, a compiled `dist/index.js`, a non-root process with UID/GID 1001, and a health endpoint on container port 3000.

The verified Compose project mounted the Markdown vault into `/vault`, with shared SELinux relabeling (`:z`) and restart policy `unless-stopped`. A distinct Obsidian GUI container mounted the **parent** host directory with `:Z`, potentially causing competing SELinux labels. The MCP service provided reading, searching and writing notes; successful write operations were observed.

## Example Compose (hardening proposal)

This example is **not** a copy of the production file. It intentionally binds the MCP service to host loopback rather than all host interfaces:

```yaml
services:
  obsidian-mcp:
    build: .
    container_name: obsidian-mcp
    restart: unless-stopped
    ports:
      - "127.0.0.1:9111:3000"
    environment:
      MCP_TRANSPORT: http
      MCP_HTTP_PORT: "3000"
      OBSIDIAN_VAULT_PATH: /vault
    volumes:
      - "${OBSIDIAN_VAULT_HOST_PATH:?set in .env}:/vault:rw,z"
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

The application source, Dockerfile, lockfile and TypeScript config are needed for a real image build; this guide does not distribute private source or vault data. Keep `OBSIDIAN_VAULT_HOST_PATH` in a non-committed `.env`, for example `/srv/obsidian/homelab-vault`. Review supported Node versions and dependencies before rebuilding.

## Permissions incident: EACCES

The MCP application initially failed to create notes, with errors such as:

```text
EACCES: permission denied, open '/vault/RHCSA/example.md'
```

The mount was writable from Docker's point of view, but the directory had owner UID 1000, mode 755, and the MCP process ran as UID 1001. Unix filesystem permissions prevented writes. The notes show a successful application-level write after troubleshooting; **the precise host remediation command was not independently confirmed**.

Investigate with:

```bash
docker exec obsidian-mcp id
docker inspect obsidian-mcp --format '{{json .Mounts}}'
docker exec obsidian-mcp ls -ld /vault
ls -ldnZ /srv/obsidian/homelab-vault
getenforce
sudo ausearch -m AVC -ts recent
```

A targeted POSIX ACL for the MCP UID may be appropriate, after reviewing ownership and backups:

```bash
# Example only; adjust path and identity
sudo setfacl -R -m u:1001:rwX /srv/obsidian/homelab-vault
sudo find /srv/obsidian/homelab-vault -type d \
  -exec setfacl -m d:u:1001:rwX {} +
```

An ACL does **not** override SELinux. Beware relabel conflicts when one container mounts a parent directory with `:Z` and another mounts a child with `:z`. Do not use `chmod -R 777`, disable SELinux, or publish an unauthenticated write-capable MCP endpoint.

## Operational checks

```bash
docker compose config --quiet
docker compose ps
docker logs --tail 100 obsidian-mcp
curl -i http://127.0.0.1:9111/health
docker inspect obsidian-mcp --format '{{json .Mounts}}'
```

Use a disposable test note and safe test folder when verifying writes. A successful health endpoint does not prove correct vault access. Protect the complete vault with a tested backup and avoid committing its notes wholesale to a public project.
