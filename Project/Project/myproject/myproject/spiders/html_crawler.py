# Project assisted and partially generated using the assistance of LLM ChatGPT
import scrapy, os
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse

class HtmlCrawler(scrapy.Spider):
    name = "html_crawler"
    # initialize crawler
    def __init__(self, seed_url="https://quotes.toscrape.com/", max_pages=20, max_depth=2, *args, **kwargs):
        super(HtmlCrawler, self).__init__(*args, **kwargs)
        self.start_urls = [seed_url]
        self.allowed_domain = urlparse(seed_url).netloc
        self.max_pages = int(max_pages)
        self.max_depth = int(max_depth)
        self.page_count = 0
        self.link_extractor = LinkExtractor(allow_domains=[self.allowed_domain])

    def parse(self, response):
        # stop if reached max pages
        if self.page_count >= self.max_pages:
            self.crawler.engine.close_spider(self, reason='max_pages_reached')
            return

        # increment and get page url and text
        self.page_count += 1
        page_url = response.url
        page_html = response.text

        # save content in file
        filename = f"downloaded_page_{self.page_count}.html"
        save_path = os.path.join("../../", filename)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        self.logger.info(f"Saved {page_url} as {filename}")

        # get next link if within depth
        current_depth = response.meta.get('depth', 0)
        if current_depth < self.max_depth:
            for link in self.link_extractor.extract_links(response):
                yield scrapy.Request(link.url, callback=self.parse, meta={'depth': current_depth + 1})