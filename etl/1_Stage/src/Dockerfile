FROM python:3.12-slim

WORKDIR /app

RUN apt-get update

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["python", "./main.py"]
