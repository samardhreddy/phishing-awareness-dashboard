# Phishing Awareness — Detection & Measurement Dashboard

Academic deliverable for an **authorized** security-awareness program. This repo covers **ethical scope**, **campaign measurement**, a **detection dashboard**, and an **awareness intervention** plan.

It does **not** include phishing lure content, credential-harvesting pages, or attack-tool setup. Use only synthetic or instructor-provided simulation exports.

## What's included

| Module | Deliverable |
|--------|-------------|
| 1 – Campaign design (ethics) | `docs/01_scope_and_ethics.md` |
| 3 – Measurement | `src/analyze_campaign.py` + `data/sample_campaign_events.csv` |
| 4 – Defense | `docs/04_awareness_intervention.md` |
| Dashboard | Open `output/dashboard.html` after running the analyzer |

## Quick start

```bash
cd ~/Projects/phishing-awareness-dashboard
python3 src/analyze_campaign.py --input data/sample_campaign_events.csv --output-dir output
open output/dashboard.html   # macOS
```

Optional: point `--input` at your own CSV (same columns as the sample).

## Metrics (definitions)

All rates use **delivered** emails as the denominator unless noted.

| Metric | Formula |
|--------|---------|
| Delivery rate | delivered ÷ targeted |
| Interaction rate | clicked ÷ delivered |
| Reporting rate | reported ÷ delivered |
| Susceptibility rate | risky_action ÷ delivered |

`risky_action` = clicked a tracked link **or** completed a mock “submit” event on a non-credential training page (no real passwords stored).

## CSV schema

```text
target_id,email,department,campaign_id,campaign_name,event,timestamp
```

Allowed `event` values: `targeted`, `delivered`, `opened`, `clicked`, `reported`, `risky_submit`.

## Ethics reminder

- Isolated lab / authorized targets only  
- No real credentials collected or stored  
- Aggregate reporting preferred over naming individuals in shared decks  
- Clear opt-out / escalation path for distress or abuse reports  
