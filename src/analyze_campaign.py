#!/usr/bin/env python3
"""Process authorized phishing-simulation event CSVs and emit metrics + dashboard.

No credentials are expected or stored. Events are behavioral flags only.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Set


VALID_EVENTS = {
    "targeted",
    "delivered",
    "opened",
    "clicked",
    "reported",
    "risky_submit",
}


@dataclass
class Rates:
    targeted: int
    delivered: int
    opened: int
    clicked: int
    reported: int
    risky_submit: int
    delivery_rate: float
    interaction_rate: float
    reporting_rate: float
    susceptibility_rate: float


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def load_events(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {
            "target_id",
            "email",
            "department",
            "campaign_id",
            "campaign_name",
            "event",
            "timestamp",
        }
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            missing = required - set(reader.fieldnames or [])
            raise SystemExit(f"CSV missing columns: {sorted(missing)}")

        rows: List[dict] = []
        for i, row in enumerate(reader, start=2):
            event = (row.get("event") or "").strip().lower()
            if event not in VALID_EVENTS:
                raise SystemExit(f"Line {i}: invalid event '{row.get('event')}'")
            row["event"] = event
            rows.append(row)
        return rows


def unique_targets(rows: Iterable[dict], event: str) -> Set[str]:
    return {r["target_id"] for r in rows if r["event"] == event}


def compute_rates(rows: List[dict]) -> Rates:
    targeted = unique_targets(rows, "targeted")
    delivered = unique_targets(rows, "delivered")
    opened = unique_targets(rows, "opened")
    clicked = unique_targets(rows, "clicked")
    reported = unique_targets(rows, "reported")
    risky = unique_targets(rows, "risky_submit")

    # Susceptibility: clicked OR mock submit (still no credentials).
    susceptible = clicked | risky
    n_delivered = len(delivered)

    return Rates(
        targeted=len(targeted),
        delivered=n_delivered,
        opened=len(opened),
        clicked=len(clicked),
        reported=len(reported),
        risky_submit=len(risky),
        delivery_rate=_rate(n_delivered, len(targeted)),
        interaction_rate=_rate(len(clicked), n_delivered),
        reporting_rate=_rate(len(reported), n_delivered),
        susceptibility_rate=_rate(len(susceptible), n_delivered),
    )


def department_breakdown(rows: List[dict]) -> Dict[str, dict]:
    by_dept: DefaultDict[str, List[dict]] = defaultdict(list)
    for row in rows:
        by_dept[row["department"] or "Unknown"].append(row)

    out: Dict[str, dict] = {}
    for dept, dept_rows in sorted(by_dept.items()):
        rates = compute_rates(dept_rows)
        out[dept] = asdict(rates)
    return out


def campaign_meta(rows: List[dict]) -> dict:
    if not rows:
        return {"campaign_id": None, "campaign_name": None}
    return {
        "campaign_id": rows[0]["campaign_id"],
        "campaign_name": rows[0]["campaign_name"],
    }


def render_dashboard(summary: dict, output_path: Path) -> None:
    rates = summary["rates"]
    depts = summary["by_department"]

    def pct(x: float) -> str:
        return f"{x * 100:.1f}%"

    cards = [
        ("Delivery rate", pct(rates["delivery_rate"]), f"{rates['delivered']} / {rates['targeted']}"),
        ("Interaction rate", pct(rates["interaction_rate"]), f"{rates['clicked']} clicked / delivered"),
        ("Reporting rate", pct(rates["reporting_rate"]), f"{rates['reported']} reported / delivered"),
        (
            "Susceptibility rate",
            pct(rates["susceptibility_rate"]),
            "clicked or mock submit / delivered",
        ),
    ]

    card_html = "\n".join(
        f"""
        <article class="card">
          <h2>{escape(title)}</h2>
          <p class="value">{escape(value)}</p>
          <p class="detail">{escape(detail)}</p>
        </article>
        """
        for title, value, detail in cards
    )

    max_sus = max((d["susceptibility_rate"] for d in depts.values()), default=0) or 1
    rows_html = []
    for name, d in depts.items():
        width = max(4, int(d["susceptibility_rate"] / max_sus * 100))
        rows_html.append(
            f"""
            <tr>
              <td>{escape(name)}</td>
              <td>{d['delivered']}</td>
              <td>{pct(d['interaction_rate'])}</td>
              <td>{pct(d['reporting_rate'])}</td>
              <td>
                <div class="bar-wrap">
                  <div class="bar" style="width:{width}%"></div>
                  <span>{pct(d['susceptibility_rate'])}</span>
                </div>
              </td>
            </tr>
            """
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Awareness Campaign Detection Dashboard</title>
  <style>
    :root {{
      --bg: #0f1714;
      --panel: #18241f;
      --ink: #e7f2ec;
      --muted: #9bb5a8;
      --accent: #3ecf8e;
      --warn: #e6b35a;
      --line: #2a3b33;
      --font: "IBM Plex Sans", "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font);
      color: var(--ink);
      background:
        radial-gradient(1200px 600px at 10% -10%, #1d3a2e 0%, transparent 55%),
        radial-gradient(900px 500px at 100% 0%, #243528 0%, transparent 40%),
        var(--bg);
      min-height: 100vh;
    }}
    main {{ max-width: 960px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
    h1 {{ font-size: clamp(1.6rem, 3vw, 2.2rem); margin: 0 0 0.35rem; letter-spacing: -0.02em; }}
    .sub {{ color: var(--muted); margin: 0 0 1.75rem; line-height: 1.5; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }}
    .card {{
      background: color-mix(in srgb, var(--panel) 88%, black);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 1rem 1.1rem 1.15rem;
    }}
    .card h2 {{ margin: 0; font-size: 0.85rem; color: var(--muted); font-weight: 600; }}
    .value {{ margin: 0.45rem 0 0.2rem; font-size: 1.85rem; font-weight: 700; color: var(--accent); }}
    .detail {{ margin: 0; font-size: 0.8rem; color: var(--muted); }}
    section {{ margin-top: 2rem; }}
    section h2 {{ font-size: 1.1rem; margin: 0 0 0.75rem; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 14px; overflow: hidden; border: 1px solid var(--line); }}
    th, td {{ text-align: left; padding: 0.75rem 0.9rem; border-bottom: 1px solid var(--line); font-size: 0.92rem; }}
    th {{ color: var(--muted); font-weight: 600; background: #14201b; }}
    tr:last-child td {{ border-bottom: none; }}
    .bar-wrap {{ display: flex; align-items: center; gap: 0.5rem; }}
    .bar {{ height: 8px; background: var(--warn); border-radius: 99px; min-width: 4px; }}
    .note {{
      margin-top: 1.5rem; padding: 1rem 1.1rem; border-left: 3px solid var(--accent);
      background: #14201b; color: var(--muted); font-size: 0.9rem; line-height: 1.45;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Detection & measurement dashboard</h1>
    <p class="sub">
      Campaign <strong>{escape(str(summary['campaign']['campaign_name']))}</strong>
      ({escape(str(summary['campaign']['campaign_id']))}) —
      aggregate view only; no credentials stored.
    </p>
    <div class="grid">
      {card_html}
    </div>
    <section>
      <h2>By department</h2>
      <table>
        <thead>
          <tr>
            <th>Department</th>
            <th>Delivered</th>
            <th>Interaction</th>
            <th>Reporting</th>
            <th>Susceptibility</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </section>
    <p class="note">
      Use these rates to prioritize awareness topics (Module 4). After training,
      re-run the analyzer on the round-2 export and compare reporting ↑ and susceptibility ↓.
    </p>
  </main>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize awareness-campaign event CSV")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/sample_campaign_events.csv"),
        help="Path to campaign events CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for summary.json and dashboard.html",
    )
    args = parser.parse_args()

    rows = load_events(args.input)
    rates = compute_rates(rows)
    summary = {
        "campaign": campaign_meta(rows),
        "source_file": str(args.input),
        "rates": asdict(rates),
        "by_department": department_breakdown(rows),
        "definitions": {
            "delivery_rate": "delivered / targeted",
            "interaction_rate": "clicked / delivered",
            "reporting_rate": "reported / delivered",
            "susceptibility_rate": "(clicked ∪ risky_submit) / delivered",
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    dashboard_path = args.output_dir / "dashboard.html"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    render_dashboard(summary, dashboard_path)

    print("Campaign summary")
    print(f"  Delivery rate:       {rates.delivery_rate:.2%}")
    print(f"  Interaction rate:    {rates.interaction_rate:.2%}")
    print(f"  Reporting rate:      {rates.reporting_rate:.2%}")
    print(f"  Susceptibility rate: {rates.susceptibility_rate:.2%}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {dashboard_path}")


if __name__ == "__main__":
    main()
