# ── Base image: Python 3.11 on Debian (full apt access) ──
FROM python:3.11-slim

# ── Install Chrome + ChromeDriver + Xvfb via apt (works perfectly on Render) ──
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    wget \
    curl \
    gnupg \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Set environment variables so Selenium finds Chrome ──
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV DISPLAY=:99

# ── Set working directory ──
WORKDIR /app

# ── Install Python dependencies ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy app files ──
COPY . .

# ── Expose Streamlit port ──
EXPOSE 8501

# ── Start Xvfb (virtual display) + Streamlit ──
CMD Xvfb :99 -screen 0 1920x1080x24 & \
    streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
