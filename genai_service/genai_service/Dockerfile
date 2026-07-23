FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose service port
EXPOSE 8100

# Run with uvicorn
CMD ["uvicorn", "genai_service.main:app", "--host", "0.0.0.0", "--port", "8100"]
