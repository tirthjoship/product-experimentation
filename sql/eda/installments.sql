-- Per-order installment buckets over the cohort window: an order's installment level is
-- MAX(payment_installments) across its payment rows; order_value = SUM(payment_value).
-- Descriptive stats only (motivates the installment-expansion hypothesis; NOT an effect estimate).
WITH per_order AS (
    SELECT
        op.order_id,
        SUM(op.payment_value) AS order_value,
        MAX(op.payment_installments) AS max_installments
    FROM order_payments op
    JOIN orders o ON op.order_id = o.order_id
    WHERE o.order_purchase_timestamp >= $start
      AND o.order_purchase_timestamp <  $end
    GROUP BY op.order_id
)
SELECT
    CASE
        WHEN max_installments <= 1 THEN '1'
        WHEN max_installments <= 3 THEN '2-3'
        WHEN max_installments <= 6 THEN '4-6'
        ELSE '7+'
    END AS bucket,
    COUNT(*) AS n_orders,
    AVG(order_value) AS aov
FROM per_order
GROUP BY 1
ORDER BY 1;
