FROM node:20-slim AS base

# Install Python and supervisord
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set up Python virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy backend and install Python dependencies
COPY backend/ ./backend/
RUN if [ -f backend/requirements.txt ]; then pip install --no-cache-dir -r backend/requirements.txt; fi

# Copy frontend and install Node dependencies
COPY frontend/ ./frontend/
RUN if [ -f frontend/package.json ]; then cd frontend && npm install; fi

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports (frontend: 3000, backend: 8000)
EXPOSE 3000 8000

# Start supervisord
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
