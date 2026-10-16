-- How duplicates distort the numbers: raw rows vs unique customers per channel.
WITH raw AS (
    SELECT channel, COUNT(*) AS raw_leads, SUM(sold) AS sales
    FROM leads GROUP BY channel
),
dedup AS (
    SELECT channel, COUNT(*) AS unique_leads
    FROM leads_dedup GROUP BY channel
)
SELECT
    r.channel,
    r.raw_leads,
    d.unique_leads,
    ROUND(100.0 * (r.raw_leads - d.unique_leads) / r.raw_leads, 1) AS duplicate_pct,
    ROUND(100.0 * r.sales / r.raw_leads, 2)    AS conversion_raw_pct,
    ROUND(100.0 * r.sales / d.unique_leads, 2) AS conversion_dedup_pct
FROM raw AS r
JOIN dedup AS d USING (channel)
ORDER BY duplicate_pct DESC;
