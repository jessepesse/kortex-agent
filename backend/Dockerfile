FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy kortex package
COPY kortex/ ./kortex/

# Copy backend code
COPY backend/ ./

# Expose Flask port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
