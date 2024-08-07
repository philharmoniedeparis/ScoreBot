ARG RASA_SDK_VERSION=2.8.2
# Extend the official Rasa SDK image
FROM rasa/rasa-sdk:${RASA_SDK_VERSION}

LABEL MAINTAINER="Tristan Deborde <tr.deborde@gmail.com>"
LABEL MAINTAINER="Dany Rafina <danyrafina@gmail.com>"
LABEL DESCRIPTION="Custom Rasa Open Source Image"
LABEL APP_VERSION=1.0.4

# Use subdirectory as working directory
WORKDIR /app

# Change back to root user to install dependencies
USER root

# To install packages from PyPI
COPY  ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# Copy actions folder to working directory
COPY ./actions /app/actions
# Copy utils folder to working directory
COPY ./utils /app/utils

# Switch back to non-root to run code
USER 1001
