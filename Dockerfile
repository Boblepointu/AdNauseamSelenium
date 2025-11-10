FROM python:3.11-slim

# Metadata
LABEL org.opencontainers.image.title="AdNauseam Browser Automation"
LABEL org.opencontainers.image.description="Advanced browser automation with anti-fingerprinting capabilities"
LABEL org.opencontainers.image.source="https://github.com/Boblepointu/AdNauseamSelenium"
LABEL org.opencontainers.image.vendor="AdNauseam"
LABEL maintainer="adnauseam@example.com"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PERSONA_ROTATION_STRATEGY=weighted \
    PERSONA_MAX_AGE_DAYS=30 \
    PERSONA_MAX_USES=100 \
    SELENIUM_HUB=selenium-hub:4444

# Install system dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY crawl.py /app/crawl.py
COPY persona_manager.py /app/persona_manager.py
COPY websites.txt /app/websites.txt

# Create persona data directory
RUN mkdir -p /app/data/personas && \
    chmod 777 /app/data/personas

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://${SELENIUM_HUB}/status || exit 1

# Expose no ports (this is a client, not a server)

# VOLUME REMOVED: Personas are generated in-memory per container
# No volume persistence needed - prevents mount thrashing in swarm mode

# Run the automation
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python3", "-u", "/app/crawl.py"]

