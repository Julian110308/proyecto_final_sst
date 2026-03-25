# ============================================================
# Dockerfile — SST Centro Minero
# Imagen base: Python 3.12 slim
# ============================================================
FROM python:3.12-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema necesarias para psycopg2 y Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Instalar Gunicorn (servidor WSGI para producción)
RUN pip install gunicorn==21.2.0

# Copiar el código fuente
COPY sst_proyecto/ .

# Copiar entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Puerto que expone el contenedor
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
