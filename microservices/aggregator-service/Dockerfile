# Base Image
FROM python:3.9-slim

# Set Working Directory
WORKDIR /app

# Copy Files
COPY requirements.txt requirements.txt
COPY src/ src/

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Entry Point
CMD ["python", "src/app.py"]
