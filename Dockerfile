FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including gcc & libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and structure
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck to verify container status
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch Streamlit web application
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
