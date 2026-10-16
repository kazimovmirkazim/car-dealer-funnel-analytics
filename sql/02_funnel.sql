-- Lead -> contacted -> showroom visit -> test drive -> sale, with step-to-step conversion.
WITH stages AS (
    SELECT 1 AS step, 'Lead'           AS stage, COUNT(*)        AS customers FROM leads_dedup
    UNION ALL SELECT 2, 'Contacted',      SUM(contacted)  FROM leads_dedup
    UNION ALL SELECT 3, 'Showroom visit', SUM(visited)    FROM leads_dedup
    UNION ALL SELECT 4, 'Test drive',     SUM(test_drive) FROM leads_dedup
    UNION ALL SELECT 5, 'Sale',           SUM(sold)       FROM leads_dedup
)
SELECT
    step,
    stage,
    customers,
    ROUND(100.0 * customers / FIRST_VALUE(customers) OVER (ORDER BY step), 1) AS pct_of_leads,
    ROUND(100.0 * customers / LAG(customers) OVER (ORDER BY step), 1)         AS pct_of_previous
FROM stages
ORDER BY step;
