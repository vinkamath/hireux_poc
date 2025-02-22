import os
import logging
import asyncio
from typing import List, Tuple
from pathlib import Path
from urllib.parse import urlparse, unquote
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor

logger = logging.getLogger("onboard.scrape")

class PortfolioSpider(Spider):
    """Spider for converting portfolio websites to PDFs."""
    name = "portfoliospider"

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
    }

    def __init__(self, output_dir: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.playwright,
                meta={"playwright": True, "playwright_include_page": True},
                errback=self.errback_close_page,
            )

    async def errback_close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()

    def _url_to_filename(self, url: str) -> Path:
        """Convert URL to a suitable filename."""
        parsed_url = urlparse(unquote(url))
        path = parsed_url.path.strip("/")

        if not path:
            path = parsed_url.netloc.replace(".", "_")

        p = Path(path)
        p = p.with_suffix(".pdf")
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    async def playwright(self, response):
        filename = self._url_to_filename(response.url)
        filepath = Path(self.output_dir) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        page = response.meta["playwright_page"]
        try:
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)
            await page.pdf(path=str(filepath))
            self.logger.info(f"Saving PDF to {filepath}")
        except TimeoutError:
            self.logger.error(f"Timeout waiting for page to load: {response.url}")
        finally:
            await page.close()

        links = LinkExtractor(allow=()).extract_links(response)
        self.logger.info(f"Found {len(links)} links on {response.url}")

        for link in links:
            yield Request(
                url=link.url,
                callback=self.playwright,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                errback=self.errback_close_page,
            )

class PortfolioScraper:
    """Scrapes UX portfolios and converts them to PDFs."""
    
    def __init__(self, output_dir: str = "data/input/raw"):
        """
        Initialize the scraper with output directory.
        
        Args:
            output_dir: Base directory for storing scraped portfolios
        """
        self.output_dir = output_dir
        
    def scrape_portfolios(self, candidates: List[Tuple[str, str]]) -> None:
        """
        Scrape portfolios for multiple candidates.
        
        Args:
            candidates: List of tuples containing (candidate_name, portfolio_url)
        """
        for candidate_name, url in candidates:
            try:
                self._scrape_single_portfolio(candidate_name, url)
            except Exception as e:
                logger.error(f"Failed to scrape portfolio for {candidate_name}: {e}")

    def _scrape_single_portfolio(self, candidate_name: str, url: str) -> None:
        """
        Scrape a single portfolio website.
        
        Args:
            candidate_name: Name of the candidate
            url: URL of the portfolio website
        """
        candidate_dir = Path(self.output_dir) / candidate_name
        candidate_dir.mkdir(parents=True, exist_ok=True)
        
        domain = url.split("//")[-1].split("/")[0]
        
        process = CrawlerProcess(settings={
            'LOG_LEVEL': 'INFO',
            'DOWNLOAD_HANDLERS': {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            },
            'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            'REQUEST_FINGERPRINTER_IMPLEMENTATION': "2.7",
        })
        
        logger.info(f"Starting scrape for {candidate_name} at {url}")
        process.crawl(
            PortfolioSpider,
            start_urls=[url],
            allowed_domains=[domain],
            output_dir=str(candidate_dir)
        )
        process.start()
        logger.info(f"Completed scraping for {candidate_name}")


if __name__ == "__main__":
    # Test data
    test_candidates = [
        ("john_doe", "https://www.example.com"),
        ("jane_smith", "https://www.portfolio.com"),
    ]
    
    scraper = PortfolioScraper()
    scraper.scrape_portfolios(test_candidates) 