#!/bin/sh
# Idempotent host bootstrap for FactorioServerManager.
#
# Creates the `fsm` service user/group, provisions the canonical data
# directories the backend bind-mounts, and gives them to that user so the
# containerised backend (which runs as this uid/gid after dropping root in
# docker-entrypoint.sh) owns everything it manages. Safe to re-run.
#
# Override the ids to match your compose/Dockerfile build args:
#   FSM_UID=10001 FSM_GID=10001 sudo -E ./scripts/setup-host.sh
#
# Run as root (needs to create a user and chown).
set -eu

FSM_UID="${FSM_UID:-10001}"
FSM_GID="${FSM_GID:-10001}"
FSM_USER="${FSM_USER:-fsm}"

# Canonical absolute data paths. These MUST match the container paths because the
# backend hands them to the host Docker daemon verbatim as bind-mount sources
# (see README / docker-compose.prod.yml).
DATA_ROOT="/app/src/api"
DIRS="${DATA_ROOT}/servers ${DATA_ROOT}/saves ${DATA_ROOT}/downloads"
DB_FILE="${DATA_ROOT}/database.db"
CONFIG_FILE="${DATA_ROOT}/config.ini"

if [ "$(id -u)" -ne 0 ]; then
    echo "setup-host.sh must run as root (creates a user and chowns files)." >&2
    exit 1
fi

# --- service group ---------------------------------------------------------
if ! getent group "${FSM_GID}" >/dev/null 2>&1; then
    groupadd --system --gid "${FSM_GID}" "${FSM_USER}"
    echo "Created group ${FSM_USER} (gid ${FSM_GID})."
else
    echo "Group with gid ${FSM_GID} already exists; leaving it."
fi

# --- service user ----------------------------------------------------------
if ! getent passwd "${FSM_UID}" >/dev/null 2>&1; then
    useradd --system --uid "${FSM_UID}" --gid "${FSM_GID}" \
        --home-dir /nonexistent --no-create-home --shell /usr/sbin/nologin "${FSM_USER}"
    echo "Created user ${FSM_USER} (uid ${FSM_UID})."
else
    echo "User with uid ${FSM_UID} already exists; leaving it."
fi

# --- data dirs / files -----------------------------------------------------
# shellcheck disable=SC2086  # word-splitting DIRS intentionally
mkdir -p ${DIRS}
[ -e "${DB_FILE}" ] || touch "${DB_FILE}"   # a FILE bind — must exist before `up`
[ -e "${CONFIG_FILE}" ] || echo "note: ${CONFIG_FILE} not present yet (copy config.prod.example.ini)."

# --- ownership -------------------------------------------------------------
# shellcheck disable=SC2086
chown -R "${FSM_UID}:${FSM_GID}" ${DIRS} "${DB_FILE}"
[ -e "${CONFIG_FILE}" ] && chown "${FSM_UID}:${FSM_GID}" "${CONFIG_FILE}"

echo "Done. ${DATA_ROOT} data owned by ${FSM_UID}:${FSM_GID}."
