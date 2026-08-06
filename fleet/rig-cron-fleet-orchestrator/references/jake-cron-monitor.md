# JAKE Cron-Monitor Idle Cycle — Cycle-Health Watcher on a Single Node

Distinct from the fleet watchdog pattern in `self-healing-monitor-cron.md` (which inspects OTHER crons with M1-M5 monitors) and the read-only analytics pattern in `read-only-analytics-cron.md` (which writes a date+hour proof file from external APIs every cycle).

This is the **per-node JAKE cron-health monitor** pattern: a single cron pinned to ONE node (e.g. `127.0.0.1:11434`, `192.168.68.80:11434`) that counts per-dept cycles, logs to a state file, restarts stuck crons, kills unhealthy Docker, and writes a per-cycle ProofPacket. The primary workload is **observational and healing**; the secondary workload (substrate processing through the node) only fires when fresh substrate appears.

The pattern's distinctive feature: **most cycles are idle** by design. The cron runs on cadence (e.g. hourly), but substrate shows up only when upstream scrape crons have fired. Honest idle cycles are the steady state; "real-work" cycles are the exception.

## When this fits

- A cron is pinned to ONE LAN endpoint (a specific Ollama/Ollama-MLX node URL)
- The cron's primary mission is node health + substrate processing + Docker watch
- Fresh substrate (`.raw` / `.md` files in `~/.rig/departments/*/substrate/`) appears irregularly — sometimes 5 files between cycles, sometimes zero for hours
- The cron writes `~/.rig/state/24x7-ops/<node>-proof.json` every cycle regardless of whether there was work
- The orchestrator reads `~/.rig/departments/heat/specs/node-jobs/<node>.last_cycle.json` to see if the monitor is alive

Examples: Jake cron-health monitor per local Ollama node, fleet per-node liveness probe, JAKE substrate processor pinned to a single endpoint.

## The three-mode cycle: idle / real-work / degraded

Every cycle fits one of three states, and the proof file must be honest about which:

| Mode | Trigger | Proof `verdict` | Substrate processing | Inference run? |
|---|---|---|---|---|
| **Idle** | 0 fresh substrate (< window) + node healthy + Docker healthy | `idle_cycle_no_fresh_substrate_docker_healthy_no_fabrication` | None | No |
| **Real-work** | N fresh substrate files + node capable + Docker healthy | `partial_inference_run_with_explicit_model_swap_documented_no_fabrication` (or full pass) | All fresh files | Yes — per file |
| **Degraded** | Node unreachable OR Docker unhealthy OR substrate present but node can't run inference | `degraded_node_unreachable_or_docker_unhealthy_*` | Partial / none | No (or failed) |

