#!/bin/bash
# Wait for PostgreSQL to be ready

set -e

host="$1"
shift
cmd="$@"

# Use environment variables with defaults
POSTGRES_USER="${POSTGRES_USER:-invoice_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-invoice_pass}"
POSTGRES_DB="${POSTGRES_DB:-invoice_db}"

until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"
exec $cmd

