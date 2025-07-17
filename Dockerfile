FROM python:3.10-slim

# Install Chrome and ChromeDriver
RUN apt-get update && apt-get install -y wget unzip chromium chromium-driver

WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

CMD ["python", "bot_with_scraper.py"]
