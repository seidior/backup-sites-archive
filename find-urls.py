#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import tldextract

def crawl_domain_main(domain):
    """
    Crawl all pages hosted under a given domain and extract external URLs.

    Args:
        domain (str): The domain to crawl (e.g., example.com).

    Returns:
        list: A list of external URLs found on the pages.
    """
    # Initialize an empty set to store unique external URLs
    external_urls = set()

    # Use a queue or other data structure to keep track of pages to crawl
    pages_to_crawl = [f"https://{domain}"]

    # Perform the crawl
    while pages_to_crawl:
        page_url = pages_to_crawl.pop(0)
        try:
            response = requests.get(page_url)
            soup = BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"Error crawling {page_url}: {e}")
            continue

        # Find all <a> tags with href attributes
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Check if the URL is external
            try:
                extracted_domain = tldextract.extract(href)
                if extracted_domain.domain!= domain:
                    # Remove any URL parameters
                    external_url = href.split("?")[0]
                    external_urls.add(external_url)
            except ValueError:
                pass  # Ignore invalid URLs

        # Add any newly discovered pages to the queue
        for link in soup.find_all("a", href=True):
            href = link["href"]
            try:
                extracted_domain = tldextract.extract(href)
                if extracted_domain.domain == domain and href.startswith("http"):
                    pages_to_crawl.append(href)
            except ValueError:
                pass  # Ignore invalid URLs

    return list(external_urls)


def main():
    domain = "nj.gov"
    external_urls = crawl_domain_main(domain)
    print("External URLs:")
    for url in external_urls:
        print(url)


if __name__ == "__main__":
    main()