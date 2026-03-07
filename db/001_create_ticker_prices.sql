CREATE SCHEMA IF NOT EXISTS market_data;

CREATE TABLE IF NOT EXISTS market_data.upload_task (
    id BIGSERIAL PRIMARY KEY,
    business_date DATE NOT NULL,
    data_source TEXT NOT NULL,    
    file_name TEXT NOT NULL,
    rows_succeeded INT NOT NULL,
    rows_failed INT NOT NULL,
    status_code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_data.raw_ticker_prices (
    id BIGSERIAL PRIMARY KEY,    
    business_date DATE NOT NULL,
    ticker TEXT NOT NULL,
    open_price NUMERIC NOT NULL,
    high_price NUMERIC NOT NULL,
    low_price NUMERIC NOT NULL,
    close_price NUMERIC NOT NULL,
    upload_task_id BIGINT NOT NULL REFERENCES market_data.upload_task(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_ticker_prices_date_ticker
    ON market_data.raw_ticker_prices (business_date, ticker);
