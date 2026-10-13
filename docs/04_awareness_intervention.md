# Module 4 — Awareness Intervention & Repeat Measurement

Based on typical first-round patterns in the sample data (and replace with your live metrics after running `analyze_campaign.py`).

## Observed pattern (sample run)

Use values from `output/summary.json` after analysis. The intervention below assumes:

- Interaction (click) rate is non-trivial  
- Reporting rate is low relative to clicks  
- Finance / HR show higher susceptibility than IT  

## Intervention design (2 weeks)

### Week 1 — Just-in-time microlearning (15 min)

1. **Recognize** — Screenshots of *generic* red flags (mismatched domains, unexpected attachment urgency, “reset now” pressure). Do not reuse live attack kits.
2. **Verify** — Official channel checklist: ticket portal, known IT number, manager confirmation for money/data requests.
3. **Report** — One-click / forward-to-security workflow; celebrate reports in team standups (no shaming).

### Week 2 — Practice & policy

1. Tabletop: “Unexpected invoice” and “password reset” scenarios — learners choose report vs ignore vs escalate.
2. Publish a one-page **reporting runbook** on the intranet.
3. Managers brief teams on not punishing good-faith reports.

## Round 2 simulation (different scenario)

Keep the same measurement pipeline; change only the **scenario theme** so results are comparable but not memorized:

| | Round 1 | Round 2 |
|--|---------|---------|
| Theme | Account / access notice | Vendor / invoice notice |
| Primary risk signal taught | Lookalike login urgency | Payment / gift-card pressure |
| Same metrics | delivery, interaction, reporting, susceptibility | identical definitions |

Export the second CSV into `data/` and re-run:

```bash
python3 src/analyze_campaign.py \
  --input data/round2_campaign_events.csv \
  --output-dir output/round2
```

Compare `susceptibility_rate` and `reporting_rate` across `output/summary.json` and `output/round2/summary.json`.

## Expected outcome targets

| Metric | Direction after intervention |
|--------|------------------------------|
| Reporting rate | ↑ |
| Susceptibility rate | ↓ |
| Interaction rate | ↓ or stable with ↑ reporting among those who interact |

## Evaluation notes for CO mapping

- **CO1 / analysis** — Interpret rates and department breakdowns.  
- **CO3 / design** — Intervention tied to observed weaknesses.  
- **CO4 / evaluation** — Round 1 vs Round 2 comparison.  
- **CO5 / ethics & responsibility** — No credential collection; aggregate reporting.  
