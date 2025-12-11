#!/bin/bash
# Wait for Redis to be ready

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

echo "Waiting for Redis at $host:$port..."
max_attempts=60
attempt=0

# Wait for Redis to be ready
until redis-cli -h "$host" -p "$port" ping 2>/dev/null | grep -q PONG; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    >&2 echo "ERROR: Redis failed to become available after $max_attempts attempts"
    >&2 echo "Trying to connect to $host:$port..."
    redis-cli -h "$host" -p "$port" ping || true
    exit 1
  fi
  >&2 echo "Redis is unavailable - sleeping (attempt $attempt/$max_attempts)"
  sleep 1
done

# Verify Redis is actually responding
>&2 echo "Redis responded to ping, verifying connection..."
redis-cli -h "$host" -p "$port" ping > /dev/null 2>&1 || {
  >&2 echo "ERROR: Redis ping failed after initial success"
  exit 1
}

>&2 echo "Redis is up and ready - executing command"
exec $cmd
