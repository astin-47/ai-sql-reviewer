-- Fictional schema: shop.customers(customer_id, region), shop.orders(order_id, customer_id, total_amount, status)
SELECT c.region, SUM(o.total_amount) AS revenue
FROM shop.customers c, shop.orders o
WHERE c.customer_id = o.customer_id
  AND o.status = 'shipped'
GROUP BY c.region
ORDER BY revenue DESC;
