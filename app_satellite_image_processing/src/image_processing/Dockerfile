FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

COPY ./requirements.txt /app/requirements.txt
COPY ./resources/roof_satellite/pictures /resources/roof_satellite/pictures

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["python", "./main.py"]
