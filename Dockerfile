FROM python:3.11-slim

# ==================================================
# INSTALL CHROMIUM + CHROMEDRIVER
# ==================================================

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# PYTHON SETTINGS
# ==================================================

ENV PYTHONUNBUFFERED=1

# ==================================================
# CHROME PATHS
# ==================================================

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# ==================================================
# WORKDIR
# ==================================================

WORKDIR /app

# ==================================================
# COPY FILES
# ==================================================

COPY . .

# ==================================================
# INSTALL REQUIREMENTS
# ==================================================

RUN pip install --no-cache-dir -r requirements.txt

# ==================================================
# START BOT
# ==================================================

CMD ["python", "-u", "main.py"]