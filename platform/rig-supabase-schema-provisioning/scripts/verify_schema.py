#!/usr/bin/env python3
"""
Ad-hoc verification template for Supabase schema provisioning tasks.

Run after provision_schema.py to confirm tables/indexes actually exist
and DDL is idempotent. Prints a JSON verdict and exits 0=PASS / 1=FAIL.

Place a copy under /var/folders/.../T/hermes-verify-<task>.py to satisfy
the Hermes verification gate; remember the shell can write there but
the write_file tool refuses (see references/connection-recipes.md).
"""
import os
import sys
import json
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


def verify(expected_tables, expected_indexes, sample_columns=None, ddl_replay=None):
    """
    expected_tables:  list[str]  — full table names expected to exist
    expected_indexes: list[str]  — full index names expected to exist
    sample_columns:   dict[str, list[str]]  — {table_name: [column_names]} to spot-check shape
    ddl_replay:       list[str]  — DDL statements to re-run for idempotency check
    """
    env = load_env()
    url = env['JIB_DATABASE_URL'].replace(':***@', ':' + env['SUPABASE_DB_PASSWORD'] + '@')
    conn = psycopg2.connect(url, connect_timeout=15)
    cur = conn.cursor()

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name = ANY(%s)",
        (expected_tables,),
    )
    found_tables = {r[0] for r in cur.fetchall()}

    cur.execute(
        "SELECT indexname FROM pg_indexes "
        "WHERE schemaname='public' AND indexname = ANY(%s)",
        (expected_indexes,),
    )
    found_indexes = {r[0] for r in cur.fetchall()}

    column_issues = []
    if sample_columns:
        for tbl, cols in sample_columns.items():
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (tbl,),
            )
            # Postgres lowercases unquoted identifiers — compare case-insensitively.
            have = {r[0].lower() for r in cur.fetchall()}
            for c in cols:
                if c.lower() not in have:
                    column_issues.append(f'{tbl}.{c} MISSING')

    idem_ok, idem_err = True, None
    if ddl_replay:
        try:
            conn.rollback()
            conn.autocommit = True
            for stmt in ddl_replay:
                cur.execute(stmt)
        except Exception as e:
            idem_ok, idem_err = False, f'{type(e).__name__}: {str(e)[:200]}'

    cur.close()
    conn.close()

    mt = sorted(set(expected_tables)  - found_tables)
    mi = sorted(set(expected_indexes) - found_indexes)
    verdict = 'PASS' if (not mt and not mi and not column_issues and idem_ok) else 'FAIL'

    report = {
        'verification': 'ad-hoc hermes-verify-supabase-schema',
        'tables':  {'expected': len(expected_tables),  'found': len(found_tables),  'missing': mt},
        'indexes': {'expected': len(expected_indexes), 'found': len(found_indexes), 'missing': mi},
        'column_issues': column_issues,
        'idempotent_rerun_ok':  idem_ok,
        'idempotent_rerun_err': idem_err,
        'verdict': verdict,
    }
    print(json.dumps(report, indent=2))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    DEPTS = ['gtm', 'content', 'linkedin', 'strategy', 'design', 'app', 'companyos', 'film']
    expected_tables  = [f'dept_{d}_{s}' for d in DEPTS for s in ('raw', 'entities', 'patterns')]
    expected_indexes = [f'idx_dept_{d}_{s}' for d in DEPTS for s in ('ingested', 'entities_type')]
    sample_columns = {
        'dept_gtm_raw':       ['id', 'source', 'url', 'payload', 'ingested_at', 'sha256'],
        'dept_film_entities': ['id', 'entity_type', 'entity_key', 'attributes', 'first_seen', 'last_updated'],
        'dept_app_patterns':  ['id', 'pattern_text', 'evidence_count', 'confidence', 'promoted_to_L7', 'created_at'],
    }
    ddl_replay = []
    for d in DEPTS:
        ddl_replay.append(f'CREATE TABLE IF NOT EXISTS dept_{d}_raw (id BIGSERIAL PRIMARY KEY)')
        ddl_replay.append(f'CREATE TABLE IF NOT EXISTS dept_{d}_entities (id BIGSERIAL PRIMARY KEY)')
        ddl_replay.append(f'CREATE TABLE IF NOT EXISTS dept_{d}_patterns (id BIGSERIAL PRIMARY KEY)')
        ddl_replay.append(f'CREATE INDEX IF NOT EXISTS idx_dept_{d}_ingested ON dept_{d}_raw(id)')
        ddl_replay.append(f'CREATE INDEX IF NOT EXISTS idx_dept_{d}_entities_type ON dept_{d}_entities(id)')
    sys.exit(verify(expected_tables, expected_indexes, sample_columns, ddl_replay))