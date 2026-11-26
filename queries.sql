-- Helpdesk KPI queries (SQLite).
-- Each query starts with a "-- name:" line so analyze.py can run them one by one.
-- They also work as-is in DB Browser for SQLite or any SQL client.

-- name: overall_kpis
-- The numbers a Service Desk manager looks at first.
SELECT
    COUNT(*)                                              AS tickets,
    ROUND(100.0 * AVG(sla_met), 1)                        AS sla_met_pct,
    ROUND(100.0 * AVG(first_contact_resolution), 1)       AS fcr_pct,
    ROUND(100.0 * AVG(escalated_to_l2), 1)                AS escalation_pct,
    ROUND(AVG(resolution_hours), 1)                       AS avg_resolution_h,
    ROUND(AVG(csat), 2)                                   AS avg_csat,
    ROUND(100.0 * COUNT(csat) / COUNT(*), 1)              AS survey_response_pct
FROM tickets;

-- name: sla_by_priority
-- Is the SLA being met where it matters most?
SELECT
    priority,
    sla_hours                                             AS sla_target_h,
    COUNT(*)                                              AS tickets,
    ROUND(100.0 * AVG(sla_met), 1)                        AS sla_met_pct,
    ROUND(AVG(resolution_hours), 1)                       AS avg_resolution_h
FROM tickets
GROUP BY priority, sla_hours
ORDER BY priority;

-- name: top_categories
-- Where the volume comes from, and which categories breach SLA most.
SELECT
    category,
    COUNT(*)                                              AS tickets,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM tickets), 1) AS share_pct,
    ROUND(100.0 * AVG(sla_met), 1)                        AS sla_met_pct,
    ROUND(100.0 * AVG(escalated_to_l2), 1)                AS escalation_pct,
    ROUND(AVG(resolution_hours), 1)                       AS avg_resolution_h
FROM tickets
GROUP BY category
ORDER BY tickets DESC;

-- name: monthly_trend
-- Volume and SLA month by month.
SELECT
    strftime('%Y-%m', opened_at)                          AS month,
    COUNT(*)                                              AS tickets,
    ROUND(100.0 * AVG(sla_met), 1)                        AS sla_met_pct,
    ROUND(AVG(csat), 2)                                   AS avg_csat
FROM tickets
GROUP BY month
ORDER BY month;

-- name: busiest_hours
-- When tickets arrive: helps plan shifts and staffing.
SELECT
    CAST(strftime('%H', opened_at) AS INTEGER)            AS hour_of_day,
    COUNT(*)                                              AS tickets
FROM tickets
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- name: channel_performance
-- Which contact channel resolves fastest and on first contact.
SELECT
    channel,
    COUNT(*)                                              AS tickets,
    ROUND(100.0 * AVG(first_contact_resolution), 1)       AS fcr_pct,
    ROUND(AVG(resolution_hours), 1)                       AS avg_resolution_h,
    ROUND(AVG(csat), 2)                                   AS avg_csat
FROM tickets
GROUP BY channel
ORDER BY tickets DESC;

-- name: agent_performance
-- Per-agent view for coaching (agents are anonymized).
SELECT
    agent,
    COUNT(*)                                              AS tickets,
    ROUND(100.0 * AVG(sla_met), 1)                        AS sla_met_pct,
    ROUND(AVG(resolution_hours), 1)                       AS avg_resolution_h,
    ROUND(AVG(csat), 2)                                   AS avg_csat
FROM tickets
GROUP BY agent
ORDER BY sla_met_pct DESC;

-- name: self_service_candidates
-- Quick, high-volume, rarely escalated categories = best candidates for
-- self-service or automation (knowledge-base articles, password reset portal, scripts).
SELECT
    category,
    COUNT(*)                                              AS tickets,
    ROUND(AVG(resolution_hours), 2)                       AS avg_resolution_h,
    ROUND(100.0 * AVG(escalated_to_l2), 1)                AS escalation_pct
FROM tickets
GROUP BY category
HAVING AVG(escalated_to_l2) < 0.2 AND COUNT(*) >= 150
ORDER BY tickets DESC;
