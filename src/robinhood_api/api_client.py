import requests
import json
import logging
import time
from typing import Dict, Any
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class APIClient:
    """
    Handles the core API communication with Robinhood.
    """
    def __init__(self, api_key: str, private_key_bytes: bytes, base_url: str = "https://trading.robinhood.com"):
        self.api_key = api_key
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes[:32])
        self.base_url = base_url

    @staticmethod
    def _get_current_timestamp() -> int:
        """Gets the current timestamp in UTC."""
        return int(time.time())

    def make_api_request(self, method: str, path: str, body: str = "") -> Any:
        """
        Makes a request to the Robinhood API.

        Args:
            method: The HTTP method (GET or POST).
            path: The API endpoint path.
            body: The request body (for POST requests).

        Returns:
            The JSON response from the API or None on error.
        """
        timestamp = self._get_current_timestamp()
        headers = self.get_authorization_header(method, path, body, timestamp)
        url = self.base_url + path
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay
        for attempt in range(max_retries):
            try:
                response = {}
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=json.loads(body), timeout=10)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:  # Rate limiting
                    logging.warning(f"Rate limited on attempt {attempt + 1}/{max_retries}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                elif response.status_code == 500: # Server error
                    logging.error(f"Server error on attempt {attempt + 1}/{max_retries}: {http_err} at URL: {url}, with response: {response.content}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                elif response.status_code == 400:
                    logging.error(f"Bad request: {http_err} at URL: {url}, with response: {response.content}")
                    return None  # Or raise a custom exception
                elif response.status_code == 401:
                    logging.error(f"Unauthorized: {http_err} at URL: {url}, with response: {response.content}")
                    return None # Or raise a custom exception
                elif response.status_code == 403:
                    logging.error(f"Forbidden: {http_err} at URL: {url}, with response: {response.content}")
                    return None # Or raise a custom exception
                elif response.status_code == 404:
                    logging.error(f"Not found: {http_err} at URL: {url}, with response: {response.content}")
                    return None # Or raise a custom exception
                else:
                    logging.error(f"An HTTP error occurred: {http_err} at URL: {url}, with response: {response.content}")
                    return None  # Or raise a custom exception
            except requests.RequestException as req_err:
                logging.error(f"A request error occurred: {req_err} at URL: {url}")
                return None
            except json.JSONDecodeError as json_err:
                logging.error(f"Failed to decode JSON: {json_err} at URL: {url}, with response: {response.content}")
                return None
        logging.error(f"Max retries exceeded for {method} {url}")
        return None  # Or raise an exception after max retries

    def get_authorization_header(
            self, method: str, path: str, body: str, timestamp: int
    ) -> Dict[str, str]:
        """
        Generates the authorization header for Robinhood API requests.

        Args:
            method: The HTTP method (GET or POST).
            path: The API endpoint path.
            body: The request body (for POST requests).
            timestamp: The current timestamp.

        Returns:
            The authorization header as a dictionary.
        """
        message_to_sign = f"{self.api_key}{timestamp}{path}{method}{body}"
        signature = self.private_key.sign(message_to_sign.encode("utf-8"))

        return {
            "x-api-key": self.api_key,
            "x-signature": base64.b64encode(signature).decode("utf-8"),
            "x-timestamp": str(timestamp),
        }