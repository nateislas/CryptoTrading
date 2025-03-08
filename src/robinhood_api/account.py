from typing import Any, Optional
from src.robinhood_api.api_client import APIClient

class Account:
    """
    Handles account-related operations with Robinhood.
    """
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def get_account(self) -> Any:
        """
        Gets the account information.

        Returns:
            The account information from the API or None on error.
        """
        path = "/api/v1/crypto/trading/accounts/"
        return self.api_client.make_api_request("GET", path)

    def get_holdings(self, *asset_codes: Optional[str]) -> Any:
        """
        Gets holdings information.

        Args:
            *asset_codes: Optional asset codes (e.g., "BTC", "ETH").

        Returns:
            The holdings from the API or None on error.
        """
        path = "/api/v1/crypto/trading/holdings/"
        if asset_codes:
            path += "?" + "&".join(f"asset_code={arg}" for arg in asset_codes)
        return self.api_client.make_api_request("GET", path)