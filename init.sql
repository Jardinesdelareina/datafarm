DROP DATABASE IF EXISTS datafarm;
CREATE DATABASE datafarm;

/* Поток рыночных данных */
CREATE TABLE IF NOT EXISTS market_stream
(
    symbol VARCHAR(10) NOT NULL,
    time DATETIME UNIQUE NOT NULL,
    price FLOAT NOT NULL
)
