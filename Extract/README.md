# Run MongoDB container
docker run -d --name mongodb -p 27017:27017 -e MONGO_INITDB_DATABASE=satellite-image -e MONGO_INITDB_ROOT_USERNAME=test -e MONGO_INITDB_ROOT_PASSWORD=test  mongo:latest

docker run -d --name mongodb -p 27017:27017 -e MONGO_INITDB_DATABASE=satellite-image mongo:latest


# Run LocalStack container for S3
docker run -d --name localstack_container -p 4566:4566 -p 4571:4571 localstack/localstack

# Set up S3 bucket (after LocalStack is running)
docker exec -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test localstack_container aws --endpoint-url=http://localhost:4566 s3api create-bucket --bucket satellite-image --region us-east-1
