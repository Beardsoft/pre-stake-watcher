# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN pip install --no-cache-dir requests prometheus_client

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the Python script when the container launches
CMD ["python", "app.py"]
