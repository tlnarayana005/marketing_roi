# Power BI Dashboard Specification

## Pages

### Executive Overview
- KPI cards: total marketing spend, total revenue, overall ROI, conversion rate.
- Clustered bar: ROI and revenue by campaign channel.
- Line chart: monthly spend versus revenue.
- Table: campaign ranking with campaign ID, channel, spend, revenue, ROI, conversions.

### Customer Value
- Bar chart: revenue, conversions, and ROI by customer segment.
- Matrix: city by RFM segment with customer count and revenue.
- Scatter: customer frequency versus monetary value, colored by RFM segment.

## Model and measures

Relate `customers[customer_id]` 1-to-many `campaign_responses[customer_id]` and `campaigns[campaign_id]` 1-to-many `campaign_responses[campaign_id]`. Import `rfm_scores` on `customer_id`.

```DAX
Total Spend = SUM(campaigns[campaign_cost])
Total Revenue = SUM(campaign_responses[revenue_generated])
Conversions = SUM(campaign_responses[conversions])
Clicks = SUM(campaign_responses[clicks])
Conversion Rate = DIVIDE([Conversions], [Clicks])
CTR = DIVIDE([Clicks], SUM(campaign_responses[impressions]))
CAC = DIVIDE([Total Spend], [Conversions])
ROI = DIVIDE([Total Revenue] - [Total Spend], [Total Spend])
Revenue per Customer = DIVIDE([Total Revenue], DISTINCTCOUNT(campaign_responses[customer_id]))
AOV = DIVIDE([Total Revenue], [Conversions])
```

## Interactions and accessibility

Add slicers for campaign ID, channel, city, campaign date, and customer segment. Enable cross-highlighting from channel and segment visuals to the campaign table. Use descriptive titles, data labels on the KPI cards, percentage formatting for CTR/conversion rate/ROI, currency formatting for spend/revenue/CAC/AOV, and a color-blind-safe blue/teal/amber palette. Keep the campaign table sorted by ROI descending and add conditional formatting for negative ROI.
