\c star;

CREATE SCHEMA IF NOT EXISTS star;

CREATE TABLE IF NOT EXISTS star.images (
    image_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    width INT NOT NULL,
    height INT NOT NULL,
    filename TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS star.predictions_roof_type (
    image_id BIGINT REFERENCES images(image_id),
    class TEXT NOT NULL,
    confidence FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS star.detection_solar_panel (
    image_id BIGINT REFERENCES images(image_id),
    class TEXT NOT NULL,
    confidence FLOAT NOT NULL
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    detected_image_name TEXT NOT NULL
);