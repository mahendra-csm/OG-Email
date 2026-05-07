FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install scrapy

WORKDIR /app/emailcrawler

CMD ["scrapy", "crawl", "email_spider"]
