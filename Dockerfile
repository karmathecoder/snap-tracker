FROM python:3.10-alpine

# Install necessary dependencies for running multiple processes and Gunicorn
RUN apk update && apk add --no-cache supervisor git bash

# Set the working directory to /app
WORKDIR /app

# Copy requirements file to the container
COPY Requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r Requirements.txt

# Configure Git with username and email
# You can set these values through environment variables or directly in the Dockerfile.
# Here, we're assuming the username and email are provided in the .env file.
ARG GIT_USER_NAME
ARG GIT_USER_EMAIL
RUN git config --global user.name "${GIT_USER_NAME}" && \
    git config --global user.email "${GIT_USER_EMAIL}"

# Clone the repository using the DOWNLOAD_DIR environment variable
# Assuming you have the repo URL stored in DOWNLOAD_DIR
ARG REPO_URL_WITH_TOKEN
ARG DOWNLOAD_DIR
RUN git clone ${REPO_URL_WITH_TOKEN} ${DOWNLOAD_DIR}

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
