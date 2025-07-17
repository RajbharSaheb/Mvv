# Use lightweight Python base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "bot_with_scraper.py"]
