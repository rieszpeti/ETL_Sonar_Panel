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

