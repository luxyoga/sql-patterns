-- sql-patterns schema.
-- Deliberately plain ANSI so the same file loads in DuckDB, SQLite, PostgreSQL and MySQL.
-- No SERIAL / AUTOINCREMENT, no foreign keys, no vendor types: IDs are supplied explicitly.

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id  INTEGER      NOT NULL,
    name         VARCHAR(100) NOT NULL,
    city         VARCHAR(60),          -- nullable on purpose
    signup_date  DATE         NOT NULL
);

CREATE TABLE orders (
    order_id     INTEGER      NOT NULL,
    customer_id  INTEGER,             -- nullable on purpose: guest checkout
    order_date   DATE         NOT NULL,
    amount       DECIMAL(10,2),       -- nullable on purpose
    channel      VARCHAR(20)  NOT NULL
);
