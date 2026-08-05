FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.api_gateway:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
