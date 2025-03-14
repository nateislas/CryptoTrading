import time
import datetime
import pandas as pd
import os
from src.robinhood_api.api_access import CryptoAPITrading
from typing import List, Dict, Any
from src.robinhood_api.market_data import MarketData


class PortfolioMonitor:
    """
    Periodically monitors portfolio data and saves it to CSV files.
    (Simplified: No trade logging or execution summaries)
    """

    def __init__(self, api_trading_client: CryptoAPITrading, data_dir: str = "data"):
        self.api_trading_client = api_trading_client
        self.data_dir = data_dir
        self.account_data_dir = os.path.join(self.data_dir, "account")
        self._ensure_directories_exist()
        self.market_data_client = MarketData(api_trading_client.api_client)

    def _ensure_directories_exist(self):
        """
        Ensures that the necessary directories exist.
        """
        os.makedirs(self.account_data_dir, exist_ok=True)

    def _save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """
        Saves data to a CSV file, appending if the file exists.

        Args:
            data: The list of dictionaries to save.
            filename: The name of the CSV file.
        """
        filepath = os.path.join(self.account_data_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(filepath, mode="a", header=not os.path.exists(filepath), index=False)
        print(f"{datetime.datetime.now()} - Saved data to {filepath}")

    def get_account_info(self) -> dict:
        """
        Retrieves the account information.

        Returns:
            A dictionary containing the account information.
        """
        try:
            account_info = self.api_trading_client.account.get_account()
            return account_info
        except Exception as e:
            print(f"Error fetching account information: {e}")
            return {}

    def get_holdings(self) -> list[dict]:
        """
        Retrieves the current holdings.

        Returns:
            A list of dictionaries, where each dictionary represents a holding.
        """
        try:
            holdings_data = self.api_trading_client.account.get_holdings()
            # check if the data has results
            if "results" in holdings_data:
                holdings_list = holdings_data["results"]
                return holdings_list
            else:
                print("Error: No results field in get_holdings data.")
                return []
        except Exception as e:
            print(f"Error fetching holdings: {e}")
            return []

    def estimate_portfolio_value(self) -> float:
        """
        Estimates the total portfolio value based on current holdings.

        Returns:
            The estimated portfolio value as a float.
        """
        total_value = 0.0
        holdings = self.get_holdings()
        for holding in holdings:
            try:
                symbol = f"{holding['asset_code']}-USD"  # Construct symbol
                quantity = float(holding["total_quantity"])
                if quantity == 0:
                    continue

                # Use 'bid' side for a more conservative estimate
                real_time_price = self.market_data_client.get_real_time_price(
                    symbol=symbol, side="bid", quantity=1.0
                )
                if real_time_price is not None:
                    holding_value = quantity * real_time_price
                    total_value += holding_value
            except Exception as e:
                print(f"Error calculating value for {symbol}: {e}")

        return total_value

    def monitor(self):
        """
        Collects and saves account, holdings, and portfolio value data.
        """
        print(f"{datetime.datetime.now()} - Monitoring portfolio...")
        try:
            account_info = self.get_account_info()
            if account_info:
                self._save_to_csv([account_info], "account_info.csv")

            holdings = self.get_holdings()
            if holdings:
                self._save_to_csv(holdings, "holdings.csv")

            portfolio_value = self.estimate_portfolio_value()
            if portfolio_value is not None:
                self._save_to_csv([{"portfolio_value": portfolio_value}], "portfolio_value.csv")
        except Exception as e:
            print(f"{datetime.datetime.now()} - An error occurred during monitoring: {e}")

    def run_continuously(self, interval_seconds: int = 120):
        """
        Runs the monitoring process continuously at a specified interval.

        Args:
            interval_seconds: The interval between monitoring runs in seconds (default: 120 seconds = 2 minutes).
        """
        while True:
            self.monitor()
            time.sleep(interval_seconds)


# Example usage (for testing):
if __name__ == "__main__":
     api_trading_client = CryptoAPITrading()
     monitor = PortfolioMonitor(api_trading_client)
     monitor.run_continuously()