-- One row per customer and brand: the first inquiry wins.
-- Repeat messages from the same person within the year are not new leads.
CREATE VIEW IF NOT EXISTS leads_dedup AS
WITH ranked AS (
    SELECT
        l.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id, brand
            ORDER BY created_at, lead_id
        ) AS rn
    FROM leads AS l
)
SELECT * FROM ranked WHERE rn = 1;
