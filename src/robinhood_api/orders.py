from typing import Any, Optional
import json
from src.robinhood_api.api_client import APIClient
import uuid

class Orders:
    """
    Handles order-related operations with Robinhood.
    """

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def _place_order(self, side: str, order_type: str, symbol: str, quantity: float, order_config: dict) -> Any:
        """
        Internal helper to place an order.

        Args:
            side: 'buy' or 'sell'.
            order_type: 'market', 'limit', 'stop_loss', 'stop_limit'.
            symbol: The trading pair (e.g., 'BTC-USD').
            quantity: The quantity to trade.
            order_config: dictionary containing the configuration of the order.

        Returns:
            The order response from the API or None on error.
        """
        client_order_id = str(uuid.uuid4())  # Generate a unique client_order_id
        if not isinstance(side, str) or side not in ["buy", "sell"]:
            raise ValueError("side must be 'buy' or 'sell'.")
        if not isinstance(order_type, str) or order_type not in ["market", "limit", "stop_loss", "stop_limit"]:
            raise ValueError("order_type must be one of 'market', 'limit', 'stop_loss', 'stop_limit'.")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("symbol must be a non-empty string.")
        if not isinstance(quantity, float) or quantity <= 0:
            raise ValueError("quantity must be a positive number.")

        body = {
            "client_order_id": client_order_id,
            "side": side,
            "type": order_type,
            "symbol": symbol,
            f"{order_type}_order_config": order_config,
        }
        path = "/api/v1/crypto/trading/orders/"
        response = self.api_client.make_api_request("POST", path, json.dumps(body))
        return response, client_order_id

    def place_market_order(self, symbol: str, side: str, quantity: float,
                           time_in_force: Optional[str] = "gtc") -> Any:
        """
        Places a market order on Robinhood.

        Args:
            symbol: The trading pair (e.g., 'BTC-USD').
            side: 'buy' or 'sell'.
            asset_quantity: The quantity of the asset to trade.
            time_in_force: 'gtc' (good 'til canceled) or 'gfd' (good for day).

        Returns:
            The order response from the API and the client_order_id.
        """
        if time_in_force not in ["gtc", "gfd"]:
            raise ValueError("time_in_force must be one of 'gtc' or 'gfd'.")

        order_config = {"asset_quantity": quantity, "time_in_force": time_in_force}
        return self._place_order(side, "market", symbol, quantity, order_config)

    def place_limit_order(self, symbol: str, side: str, quantity: float, limit_price: float, time_in_force: Optional[str] = "gtc") -> Any:
        """
        Places a limit order on Robinhood.

        Args:
            symbol: The trading pair (e.g., 'BTC-USD').
            side: 'buy' or 'sell'.
            quantity: The quantity to trade.
            limit_price: The limit price for the order.
            time_in_force: gtc or gfd

        Returns:
             The order response from the API and the client_order_id
        """
        if not isinstance(limit_price, float) or limit_price <= 0:
            raise ValueError("limit_price must be a positive number for limit orders.")
        if time_in_force not in ["gtc", "gfd"]:
            raise ValueError("time_in_force must be one of 'gtc', 'gfd'.")

        order_config = {"quantity": quantity, "limit_price": limit_price, "time_in_force": time_in_force}
        return self._place_order(side, "limit", symbol, quantity, order_config)

    def place_stop_loss_order(self, symbol: str, side: str, quantity: float, stop_price: float, time_in_force: Optional[str] = "gtc") -> Any:
        """
        Places a stop-loss order on Robinhood.

        Args:
            symbol: The trading pair (e.g., 'BTC-USD').
            side: 'buy' or 'sell'.
            quantity: The quantity to trade.
            stop_price: The stop price for the order.
            time_in_force: gtc or gfd

        Returns:
            The order response from the API and the client_order_id
        """
        if not isinstance(stop_price, float) or stop_price <= 0:
            raise ValueError("stop_price must be a positive number for stop orders.")
        if time_in_force not in ["gtc", "gfd"]:
            raise ValueError("time_in_force must be one of 'gtc', 'gfd'.")

        order_config = {"quantity": quantity, "stop_price": stop_price, "time_in_force": time_in_force}
        return self._place_order(side, "stop_loss", symbol, quantity, order_config)

    def cancel_order(self, order_id: str) -> Any:
        """
        Cancels an order on Robinhood.

        Args:
            order_id: The ID of the order to cancel.

        Returns:
            The response from the API or None on error.
        """
        if not isinstance(order_id, str):
            raise ValueError("order_id must be a string.")
        path = f"/api/v1/crypto/trading/orders/{order_id}/cancel/"
        return self.api_client.make_api_request("POST", path)

    def get_order(self, order_id: str) -> Any:
        """
        Gets information about a specific order.

        Args:
            order_id: The ID of the order.

        Returns:
            The order information from the API or None on error.
        """
        if not isinstance(order_id, str):
            raise ValueError("order_id must be a string.")
        path = f"/api/v1/crypto/trading/orders/{order_id}/"
        return self.api_client.make_api_request("GET", path)

    def get_orders(self) -> Any:
        """
        Gets all orders.

        Returns:
            All the order information from the API or None on error.
        """
        path = "/api/v1/crypto/trading/orders/"
        return self.api_client.make_api_request("GET", path)