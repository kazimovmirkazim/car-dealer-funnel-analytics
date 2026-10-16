-- Q4 sales against target, next to stock. A brand can hit 100% while one model is far behind.
WITH q4_sales AS (
    SELECT brand, model, COUNT(*) AS sold_q4
    FROM leads
    WHERE sold = 1 AND sale_date BETWEEN '2025-10-01' AND '2025-12-31'
    GROUP BY brand, model
)
SELECT
    s.brand,
    s.model,
    s.q4_target,
    COALESCE(q.sold_q4, 0)                                   AS sold_q4,
    ROUND(100.0 * COALESCE(q.sold_q4, 0) / s.q4_target, 0)  AS target_pct,
    s.stock_units,
    CASE
        WHEN 1.0 * COALESCE(q.sold_q4, 0) / s.q4_target < 0.7 AND s.stock_units >= 30
        THEN 'behind target, high stock'
        WHEN 1.0 * COALESCE(q.sold_q4, 0) / s.q4_target < 0.7
        THEN 'behind target'
        ELSE 'on track'
    END AS flag
FROM stock AS s
LEFT JOIN q4_sales AS q USING (brand, model)
ORDER BY target_pct;
