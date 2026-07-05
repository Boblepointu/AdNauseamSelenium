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
    SELENIUM_HUB=selenium-hub:4444 \
    HEARTBEAT_FILE=/tmp/crawler_heartbeat \
    NOISE_ENABLED=true \
    NOISE_RATIO=10 \
    NOISE_MAX_CONCURRENCY=10 \
    NOISE_SAMPLE_SIZE=400 \
    NOISE_CORPUS_PATH=/data/noise/noise_domains.txt \
    NOISE_CORPUS_MAX_AGE_DAYS=7

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
COPY build_noise_corpus.py /app/build_noise_corpus.py
COPY crawler/ /app/crawler/
COPY websites.txt /app/websites.txt

# Create a non-root user to run the crawler
RUN useradd -m -u 10001 crawler

# Create persona data directory (owned by the non-root user, safe 755 perms)
RUN mkdir -p /app/data/personas && \
    chmod 755 /app/data/personas

# Create the shared noise corpus directory, writable by the non-root user so the
# entrypoint's corpus build and the crawler's runtime harvesting can write to it.
RUN mkdir -p /data/noise && \
    chown -R crawler:crawler /data/noise

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Give the non-root user ownership of the app and data directories
RUN chown -R crawler:crawler /app /app/data

# Health check: verify the crawler heartbeat is fresh (updated within 180s)
# instead of probing the Selenium hub, so the container is marked unhealthy
# if the crawl loop stalls.
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD test $(( $(date +%s) - $(stat -c %Y "$HEARTBEAT_FILE" 2>/dev/null || echo 0) )) -lt 180 || exit 1

# Run as the non-root user
USER crawler

# Expose no ports (this is a client, not a server)

# VOLUME REMOVED: Personas are generated in-memory per container
# No volume persistence needed - prevents mount thrashing in swarm mode

# Run the automation
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python3", "-u", "/app/crawl.py"]

