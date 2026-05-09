    CREATE SCHEMA IF NOT EXISTS security_master;

    CREATE TABLE IF NOT EXISTS security_master.asset_equity (
        id BIGSERIAL PRIMARY KEY,    
        name TEXT NOT NULL,
        country_of_incorporation TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS security_master.asset_equity_ticker (
        ticker_id BIGSERIAL PRIMARY KEY,    
        asset_equity_id BIGINT NOT NULL REFERENCES security_master.asset_equity(id) ON DELETE CASCADE,
        ticker TEXT NOT NULL,
        effective_date DATE NOT NULL,
        expiry_date DATE,        
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_asset_equity_ticker_effective_date
        ON security_master.asset_equity_ticker (ticker, effective_date);

    CREATE INDEX IF NOT EXISTS idx_asset_equity_ticker_expiry_date
        ON security_master.asset_equity_ticker (ticker, expiry_date);        