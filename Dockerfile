FROM python:3.11-slim-bookworm

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ACCEPT_EULA=Y

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Agregar repositorio de Microsoft e instalar ODBC Drivers 17 y 18 for SQL Server
# (la app y las cadenas de conexión usan "ODBC Driver 17 for SQL Server";
#  el Driver 18 se instala también para scripts que lo requieren)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/microsoft-prod.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y \
       msodbcsql17 \
       msodbcsql18 \
       mssql-tools18 \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# Configurar OpenSSL para permitir protocolos/firmas antiguos (SQL Server 2008 R2
# usa certificados con firma legacy que OpenSSL 3 rechaza: "legacy sigalg disallowed")
# El openssl.cnf de esta imagen no trae system_default_sect -> se agrega completo
RUN sed -i '/^\[openssl_init\]/a ssl_conf = ssl_sect' /etc/ssl/openssl.cnf \
    && printf '\n[ssl_sect]\nsystem_default = system_default_sect\n\n[system_default_sect]\nCipherString = DEFAULT@SECLEVEL=0\nMinProtocol = TLSv1\nOptions = UnsafeLegacyRenegotiation\n' \
       >> /etc/ssl/openssl.cnf

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto completo
COPY . .

# Exponer el puerto de la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación con recarga automática para desarrollo
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
