# Data disk migration and Nextcloud recovery — 2026-10-31

## Outcome and evidence

A smaller data disk was replaced with a larger disk to retain Docker persistent data and the existing Nextcloud instance. The operator reported creating mount points, copying data, editing /etc/fstab, and later installing the replacement internally after using a USB-to-SATA adapter during transfer.

The first application start appeared to be a fresh installation. After correcting the copied directory layout by moving its contents up one level, the operator confirmed: “it's working properly rn”.

This is a session report, not a captured shell transcript. Exact device models, capacities, UUIDs, mount paths, the original copy command and stop/start history were not supplied. Commands below are reusable examples from the procedure, not assertions that every command was executed. No whole-disk clone or partition-table repair was established.

## Work sequence

1. Identify container persistence using Docker inspect: distinguish host bind mounts from named volumes, and locate both Nextcloud files/config and its database.
2. Create the destination mount point and preserve the relevant directory ownership and permissions.
3. Copy existing data to the larger disk, preserving filesystem attributes and hidden files.
4. Switch the mount configuration in /etc/fstab so the replacement supplies the path expected by the containers.
5. Investigate the apparent fresh Nextcloud setup; correct an extra directory level in the copied data.
6. Confirm working application behavior, then shut down for physical replacement.
7. Install the disk internally. The operator described this as PCIe; the exact internal interface was not independently verified.
8. Review the subsequent monitoring warning about historical USB reads and GPT metadata.

## Reference procedure and command explanations

All paths, container names and UUIDs below are placeholders. Verify source and destination before using them.

### Inspect storage

~~~bash
lsblk -f
findmnt
docker ps -a
docker inspect <container_name> --format '{{json .Mounts}}' | jq
~~~

In Mounts, Source is the host storage path and Destination is the container path. Named volumes may be on another filesystem; copying one disk does not automatically migrate every volume, Docker's data root, or container writable layers. Persistent application state is not the same as a running process's memory.

### Prepare mount points and permissions

~~~bash
sudo mkdir -p /new/mountpoint
# Mount the intended replacement filesystem here before setting its root attributes.
sudo mount UUID=<NEW_UUID> /new/mountpoint
sudo chown --reference=/old/mountpoint /new/mountpoint
sudo chmod --reference=/old/mountpoint /new/mountpoint
~~~

Apply attributes after mounting; otherwise they affect the underlying directory hidden by the mount. chown copies owner/group and chmod copies mode bits; these two commands alone do not reproduce every ACL, extended attribute or SELinux context.

### Copy contents with attributes

Stop affected application containers, background writers and the database cleanly before the final copy. Pause automatic restart jobs during maintenance as appropriate. The session does not include proof that these stops occurred.

~~~bash
sudo cp -a /old/source/. /new/destination/
~~~

The /. includes hidden files and copies the contents into the destination. GNU cp -a recursively preserves ownership, permissions, timestamps, symlinks and hard-link relationships, and attempts to preserve extended attributes and SELinux contexts. Destination filesystem support and privileges matter; verify attributes rather than assuming complete preservation.

An alternative discussed was:

~~~bash
sudo rsync -aHAX --numeric-ids --info=progress2 /old/source/ /new/destination/
~~~

Do not copy a live database datadir as a consistent backup. Use a stopped database or a supported database backup procedure. Nextcloud recovery requires matching database state, files and configuration.

### Correct the directory layout

Symptom: Nextcloud presented an initial setup instead of its previous instance. Recovery after moving contents up one directory strongly supports a path/layout mismatch; the exact before/after tree was not captured.

A common example is data copied into /new/destination/source/ while the bind mount expects the files directly in /new/destination/.

The Bash command provided in the session was:

~~~bash
(shopt -s dotglob nullglob; files=(*); (("${#files[@]}")) && mv -i -- "${files[@]}" ../)
~~~

Run only from the verified unwanted nested directory, with affected containers stopped and sufficient permissions. dotglob includes hidden entries, nullglob avoids a literal unmatched *, and -i prompts before overwriting. Existing destination directories require inspection; mv is not a directory-merging tool.

A move within one filesystem preserves the existing file objects and their permissions, ownership and extended attributes; inode change time can change. A cross-filesystem move is a copy/delete operation and has different failure and attribute-preservation considerations. This is why confirming the mount layout matters.

### Switch /etc/fstab

Back up /etc/fstab before editing. Replace the old data-filesystem UUID with the new UUID while preserving the host path expected by the containers and appropriate options. Update the filesystem type if needed.

Example only:

~~~fstab
UUID=<NEW_UUID> /srv/container-data ext4 defaults 0 2
~~~

Device names such as /dev/sdb can change when moving from USB to an internal connection or after reboot. A filesystem UUID normally remains unchanged when moving the same disk between interfaces.

For a planned switch: stop writers, leave directories on the old filesystem, unmount the temporary destination and the old mount, then mount the new filesystem at the original path. Do not format either disk during this step.

After editing:

~~~bash
sudo systemctl daemon-reload
sudo findmnt --verify --verbose
sudo mount /srv/container-data
findmnt -T /srv/container-data
df -hT /srv/container-data
~~~

These use the example path. Check that the actual mounted UUID and filesystem match the intended replacement before starting applications. Avoid allowing containers to initialize empty directories underneath a missing data mount.

### Shutdown and physical replacement

~~~bash
sudo poweroff
~~~

On this systemd-based host, sudo shutdown -h now was also discussed as a clean power-off command. Wait for full power-off and disconnect power before replacing the drive.

## Validation and remaining work

- Confirmed by the operator: application behavior recovered after the directory move.
- Independently observed earlier in this session: Linux MCP could reach the host after reboot and reported RHEL 10.1 with approximately 32 minutes uptime.
- Not established by that connectivity check: complete file integrity, database consistency, the exact new mount mapping, or disk health.
- Still to verify: intended UUID mounted after boot; Nextcloud login, existing-file download and new upload; other affected containers; ownership, ACLs and SELinux labels; fresh kernel I/O errors.
- Keep the original disk until validation is complete. If rolling back after new writes, account for divergence between old and new data rather than blindly switching back.

## USB errors and GPT warning

The monitoring report shown during the session mentioned USB descriptor failures and I/O read errors for /dev/sdb at 18:53, followed by a GPT alternate-header warning at the latest boot. The screenshot's timezone and device identity were not independently verified.

The operator confirmed USB-to-SATA was used during transfer and an internal connection afterward. The earlier USB errors may therefore relate to the transfer connection or disconnection, but adapter failure, disk failure or data corruption was not proven. /etc/fstab edits do not cause USB descriptor errors.

The GPT warning is separate: the backup GPT header was not at the expected disk end. A file-level copy does not relocate GPT metadata. Identify the affected physical disk and inspect its partition table read-only before considering a repair. No GPT repair was performed or verified in this session.

## Lessons

- Preserve both filesystem metadata and the exact directory hierarchy expected by bind mounts.
- Include hidden files; copying directory contents differs from nesting the source directory.
- Keep Nextcloud files/config and database consistent during migration.
- Use UUID-based mounts and verify the mount before starting containers.
- Separate historical USB events from current internal-disk errors and partition-table warnings.
