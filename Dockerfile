# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install CA certificates tools
RUN apt-get update && apt-get install -y ca-certificates

# Copy your PEM file
COPY trusted_certs_12_27.pem /usr/local/share/ca-certificates/trusted_certs_12_27.crt

# Update the system CA store
RUN update-ca-certificates

# Run your script
CMD ["python", "-u", "main.py"]

