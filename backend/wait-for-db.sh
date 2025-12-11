#!/bin/bash
# Wait for PostgreSQL to be ready

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=invoice_pass psql -h "$host" -U invoice_user -d invoice_db -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"
exec $cmd

