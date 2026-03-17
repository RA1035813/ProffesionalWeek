# Gebruik een lichtgewicht Python base image
FROM python:3.11-slim

# Zet de werkmap in de container
WORKDIR /app

# Installeer systeemafhankelijkheden voor psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopieer de requirements en installeer Python pakketten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary

# Kopieer de rest van de applicatiecode
COPY . .

# Exposeer de poort waarop Flask draait
EXPOSE 5000

# Start de applicatie met database-ondersteuning
CMD ["python", "analysis_server_db.py"]
