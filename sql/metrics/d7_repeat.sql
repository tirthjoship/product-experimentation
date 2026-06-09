-- Share of persons whose 2nd order falls within 7 days of their 1st, per variant.
WITH firsts AS (
    SELECT customer_unique_id, variant, MIN(order_purchase_timestamp) AS first_ts
    FROM experiment_frame
    GROUP BY customer_unique_id, variant
),
flags AS (
    SELECT
        f.customer_unique_id,
        f.variant,
        MAX(CASE
                WHEN e.order_purchase_timestamp > f.first_ts
                 AND e.order_purchase_timestamp <= f.first_ts + INTERVAL 7 DAY
                THEN 1 ELSE 0
            END) AS repeated
    FROM firsts f
    JOIN experiment_frame e
      ON e.customer_unique_id = f.customer_unique_id
     AND e.variant = f.variant
    GROUP BY f.customer_unique_id, f.variant
)
SELECT variant, AVG(repeated) AS d7_repeat, COUNT(*) AS n_persons
FROM flags
GROUP BY variant
ORDER BY variant;
