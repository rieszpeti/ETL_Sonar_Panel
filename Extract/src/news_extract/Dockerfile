FROM python:3.12

WORKDIR /app

COPY requirements.txt .

COPY ../common /app
COPY ../mongodb_config.py /app/mongodb_config.py

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
