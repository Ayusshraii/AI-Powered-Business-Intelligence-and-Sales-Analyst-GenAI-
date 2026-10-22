"""Fixed analytics queries (no AI involved). The agent reuses these for the 'why' questions."""
import pandas as pd
from .db import connect_ro


def run(sql, params=None):
    con = connect_ro()
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


def monthly_summary():
    # CTE + LAG window function for month over month change
    return run("""
        WITH m AS (
            SELECT strftime('%Y-%m', order_date) AS month,
                   SUM(sales) AS revenue, SUM(profit) AS profit,
                   AVG(discount) AS avg_discount
            FROM v_sales GROUP BY 1
        )
        SELECT month,
               ROUND(revenue, 2) AS revenue,
               ROUND(profit, 2) AS profit,
               ROUND(100.0 * profit / revenue, 2) AS margin_pct,
               ROUND(avg_discount * 100, 1) AS avg_discount_pct,
               ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                     / LAG(revenue) OVER (ORDER BY month), 1) AS revenue_mom_pct,
               ROUND(100.0 * (profit - LAG(profit) OVER (ORDER BY month))
                     / ABS(LAG(profit) OVER (ORDER BY month)), 1) AS profit_mom_pct
        FROM m ORDER BY month
    """)


def top_products(n=5):
    return run("""
        SELECT product_name, ROUND(SUM(sales), 2) AS revenue, ROUND(SUM(profit), 2) AS profit
        FROM v_sales GROUP BY product_id ORDER BY revenue DESC LIMIT ?
    """, (n,))


def category_margins():
    return run("""
        SELECT category, sub_category,
               ROUND(SUM(sales), 0) AS revenue, ROUND(SUM(profit), 0) AS profit,
               ROUND(100.0 * SUM(profit) / SUM(sales), 1) AS margin_pct
        FROM v_sales GROUP BY category, sub_category ORDER BY margin_pct
    """)


def risky_products(min_sales=500):
    # lots of sales but losing money or very thin margin
    return run("""
        SELECT product_name, category, ROUND(SUM(sales), 0) AS revenue,
               ROUND(SUM(profit), 0) AS profit,
               ROUND(100.0 * SUM(profit) / SUM(sales), 1) AS margin_pct,
               ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
        FROM v_sales GROUP BY product_id
        HAVING SUM(sales) >= ? AND (SUM(profit) < 0 OR 100.0 * SUM(profit) / SUM(sales) < 5)
        ORDER BY profit LIMIT 20
    """, (min_sales,))


def discount_bands():
    return run("""
        SELECT CASE WHEN discount = 0 THEN '0%'
                    WHEN discount <= 0.2 THEN '1-20%'
                    WHEN discount <= 0.4 THEN '21-40%'
                    ELSE '40%+' END AS discount_band,
               COUNT(*) AS line_items, ROUND(SUM(sales), 0) AS revenue,
               ROUND(SUM(profit), 0) AS profit,
               ROUND(100.0 * SUM(profit) / SUM(sales), 1) AS margin_pct
        FROM v_sales GROUP BY 1 ORDER BY MIN(discount)
    """)


def category_change(month):
    """Profit and discount by category for `month` vs the month before it."""
    prev = str(pd.Period(month, "M") - 1)
    return run("""
        WITH cur AS (
            SELECT category, SUM(sales) AS s, SUM(profit) AS p, AVG(discount) AS d
            FROM v_sales WHERE strftime('%Y-%m', order_date) = :cur GROUP BY category),
        prev AS (
            SELECT category, SUM(sales) AS s, SUM(profit) AS p, AVG(discount) AS d
            FROM v_sales WHERE strftime('%Y-%m', order_date) = :prev GROUP BY category)
        SELECT cur.category,
               ROUND(cur.s) AS revenue, ROUND(prev.s) AS prev_revenue,
               ROUND(cur.p) AS profit, ROUND(prev.p) AS prev_profit,
               ROUND(cur.p - prev.p) AS profit_change,
               ROUND(cur.d * 100, 1) AS discount_pct, ROUND(prev.d * 100, 1) AS prev_discount_pct
        FROM cur JOIN prev USING (category) ORDER BY profit_change
    """, {"cur": month, "prev": prev})
