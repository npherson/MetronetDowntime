D=docker
$D ps >/dev/null 2>&1 || D="sudo docker"
C=$($D ps --format '{{.Names}} {{.Image}}' | grep -i kuma | head -1 | cut -d' ' -f1)
echo "=== container: $C" >&2
$D ps --format '{{.Names}}  {{.Image}}  {{.Status}}' >&2
$D inspect -f '{{range .Mounts}}{{.Type}} {{.Name}} {{.Source}} -> {{.Destination}}{{println}}{{end}}' "$C" >&2
$D exec "$C" ls -la /app/data >&2
$D exec "$C" cat /app/data/db-config.json >&2 2>/dev/null
echo "=== streaming db" >&2
$D exec "$C" sh -c 'cd /app/data && tar -cf - kuma.db kuma.db-wal kuma.db-shm db-config.json 2>/dev/null'
echo "=== done" >&2
