FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY studio_os/ ./studio_os/

# Default command
CMD ["python", "-m", "studio_os.worker"]
