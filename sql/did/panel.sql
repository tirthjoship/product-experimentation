-- State × ISO-week DiD panel (spec §10). Aggregation only; assignment, donut filter,
-- and post-period blinding live in src/did/panel.py. ORDER BY pinned: the bootstrap
-- determinism incident (Phase F) taught us never to rely on engine row order.
SELECT
    c.customer_state,
    DATE_TRUNC('week', o.order_purchase_timestamp) AS week,
    COUNT(*) AS n_orders,
    AVG(
        CASE
            WHEN o.order_status = 'delivered'
            THEN date_diff(
                'day',
                o.order_purchase_timestamp,
                TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP)
            )
        END
    ) AS delivery_days
FROM orders o
JOIN customers c USING (customer_id)
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end
GROUP BY 1, 2
ORDER BY 1, 2;
