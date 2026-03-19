FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY sms_send/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project for access to FastAPI, SMS, localAI etc.
COPY . .

# Run the application
CMD ["python", "sms_send/sms.py"]
