# Use an official Python runtime as a parent image
# Choose a specific version for reproducibility, -slim is smaller
FROM python:3.12-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any (e.g., for libraries that need compilation)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip
# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt requirements.txt
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# Copy the 'app' directory from your host to '/app/app' in the container
COPY ./app /app/app
COPY ./.env /app

# Expose the port the app runs on
# This is documentation; the actual port mapping happens in docker-compose.yml
EXPOSE 8000

# Define the command to run the application using uvicorn
# Runs the FastAPI app instance located in app/main.py
# Use 0.0.0.0 to make it accessible from outside the container within the Docker network
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
