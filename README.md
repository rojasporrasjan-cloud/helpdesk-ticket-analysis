# Helpdesk Ticket Analysis (SQL + Python)

KPI analysis of Service Desk tickets with SQL: SLA compliance, first-contact resolution, escalations,
volume by category, channel and hour, and which ticket types are worth automating.

The data is **100% synthetic**, created by a seeded generator that mimics what I saw in real Service Desk work
(password resets dominate the volume, hardware breaches SLA, P1s are rare but hard). No real company or user data is used.

## What's inside

| File | Purpose |
|---|---|
| `generate_tickets.py` | Creates 2,000 realistic tickets in SQLite (`data/tickets.db`) and CSV (`data/tickets.csv`) |
| `queries.sql` | 8 KPI queries, readable on their own in any SQL client |
| `analyze.py` | Runs every query, prints the results and writes `report.md` and `report.html` |

Only the Python standard library is used (`sqlite3`, `csv`, `random`), so there is nothing to install.

## Run it

```bash
python generate_tickets.py      # builds data/tickets.db
python analyze.py               # prints KPIs, writes report.md + report.html
```

## Key findings (seed 42, Jan–Jun 2026, 2,000 tickets)

| KPI | Value |
|---|---|
| SLA met | 88.4% |
| First-contact resolution | 14.9% |
| Escalated to L2 | 19.8% |
| Average resolution time | 10.7 h |
| Average CSAT (1–5) | 4.37 (35.1% survey response) |

1. **P1 tickets miss SLA almost half the time (54.3% met, target 4 h).** P1 is only 2.3% of volume, so a dedicated
   on-call path for P1 would lift the most critical metric without much cost.
2. **Hardware is the SLA problem: 52.5% met, 33.5 h average, 43.9% escalated.** Keeping spare devices or a faster
   L2 hand-off would help more than anything on the L1 side.
3. **Password / account lockouts are 23.9% of all tickets and take under 1 hour.** They are the top candidate for a
   self-service password reset portal, which would free roughly a quarter of the team's queue.
4. **Volume peaks from 08:00 to 12:00** (48% of tickets arrive in those four hours), so the morning shift needs
   the most staff.
5. **Phone and chat are the only channels with first-contact resolution (about 21%)**; email and portal tickets always
   need a follow-up.

See the full output in [`report.md`](report.md).

## Example query

```sql
-- Quick, high-volume, rarely escalated categories = best candidates for self-service
SELECT category,
       COUNT(*)                               AS tickets,
       ROUND(AVG(resolution_hours), 2)        AS avg_resolution_h,
       ROUND(100.0 * AVG(escalated_to_l2), 1) AS escalation_pct
FROM tickets
GROUP BY category
HAVING AVG(escalated_to_l2) < 0.2 AND COUNT(*) >= 150
ORDER BY tickets DESC;
```

## Skills shown

SQL (aggregations, `GROUP BY` / `HAVING`, subqueries, date functions) · SQLite · Python · ITSM metrics (SLA, FCR,
escalation rate, CSAT) · turning data into recommendations.

## How I built it

Built with the help of AI (Claude) for the code, with the metrics, scenarios and conclusions based on my
3.5 years of Service Desk experience at Kyndryl and Blue Mantis.

## License

MIT
