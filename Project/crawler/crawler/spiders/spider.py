# Crawler made using reference to scrapy documentation and additional help from ChatGPT

import scrapy
from urllib.parse import urljoin

class Spider(scrapy.Spider):
    name = "spider"

# Initialize the crawler with the initial url, maximum pages, and max depth, can be run using:
# scrapy crawl spider -a seed_url="https://quotes.toscrape.com" -a max_pages=20 -a max_depth=2 -O crawl_output.json
# The output file will simply be urls and the html associated as a json file.
    def __init__(self, seed_url=None, max_pages=20, max_depth=2, *args, **kwargs):
        super().__init__(*args, **kwargs) #Gets from comand line arguments
        self.start_urls = [seed_url]
        self.max_pages = int(max_pages)
        self.max_depth = int(max_depth)
        self.visited = 0

    # Parse and gather html and urls to follow
    def parse(self, response):
        # If the max pages has been reached close the spider
        if self.visited >= self.max_pages:
            self.crawler.engine.close_spider(self, reason='max_pages_reached')
            return
        self.visited += 1
        # Otherwise yield the url and html
        yield {
            "url": response.url,
            "html": response.text
        }
        # Follow links and add them to the queue if max depth hasn't been reached
        current_depth = response.meta.get("depth", 0)
        if current_depth < self.max_depth:
            for link in response.css("a::attr(href)").getall():
                next_url = urljoin(response.url, link)
                yield response.follow(next_url, callback=self.parse,
                                      meta={"depth": current_depth + 1})
