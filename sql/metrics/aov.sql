-- Average order value per variant. order_value is SUM(payment_value) per order,
-- already aggregated into experiment_frame.
SELECT
    variant,
    AVG(order_value) AS aov,
    COUNT(order_value) AS n
FROM experiment_frame
WHERE order_value IS NOT NULL
GROUP BY variant
ORDER BY variant;
