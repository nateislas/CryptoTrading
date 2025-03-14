import csv
import time
from datetime import datetime

class OrderLogger:
    """
    Handles logging of all placed orders and their execution details.
    """

    def __init__(self, log_file="trade_log.csv"):
        self.log_file = log_file

        # Initialize CSV with headers if not present
        with open(self.log_file, "a", newline="") as file:
            writer = csv.writer(file)
            if file.tell() == 0:  # Write headers only if file is empty
                writer.writerow([
                    "Timestamp", "Order ID", "Symbol", "Side", "Quantity", "Order Type",
                    "Best Bid", "Best Ask", "Estimated Price", "Execution Price",
                    "Estimated Slippage ($)", "Estimated Slippage (%)",
                    "Actual Slippage ($)", "Actual Slippage (%)"
                ])

    def log_trade(self, order_id, symbol, side, quantity, order_type,
                  best_bid, best_ask, estimated_price, execution_price):
        """
        Logs an executed trade with execution details.

        Args:
            order_id: Unique order ID.
            symbol: Trading pair (e.g., 'DOGE-USD').
            side: 'buy' or 'sell'.
            quantity: Amount traded.
            order_type: Market, Limit, etc.
            best_bid: Best bid price at execution.
            best_ask: Best ask price at execution.
            estimated_price: Pre-trade estimated execution price.
            execution_price: Actual execution price.
        """

        estimated_slippage = estimated_price - best_ask if side == "buy" else estimated_price - best_bid
        estimated_slippage_percent = (estimated_slippage / best_ask) * 100 if side == "buy" else (estimated_slippage / best_bid) * 100

        actual_slippage = execution_price - best_ask if side == "buy" else execution_price - best_bid
        actual_slippage_percent = (actual_slippage / best_ask) * 100 if side == "buy" else (actual_slippage / best_bid) * 100

        with open(self.log_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now(), order_id, symbol, side, quantity, order_type,
                best_bid, best_ask, estimated_price, execution_price,
                estimated_slippage, estimated_slippage_percent,
                actual_slippage, actual_slippage_percent
            ])

        print(f"[LOG] Order {order_id} logged successfully at {datetime.now()}")
