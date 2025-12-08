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
# Copy backend code
COPY backend/ ./backend/

# Expose Flask port
EXPOSE 5001

# Set PYTHONPATH to include /app so we can import from backend and kortex
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "backend/app.py"]
