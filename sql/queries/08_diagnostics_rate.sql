-- 08_diagnostics_rate.sql
-- Measures the proportion of patient visits requiring diagnostic imaging/labs versus those skipping Diagnostics

WITH DiagnosticsPresence AS (
    SELECT
        v.visit_id,
        CASE
            WHEN COUNT(CASE WHEN e.event_name = 'Diagnostics' THEN 1 END) > 0 THEN 1
            ELSE 0
        END AS had_diagnostics
    FROM visits v
    LEFT JOIN events e ON v.visit_id = e.visit_id
    GROUP BY v.visit_id
)
SELECT
    COUNT(*) AS total_visits,
    SUM(had_diagnostics) AS visits_with_diagnostics,
    COUNT(*) - SUM(had_diagnostics) AS visits_without_diagnostics,
    ROUND(100.0 * SUM(had_diagnostics) / COUNT(*), 2) AS diagnostics_usage_rate_pct,
    ROUND(100.0 * (COUNT(*) - SUM(had_diagnostics)) / COUNT(*), 2) AS diagnostics_skip_rate_pct
FROM DiagnosticsPresence;
