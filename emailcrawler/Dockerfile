FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install scrapy rapidfuzz dnspython

WORKDIR /app

CMD ["scrapy", "crawl", "email_spider"]
