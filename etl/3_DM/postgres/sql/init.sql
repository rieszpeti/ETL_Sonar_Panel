\c star;

CREATE SCHEMA IF NOT EXISTS star;

SET search_path TO star;

CREATE TABLE IF NOT EXISTS dim_images (
    dim_image_id BIGSERIAL PRIMARY KEY,
    image_id BIGINT NOT NULL UNIQUE,
    width INT NOT NULL,
    height INT NOT NULL,
    filename TEXT NOT NULL,
    latitude DECIMAL(10, 5) NOT NULL,
    longitude DECIMAL(10, 5) NOT NULL,
    date_loaded TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_predictions_roof_type (
    dim_roof_type_id BIGSERIAL PRIMARY KEY,
    prediction_id BIGINT UNIQUE,
    class_name TEXT NOT NULL,
    time_taken DECIMAL(10, 5) NOT NULL,
    confidence DECIMAL(10, 5) NOT NULL,
    prediction_type TEXT NOT NULL,
    date_processed TIMESTAMPTZ NOT NULL,
    date_loaded TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_detections_solar_panel (
    dim_solar_panel_id BIGSERIAL PRIMARY KEY,
    detection_id BIGINT UNIQUE,
    class_name TEXT,
    confidence DECIMAL(10, 5),
    x INT,
    y INT,
    width INT,
    height INT,
    image_data BYTEA,
    date_processed TIMESTAMPTZ NOT NULL,
    date_loaded TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id INT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    week INT NOT NULL,
    quarter INT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_images (
    fact_id BIGSERIAL PRIMARY KEY NOT NULL,
    image_id BIGINT REFERENCES dim_images(dim_image_id) NOT NULL,
    dim_roof_type_id BIGINT REFERENCES star.dim_predictions_roof_type(dim_roof_type_id) NULL,
    dim_solar_panel_id BIGINT REFERENCES star.dim_detections_solar_panel(dim_solar_panel_id) NULL,
    date_id INT REFERENCES star.dim_date(date_id) NOT NULL,
    image_date_uploaded TIMESTAMPTZ NOT NULL,
    date_loaded TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
