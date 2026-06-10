-- Cohort orders in the stable window, with order_value = SUM(payment_value) per order.
-- Window bounds are passed as parameters ($start, $end) from src.constants.
SELECT
    o.order_id,
    c.customer_unique_id,
    o.order_status,
    p.order_value,
    o.order_purchase_timestamp
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN (
    SELECT order_id, SUM(payment_value) AS order_value
    FROM order_payments
    GROUP BY order_id
) p ON o.order_id = p.order_id
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end
ORDER BY o.order_id;
