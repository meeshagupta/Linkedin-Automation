# ── Base image ──
FROM python:3.11-slim

# ── Install Chrome + ChromeDriver + Xvfb ──
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    curl \
    gnupg \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Environment variables ──
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV DISPLAY=:99

# ── Hugging Face Spaces runs as user 1000 (not root) ──
RUN useradd -m -u 1000 appuser && \
    mkdir -p /tmp && \
    chmod 777 /tmp

# ── Set working directory ──
WORKDIR /app

# ── Install Python dependencies ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy app files ──
COPY . .

# ── Give appuser ownership ──
RUN chown -R appuser:appuser /app

# ── Switch to non-root user (required by HF Spaces) ──
USER appuser

# ── Expose port 7860 (Hugging Face Spaces requirement) ──
EXPOSE 7860

# ── Start Xvfb + Streamlit on port 7860 ──
CMD Xvfb :99 -screen 0 1920x1080x24 & \
    streamlit run app.py \
    --server.port=7860 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
