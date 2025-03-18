## trade_persistence_manager.py
import logging
import csv
import os
from enum import Enum
from typing import Optional, List
from trade import ExecutedTrade, TrackedTrade, TradeStatus
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradePersistenceManager:
    """
    A simple class to persist and retrieve trade states (PENDING, OPEN, CLOSED) from a CSV file.
    """

    def __init__(self, filename: str = "logs/trade_execution/open_trades.csv"):
        today_date = datetime.now().strftime("%Y-%m-%d")
        self.filename =  f"logs/trade_execution/{today_date}/open_trades.csv"
        # If file doesn't exist, create it with a header
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_fields())
                writer.writeheader()

    @staticmethod
    def csv_fields() -> List[str]:
        """Define the columns to store in CSV."""
        return [
            "symbol",
            "quantity",
            "buy_order_id",
            "buy_price",
            "best_bid_buy",
            "best_ask_buy",
            "estimated_price_buy",
            "sell_order_id",
            "sell_price",
            "best_bid_sell",
            "best_ask_sell",
            "estimated_price_sell",
            "status"
        ]

    def load_trades(self):
        """
        Loads all trades from CSV and separates them into lists
        for 'PENDING' and 'OPEN' statuses. (CLOSED can be loaded
        too if you want to keep a record, but we typically don't
        monitor them anymore.)
        """
        pending_list = []
        open_list = []

        with open(self.filename, mode='r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert the row dict into an ExtendedTrade
                trade_obj = self.dict_to_trade(row)

                if trade_obj.status == TradeStatus.PENDING:
                    pending_list.append(trade_obj)
                elif trade_obj.status == TradeStatus.OPEN:
                    open_list.append(trade_obj)
                # If it's CLOSED, you can either skip or store it if you want
                # for historical reference. We'll skip for now.

        return pending_list, open_list

    def save_trades(self, pending_list: List[TrackedTrade], open_list: List[TrackedTrade]):
        """
        Saves pending, open, and (optionally) closed trades to the CSV file.
        For simplicity, we'll store only PENDING + OPEN in the CSV, and let
        closed trades remain purely in logs or somewhere else.
        """
        # Read any existing CLOSED trades so we don't lose them
        closed_trades = []
        with open(self.filename, mode='r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"] == "CLOSED":
                    closed_trades.append(row)  # keep them as dict rows

        # Convert our pending & open trades to CSV rows
        pending_dicts = [self.trade_to_dict(t) for t in pending_list]
        open_dicts = [self.trade_to_dict(t) for t in open_list]

        # Re-write CSV with PENDING + OPEN + old CLOSED
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fields())
            writer.writeheader()

            # Write pending
            for pd in pending_dicts:
                writer.writerow(pd)

            # Write open
            for od in open_dicts:
                writer.writerow(od)

            # Write old closed trades
            for cd in closed_trades:
                writer.writerow(cd)

    @staticmethod
    def trade_to_dict(trade: TrackedTrade) -> dict:
        """Convert an ExtendedTrade object to a CSV row dictionary."""
        return {
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "buy_order_id": trade.buy_order_id,
            "buy_price": trade.buy_price,
            "best_bid_buy": trade.best_bid_buy,
            "best_ask_buy": trade.best_ask_buy,
            "estimated_price_buy": trade.estimated_price_buy,
            "sell_order_id": trade.sell_order_id,
            "sell_price": trade.sell_price,
            "best_bid_sell": trade.best_bid_sell,
            "best_ask_sell": trade.best_ask_sell,
            "estimated_price_sell": trade.estimated_price_sell,
            "status": trade.status.value  # Store the enum as a string
        }

    @staticmethod
    def dict_to_trade(row: dict) -> TrackedTrade:
        """Convert a CSV row dict into an ExtendedTrade object."""
        trade_obj = TrackedTrade(
            symbol=row["symbol"],
            quantity=float(row["quantity"]),
            buy_order_id=row["buy_order_id"],
            buy_price=float(row["buy_price"]),
            best_bid=float(row["best_bid_buy"]) if row["best_bid_buy"] else None,
            best_ask=float(row["best_ask_buy"]) if row["best_ask_buy"] else None,
            estimated_price=float(row["estimated_price_buy"]) if row["estimated_price_buy"] else None,
            status=row["status"]  # e.g. "PENDING", "OPEN", or "CLOSED"
        )
        # Fill in sell details if present
        trade_obj.sell_order_id = row["sell_order_id"] if row["sell_order_id"] else None
        trade_obj.sell_price = float(row["sell_price"]) if row["sell_price"] else None
        trade_obj.best_bid_sell = float(row["best_bid_sell"]) if row["best_bid_sell"] else None
        trade_obj.best_ask_sell = float(row["best_ask_sell"]) if row["best_ask_sell"] else None
        trade_obj.estimated_price_sell = float(row["estimated_price_sell"]) if row["estimated_price_sell"] else None

        return trade_obj