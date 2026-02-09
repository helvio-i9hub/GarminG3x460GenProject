#CREATE DATABASE nmea_db;
\c nmea_db;

CREATE TABLE data_source_config (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(10) NOT NULL CHECK (source_type IN ('TCP', 'SERIAL')),
    tcp_host VARCHAR(100),
    tcp_port INTEGER,
    serial_port VARCHAR(100),
    baudrate INTEGER DEFAULT 4800,
    enabled BOOLEAN DEFAULT TRUE
);

INSERT INTO data_source_config
(source_type, tcp_host, tcp_port)
VALUES
('TCP', '127.0.0.1', 3100);

CREATE TABLE nmea_raw (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentence TEXT NOT NULL
);

CREATE TABLE nmea_parsed (
    id SERIAL PRIMARY KEY,
    raw_id INTEGER REFERENCES nmea_raw(id),
    talker VARCHAR(10),
    sentence_type VARCHAR(10),
    fields JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nmea_type ON nmea_parsed(sentence_type);
