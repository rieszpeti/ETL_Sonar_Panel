FROM python:3.12

WORKDIR /app

COPY requirements.txt .

COPY ../common /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
