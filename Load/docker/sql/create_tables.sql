\c star;

CREATE SCHEMA IF NOT EXISTS star;

SET search_path TO star;

CREATE TABLE IF NOT EXISTS star.images (
    image_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    width INT NOT NULL,
    height INT NOT NULL,
    filename TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS star.predictions_roof_type (
    prediction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    image_id BIGINT REFERENCES images(image_id),
    class_name TEXT NOT NULL,
    time_taken DOUBLE PRECISION NOT NULL,
    confidence FLOAT NOT NULL,
    prediction_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS star.detection_solar_panel (
    detection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    image_id BIGINT REFERENCES images(image_id),
    class_name TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    detected_image_name TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS star.sentiment (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    oid TEXT UNIQUE,
    title TEXT NOT NULL,
    CONTENT TEXT NOT NULL,
    label TEXT NOT NULL,
    score FLOAT NOT NULL,
    date_fetched DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sentiment_id ON star.sentiment(id);
COMMENT ON COLUMN sentiment.label is 'e.g., positive, negative';


CREATE TABLE IF NOT EXISTS star.stock_data (
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    price FLOAT NOT NULL,
    PRIMARY KEY (symbol, date)
);