# GBrain Postgres Schema (S78, S87)

## Connection

GBrain is a local Postgres database. Connect via:
```bash
psql -d gbrain
```

Or via psycopg2 (no-auth local):
```python
conn = psycopg2.connect("postgresql://localhost:5432/gbrain")
```

## Key Tables

### pages
Primary content table. **Does NOT have a `tags` column.** **Does NOT have a `content` column** — use `compiled_truth` for short content and `content_chunks` for full text. **`slug` has no unique constraint** — cannot use `ON CONFLICT (slug)`.

| Column | Type |
|--------|------|
| id | integer |
| source_id | text |
| slug | text |
| type | text |
| page_kind | text |
| title | text |
| compiled_truth | text |
| timeline | text |
| frontmatter | jsonb |
| content_hash | text |
| emotional_weight | real |
| created_at | timestamp with time zone |
| updated_at | timestamp with time zone |
| deleted_at | timestamp with time zone |
| effective_date | timestamp with time zone |
| effective_date_source | text |
| import_filename | text |
| salience_touched_at | timestamp with time zone |
| last_retrieved_at | timestamp with time zone |
| contextual_retrieval_mode | text |
| corpus_generation | text |
| generation | bigint |
| search_vector | tsvector |
| emotional_weight_recomputed_at | timestamp with time zone |
| chunker_version | smallint |
| source_path | text |
| ingested_via | text |
| ingested_at | timestamp with time zone |
| source_uri | text |
| source_kind | text |
| embedding_signature | text |
| links_extracted_at | timestamp with time zone |

### content_chunks
Full text content for pages. **Column is `chunk_index`, NOT `chunk_order`** (confirmed S87).

| Column | Type |
|--------|------|
| id | integer |
| page_id | integer (FK to pages.id) |
| chunk_index | integer |
| chunk_text | text |
| chunk_source | text |
| embedding | vector (USER-DEFINED) |
| model | text |
| token_count | integer |
| embedded_at | timestamp with time zone |
| created_at | timestamp with time zone |
| language | text |
| symbol_name | text |
| symbol_type | text |
| start_line | integer |
| end_line | integer |
| parent_symbol_path | ARRAY |
| doc_comment | text |
| symbol_name_qualified | text |
| search_vector | tsvector |
| modality | text |
| embedding_image | vector (USER-DEFINED) |
| embedding_multimodal | vector (USER-DEFINED) |
| edges_backfilled_at | timestamp with time zone |

### tags
Separate tag table. JOIN to `pages` on `page_id`.

| Column | Type |
|--------|------|
| id | integer |
| page_id | integer |
| tag | text |

### page_links
| Column | Type |
|--------|------|
| id | integer |
| from_page_id | integer |
| to_page_id | integer |

### All Tables (as of S78)

access_tokens, budget_ledger, budget_reservations, calibration_profiles, code_edges_chunk, code_edges_symbol, code_traversal_cache, config, content_chunks, context_volunteer_events, conversation_parser_llm_cache, dream_verdicts, drift_decisions, eval_candidates, eval_capture_failures, eval_contradictions_cache, eval_contradictions_runs, eval_takes_quality_runs, extract_rollup_7d, facts, file_migration_ledger, files, gbrain_cycle_locks, ingest_log, links, mcp_request_log, mcp_spend_log, mcp_spend_reservations, migration_impact_log, minion_attachments, minion_budget_log, minion_inbox, minion_jobs, minion_lease_pressure_log, minion_self_fix_log, oauth_clients, oauth_codes, oauth_tokens, op_checkpoint_paths, op_checkpoints, page_aliases, page_generation_clock, page_links, page_versions, pages, query_cache, raw_data, search_telemetry, slug_aliases, sources, subagent_messages, subagent_rate_leases, subagent_tool_executions, synthesis_evidence, tags, take_domain_assignments, take_grade_cache, take_nudge_log, take_proposals, takes, think_ab_results, timeline_entries

## Common Queries

### Tag-filtered page search
```sql
SELECT p.id, p.slug, p.title, p.content_hash, p.updated_at, p.source_uri,
       array_agg(t2.tag) as all_tags
FROM pages p
JOIN tags t2 ON t2.page_id = p.id
WHERE t2.tag ILIKE '%gtm%' AND p.deleted_at IS NULL
GROUP BY p.id, p.slug, p.title, p.content_hash, p.updated_at, p.source_uri
ORDER BY p.updated_at DESC LIMIT 30;
```

### Read page content via content_chunks
```sql
SELECT chunk_text FROM content_chunks cc
JOIN pages p ON cc.page_id = p.id
WHERE p.slug = %s
ORDER BY cc.chunk_index;
```

### Upsert IntelPacket (check-then-insert-or-update)
See SKILL.md section "GBrain Postgres Upsert — ON CONFLICT (slug) Fails" for the full pattern.

### Recent pages
```sql
SELECT id, slug, title, content_hash, updated_at, source_uri
FROM pages WHERE deleted_at IS NULL
ORDER BY updated_at DESC LIMIT 20;
```

### Schema introspection
```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='pages' ORDER BY ordinal_position;
```
