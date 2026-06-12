-- Credit card share of total payment value in the cohort window.
SELECT
    SUM(CASE WHEN op.payment_type = 'credit_card' THEN op.payment_value ELSE 0 END)
        / SUM(op.payment_value) AS credit_card_value_share
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end;
