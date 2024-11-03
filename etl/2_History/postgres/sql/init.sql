\c history;

CREATE SCHEMA IF NOT EXISTS history;

SET search_path TO history;

CREATE TABLE IF NOT EXISTS history.images (
    image_id BIGSERIAL PRIMARY KEY,
    width INT NOT NULL,
    height INT NOT NULL,
    filename TEXT NOT NULL UNIQUE,
    image_data BYTEA NOT NULL,
    date_uploaded TIMESTAMPTZ NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS history.coordinates (
    coordinates_id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(image_id),
    latitude DECIMAL(10, 5) NOT NULL,
    longitude DECIMAL(10, 5) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS history.predictions_roof_type (
    prediction_id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(image_id),
    class_name TEXT NOT NULL,
    time_taken DECIMAL(10, 5) NOT NULL,
    confidence DECIMAL(10, 5) NOT NULL,
    prediction_type TEXT NOT NULL,
    date_processed TIMESTAMPTZ NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS history.detection_solar_panel (
    detection_id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(image_id),
    class_name TEXT,
    confidence DECIMAL(10, 5),
    x INT,
    y INT,
    width INT,
    height INT,
    image_data BYTEA,
    date_processed TIMESTAMPTZ NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ NULL
);
