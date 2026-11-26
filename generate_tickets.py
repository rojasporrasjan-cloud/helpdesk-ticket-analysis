"""Generate a realistic, fully synthetic helpdesk ticket dataset in SQLite.

No real company or user data is used. The generator is seeded, so every run
produces the same data and the analysis results in the README are reproducible.

Usage:
    python generate_tickets.py            # 2,000 tickets -> data/tickets.db
    python generate_tickets.py --tickets 5000 --seed 7
"""
from __future__ import annotations

import argparse
import csv
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# category: (weight, typical resolution hours, chance of escalation to L2)
CATEGORIES = {
    "Password / Account lockout": (24, 0.4, 0.03),
    "Microsoft 365 / Outlook":    (18, 3.0, 0.15),
    "VPN / Remote access":        (12, 4.0, 0.25),
    "Hardware":                   (10, 18.0, 0.45),
    "Software install / license": (11, 6.0, 0.20),
    "Network / Wi-Fi":            (8, 5.0, 0.30),
    "Intune / Device enrollment": (7, 8.0, 0.35),
    "Printer":                    (6, 4.0, 0.20),
    "Access request":             (4, 10.0, 0.10),
}
PRIORITIES = {"P1 - Critical": 2, "P2 - High": 13, "P3 - Medium": 55, "P4 - Low": 30}
SLA_HOURS = {"P1 - Critical": 4, "P2 - High": 8, "P3 - Medium": 24, "P4 - Low": 72}
PRIORITY_SPEED = {"P1 - Critical": 0.35, "P2 - High": 0.6, "P3 - Medium": 1.0, "P4 - Low": 1.6}
CHANNELS = {"Phone": 40, "Chat": 30, "Email": 15, "Self-service portal": 15}
AGENTS = ["Agent A", "Agent B", "Agent C", "Agent D", "Agent E", "Agent F"]
AGENT_SKILL = {"Agent A": 0.8, "Agent B": 1.0, "Agent C": 1.25, "Agent D": 0.9, "Agent E": 1.1, "Agent F": 1.4}

SCHEMA = """
DROP TABLE IF EXISTS tickets;
CREATE TABLE tickets (
    ticket_id        TEXT PRIMARY KEY,
    opened_at        TEXT NOT NULL,
    resolved_at      TEXT NOT NULL,
    category         TEXT NOT NULL,
    priority         TEXT NOT NULL,
    channel          TEXT NOT NULL,
    agent            TEXT NOT NULL,
    escalated_to_l2  INTEGER NOT NULL,
    first_contact_resolution INTEGER NOT NULL,
    sla_hours        INTEGER NOT NULL,
    resolution_hours REAL NOT NULL,
    sla_met          INTEGER NOT NULL,
    csat             INTEGER            -- 1-5, NULL when the user did not answer the survey
);
"""


def weighted_choice(rng: random.Random, options: dict) -> str:
    keys = list(options)
    weights = [v[0] if isinstance(v, tuple) else v for v in options.values()]
    return rng.choices(keys, weights=weights, k=1)[0]


def business_hour_timestamp(rng: random.Random, start: datetime, days: int) -> datetime:
    """Random timestamp weighted toward weekdays and office hours (most tickets arrive 8:00-17:00)."""
    while True:
        day = start + timedelta(days=rng.randrange(days))
        if day.weekday() >= 5 and rng.random() < 0.8:
            continue  # far fewer tickets on weekends
        hour = int(rng.triangular(6, 20, 10))
        return day.replace(hour=hour, minute=rng.randrange(60), second=0)


def make_ticket(rng: random.Random, n: int, start: datetime, days: int) -> dict:
    category = weighted_choice(rng, CATEGORIES)
    _, base_hours, escalation_rate = CATEGORIES[category]
    priority = weighted_choice(rng, PRIORITIES)
    channel = weighted_choice(rng, CHANNELS)
    agent = rng.choice(AGENTS)

    escalated = rng.random() < escalation_rate
    hours = rng.lognormvariate(0, 0.6) * base_hours * PRIORITY_SPEED[priority] * AGENT_SKILL[agent]
    if escalated:
        hours += rng.uniform(4, 30)
    hours = round(max(hours, 0.1), 2)

    fcr = (not escalated) and hours < 1 and channel in ("Phone", "Chat")
    sla = SLA_HOURS[priority]
    sla_met = hours <= sla

    csat = None
    if rng.random() < 0.35:  # ~35% survey response rate
        score = 4.6 - (0.0 if sla_met else 1.3) - (0.4 if escalated else 0.0) + rng.gauss(0, 0.6)
        csat = int(min(5, max(1, round(score))))

    opened = business_hour_timestamp(rng, start, days)
    resolved = opened + timedelta(hours=hours)
    return {
        "ticket_id": f"INC{100000 + n}",
        "opened_at": opened.isoformat(sep=" "),
        "resolved_at": resolved.isoformat(sep=" ", timespec="seconds"),
        "category": category,
        "priority": priority,
        "channel": channel,
        "agent": agent,
        "escalated_to_l2": int(escalated),
        "first_contact_resolution": int(fcr),
        "sla_hours": sla,
        "resolution_hours": hours,
        "sla_met": int(sla_met),
        "csat": csat,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tickets", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", default="2026-01-01", help="first day of the period (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=181)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    start = datetime.fromisoformat(args.start)
    tickets = [make_ticket(rng, i, start, args.days) for i in range(1, args.tickets + 1)]
    tickets.sort(key=lambda t: t["opened_at"])

    DATA_DIR.mkdir(exist_ok=True)
    db_path = DATA_DIR / "tickets.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        cols = list(tickets[0])
        conn.executemany(
            f"INSERT INTO tickets ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            [tuple(t[c] for c in cols) for t in tickets],
        )

    csv_path = DATA_DIR / "tickets.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(tickets[0]))
        writer.writeheader()
        writer.writerows(tickets)

    print(f"Created {len(tickets)} synthetic tickets -> {db_path} and {csv_path}")


if __name__ == "__main__":
    main()
