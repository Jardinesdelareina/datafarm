last_price = "SELECT price FROM market_stream ORDER BY time DESC LIMIT 1"
min_price_range = "SELECT MIN(price) FROM market_stream WHERE TO_TIMESTAMP(time, 'YYYY-MM-DD HH24:MI:SS') > CAST(NOW() - INTERVAL '1 HOUR' AS TIMESTAMP)"
max_price_range = "SELECT MAX(price) FROM market_stream WHERE TO_TIMESTAMP(time, 'YYYY-MM-DD HH24:MI:SS') > CAST(NOW() - INTERVAL '1 HOUR' AS TIMESTAMP)"
drop_data = "DELETE FROM market_stream"