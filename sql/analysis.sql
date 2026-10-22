-- Queries I used while exploring the data (run in DB Browser for SQLite or sqlite3)

-- 1. top 5 products by revenue
SELECT product_name, SUM(sales) AS revenue FROM v_sales GROUP BY product_id ORDER BY revenue DESC LIMIT 5;

-- 2. rank sub-categories by profit inside each category (window function)
SELECT category, sub_category, SUM(profit) AS profit,
       RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) AS rank_in_category
FROM v_sales GROUP BY category, sub_category;

-- 3. customers who bought in more than 3 different months (CTE)
WITH cm AS (SELECT customer_id, COUNT(DISTINCT strftime('%Y-%m', order_date)) AS months FROM v_sales GROUP BY 1)
SELECT * FROM cm WHERE months > 3 ORDER BY months DESC;

-- 4. running total of profit
SELECT month, profit, SUM(profit) OVER (ORDER BY month) AS running_profit
FROM (SELECT strftime('%Y-%m', order_date) AS month, SUM(profit) AS profit FROM v_sales GROUP BY 1);
