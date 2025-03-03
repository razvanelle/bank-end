CREATE DATABASE IF NOT EXISTS payments;
USE payments;

CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(255) PRIMARY KEY,
    balance DECIMAL(15, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(255) PRIMARY KEY,
    account_id VARCHAR(255),
    transaction_type ENUM('deposit', 'withdrawal', 'payment') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL,
    details TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Insert 5 accts for testing
INSERT INTO accounts (account_id, balance) VALUES
('101', 1000.00),
('102', 1000.00),
('103', 1000.00),
('104', 1000.00),
('105', 1000.00);
