#!/bin/bash
set -e

cat > "$PGDATA/pg_hba.conf" << EOF
local   all   all              trust
host    all   all   0.0.0.0/0  md5
host    all   all   ::1/128    md5
EOF

echo "password_encryption = md5" >> "$PGDATA/postgresql.conf"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
EOSQL