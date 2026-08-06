# Template Placeholder Hygiene

## Problem: Article Duplication
When a template starts with an article ("the {value}") and the selected
value ALSO starts with "the", the result is "the the value".

### Bad (leads to "the the"):
```python
templates = ["the {missing_layer} rarely gets airtime"]
replacements = {
    "{missing_layer}": "the operational layer between tool and action",
}
# Result: "the the operational layer between tool and action rarely gets airtime"
```

### Good:
```python
templates = ["the {missing_layer} rarely gets airtime"]
replacements = {
    "{missing_layer}": "operational layer between tool and action",
}
# Result: "the operational layer between tool and action rarely gets airtime"
```

## Rule: Audit All Placeholders
Every placeholder used in COMMENT_BANK templates MUST appear in the
`replacements` dict in `_fill_comment_template`. If a placeholder is
missing, it stays as a literal `{key}` string in the output.

### Audit Method
1. Grep all templates for `{placeholder}` patterns
2. Check each appears in the replacements dict
3. For each value, ensure it doesn't start with an article if the template
   already provides that article contextually

### Placeholders in 7 Hook Types
| Hook Type       | Placeholders Used                          |
|-----------------|--------------------------------------------|
| announcement    | {conference}, {topic}, {vertical}          |
| session         | {topic}, {client_count}, {common_approach}, {rig_insight}, {speaker} |
| speaker         | {speaker}, {topic}, {vertical}, {client_count}, {data_point}, {finding} |
| attendee        | {topic}, {context}, {event_type}, {emergent_theme}, {observation} |
| sponsor         | {conference}, {specific_stat}, {specific_metric}, {technology_gap} |
| afterparty      | {conference}, {topic}, {common_thread}, {emergent_theme}, {insight} |
| individual_post | {speaker}, {topic}, {vertical}, {contrarian_data}, {client_count}, {missing_dimension}, {specific_factor} |

### Missing From Replacements (FIXED)
- `{common_thread}` — added
- `{missing_dimension}` — added
- `{contrarian_data}` — already present, fixed values to not start with "the"
- `{observation}`, `{context}`, `{insight}`, `{specific_stat}`, `{specific_metric}`, `{technology_gap}`, `{specific_detail}` — already present, fixed values
