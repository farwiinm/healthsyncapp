# Base Image
FROM python:3.9-slim

# Set Working Directory
WORKDIR /app

# Copy Files
COPY requirements.txt requirements.txt
COPY src/ src/
COPY models/ models/

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Flask Environment Variables
ENV FLASK_APP src/app.py
ENV FLASK_RUN_HOST 0.0.0.0

# Expose Port
EXPOSE 5000

# Run Flask App
CMD ["flask", "run"]
