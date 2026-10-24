# SELinux enforcing with RHEL and Docker

## Baseline

The source RHEL 10.1 homelab ran **SELinux enforcing**, targeted policy. Some SELinux boolean and port overrides were present; the goal is to inspect and apply **only what a fresh deployment actually requires**, rather than copying every override.

```bash
getenforce
sestatus
sudo semanage boolean -l -C
sudo semanage port -l -C
sudo semodule -lfull
sudo ausearch -m AVC -ts recent
```

## Nginx as reverse proxy

Host-level Nginx may need permission for outbound upstream connections when SELinux is enforcing:

```bash
getsebool httpd_can_network_connect
# Only if justified after observing an AVC/blocked upstream:
sudo setsebool -P httpd_can_network_connect on
```

A locally customized `http_port_t` mapping existed in the source. Do not copy its exact port blindly: inspect `semanage port -l`, and add only the needed listening port type on the new host if policy denies binding.

## Persistent container storage

In Compose, `:Z` relabels a bind mount for private use by a specific container; `:z` is shared labeling when multiple containers legitimately need access. Use the appropriate option for the data model, and avoid blindly relabeling broad host paths:

```yaml
services:
  app:
    image: example/image:tag
    volumes:
      - ./app-data:/var/lib/example:Z
```

Check file contexts carefully:

```bash
ls -Zd /srv/example /srv/example/app-data
sudo ausearch -m AVC -ts recent
sudo restorecon -Rv /srv/example/app-data
```

**Caution:** `restorecon` uses default or custom persistent file-context rules and can undo a Docker volume's runtime `:Z` label when applied inappropriately. Do not run it as a universal fix. Check `semanage fcontext -l -C` and effective labels first.

## Migration / recovery

1. Capture `/etc/selinux/config`, local booleans, custom port contexts and modules.
2. Inspect actual labels on storage volumes **before** backups and after restoration; preserve/restore labels deliberately.
3. Reapply only justified customizations on the target using documented commands.
4. Troubleshoot AVC messages in enforcing mode; do not use `setenforce 0` as a routine deployment workaround.
5. Confirm Nginx upstream connectivity and every Docker persistent volume access after reboot.

## Common pitfall

An unlabeled mount point or directory can cause confusing access denials even if nested directories display `container_file_t`. Investigate the whole path and mount options rather than broadly disabling SELinux.
