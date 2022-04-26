# Extend the official Rasa image
ARG rasa_version=2.8.3
FROM rasa/rasa:$rasa_version

# Copy components folder to working directory
COPY ./*connector* /app/

# By best practices, don't run the code with root user
USER 1001

ENV PYTHONPATH "${PYTHONPATH}:/app"