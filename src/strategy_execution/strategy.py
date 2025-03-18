## strategy.py

import numpy as np


class Strategy:
    def __init__(self, symbol, model, portfolio_value, max_capital_allocation=0.2, risk_per_trade=0.02,
                 daily_loss_limit=0.05):
        """
        Initialize the trading strategy.

        :param symbol: The asset symbol (e.g., 'DOGE-USD')
        :param model: A machine learning model (e.g., scikit-learn, PyTorch, etc.)
        :param portfolio_value: The total portfolio value in USD
        :param max_capital_allocation: Max percentage of portfolio allocated to trading (default: 20%)
        :param risk_per_trade: Max risk per trade as a percentage of portfolio value (default: 2%)
        :param daily_loss_limit: Max allowable loss per day as a percentage of portfolio value (default: 5%)
        """
        self.symbol = symbol
        self.model = model  # ML model for trade decision-making
        self.portfolio_value = portfolio_value  # Total account value in USD
        self.max_capital_allocation = max_capital_allocation  # Max capital used for trading (e.g., 20% of total)
        self.risk_per_trade = risk_per_trade  # Maximum loss per trade (e.g., 2% of total portfolio)
        self.daily_loss_limit = daily_loss_limit  # Max allowable loss per day

        # Track daily loss
        self.daily_loss = 0.0

    def calculate_position_size(self, entry_price):
        """
        Calculate the max position size for each trade based on the maximum loss per trade
        and the price of the asset.

        Uses position sizing formula:
            Position Size = (Risk Per Trade * Portfolio Value) / Stop-Loss Distance
        """

        # Define a stop-loss distance (can be dynamic based on volatility)
        stop_loss_distance = entry_price * 0.02  # Assume 2% stop loss

        # Max allowable risk per trade (e.g., 2% of portfolio)
        max_risk_dollars = self.risk_per_trade * self.portfolio_value

        # Position size (number of units to buy)
        position_size = max_risk_dollars / stop_loss_distance

        # Ensure we don't exceed max capital allocation
        max_trade_value = self.max_capital_allocation * self.portfolio_value
        max_units = max_trade_value / entry_price

        return min(position_size, max_units)  # Return the lesser of the two

    def should_enter(self, market_data) -> bool:
        """
        Uses the machine learning model to determine whether to enter a trade.
        :param market_data: Dictionary containing relevant market indicators (features)
        :return: True if entry conditions are met, else False
        """
        # Convert market data into model input format
        model_input = np.array([market_data["feature1"], market_data["feature2"]]).reshape(1, -1)

        # Predict using model (binary classification: 1 = Buy, 0 = No action)
        prediction = self.model.predict(model_input)

        return prediction == 1  # If model predicts 1, enter a trade

    def get_entry_details(self, market_data) -> dict:
        """
        Get trade entry details based on risk management and position sizing.

        :param market_data: Dictionary containing current price and indicators
        :return: Trade details dictionary
        """
        entry_price = market_data["current_price"]
        quantity = self.calculate_position_size(entry_price)

        return {
            "symbol": self.symbol,
            "quantity": quantity,
            "entry_price": entry_price
        }

    def should_exit(self, trade, market_data) -> bool:
        """
        Determines whether to exit a trade using predefined exit conditions.
        Uses a stop-loss or profit target approach.

        :param trade: The active trade object
        :param market_data: Dictionary containing latest price and indicators
        :return: True if exit conditions are met, else False
        """
        current_price = market_data["current_price"]

        # Stop-Loss Condition (fixed percentage loss)
        stop_loss_price = trade.buy_price * 0.98  # 2% stop-loss
        if current_price <= stop_loss_price:
            return True  # Exit trade to limit loss

        # Profit Target Condition (fixed percentage gain)
        profit_target_price = trade.buy_price * 1.05  # 5% profit target
        if current_price >= profit_target_price:
            return True  # Take profit

        return False  # Otherwise, hold position

    def update_daily_loss(self, pnl):
        """
        Track daily loss and enforce loss limit.
        """
        self.daily_loss += pnl
        if self.daily_loss < -self.daily_loss_limit * self.portfolio_value:
            logging.warning("Daily loss limit reached. No more trades for today.")
            return False  # Stop trading for the day
        return True  # Continue trading