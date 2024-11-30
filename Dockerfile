FROM python:3.10-alpine

# Install necessary dependencies for running multiple processes and Gunicorn
RUN apk update && apk add --no-cache supervisor 

# Set the working directory to /app
WORKDIR /app

# Copy requirements file to the container
COPY Requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r Requirements.txt

# Copy the entire project to the container
COPY . .

# Create the logs directory inside the container
RUN mkdir -p /app/logs

# Supervisor configuration for running multiple processes
COPY supervisord.conf /etc/supervisord.conf

# Expose Flask's default port (5000 for Gunicorn)
EXPOSE $PORT

# Run supervisor to manage processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
