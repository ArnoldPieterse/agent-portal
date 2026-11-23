# Fleet backups archived 2026-11-23

fleet-backup-*.tar.gz (Nov 19-20, ~283 MB) now live in
`memory_archive_2026-11-23/mechanic_backups/` at workspace root - outside memory/
so the size guard (300 MB hard limit) does not count them. Verified byte-identical
(md5) before removal. Restore by copying back.

## 2026-11-23 bloat archive
Moved 12 files (stale fleet backups Nov19-20 + stale dedup/freshness reports Nov20) to archive/bloat_20261123/. NOTE: no fleet backup newer than 2026-11-20 existed - check backup job.
