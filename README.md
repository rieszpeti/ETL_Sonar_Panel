# Run MongoDB container
docker run -d --name mongodb -p 27017:27017 -e MONGO_INITDB_DATABASE=satellite-image mongo:latest


# Run LocalStack container for S3
docker run -d --name localstack_container -p 4566:4566 -p 4571:4571 localstack/localstack

# Set up S3 bucket (after LocalStack is running)
docker exec -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test localstack_container aws --endpoint-url=http://localhost:4566 s3api create-bucket --bucket satellite-image --region us-east-1

# TimescaleDB for stockdata
docker run -d --name timescaledb -e POSTGRES_DB=stock_data -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -p 5432:5432 timescale/timescaledb:latest-pg16

docker exec -it timescaledb psql -U test -d stock_data -c "
CREATE SCHEMA stock;

CREATE TABLE stock.stock_data (
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    price FLOAT NOT NULL,
    PRIMARY KEY (symbol, date)
);
SELECT create_hypertable('stock.stock_data', 'date');
"

docker compose up --build --force-recreate --no-deps [-d] [<service_name>..]

docker compose up --build --force-recreate --no-deps -d image_process_extractor

docker compose build --no-cache [<service_name>..]

docker compose build --no-cache image_process_extractor


docker compose build --no-cache stock_market_extractor

docker compose build --no-cache upload_images_webpage

docker compose up --build --force-recreate --no-deps -d stock_market_extractor

'postgresql+psycopg2://yourUserDBName:yourUserDBPassword@yourDBDockerContainerName/yourDBName'


CREATE TABLE IF NOT EXISTS fact_solar_installation (
    id SERIAL PRIMARY KEY,
    date_id INTEGER REFERENCES dim_date(date_id),
    symbol_id INTEGER REFERENCES dim_symbol(symbol_id),
    price FLOAT,                     -- Price of the solar installation
    sentiment_score FLOAT,           -- Sentiment score from analysis
    image_id INTEGER REFERENCES dim_image(image_id) -- Image associated with the installation
);
CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,       -- The actual date
    year INT,                        -- Year of the date
    month INT,                       -- Month of the date
    day INT                          -- Day of the date
);
CREATE TABLE IF NOT EXISTS dim_symbol (
    symbol_id SERIAL PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,      -- Stock symbol for the solar company
    company_name TEXT                 -- Name of the company associated with the symbol
);
CREATE TABLE IF NOT EXISTS dim_image (
    image_id SERIAL PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,    -- File name of the image
    width INT,                        -- Width of the image
    height INT,                       -- Height of the image
    prediction_type TEXT              -- Type of prediction related to the image
);

CREATE TABLE IF NOT EXISTS dim_sentiment (
    sentiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  
    sentiment_uuid UUID UNIQUE,                               
    sentiment_label TEXT,                                         -- Sentiment label (e.g., positive, negative)
    sentiment_score FLOAT                                         -- Sentiment score
);

CREATE INDEX IF NOT EXISTS idx_sentiment_id ON dim_sentiment(sentiment_id);
