-- Fictional schema: shop.orders(order_id, customer_id, order_date, status, total_amount)
SELECT *
FROM shop.orders
WHERE DATE(order_date) = '2026-01-01';
