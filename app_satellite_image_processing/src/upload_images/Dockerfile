
FROM python:3.12


WORKDIR /app


COPY ./requirements.txt /app/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install python-multipart


COPY ./app /app


CMD ["fastapi", "run", "app/main.py", "--port", "80"]