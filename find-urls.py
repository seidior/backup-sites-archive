#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import tldextract
from urllib.parse import urlsplit, urlunsplit
from queue import Queue
import threading
from typing import Set

class URLCrawler:
    """
    A class responsible for crawling URLs and extracting external links.

    Attributes:
        domain (str): The domain to crawl.
        queue (Queue): A thread-safe queue for storing URLs to crawl.
        crawled_urls (Set): A set of already crawled URLs.
        external_urls (list): A list of extracted external URLs.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.queue = Queue()
        self.crawled_urls: Set[str] = set()
        self.external_urls: list = []
        try:
            with open("crawled.txt", "r") as f:
                for line in f.readlines():
                    self.queue.put(line.strip())
        except FileNotFoundError:
            self.queue.put("https://www.example.org")
        print(f"Seeded queue with {self.queue.qsize()} URLs")

    def _extract_external_url(self, href: str) -> str:
        """
        Extract the external URL from a given link.

        Args:
            href (str): The URL to extract.

        Returns:
            str: The extracted external URL.
        """
        # Remove any URL parameters
        return href.split("?")[0]

    def _is_external(self, extracted_domain) -> bool:
        """
        Check if a given URL is external to the domain.

        Args:
            extracted_domain: The extracted URL components.

        Returns:
            bool: True if the URL is external, False otherwise.
        """
        # Check if the domain of the extracted URL matches the main domain
        return extracted_domain.domain!= self.domain.split('.')[0]

    def _is_valid_url(self, href: str) -> bool:
        """
        Check if a given URL is valid.

        Args:
            href (str): The URL to check.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        try:
            result = urlsplit(href)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _process_url(self):
        """
        Process a URL from the queue.
        """
        while True:
            url = self.queue.get()
            print(f"Thread took {url}")
            if url in self.crawled_urls:
                self.queue.task_done()
                continue
            try:
                response = requests.head(url, allow_redirects=False)
                final_url = response.url
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                self.queue.put(url)
                continue
            if response.status_code in [301, 302]:
                final_url = response.headers.get('Location')
            self.crawled_urls.add(final_url)
            with open("crawled.txt", "a") as f:
                f.write(final_url + "\n")
            try:
                response = requests.get(final_url)
                soup = BeautifulSoup(response.content, "html.parser")
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                self.queue.put(final_url)
                continue

            # Find all <a> tags with href attributes
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if not self._is_valid_url(href):
                    continue
                print(f"Found {href} on {url}")
                try:
                    extracted_domain = tldextract.extract(href)
                    if self._is_external(extracted_domain):
                        external_url = self._extract_external_url(href)
                        with open("urls.txt", "a") as f:
                            f.write(external_url + "\n")
                        self.external_urls.append(external_url)
                    elif extracted_domain.domain == self.domain.split('.')[0] and href.startswith("http"):
                        if href not in self.crawled_urls:
                            self.queue.put(href)
                except ValueError:
                    pass  # Ignore invalid URLs
            self.queue.task_done()

    def crawl(self, num_threads: int = 5):
        """
        Crawl the URLs in the queue using multiple threads.

        Args:
            num_threads (int): The number of threads to use. Defaults to 5.
        """
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self._process_url)
            thread.daemon = True
            threads.append(thread)
            thread.start()

        self.queue.join()
        for thread in threads:
            thread.join()


def main():
    domain = "example.org"
    crawler = URLCrawler(domain)
    crawler.crawl()
    print("External URLs:")
    for url in set(crawler.external_urls):
        print(url)


if __name__ == "__main__":
    main()
