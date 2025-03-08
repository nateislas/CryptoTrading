from typing import Any, Optional
from src.robinhood_api.api_client import APIClient

class MarketData:
    """
    Handles market data retrieval from Robinhood.
    """
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def get_trading_pairs(self, *symbols: Optional[str]) -> Any:
        """
        Gets trading pairs from Robinhood.

        Args:
            *symbols: Optional trading pair symbols (e.g., "BTC-USD").

        Returns:
            The trading pairs from the API or None on error.
        """
        path = "/api/v1/crypto/trading/trading_pairs/"
        if symbols:
            path += "?" + "&".join(f"symbol={arg}" for arg in symbols)
        return self.api_client.make_api_request("GET", path)

    def get_best_bid_ask(self, *symbols: Optional[str]) -> Any:
        """
        Gets the best bid and ask prices for the given symbols.

        Args:
            *symbols: Optional trading pair symbols (e.g., "BTC-USD").

        Returns:
            The best bid/ask prices from the API or None on error.
        """
        path = "/api/v1/crypto/marketdata/best_bid_ask/"
        if symbols:
            path += "?" + "&".join(f"symbol={arg}" for arg in symbols)
        return self.api_client.make_api_request("GET", path)

    def get_estimated_price(self, symbol: str, side: str, quantity: float) -> Any:
        """
        Gets the estimated price for a given symbol, side, and quantity.

        Args:
            symbol: The trading pair symbol (e.g., "BTC-USD").
            side: 'bid', 'ask', or 'both'.
            quantity: The quantity.

        Returns:
            The estimated price from the API or None on error.
        """
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("symbol must be a non-empty string")
        if not isinstance(side, str) or side not in ["bid", "ask", "both"]:
            raise ValueError("side must be one of 'bid', 'ask', or 'both'")
        if not isinstance(quantity, float) or quantity <= 0:
            raise ValueError("quantity must be a positive number.")

        path = f"/api/v1/crypto/marketdata/estimated_price/?symbol={symbol}&side={side}&quantity={quantity}"
        return self.api_client.make_api_request("GET", path)