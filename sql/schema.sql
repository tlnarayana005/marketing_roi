PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS rfm_scores;
DROP TABLE IF EXISTS campaign_responses;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    city TEXT NOT NULL,
    customer_segment TEXT NOT NULL,
    previous_purchases INTEGER NOT NULL,
    days_since_last_purchase INTEGER NOT NULL
);

CREATE TABLE campaigns (
    campaign_id TEXT PRIMARY KEY,
    campaign_channel TEXT NOT NULL,
    campaign_date DATE NOT NULL,
    campaign_cost REAL NOT NULL
);

CREATE TABLE campaign_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
    impressions INTEGER NOT NULL,
    clicks INTEGER NOT NULL,
    conversions INTEGER NOT NULL,
    revenue_generated REAL NOT NULL
);

CREATE TABLE rfm_scores (
    customer_id TEXT PRIMARY KEY REFERENCES customers(customer_id),
    recency INTEGER NOT NULL,
    frequency INTEGER NOT NULL,
    monetary REAL NOT NULL,
    rfm_score INTEGER NOT NULL,
    rfm_segment TEXT NOT NULL
);
