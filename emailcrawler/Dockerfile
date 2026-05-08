FROM python:3.10

WORKDIR /app

# We copy everything from repo-root/emailcrawler into /app
COPY . /app

RUN pip install scrapy rapidfuzz dnspython

# Scrapy will now see scrapy.cfg in /app and find the spiders
CMD ["scrapy", "crawl", "email_spider"]
