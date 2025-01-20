# Use the official Python image as the base image
FROM python:3.12.1

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to take advantage of Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .env file into the container
COPY .env .env

# Copy the rest of the application code into the container
COPY . .

# Expose the port on which the FastAPI app will run
EXPOSE 8000

# Command to run the FastAPI app using Gunicorn with Uvicorn workers
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
