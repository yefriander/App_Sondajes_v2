FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 1) Dependencias del sistema (weasyprint, build, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    unixodbc \
    unixodbc-dev \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff6 \
    libfreetype6-dev \
    mupdf-tools \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2) Instalar Microsoft ODBC Driver 17 (para Debian 12 Bookworm)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3) Font Aria pdf docx
RUN apt-get update && \
    apt-get install -y fonts-liberation fontconfig && \
    fc-cache -f -v

COPY staticfiles/fonts/arial.ttf /usr/share/fonts/truetype/arial.ttf
COPY staticfiles/fonts/arialbd.ttf /usr/share/fonts/truetype/arialbd.ttf
COPY staticfiles/fonts/ariali.ttf /usr/share/fonts/truetype/ariali.ttf
COPY staticfiles/fonts/arialbi.ttf /usr/share/fonts/truetype/arialbi.ttf

RUN apt-get update && \
    apt-get install -y fontconfig && \
    fc-cache -f -v

# 4) Instalar dependencias Python
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && rm -rf /root/.cache/pip

# 5) Copiar el proyecto
COPY . /app

RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R root:root /app

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "10800", "testigos.wsgi:application"]