-- Delivered rate per variant. Runs on the registered experiment_frame relation.
SELECT
    variant,
    AVG(CASE WHEN order_status = 'delivered' THEN 1.0 ELSE 0.0 END) AS conversion,
    COUNT(*) AS n
FROM experiment_frame
GROUP BY variant
ORDER BY variant;
