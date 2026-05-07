FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install scrapy rapidfuzz dnspython

CMD ["scrapy", "crawl", "email_spider"]
