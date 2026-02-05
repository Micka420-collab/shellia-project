FROM python:3.11-slim

WORKDIR /app

# Dépendances
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code source
COPY *.py ./
COPY deployment/ ./deployment/

# Dossiers
RUN mkdir -p logs data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "maxis_bot.py"]
