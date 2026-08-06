#!/usr/bin/env python3
"""
Reusable Supabase schema provisioning template.

Customize `DEPTS` and `DDL_PER_DEPT` for the task, then run:

    source ~/.hermes/hermes-agent/venv/bin/activate
    python3 scripts/provision_schema.py

Writes a proof JSON to ~/.rig/state/<task_slug>-proof.json.
"""
import os
import json
import datetime
import sys
import psycopg2


def load_env():
    env = {}
    for line in open(os.path.expanduser('~/.hermes/.env')):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k] = v
    return env


def connect(env):
    url = env['JIB_DATABASE_URL'].replace(':***@', ':' + env['SUPABASE_DB_PASSWORD'] + '@')
    return psycopg2.connect(url, connect_timeout=15)


def provision(tables_spec, indexes_spec, task_slug='supabase-schema'):
    """
    tables_spec:  list of (table_name, ddl_sql)
    indexes_spec: list of (index_name, ddl_sql)
    """
    env = load_env()
    conn = connect(env)
    conn.autocommit = True
    cur = conn.cursor()

    created_tables = []
    for tname, ddl in tables_spec:
        cur.execute(ddl)
        created_tables.append(tname)

    created_indexes = []
    for iname, ddl in indexes_spec:
        cur.execute(ddl)
        created_indexes.append(iname)

    cur.close()
    conn.close()

    proof = {
        'ran_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'tables_created':  created_tables,
        'indexes_created': created_indexes,
        'status': 'PASS',
    }
    out_dir = os.path.expanduser('~/.rig/state')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{task_slug}-proof.json')
    with open(out_path, 'w') as f:
        json.dump(proof, f, indent=2, sort_keys=True)
    print(json.dumps({'status': 'PASS', 'tables_created': len(created_tables),
                      'indexes_created': len(created_indexes), 'proof_path': out_path}))
    return proof


if __name__ == '__main__':
    # Example: 8 RIG departments (gtm, content, linkedin, strategy, design, app, companyos, film).
    # Override or replace DEPTS / DDL_PER_DEPT for your task.
    DEPTS = ['gtm', 'content', 'linkedin', 'strategy', 'design', 'app', 'companyos', 'film']

    tables_spec = []
    indexes_spec = []
    for d in DEPTS:
        for kind, body in [
            ('raw', 'id BIGSERIAL PRIMARY KEY, source TEXT NOT NULL, url TEXT, payload JSONB NOT NULL, ingested_at TIMESTAMPTZ DEFAULT NOW(), sha256 TEXT NOT NULL'),
            ('entities', 'id BIGSERIAL PRIMARY KEY, entity_type TEXT, entity_key TEXT UNIQUE, attributes JSONB, first_seen TIMESTAMPTZ DEFAULT NOW(), last_updated TIMESTAMPTZ DEFAULT NOW()'),
            ('patterns', 'id BIGSERIAL PRIMARY KEY, pattern_text TEXT, evidence_count INT, confidence DECIMAL, promoted_to_L7 BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW()'),
        ]:
            tname = f'dept_{d}_{kind}'
            tables_spec.append((tname, f'CREATE TABLE IF NOT EXISTS {tname} ({body});'))
        indexes_spec.append((f'idx_dept_{d}_ingested',
                             f'CREATE INDEX IF NOT EXISTS idx_dept_{d}_ingested ON dept_{d}_raw(ingested_at DESC);'))
        indexes_spec.append((f'idx_dept_{d}_entities_type',
                             f'CREATE INDEX IF NOT EXISTS idx_dept_{d}_entities_type ON dept_{d}_entities(entity_type);'))

    provision(tables_spec, indexes_spec, task_slug='supabase-schema-8depts')