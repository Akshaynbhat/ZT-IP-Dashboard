FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy model files from the build context
COPY ml/models /app/ml_models

COPY . .

ENV MODEL_DIR=/app/ml_models

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]