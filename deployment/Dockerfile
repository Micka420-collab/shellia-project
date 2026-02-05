# ============================================
# SHELLIA AI BOT - DOCKERFILE
# ============================================

FROM python:3.11-slim

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier requirements
COPY bot/requirements.txt .

# Installer dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY bot/ .

# Créer répertoire pour les logs
RUN mkdir -p /app/logs

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Commande de démarrage
CMD ["python", "bot.py"]
