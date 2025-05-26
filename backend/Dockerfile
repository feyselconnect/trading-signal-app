# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port your Flask app runs on
EXPOSE 8000

# Set environment variables (optional, for Flask)
ENV FLASK_APP=app/app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"] 