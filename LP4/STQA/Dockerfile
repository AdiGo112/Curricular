# STQA test runner: Python + headless Chromium (Selenium) + Node.js (JS regex tests)
#   docker build -t stqa .
#   docker run --rm stqa                     run every test suite
#   docker compose up --build                + COVID-19 PHP/MySQL site and TaskTrack app (see compose.yaml)
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium chromium-driver nodejs \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver \
    HEADLESS=1 \
    PYTHONUNBUFFERED=1

WORKDIR /stqa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "run_all.py"]
