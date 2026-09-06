#!/bin/bash
set -e

cat > "$PGDATA/pg_hba.conf" << EOF
local   all   all              trust
host    all   all   0.0.0.0/0  trust
host    all   all   ::1/128    trust
EOF

pg_ctl reload -D "$PGDATA"