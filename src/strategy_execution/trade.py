import os
import csv
import logging
from datetime import datetime
from enum import Enum
from typing import Optional

class TradeStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class ExecutedTrade:
    """
    Represents a single trade (Buy -> Sell).
    Stores the raw execution data for later post-processing.
    """
    def __init__(self, symbol, quantity, buy_order_id, buy_price, best_bid, best_ask, estimated_price):
        self.symbol = symbol
        self.quantity = quantity
        self.buy_order_id = buy_order_id
        self.buy_price = buy_price
        self.best_bid_buy = best_bid          # Snapshot of best bid when buying
        self.best_ask_buy = best_ask          # Snapshot of best ask when buying
        self.estimated_price_buy = estimated_price  # Estimated price provided by API at buy
        self.sell_order_id = None
        self.sell_price = None
        self.best_bid_sell = None             # Snapshot of best bid when selling
        self.best_ask_sell = None             # Snapshot of best ask when selling
        self.estimated_price_sell = None      # Estimated price provided by API at sell
        self.timestamp_buy = datetime.now()
        self.timestamp_sell = None
        self.pnl = None  # Profit/Loss (calculated when trade is closed)

    def close_trade(self, sell_order_id, sell_price, best_bid, best_ask, estimated_price):
        """Closes the trade when a sell order is executed by storing raw sell data and calculating PnL."""
        self.sell_order_id = sell_order_id
        self.sell_price = sell_price
        self.best_bid_sell = best_bid
        self.best_ask_sell = best_ask
        self.estimated_price_sell = estimated_price
        self.timestamp_sell = datetime.now()
        self.pnl = (self.sell_price - self.buy_price) * self.quantity  # Simple PnL Calculation

    def is_closed(self):
        """Checks if the trade has been closed (i.e., sell executed)."""
        return self.sell_price is not None

class TrackedTrade(ExecutedTrade):
    """
    Extends ExecutedTrade with additional tracking for trade status.
    """
    def __init__(self, symbol, quantity, buy_order_id, buy_price, best_bid, best_ask, estimated_price, status):
        super().__init__(symbol, quantity, buy_order_id, buy_price, best_bid, best_ask, estimated_price)
        if isinstance(status, str):
            self.status = TradeStatus(status)
        else:
            self.status = status
        self.sell_order_id: Optional[str] = None