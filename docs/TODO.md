# TODO

## Off-disk backup with QNAP Hybrid Backup Sync (HBS)

The `postgres-backup` CronJob (see `deploy/README.md`, "Database backup") writes daily `pg_dump` files to the
same NAS volume as the database. That protects against bad data, not against a dead disk, so copy them elsewhere.

- [ ] Confirm the NAS path of Docker volume `yuyang-management` (Container Station > Storage > Volumes > Mount point).
      Expected: `/share/CACHEDEV1_DATA/Container/container-station-data/lib/docker/volumes/yuyang-management/_data/backups`
- [ ] Check whether HBS can select that folder. `lib/docker` is restricted for non-admin accounts and may be hidden.
      If it cannot, make the CronJob write to a regular QNAP shared folder instead (needs the k3s container's mounts rebuilt).
- [ ] Create an HBS job that copies the `backups` folder to a different location (external USB, another NAS, or cloud), with a schedule after 03:00 Asia/Taipei and encryption if the target is not local.
- [ ] Do a restore drill from the copied file (see "Restore" in `deploy/README.md`).
- [ ] Do NOT use HBS on the live Postgres data directory (`/mnt/yuyang-management/postgres`) as the only backup: copying files of a running database can give an inconsistent backup.
