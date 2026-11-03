-- =========================================================
-- COVID-19 Information Portal - MySQL database
-- Import in phpMyAdmin (Import tab) or run:
--   mysql -u root < database.sql
-- =========================================================

CREATE DATABASE IF NOT EXISTS covid_portal;
USE covid_portal;

-- Registration form details + user account
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(60)  NOT NULL,
    username    VARCHAR(15)  NOT NULL UNIQUE,
    email       VARCHAR(100) NOT NULL UNIQUE,
    phone       CHAR(10)     NOT NULL,
    age         TINYINT UNSIGNED NOT NULL,
    pincode     CHAR(6)      NOT NULL,
    vaccinated  ENUM('None', 'Dose 1', 'Dose 2', 'Booster') NOT NULL DEFAULT 'None',
    password    VARCHAR(255) NOT NULL,          -- password_hash() output, never plain text
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User comments
CREATE TABLE IF NOT EXISTS comments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    comment     VARCHAR(500) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- State-wise statistics shown on the home page.
-- SAMPLE FIGURES for the project; update them from the official MoHFW source.
CREATE TABLE IF NOT EXISTS covid_stats (
    state       VARCHAR(40) PRIMARY KEY,
    confirmed   INT NOT NULL,
    recovered   INT NOT NULL,
    deaths      INT NOT NULL,
    vaccinated  INT NOT NULL
);

INSERT IGNORE INTO covid_stats VALUES
    ('Maharashtra',    8100000, 7950000, 148000, 179000000),
    ('Kerala',         6900000, 6820000,  72000,  64000000),
    ('Karnataka',      4100000, 4060000,  40300, 130000000),
    ('Tamil Nadu',     3600000, 3560000,  38100, 128000000),
    ('Delhi',          2000000, 1980000,  26500,  37000000);
