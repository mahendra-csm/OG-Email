FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir scrapy rapidfuzz dnspython

WORKDIR /app/emailcrawler

CMD ["scrapy", "crawl", "email_spider"]
