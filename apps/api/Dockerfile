FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --timeout 120 \
    --retries 10 \
    -r requirements.txt

COPY requirements-dev.txt .

RUN pip install \
    --no-cache-dir \
    --timeout 120 \
    --retries 10 \
    -r requirements-dev.txt

COPY app ./app
COPY scripts ./scripts
COPY tests ./tests
COPY pytest.ini ./pytest.ini

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]