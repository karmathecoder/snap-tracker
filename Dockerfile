# Dockerfile

FROM python:3.10-alpine

# Copy requirements file to the container
COPY Requirements.txt .

# Install dependencies
RUN pip install --user git+git://github.com/skyme5/snapchat-dl
RUN pip install --no-cache-dir -r Requirements.txt

# Copy the entire project to the container
COPY . .

# Set execution permission for the script
RUN chmod +x run.sh

# Accept environment variables at runtime (these will come from GitHub Secrets)
ARG SNAPCHAT_USERNAME
ARG TELEGRAM_API_TOKEN
ARG TELEGRAM_CHAT_ID
ARG DOWNLOAD_DIR

# Optionally, set default values or pass the build-time arguments as environment variables
ENV SNAPCHAT_USERNAME=${SNAPCHAT_USERNAME}
ENV TELEGRAM_API_TOKEN=${TELEGRAM_API_TOKEN}
ENV TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
ENV DOWNLOAD_DIR=${DOWNLOAD_DIR:-./downloads}

# Define the entry point for the container
ENTRYPOINT [ "/bin/sh", "./run.sh" ]