\c stage;

CREATE SCHEMA IF NOT EXISTS stage;

SET search_path TO stage;

CREATE TABLE IF NOT EXISTS stage.images (
    image_id TEXT,
    width TEXT,
    height TEXT,
    filename TEXT,
    image_data TEXT,
    date_uploaded TEXT
);

CREATE TABLE IF NOT EXISTS stage.coordinates (
    coordinates_id TEXT,
    image_id TEXT,
    latitude TEXT,
    longitude TEXT
);

CREATE TABLE IF NOT EXISTS stage.predictions_roof_type (
    prediction_id TEXT,
    image_id TEXT,
    class_name TEXT,
    time_taken TEXT,
    confidence TEXT,
    prediction_type TEXT,
    date_processed TEXT
);

CREATE TABLE IF NOT EXISTS stage.detection_solar_panel (
    detection_id TEXT,
    image_id TEXT,
    class_name TEXT,
    confidence TEXT,
    x TEXT,
    y TEXT,
    width TEXT,
    height TEXT,
    image_data TEXT,
    date_processed TEXT
);
