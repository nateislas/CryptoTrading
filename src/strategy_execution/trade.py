import csv
import os
import logging
from datetime import datetime

class Trade:
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


class TradeLogger:
    """
    Handles logging of full trades.
    """

    def __init__(self, log_file="logs/trade_execution/trade_log.csv"):
        today_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = f"logs/trade_execution/trade_log_{today_date}.csv"

        logging.info(f"Initializing TradeLogger. Log file: {self.log_file}")

        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Initialize CSV with headers if the file does not exist
        with open(self.log_file, "a", newline="") as file:
            writer = csv.writer(file)
            if file.tell() == 0:  # Write headers only if file is empty
                writer.writerow([
                    "Buy Timestamp", "Buy Order ID", "Sell Timestamp", "Sell Order ID",
                    "Symbol", "Quantity", "Buy Price", "Sell Price", "PnL ($)", "Win/Loss",
                    "Best Bid (Buy)", "Best Ask (Buy)", "Estimated Price (Buy)",
                    "Best Bid (Sell)", "Best Ask (Sell)", "Estimated Price (Sell)"
                ])

    def log_trade(self, trade: Trade):
        """
        Logs a completed trade to the CSV file.
        """
        if not trade.is_closed():
            logging.warning(f"Trade for {trade.symbol} not closed yet. Skipping logging.")
            return

        win_loss = "Win" if trade.pnl > 0 else "Loss"

        try:
            with open(self.log_file, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    trade.timestamp_buy, trade.buy_order_id, trade.timestamp_sell, trade.sell_order_id,
                    trade.symbol, trade.quantity, trade.buy_price, trade.sell_price, trade.pnl, win_loss,
                    trade.best_bid_buy, trade.best_ask_buy, trade.estimated_price_buy,
                    trade.best_bid_sell, trade.best_ask_sell, trade.estimated_price_sell
                ])

            logging.info(f"[SUCCESS] Trade logged: {trade.symbol}, PnL: {trade.pnl:.6f} ({win_loss})")

        except Exception as e:
            logging.error(f"[ERROR] Failed to log trade for {trade.symbol}: {e}")