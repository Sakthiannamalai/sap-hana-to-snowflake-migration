# Use the official Python image as the base image
FROM python:3.12.1

# Set the working directory in the container
WORKDIR /app

# Copy and install the .whl package
COPY dist/*.whl .
RUN pip install --no-cache-dir *.whl

# Copy the application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI app using Gunicorn with Uvicorn workers
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