**Critical principle:** an idle cycle is **not a failure**. The cron ran successfully; there was just nothing to do. The proof should say so clearly with `files_under_2h: 0`, `lan_completed_inference_runs: 0`, `cycle_output_written_this_pass: false`, and `reuses_cycle_N_artifacts_intentionally: true` (pointing at the prior cycle's entities).

The temptation is to manufacture work — widen the window, re-process already-processed files, run inference on stale substrate "just to have output." **Don't.** The compounding principle (see `read-only-analytics-cron.md` §"Honest no-op → real-work compounding transition") means every cycle must compound on the prior, never duplicate.

## The idle-cycle proof schema

When the cycle is idle, the proof file is shorter but carries the same top-level shape as a real-work cycle:

```json
{
  "schema_version": 1,
  "node_endpoint": "http://<ip>:<port>/v1/chat/completions",
  "cycle_number": 12,
  "timestamp": "2026-07-14T15:40:00Z",
  "verdict": "idle_cycle_no_fresh_substrate_docker_healthy_no_fabrication",

  "node_health": {
    "endpoint": "...",
    "api_tags_endpoint": "...:11434/api/tags",
    "reachable": true,
    "ollama_alive": true,
    "ollama_version": "0.32.0",
    "post_chat_completions_status_ornith_35b": 404,
    "post_chat_completions_status_ornith_9b": 200,
    "models_present_on_node": ["ornith:9b", "nomic-embed-text:latest"],
    "model_requested_by_cron": "ornith:35b",
    "model_present_for_cron_request": false,
    "model_used_for_inference_this_cycle": "none_no_substrate_to_process",
    "models_re_checked_this_cycle": true
  },

  "substrate_inventory": {
    "files_under_2h": 0,
    "files_already_processed_by_prior_cycles_today": 3,
    "fresh_substrate_to_process": 0,
    "files_considered_but_out_of_window": [
      {"path": "...", "bytes": 459, "mtime": "...", "reason_skipped": "6_days_old_outside_2h_window_compound_principle_dont_repeat"}
    ],
    "files": []
  },

  "inference": {
    "lan_primary_attempted": true,
    "lan_silent_swap_to_ornith_9b": false,
    "silently_labeling_ornith_9b_output_as_ornith_35b": false,
    "rationale": "Cycle-12. Substrate scan: 0 files under 2h. ...",
    "lan_completed_inference_runs": 0,
    "cloud_fallback_attempted": false,
    "cycle_output_written_this_pass": false,
    "cycle_output_artifacts": [],
    "reuses_cycle_N_artifacts_intentionally": true,
    "reused_artifact_paths": ["..."]
  },

  "fallback": {
    "lan_status": "reachable_but_model_missing_35b_then_capable_with_9b",
    "decision": "no inference performed this cycle",
    "doc_link": "/Users/rig128gb/.rig/agent-doctrine/RIG_GLOBAL_AGENT_POLICY.md"
  },

  "docker_health": {
    "total": 10, "up": 10, "healthy": 1, "unhealthy": 0, "restarting": 0,
    "containers": ["..."],
    "action": "none_required_all_healthy"
  },

  "blocklist_quarantine": {
    "scanned_against": ["HED","IdeaWake","Anthony Langeweg","hed-forge","dec-1783268304352-va5c","dec-1783268340018-db8f"],
    "matches_strict_word_boundary": 0, "matches_substring": 0,
    "action": "none_required_strict_check_clean"
  },

  "quality_gates": {
    "all_entity_files_have_facts_fence": "n/a_no_entities_written_this_cycle",
    "entity_files_count": 0,
    "no_fabrication_principle": "PASS — no inference attempted when no substrate exists"
  },

  "escalation": {
    "needs_human": true,
    "reason": "cron-pinned model 'ornith:35b' still missing on local Ollama node (Nth cycle of unresolved escalation)",
    "escalation_age_cycles": 6,
    "action_choices_for_user": ["ollama pull ornith:35b", "formally accept ornith:9b", "re-pin cron to other node", "configure OLLAMA_CLOUD_API_KEY"]
  },

  "compound": {
    "prior_cycle_outputs_consulted": true,
    "prior_cycle_artifact_reuse_intentional": true,
    "no_duplicate_inference_run": true,
    "cycle_increments_monotonically": "12 (was 11 at ...)"
  }
}
```

The proof is **always the same shape** regardless of mode. The differences are: `verdict` string, `cycle_output_written_this_pass`, `substrate_inventory.files_under_2h`, and `inference.lan_completed_inference_runs`. The orchestrator and the operator can `jq .verdict` and immediately know the mode.

## The escalation-age-cycle counter

When a recurring error persists across cycles (e.g. the cron asks for `ornith:35b` but only `ornith:9b` is installed on the node), the proof file must carry an **escalation_age_cycles** counter that monotonically increments every cycle the error persists:

```json
"escalation": {
  "needs_human": true,
  "reason": "cron-pinned model 'ornith:35b' still missing on local Ollama node (6th cycle of unresolved escalation, c07..c12). ...",
  "escalation_age_cycles": 6
}
```

**Why this matters:** without the counter, an operator sees the same `needs_human: true` proof every cycle and can't tell whether (a) they missed this last cycle or (b) the cron has been nagging for 12 cycles and they have a pattern of not acting. The counter turns nagging into observable trajectory — "this has been escalated 6 cycles in a row, Mike."

**Rules:**

- **Monotonically increments** while the underlying issue persists. A new cycle that hits the same wall reads the prior proof, increments by 1, and writes.
- **Resets to 0** when the underlying issue resolves AND a new issue appears, OR when the previous escalation was actioned and closed.
- **Escalation age × cadence minutes** tells the operator how long this has been broken in wall-clock time. Always include both numbers in the `needs_human` reason string.
- **Don't reset on idle cycles** — the model is still missing, the escalation is still in flight, even if this particular cycle didn't need inference.
- **State-then-counter order:** `escalation_age_cycles` is a STATE field (stored in the proof file). The cron does NOT need a separate state file; the prior proof IS the state. Read the prior proof, increment, write the new one.

## Pre-inference dual-probe: `/v1/chat/completions` AND `/api/tags`

A naive first probe against an Ollama node hits `/v1/chat/completions` (OpenAI-compat path) and gets a 404 when:
1. The model isn't installed (most common cause) — 404 with `{"error":{"message":"model 'X' not found"}}`
2. The endpoint path is wrong — 404 with empty body
3. The Ollama version doesn't have the OpenAI-compat adapter — 404

A 404 on the OpenAI path does NOT mean the node is dead. The Ollama-native API at `/api/tags` will tell you what IS available. **Probe both, in this order:**

```bash
# Step 1: try the cron-pinned model via OpenAI-compat
curl -s -m 5 -o /tmp/probe1.json -w "HTTP:%{http_code}\n" \
  http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"ornith:35b","messages":[{"role":"user","content":"ping"}],"max_tokens":3}'

# Step 2: enumerate loaded models via Ollama-native (ALWAYS also do this)
curl -s -m 5 http://127.0.0.1:11434/api/tags | jq '.models[].name'
# → ["ornith:9b", "nomic-embed-text:latest"]

# Step 3: confirm the node itself is alive
curl -s -m 5 http://127.0.0.1:11434/api/version | jq '.version'
# → "0.32.0"
```

The two probes answer different questions:
- **OpenAI-compat probe** = "can the cron run the model it asked for?"
- **`/api/tags` probe** = "what IS actually loaded on this node?"
- **`/api/version` probe** = "is the Ollama daemon itself running?"

Always do all three in the first cycle, then drop to a single OpenAI-compat probe in subsequent cycles once you've confirmed the node is stable. Note in the proof that `models_re_checked_this_cycle: true` is a fact, not a label — the cron actually queried `/api/tags`, it didn't assume.

## Docker health-check sequence

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}"
docker ps --filter "health=unhealthy" --format "{{.Names}}"   # ← explicit empty-string check, not exit code
docker ps --filter "status=restarting" --format "{{.Names}}"
```

The filter queries return empty strings (no rows) when healthy. Don't trust `docker ps` exit code — it returns 0 even when no containers exist. The empty-string check is the actual signal.

Always capture:
- `total` = number of containers in `docker ps`
- `up` = number with State `running`
- `healthy` = number with `Status` containing `(healthy)`
- `unhealthy` = number from the `health=unhealthy` filter
- `restarting` = number from the `status=restarting` filter
- `containers` = full list of names (for diff against prior cycle)

**Action policy:**
- `unhealthy > 0` → write a per-container alert file under `~/.rig/state/24x7-ops/docker/<container>-unhealthy-<ts>.alert`
- `restarting > 0` → write a per-container alert file and try `docker restart <name>` ONCE; if it still fails, alert without restart loops (we don't want a restart storm)
- `up < total` → containers exist but stopped; alert and surface to operator

A healthy Docker block reads:
```json
"docker_health": {
  "total": 10, "up": 10, "healthy": 1, "unhealthy": 0, "restarting": 0,
  "containers": ["buildx_buildkit_rig-qnap-fabric-v10", "rig-console-postgres", ...],
  "action": "none_required_all_healthy"
}
```

`action: "none_required_all_healthy"` is the green path. Anything else is a red flag.

## The 1-line status file the orchestrator reads

```bash
# ~/.rig/departments/heat/specs/node-jobs/<node>.last_cycle.json
{"node":"127.0.0.1:11434","cycle":12,"ts":"2026-07-14T15:40:00Z","status":"idle_no_substrate","model_requested":"ornith:35b","model_used":"none","entities_written":0,"docker_up":10,"escalation_age_cycles":6}
```

This file is read by the orchestrator on every cycle to verify the monitor is alive. It must:
- Be **under 300 bytes** — orchestrator polls fast
- Carry the **monotonic cycle number** (compare against prior)
- Carry `status` which is one of: `ok_with_disclosure`, `idle_no_substrate`, `degraded_node_unreachable`, `degraded_docker_unhealthy`, `error`
- Carry `escalation_age_cycles` so the orchestrator can detect nagging-into-staleness
- Be overwritten with `write_file` each cycle (no append)

If the file is **stale (> 2× the cron cadence)** the orchestrator knows the monitor died.

## Compounding: don't repeat the work of prior cycles

This is the discipline that distinguishes a JAKE cron-monitor from a naive cycle loop:

1. **Read the prior proof first.** Before computing "files under 2h", scan the prior proof's `compound.prior_cycle_outputs_consulted`, `substrate_inventory.files_already_processed_by_prior_cycles_today`, and `cycle_output_artifacts` from prior real-work cycles.
2. **Compose, don't duplicate.** If a real-work cycle on `node A` already wrote `entities/threat-patterns-cycle-2026-07-14.md`, the same cycle on `node B` writes `entities/threat-patterns-cycle-2026-07-14-node-B.md` with `prior_cycle_compounded: true` frontmatter. Don't re-process the same substrate and call it fresh.
3. **Honest de-dupe in the proof.** On an idle cycle, list `reused_artifact_paths` from the prior cycle and explicitly say `reuses_cycle_N_artifacts_intentionally: true`. Don't pretend the prior cycle never happened.
4. **Skip substrate already processed today.** If 3 files were processed in c11 at 20:50Z, and c12 fires at 15:40Z the next day (after a node reboot), those same 3 files are now 18h old — but they should still be considered processed. The proof should say `files_already_processed_by_prior_cycles_today: 3` even when `files_under_2h: 0`.

## When to escalate vs when to idle

Escalate when ANY of these holds:
- Node is unreachable (`reachable: false` in node_health)
- Docker has unhealthy OR restarting containers
- Model is missing AND substrate is present AND no fallback works (escalation_age_cycles > 0)
- Blocklist strict-match > 0

DO NOT escalate (idle is honest) when:
- Substrate is < 2h empty
- Node is reachable with at least one capable model
- Docker is fully healthy
- Blocklist is strictly clean

The temptation is to escalate on every model mismatch. **Don't** — model mismatch with no fresh substrate is idle, not degraded. The escalation is fired when the model mismatch actually blocks a real inference job.

## Verification before claiming done

After writing the proof and status file:

- [ ] `os.path.getsize(proof_path) > 1000` (idle proofs are smaller but not empty)
- [ ] `os.path.getsize(status_path) < 400` and JSON-parseable
- [ ] `cycle_number` in proof == `cycle` in status file + 1 from prior
- [ ] `node_health` includes all three probe results (openai-compat, /api/tags, /api/version)
- [ ] `substrate_inventory.files_under_2h` matches an actual `find -mmin -120` count
- [ ] `docker_health.action` is one of the four enumerated values
- [ ] `escalation.escalation_age_cycles` is monotonically +1 from prior if issue persists
- [ ] `compound.cycle_increments_monotonically` carries the prior cycle's number for diff

## Anti-patterns

- **Manufacturing substrate processing on idle cycles.** Don't run a model on stale substrate "to have output." Idle is honest; idle gets reported.
- **Resetting escalation_age_cycles on idle.** A persistent model mismatch is still a mismatch even when this cycle didn't need inference. Counter increments.
- **Trusting `docker ps` exit code.** Empty filter results look the same as success in exit codes. Use empty-string check from the filter output.
- **Treating a 404 on `/v1/chat/completions` as "node down."** The OpenAI-compat path can 404 while Ollama native `/api/tags` works fine. Dual-probe before concluding.
- **Widening the freshness window to manufacture work.** If `< 2h` returns 0 files, report 0. Don't expand to 6h, don't re-process 4-day-old files "to have output."
- **Skipping the blocklist scan because there's no fresh substrate.** Even on idle cycles, scan the cycle-in-scope artifacts. The blocklist discipline is part of every cycle, real-work or idle.
- **Auto-restarting Docker containers on first unhealthy signal.** One restart attempt; if it doesn't recover, alert and stop. Don't restart-loop.

## See also

- `self-healing-monitor-cron.md` — for the M1-M5 fleet watchdog pattern (inspecting other crons)
- `read-only-analytics-cron.md` §"Honest no-op → real-work compounding transition" — for the cross-cycle compounding discipline
- `cron-pin-pitfalls.md` §"Model not found — explicit disclosure, never silent" — for the model-swap disclosure policy that this cycle type inherits
- `lan-probe-recipe.md` — for parallel fleet scanning; this reference covers the per-node dual-probe, which is a different question
- SKILL.md §1 — "Probe the LAN before you trust the config"; §4 — "State files, not live dashboards"
