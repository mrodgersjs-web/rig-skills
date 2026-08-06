# Dry-Run Verification Patterns

## Testing the A1/A3/A4 Pipeline

### 1. Test A1 Schema (no dependencies)
```bash
PYTHONPATH=products/legacy/linkedin-studio/src python3 -c "
from linkedin_studio.A1_contracts.conference_comment_schema import (
    CONFERENCE_REGISTRY, COMMENT_BANK, score_comment,
    CommentCandidate, CommentTargetType, CommentHookType
)
print('Conferences:', list(CONFERENCE_REGISTRY.keys()))
print('Hook types:', list(COMMENT_BANK.keys()))
print('Score:', score_comment('74 hours approval latency vs 2.9 hours top-quartile. The continuity maps reveal the real gap.'))
"
```

### 2. Test A3 Engine (requires langgraph)
```bash
PYTHONPATH=products/legacy/linkedin-studio/src python3 -c "
from linkedin_studio.A3_workflows.engines.conference_comment_engine import (
    ConferenceCommentEngine, CommentRunResult
)
engine = ConferenceCommentEngine()
result = engine.run(dry_run=True, max_results=5)
print(f'targets={result.total_targets} candidates={result.candidates_generated}')
for r in result.results:
    print(f'  [{r.status}] score={r.score:.1f} -> {r.comment[:80]}')
"
```

### 3. Test A4 Wrapper
```bash
PYTHONPATH=products/legacy/linkedin-studio/src python3 -c "
from linkedin_studio.A4_control.engines.comment_engine_wrapper import run
result = run({'dry_run': True, 'limit': 5, 'target_type': 'conference'})
print(f'status={result[\"status\"]} targets={result[\"run_details\"][\"total_targets\"]}')
"
```

### 4. Test Platform Bridge
```bash
python3 platform/legacy/rig-linkedin-scripts/rig_conference_comment_bridge.py \
    --dry-run --limit 5 --target-type conference
```

### 5. Test Cron Script
```bash
bash platform/legacy/rig-linkedin-scripts/rig_conference_commenting.sh \
    --limit 5
```

## Acceptance Criteria
- [ ] All imports resolve without ModuleNotFoundError
- [ ] Engine discovers 3+ target posts in dry-run
- [ ] All generated comments have score >= 70.0
- [ ] No "the the" duplicates in comments
- [ ] No `{unfilled}` placeholders in output
- [ ] All comments pass anti-generic check (>= 40.0)
- [ ] Cron script produces log file in logs/
