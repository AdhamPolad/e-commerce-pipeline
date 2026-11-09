-- 1. Total sales value by product (headline demo query)
SELECT p.product_id, p.title, p.category,
       SUM(oi.quantity)                  AS units_sold,
       SUM(oi.quantity * oi.unit_price)  AS total_sales_value
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.title, p.category
ORDER BY total_sales_value DESC
LIMIT 10;

-- 2. Revenue by category
SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi JOIN products p USING (product_id)
GROUP BY p.category ORDER BY revenue DESC;

-- 3. Top customers
SELECT c.customer_id, c.full_name, c.country,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS spent
FROM customers c
JOIN orders o USING (customer_id)
JOIN order_items oi USING (order_id)
GROUP BY c.customer_id, c.full_name, c.country
ORDER BY spent DESC LIMIT 5;

-- 4. Monthly revenue
SELECT date_trunc('month', o.order_date)::date AS month,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM orders o JOIN order_items oi USING (order_id)
GROUP BY 1 ORDER BY 1;
