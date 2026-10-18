-- Fictional schema: shop.customers(customer_id, email, region), shop.orders(order_id, customer_id, order_date)
SELECT c.customer_id, c.email
FROM shop.customers c
WHERE c.customer_id NOT IN (SELECT o.customer_id FROM shop.orders o)
  AND c.email LIKE '%@example.com';
