#!/usr/bin/env python

import threading
from queue import Queue
import requests
import time
from typing import List, Tuple

ENDPOINT_URL = "https://web.archive.org/save"

class URLSubmitter:
    """
    Handles the submission of URLs to a POST endpoint.

    Attributes:
        post_endpoint (str): The URL of the POST endpoint.
        credentials (List[Tuple[str, str]]): A list of tuples containing usernames and passwords.
    """

    def __init__(self, post_endpoint: str, credentials: List[Tuple[str, str]]):
        """
        Initializes the URLSubmitter.

        Args:
            post_endpoint (str): The URL of the POST endpoint.
            credentials (List[Tuple[str, str]]): A list of tuples containing usernames and passwords.
        """
        self.post_endpoint = post_endpoint
        self.credentials_queue = Queue()
        for credential in credentials:
            self.credentials_queue.put(credential)
        self.url_queue = Queue()
        # Create a session for each credential
        self.sessions = {}
        for credential in credentials:
            self.sessions[credential] = requests.Session()

    def _submit_url(self, url: str) -> None:
        """
        Submits a URL to the POST endpoint.

        Args:
            url (str): The URL to submit.
        """
        try:
            credential = self.credentials_queue.get(block=False)
        except:  # If queue is empty, wait for an item
            credential = self.credentials_queue.get()
        try:
            # Update the headers and data for the POST request
            auth_header = f"LOW {credential[0]}:{credential[1]}"
            headers = {
                "Accept": "application/json",
                "Authorization": auth_header
            }
            data = f"url={url}"
            
            session = self.sessions[credential]
            response = session.post(self.post_endpoint, headers=headers, data=data)
            response.raise_for_status()  # Raise an exception for HTTP errors
            print(f"Success: {url}, Status Code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"Failure: {url}, Error: Connection refused")
            self.url_queue.put(url)  # Requeue the URL
            time.sleep(20)  # Pause for 20 seconds before next attempt
        except requests.exceptions.RequestException as e:
            print(f"Failure: {url}, Error: {e}")
            self.url_queue.put(url)  # Requeue the URL
            time.sleep(10)  # Pause for 10 seconds before next attempt
        finally:
            self.credentials_queue.put(credential)  # Return credential to queue

    def _worker(self) -> None:
        """
        Worker function for threads.
        """
        while True:
            try:
                url = self.url_queue.get(block=False)
            except:  # If queue is empty, exit thread
                break
            self._submit_url(url)
            self.url_queue.task_done()

    def start_submission(self, num_threads: int, urls: List[str]) -> None:
        """
        Starts the submission process.

        Args:
            num_threads (int): The number of threads to use for simultaneous submission.
            urls (List[str]): A list of URLs to submit.
        """
        for url in urls:
            self.url_queue.put(url)

        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self._worker)
            threads.append(thread)
            thread.start()

        # Wait for all tasks to be processed
        self.url_queue.join()
        for _ in range(num_threads):
            self.url_queue.put(None)  # Signal threads to exit

        for thread in threads:
            thread.join()

def read_urls_from_file(filename: str) -> List[str]:
    """
    Reads URLs from a file, one URL per line.

    Args:
        filename (str): The name of the file containing URLs.

    Returns:
        List[str]: A list of URLs.
    """
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Example usage
if __name__ == "__main__":
    post_endpoint = ENDPOINT_URL
    credentials = [
        ("accesskey1", "secretkey1"),
        ("accesskey2", "secretkey2")
    ]
    filename = "urls2.txt"  # File containing URLs, one per line
    urls = read_urls_from_file(filename)
    
    if urls:
        submitter = URLSubmitter(post_endpoint, credentials)
        submitter.start_submission(credentials.count, urls)
