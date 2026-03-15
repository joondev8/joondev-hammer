CREATE SCHEMA IF NOT EXISTS market_data;

CREATE TABLE IF NOT EXISTS market_data.upload_task (
    task_id BIGSERIAL PRIMARY KEY,
    business_date DATE NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key TEXT NOT NULL,
    data_source TEXT NOT NULL,   
    row_count INTEGER NOT NULL, -- Useful for verifying data integrity     
    rows_inserted INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED')),
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
    upload_task_id BIGINT NOT NULL REFERENCES market_data.upload_task(task_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_ticker_prices_date_ticker
    ON market_data.raw_ticker_prices (business_date, ticker);

CREATE OR REPLACE FUNCTION market_data.set_last_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_upload_task_set_last_updated_at
    ON market_data.upload_task;

CREATE TRIGGER trg_upload_task_set_last_updated_at
BEFORE UPDATE ON market_data.upload_task
FOR EACH ROW
EXECUTE FUNCTION market_data.set_last_updated_at();

DROP TRIGGER IF EXISTS trg_raw_ticker_prices_set_last_updated_at
    ON market_data.raw_ticker_prices;

CREATE TRIGGER trg_raw_ticker_prices_set_last_updated_at
BEFORE UPDATE ON market_data.raw_ticker_prices
FOR EACH ROW
EXECUTE FUNCTION market_data.set_last_updated_at();
