# Use the official Python image as the base image
FROM python:3.12.1

# Set the working directory in the container
WORKDIR /app

# Copy and install the .whl package
COPY dist/*.whl .
RUN pip install --no-cache-dir *.whl

# Copy the .env file to the container
COPY .env .env

# Corrected CMD to properly execute the FastAPI app
CMD ["nohup", "sap_hana_to_snowflake_migration", ">", "output.log", "2>&1"]
