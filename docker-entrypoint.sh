#!/bin/sh
# Reconcile ownership of the app's managed files, then drop to the unprivileged
# runtime user. The container starts as root ONLY for this step: the Factorio
# containers the backend spawns (and legacy directories from older versions) can
# leave files owned by a different uid that the app must still read/write/delete.
# chown-ing the tree to FSM_UID:FSM_GID here means the dropped-privilege app owns
# everything it manages, so deletion and file management never hit EPERM/EACCES.
set -e

: "${FSM_UID:=10001}"
: "${FSM_GID:=10001}"

# Re-chowns the copied source too, but that is cheap; the data dirs
# (servers/saves/downloads, database.db, config.ini) are the point. If startup
# ever gets slow at scale, scope this to those paths or use `find ... -not -uid`.
chown -R "${FSM_UID}:${FSM_GID}" /app/src/api 2>/dev/null || true

exec gosu "${FSM_UID}:${FSM_GID}" "$@"
