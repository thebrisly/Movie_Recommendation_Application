
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app.py .

COPY ./images ./images

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8080"]
