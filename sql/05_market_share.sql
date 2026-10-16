-- Monthly market share. The change is shown two ways on purpose:
-- percentage points (pp) and percent (%) are not the same thing.
-- January is left out: the data starts in January, so sales from December leads are missing.
WITH our_sales AS (
    SELECT SUBSTR(sale_date, 1, 7) AS month, COUNT(*) AS our_units
    FROM leads
    WHERE sold = 1 AND sale_date BETWEEN '2025-02-01' AND '2025-12-31'
    GROUP BY 1
),
share AS (
    SELECT
        m.month,
        o.our_units,
        m.market_units,
        100.0 * o.our_units / m.market_units AS share_pct
    FROM market AS m
    JOIN our_sales AS o USING (month)
)
SELECT
    month,
    our_units,
    market_units,
    ROUND(share_pct, 2)                                                   AS share_pct,
    ROUND(share_pct - LAG(share_pct) OVER (ORDER BY month), 2)            AS change_pp,
    ROUND(100.0 * (share_pct / LAG(share_pct) OVER (ORDER BY month) - 1), 1) AS change_pct
FROM share
ORDER BY month;
