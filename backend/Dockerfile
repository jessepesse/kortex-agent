FROM python:3.11-slim

WORKDIR /app

# Copy requirements from both locations and install
COPY backend/requirements.txt ./backend/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

# Copy kortex package
COPY kortex/ ./kortex/

# Copy backend code
COPY backend/ ./

# Expose Flask port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
