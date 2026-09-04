CREATE TABLE IF NOT EXISTS products (
 id SERIAL PRIMARY KEY, sku VARCHAR(50) UNIQUE NOT NULL, barcode VARCHAR(100) UNIQUE,
 name VARCHAR(200) NOT NULL, category VARCHAR(100), mrp NUMERIC(10,2) NOT NULL,
 current_price NUMERIC(10,2) NOT NULL, manufacture_date DATE, expiry_date DATE, created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS inventory (
 id SERIAL PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
 store_id VARCHAR(50) NOT NULL, stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
 updated_at TIMESTAMP DEFAULT NOW(), UNIQUE(product_id, store_id)
);
CREATE TABLE IF NOT EXISTS sales_history (
 id SERIAL PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
 store_id VARCHAR(50) NOT NULL, sale_date DATE NOT NULL, units_sold INTEGER NOT NULL CHECK(units_sold >= 0),
 price_sold NUMERIC(10,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS discount_recommendations (
 id SERIAL PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
 store_id VARCHAR(50) NOT NULL, predicted_demand NUMERIC(10,2), risk_score NUMERIC(5,4),
 risk_level VARCHAR(20), recommended_min_discount NUMERIC(5,2), recommended_max_discount NUMERIC(5,2),
 recommended_discount_pct NUMERIC(5,2), recommended_price NUMERIC(10,2),
 status VARCHAR(20) DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW(), decided_at TIMESTAMP, decided_by VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS discount_events (
 id SERIAL PRIMARY KEY, recommendation_id INTEGER REFERENCES discount_recommendations(id) ON DELETE CASCADE,
 discount_percentage NUMERIC(5,2) NOT NULL, original_price NUMERIC(10,2) NOT NULL,
 applied_price NUMERIC(10,2) NOT NULL, applied_at TIMESTAMP DEFAULT NOW(),
 units_sold_after INTEGER DEFAULT 0, revenue_recovered NUMERIC(12,2) DEFAULT 0
);
CREATE TABLE IF NOT EXISTS excel_sync_logs (
 id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL, store_id VARCHAR(50) NOT NULL,
 discount_percentage NUMERIC(5,2) NOT NULL, updated_price NUMERIC(10,2) NOT NULL,
 file_path VARCHAR(500), synced_at TIMESTAMP DEFAULT NOW(), success BOOLEAN DEFAULT TRUE
);
