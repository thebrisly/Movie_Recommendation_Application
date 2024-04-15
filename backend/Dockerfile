
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main_app.py .

COPY ./testapi-415115-18f8f1b39899.json ./


CMD ["python", "main_app.py"]