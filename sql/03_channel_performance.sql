-- Volume and conversion side by side: the channel with the most leads
-- is not always the one with the most buyers.
SELECT
    channel,
    COUNT(*)                                   AS leads,
    SUM(visited)                               AS visits,
    SUM(sold)                                  AS sales,
    ROUND(100.0 * SUM(visited) / COUNT(*), 1)  AS visit_rate_pct,
    ROUND(100.0 * SUM(sold) / COUNT(*), 1)     AS lead_to_sale_pct,
    ROUND(100.0 * SUM(sold) / SUM(SUM(sold)) OVER (), 1) AS share_of_sales_pct
FROM leads_dedup
GROUP BY channel
ORDER BY leads DESC;
