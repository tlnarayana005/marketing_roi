-- Run against data/marketing_roi.db. KPI ratios use NULLIF to avoid divide-by-zero.

-- 1. Overall KPIs
SELECT SUM(DISTINCT c.campaign_cost) AS spend, SUM(r.revenue_generated) AS revenue,
       (SUM(r.revenue_generated) - SUM(DISTINCT c.campaign_cost)) / NULLIF(SUM(DISTINCT c.campaign_cost), 0) AS roi,
       SUM(r.conversions) / NULLIF(SUM(r.clicks), 0) AS conversion_rate
FROM campaigns c JOIN campaign_responses r USING (campaign_id);

-- 2. Channel performance
SELECT c.campaign_channel, SUM(DISTINCT c.campaign_cost) AS spend, SUM(r.revenue_generated) AS revenue,
       (SUM(r.revenue_generated) - SUM(DISTINCT c.campaign_cost)) / NULLIF(SUM(DISTINCT c.campaign_cost), 0) AS roi
FROM campaigns c JOIN campaign_responses r USING (campaign_id)
GROUP BY c.campaign_channel ORDER BY roi DESC;

-- 3. Campaign ranking with a window function
WITH campaign_kpis AS (
    SELECT c.campaign_id, c.campaign_channel, SUM(DISTINCT c.campaign_cost) spend, SUM(r.revenue_generated) revenue
    FROM campaigns c JOIN campaign_responses r USING (campaign_id) GROUP BY c.campaign_id, c.campaign_channel
)
SELECT *, RANK() OVER (ORDER BY (revenue - spend) / NULLIF(spend, 0) DESC) AS roi_rank FROM campaign_kpis;

-- 4. Segment performance
SELECT cu.customer_segment, COUNT(DISTINCT cu.customer_id) customers, SUM(r.revenue_generated) revenue,
       AVG(r.revenue_generated) AS revenue_per_response
FROM customers cu JOIN campaign_responses r USING (customer_id)
GROUP BY cu.customer_segment ORDER BY revenue DESC;

-- 5. Monthly trend using a date function
SELECT strftime('%Y-%m', c.campaign_date) AS month, SUM(DISTINCT c.campaign_cost) spend, SUM(r.revenue_generated) revenue
FROM campaigns c JOIN campaign_responses r USING (campaign_id) GROUP BY month ORDER BY month;

-- 6. City and channel cross-tab
SELECT cu.city, c.campaign_channel, SUM(r.revenue_generated) revenue, SUM(r.conversions) conversions
FROM customers cu JOIN campaign_responses r USING (customer_id) JOIN campaigns c USING (campaign_id)
GROUP BY cu.city, c.campaign_channel ORDER BY revenue DESC;

-- 7. Poor-return campaigns (CASE expression)
SELECT c.campaign_id, c.campaign_channel,
    (SUM(r.revenue_generated) - SUM(DISTINCT c.campaign_cost)) / NULLIF(SUM(DISTINCT c.campaign_cost), 0) roi,
    CASE WHEN (SUM(r.revenue_generated) - SUM(DISTINCT c.campaign_cost)) / NULLIF(SUM(DISTINCT c.campaign_cost), 0) < 1 THEN 'Review or reduce' ELSE 'Scale candidate' END AS action
FROM campaigns c JOIN campaign_responses r USING (campaign_id) GROUP BY c.campaign_id, c.campaign_channel;

-- 8. High-value RFM customers
SELECT cu.customer_id, cu.city, f.rfm_score, f.rfm_segment, f.monetary
FROM customers cu JOIN rfm_scores f USING (customer_id) WHERE f.rfm_segment = 'Champions' ORDER BY f.monetary DESC;

-- 9. Channel conversion funnel
SELECT c.campaign_channel, SUM(r.impressions) impressions, SUM(r.clicks) clicks, SUM(r.conversions) conversions,
       SUM(r.clicks) * 1.0 / NULLIF(SUM(r.impressions), 0) ctr,
       SUM(r.conversions) * 1.0 / NULLIF(SUM(r.clicks), 0) conversion_rate
FROM campaigns c JOIN campaign_responses r USING (campaign_id) GROUP BY c.campaign_channel;

-- 10. Above-average campaign revenue (subquery)
SELECT c.campaign_id, SUM(r.revenue_generated) revenue
FROM campaigns c JOIN campaign_responses r USING (campaign_id)
GROUP BY c.campaign_id HAVING revenue > (SELECT AVG(campaign_revenue) FROM (SELECT SUM(revenue_generated) campaign_revenue FROM campaign_responses GROUP BY campaign_id));

-- 11. Loyal customer response economics
SELECT SUM(r.revenue_generated) / NULLIF(SUM(r.conversions), 0) AS loyal_aov
FROM customers cu JOIN campaign_responses r USING (customer_id) WHERE cu.customer_segment = 'Loyal';

-- 12. Top campaign per channel using ROW_NUMBER
WITH ranked AS (
    SELECT c.campaign_channel, c.campaign_id, SUM(r.revenue_generated) revenue,
           ROW_NUMBER() OVER (PARTITION BY c.campaign_channel ORDER BY SUM(r.revenue_generated) DESC) AS row_num
    FROM campaigns c JOIN campaign_responses r USING (campaign_id) GROUP BY c.campaign_channel, c.campaign_id
)
SELECT * FROM ranked WHERE row_num = 1;

-- 13. Customers with no conversion
SELECT DISTINCT cu.customer_id, cu.city FROM customers cu JOIN campaign_responses r USING (customer_id) WHERE r.conversions = 0;

-- 14. RFM segment mix by city
SELECT cu.city, f.rfm_segment, COUNT(*) customers FROM customers cu JOIN rfm_scores f USING (customer_id)
GROUP BY cu.city, f.rfm_segment ORDER BY cu.city, customers DESC;

-- 15. Running monthly revenue
WITH monthly AS (
    SELECT strftime('%Y-%m', c.campaign_date) month, SUM(r.revenue_generated) revenue
    FROM campaigns c JOIN campaign_responses r USING (campaign_id) GROUP BY month
)
SELECT month, revenue, SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
FROM monthly ORDER BY month;
