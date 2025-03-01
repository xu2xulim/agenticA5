FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install logfire[asyncpg]
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl && \
    pip install playwright && \
    playwright install-deps && \
    playwright install && \
    rm -rf /var/lib/apt/lists/*  # Clean up APT cache to reduce image size
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]