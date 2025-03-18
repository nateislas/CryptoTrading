import os
import csv
import logging
from datetime import datetime
from typing import List, Optional
from trade import TrackedTrade, TradeStatus

class TradeManager:
    """
    Unifies trade persistence (tracking pending/open trades) and logging (closed trades)
    into a single CSV file.
    """
    def __init__(self, filename: Optional[str] = None):
        if filename is None:
            today_date = datetime.now().strftime("%Y-%m-%d")
            self.filename = f"logs/trade_execution/{today_date}/trades.csv"
        else:
            self.filename = filename
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        # Initialize CSV with header if file doesn't exist or is empty.
        if not os.path.exists(self.filename) or os.path.getsize(self.filename) == 0:
            with open(self.filename, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_fields())
                writer.writeheader()

    def csv_fields(self) -> List[str]:
        """Unified CSV header combining tracking and logging fields."""
        return [
            "buy_timestamp",
            "buy_order_id",
            "sell_timestamp",
            "sell_order_id",
            "symbol",
            "quantity",
            "buy_price",
            "sell_price",
            "pnl",
            "win_loss",
            "best_bid_buy",
            "best_ask_buy",
            "estimated_price_buy",
            "best_bid_sell",
            "best_ask_sell",
            "estimated_price_sell",
            "status"
        ]

    def trade_to_dict(self, trade: TrackedTrade) -> dict:
        """Converts a TrackedTrade object into a dictionary for CSV writing."""
        return {
            "buy_timestamp": trade.timestamp_buy.strftime("%Y-%m-%d %H:%M:%S") if trade.timestamp_buy else "",
            "buy_order_id": trade.buy_order_id,
            "sell_timestamp": trade.timestamp_sell.strftime("%Y-%m-%d %H:%M:%S") if trade.timestamp_sell else "",
            "sell_order_id": trade.sell_order_id if trade.sell_order_id else "",
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "buy_price": trade.buy_price,
            "sell_price": trade.sell_price if trade.sell_price is not None else "",
            "pnl": trade.pnl if trade.pnl is not None else "",
            "win_loss": "Win" if (trade.pnl is not None and trade.pnl > 0) else ("Loss" if trade.pnl is not None else ""),
            "best_bid_buy": trade.best_bid_buy,
            "best_ask_buy": trade.best_ask_buy,
            "estimated_price_buy": trade.estimated_price_buy,
            "best_bid_sell": trade.best_bid_sell if trade.best_bid_sell is not None else "",
            "best_ask_sell": trade.best_ask_sell if trade.best_ask_sell is not None else "",
            "estimated_price_sell": trade.estimated_price_sell if trade.estimated_price_sell is not None else "",
            "status": trade.status.value
        }

    def dict_to_trade(self, row: dict) -> TrackedTrade:
        """Converts a CSV row dictionary into a TrackedTrade object."""
        trade = TrackedTrade(
            symbol=row["symbol"],
            quantity=float(row["quantity"]),
            buy_order_id=row["buy_order_id"],
            buy_price=float(row["buy_price"]),
            best_bid=float(row["best_bid_buy"]),
            best_ask=float(row["best_ask_buy"]),
            estimated_price=float(row["estimated_price_buy"]),
            status=row["status"]
        )
        trade.timestamp_buy = datetime.strptime(row["buy_timestamp"], "%Y-%m-%d %H:%M:%S") if row["buy_timestamp"] else None
        trade.timestamp_sell = datetime.strptime(row["sell_timestamp"], "%Y-%m-%d %H:%M:%S") if row["sell_timestamp"] else None
        trade.sell_order_id = row["sell_order_id"] if row["sell_order_id"] else None
        trade.sell_price = float(row["sell_price"]) if row["sell_price"] not in ("", None) else None
        trade.best_bid_sell = float(row["best_bid_sell"]) if row["best_bid_sell"] not in ("", None) else None
        trade.best_ask_sell = float(row["best_ask_sell"]) if row["best_ask_sell"] not in ("", None) else None
        trade.estimated_price_sell = float(row["estimated_price_sell"]) if row["estimated_price_sell"] not in ("", None) else None
        trade.pnl = float(row["pnl"]) if row["pnl"] not in ("", None) else None
        return trade

    def load_trades(self):
        """
        Loads trades from CSV and separates them into lists for PENDING and OPEN statuses.
        CLOSED trades are preserved only as historical records.
        """
        pending_trades = []
        open_trades = []
        if not os.path.exists(self.filename):
            return pending_trades, open_trades
        with open(self.filename, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"] == TradeStatus.PENDING.value:
                    pending_trades.append(self.dict_to_trade(row))
                elif row["status"] == TradeStatus.OPEN.value:
                    open_trades.append(self.dict_to_trade(row))
        return pending_trades, open_trades

    def save_trades(self, pending_list: List[TrackedTrade], open_list: List[TrackedTrade]):
        """
        Persists the PENDING and OPEN trades while preserving already logged CLOSED trades.
        """
        closed_rows = []
        if os.path.exists(self.filename):
            with open(self.filename, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["status"] == TradeStatus.CLOSED.value:
                        closed_rows.append(row)
        with open(self.filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fields())
            writer.writeheader()
            for trade in pending_list:
                writer.writerow(self.trade_to_dict(trade))
            for trade in open_list:
                writer.writerow(self.trade_to_dict(trade))
            for row in closed_rows:
                writer.writerow(row)

    def log_trade(self, trade: TrackedTrade):
        """
        Logs a closed trade by appending it to the CSV.
        """
        if not trade.is_closed():
            logging.warning(f"Trade for {trade.symbol} not closed yet. Skipping logging.")
            return
        with open(self.filename, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fields())
            writer.writerow(self.trade_to_dict(trade))
        logging.info(f"[SUCCESS] Trade logged: {trade.symbol}, PnL: {trade.pnl} ({'Win' if trade.pnl and trade.pnl > 0 else 'Loss'})")