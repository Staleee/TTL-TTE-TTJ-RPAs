FROM python:3.11-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/google-chrome.deb \
    && rm /tmp/google-chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver: exact Chrome build is often NOT on the CfT bucket (wget exit 8 = 404).
# Try exact version first; else use Google's LATEST_RELEASE_<major> for a published driver.
ARG CHROMEDRIVER_FALLBACK_VER=131.0.6778.264
RUN set -eux; \
    FULL_VER=$(google-chrome --version | awk '{print $3}'); \
    MAJOR=$(echo "$FULL_VER" | cut -d. -f1); \
    BASE="https://storage.googleapis.com/chrome-for-testing-public"; \
    ZIP_PATH="linux64/chromedriver-linux64.zip"; \
    echo "Installed Chrome: $FULL_VER (major $MAJOR)"; \
    if curl -fsS -o /dev/null --head "${BASE}/${FULL_VER}/${ZIP_PATH}"; then \
      DRIVER_VER="$FULL_VER"; \
      echo "Using exact-match ChromeDriver: $DRIVER_VER"; \
    elif DRIVER_VER=$(curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${MAJOR}"); then \
      echo "Using CfT LATEST_RELEASE_${MAJOR}: $DRIVER_VER"; \
    else \
      DRIVER_VER="${CHROMEDRIVER_FALLBACK_VER}"; \
      echo "Fallback pinned ChromeDriver: $DRIVER_VER"; \
    fi; \
    wget -q -O /tmp/chromedriver.zip "${BASE}/${DRIVER_VER}/${ZIP_PATH}"; \
    unzip -q /tmp/chromedriver.zip -d /tmp/; \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
    chmod +x /usr/local/bin/chromedriver; \
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64; \
    chromedriver --version

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs output screenshots

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run Flask app with proper binding and verbose logging
# Use shell form to allow variable expansion
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 300 --log-level debug --access-logfile - --error-logfile - app:app
