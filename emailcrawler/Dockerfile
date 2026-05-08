FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir scrapy rapidfuzz dnspython

CMD ["scrapy", "crawl", "email_spider"]
